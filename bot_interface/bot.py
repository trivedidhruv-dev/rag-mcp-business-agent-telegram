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
        "/ingest - Manually trigger document ingestion"
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    thread_id = str(chat_id)
    
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # 1. Start/Continue Agent
        response = await get_response(user_text, thread_id=thread_id)
        
        # 2. Check for Interrupt (HITL)
        state = await agent_app.aget_state({"configurable": {"thread_id": thread_id}})
        
        if state.next:  # If the graph is paused at "tools"
            last_msg = state.values["messages"][-1]
            tool_call = last_msg.tool_calls[0]
            tool_name = tool_call["name"]
            
            # For now, let's require approval for ALL tools to show the flow, 
            # or specifically for email. Let's do all for maximum "Wow" factor.
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{thread_id}"),
                    InlineKeyboardButton("❌ Stop", callback_data=f"stop_{thread_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            approval_msg = (
                f"🛡️ **Action Required**\n"
                f"The agent wants to use: `{tool_name}`\n"
                f"Details: `{tool_call['args']}`\n\n"
                "Should I proceed?"
            )
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=approval_msg,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # Normal response if no tool call was pending
            await context.bot.send_message(chat_id=chat_id, text=response)
            
    except Exception as e:
        logging.error(f"Error in handle_message: {e}")
        traceback.print_exc()
        await context.bot.send_message(chat_id=chat_id, text=f"Error: {e}")

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user clicking Approve/Stop buttons."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, thread_id = data.split("_")
    
    try:
        if action == "approve":
            await query.edit_message_text("✅ Approved! Processing...")
            # Resume the agent
            config = {"configurable": {"thread_id": thread_id}}
            # Resuming with None tells LangGraph to just proceed with existing state
            final_state = await agent_app.ainvoke(None, config=config)
            
            # Send the final response
            ai_response = final_state["messages"][-1].content
            await context.bot.send_message(chat_id=query.message.chat_id, text=ai_response)
            
        else:
            await query.edit_message_text("❌ Action stopped by user.")
            # To "cancel", we inject a fake tool error message so the agent stops or reacts
            state = await agent_app.aget_state({"configurable": {"thread_id": thread_id}})
            last_msg = state.values["messages"][-1]
            tool_call_id = last_msg.tool_calls[0]["id"]
            
            cancel_msg = ToolMessage(
                tool_call_id=tool_call_id,
                content="Action cancelled by user approval check."
            )
            
            # Resume with the cancellation message
            await agent_app.ainvoke({"messages": [cancel_msg]}, config={"configurable": {"thread_id": thread_id}})
            await context.bot.send_message(chat_id=query.message.chat_id, text="Agent has been informed the action was cancelled.")

    except Exception as e:
        logging.error(f"Error in handle_approval: {e}")
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"Resumption error: {e}")

application = None

def setup_bot():
    global application
    if not TOKEN or TOKEN == "your_telegram_bot_token_here":
        print("Error: TELEGRAM_BOT_TOKEN not found in Environment Variables")
        return None
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help_command)
    status_handler = CommandHandler('status', status_command)
    ingest_handler = CommandHandler('ingest', ingest_command)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    approval_handler = CallbackQueryHandler(handle_approval)
    
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(status_handler)
    application.add_handler(ingest_handler)
    application.add_handler(message_handler)
    application.add_handler(approval_handler)
    return application

if __name__ == '__main__':
    app = setup_bot()
    if app:
        print("Bot is starting...")
        app.run_polling()
else:
    # When imported
    application = setup_bot()
