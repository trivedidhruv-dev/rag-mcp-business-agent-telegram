import sys
import os
from dotenv import load_dotenv
import socket

# Force IPv4 for all connections (Fixes httpx.ConnectTimeout on Hugging Face Spaces for Telegram API)
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_interface.bot import application, setup_bot
from mcp_server.db_tools import init_db

if __name__ == "__main__":
    load_dotenv()
    
    # Initialize the database table if it doesn't exist
    print("Initializing database...")
    init_db()
    
    # Check for keys
    if not os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") == "your_telegram_bot_token_here":
        print("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)
        
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        print("WARNING: GROQ_API_KEY environment variable not set. LLM features will fail.")

    print("--- 🤖 RAG + MCP Business Agent Starting ---")
    
    # Render requires a web server to bind to a port for 'Web Service' plan.
    # We add a tiny health check server in a background thread.
    from fastapi import FastAPI
    import uvicorn
    import threading

    web_app = FastAPI()

    @web_app.get("/")
    def health():
        return {"status": "ok"}

    def run_server():
        port = int(os.getenv("PORT", 8080))
        uvicorn.run(web_app, host="0.0.0.0", port=port)

    # Start health check server
    print(f"Starting health check server on port {os.getenv('PORT', 8080)}...")
    threading.Thread(target=run_server, daemon=True).start()

    # In Phase 1, we just run the bot. 
    try:
        if not application:
            print("Initializing bot setup...")
            application = setup_bot()
            
        if application:
            print("Bot is starting up... Press Ctrl+C to stop.")
            application.run_polling(drop_pending_updates=True)
        else:
            print("Failed to initialize bot. Check your TOKEN in .env")
    except KeyboardInterrupt:
        print("\nAgent shutting down...")
    except Exception as e:
        print(f"Error: {e}")

