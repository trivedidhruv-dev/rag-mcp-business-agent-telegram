import asyncio
import logging
import os
import traceback
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from agent.graph import get_response, agent_app
from rag.ingest import ingest_documents
from mcp_server.db_tools import search_database
from langchain_core.messages import ToolMessage

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Keep track of active sessions to allow users to "refresh" their memory
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🤖 Hello! I am your RAG + MCP Business Agent. How can I help you today?"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/status - Check agent system status\n"
        "/ingest - Manually trigger document ingestion\n"
        "/refresh - Clear the bot's memory and start a fresh conversation"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reports system status."""
    try:
        # Check DB
        db_check = search_database("Alice")
        db_status = "✅ Connected" if db_check else "⚠️ DB Empty"
        
        # Check Docs
        docs_path = os.path.join(os.getcwd(), "rag", "documents")
        if os.path.exists(docs_path):
            doc_count = len([f for f in os.listdir(docs_path) if f.endswith(('.pdf', '.txt'))])
        else:
            doc_count = 0
        
        status_text = (
            "📊 System Status:\n" 
            f"- Database: {db_status}\n"
            f"- Documents Found: {doc_count}\n"
            "- AI Model: Groq Llama 3.3\n"
            "- Agent Loop: LangGraph Active"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=status_text)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error checking status: {e}")

async def ingest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers document ingestion."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="📥 Starting document ingestion... please wait.")
    try:
        # Run ingestion in a separate thread to not block the bot
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ingest_documents)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Ingestion complete! The agent is now updated with new documents.")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Ingestion failed: {e}")

async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refreshes the user's session by changing their LangGraph thread_id."""
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = user_sessions.get(chat_id, 0) + 1
    await context.bot.send_message(
        chat_id=chat_id, 
        text="🔄 Session refreshed! I have cleared my memory of our previous conversation. How can I help you now?"
    )async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Generate a unique thread ID based on the user's current session
    session_id = user_sessions.get(chat_id, 0)
    thread_id = f"{chat_id}_{session_id}"
    
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # 1. Start/Continue Agent
        response = await get_response(user_text, thread_id=thread_id)
        
        # 2. Send Response
        if response:
            await context.bot.send_message(chat_id=chat_id, text=response)
            
    except Exception as e:
        logging.error(f"Error in handle_message: {e}")
        traceback.print_exc()
        await context.bot.send_message(chat_id=chat_id, text=f"Error: {e}")



application = None

def setup_bot():
    global application
    if not TOKEN or TOKEN == "your_telegram_bot_token_here":
        print("Error: TELEGRAM_BOT_TOKEN not found in Environment Variables")
        return None
        
    from telegram.request import HTTPXRequest
    
    # Configure custom HTTPX request to bypass broken system proxies in HF Spaces
    request = HTTPXRequest(
        connection_pool_size=8,
        proxy=None, # Explicitly ignore any HF proxy environment variables
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0
    )
    
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .request(request)
        .build()
    )    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help_command)
    status_handler = CommandHandler('status', status_command)
    ingest_handler = CommandHandler('ingest', ingest_command)
    refresh_handler = CommandHandler('refresh', refresh_command)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(status_handler)
    application.add_handler(ingest_handler)
    application.add_handler(refresh_handler)
    application.add_handler(message_handler)
    return application

if __name__ == '__main__':
    app = setup_bot()
    if app:
        print("Bot is starting...")
        app.run_polling()
else:
    # When imported
    application = setup_bot()
