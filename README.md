# RAG + MCP Business Agent

> An autonomous, production-ready AI assistant for Telegram — powered by LangGraph, Groq (Llama 3.3 70B), ChromaDB, and the Model Context Protocol.

![Business Agent Logo](./business_agent_logo.png)

---

## Overview

This project is a fully autonomous business AI agent that runs inside Telegram. It combines **Retrieval-Augmented Generation (RAG)** for private document knowledge with a comprehensive **MCP (Model Context Protocol) toolset** for real-world business actions.

The agent reasons step-by-step using a LangGraph state machine, decides which tools to call, executes them, and responds — all without manual prompting or hard-coded logic.

---

## Features

| Capability | Details |
|---|---|
| 🧠 **Autonomous Reasoning** | LangGraph + Llama 3.3 70B agent loop with multi-step tool chaining |
| 📚 **RAG Knowledge Base** | ChromaDB vector store with Hugging Face Inference API embeddings |
| 🗄️ **Customer Database** | SQLite-backed MCP tool for searching and retrieving customer records |
| 📧 **Email Automation** | Gmail SMTP via App Passwords — sends structured emails on demand |
| 🎫 **Support Ticketing** | Logs and tracks support issues to a local ticket file |
| 🌐 **Real-Time Web Search** | DuckDuckGo integration for live internet queries |
| 💳 **Stripe Payments** | Check customer payment status and history |
| 🛒 **Shopify Orders** | Retrieve order status and shipment tracking numbers |
| 📅 **Calendar Scheduling** | Book and log meetings in the company calendar |
| 💾 **Persistent Memory** | Per-user conversation memory with session refresh support |
| 📝 **Audit Logging** | Every agent action and tool call is logged to `agent.log` |
| ⚡ **Health Check Server** | Built-in FastAPI server for Render/cloud deployment health checks |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot Interface                │
│              (python-telegram-bot v21+)                 │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  LangGraph Agent Loop                   │
│    ┌──────────┐   tools?   ┌──────────────────────┐     │
│    │  agent   │ ─────────► │     ToolNode (MCP)   │     │
│    │ (Llama3) │ ◄───────── │  (runs tool, loops)  │     │
│    └──────────┘            └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
          │                            │
          ▼                            ▼
┌──────────────────┐       ┌──────────────────────────────┐
│   ChromaDB (RAG) │       │        MCP Toolset           │
│  HuggingFace API │       │  DB │ Email │ Stripe │ etc.  │
└──────────────────┘       └──────────────────────────────┘
```

**Flow:** User sends a message → Bot forwards it to the LangGraph agent → Agent invokes the LLM → LLM decides which tools (if any) to call → Tools execute and return results → LLM formulates a final response → Bot replies to the user.

---

## Project Structure

```
.
├── main.py                  # Entry point — starts bot + health check server
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image for Render deployment
├── render.yaml              # Render service configuration
├── Procfile                 # Process file (fallback)
│
├── agent/
│   ├── graph.py             # LangGraph state machine & agent loop
│   ├── tools.py             # Tool definitions exposed to the LLM
│   └── logging_config.py    # Structured audit logger
│
├── bot_interface/
│   └── bot.py               # Telegram handlers, commands, session management
│
├── rag/
│   ├── ingest.py            # Document loader, splitter & ChromaDB ingestion
│   ├── retriever.py         # Vector store singleton & RAG query function
│   └── documents/           # Place your PDF / TXT files here
│
├── mcp_server/
│   ├── db_tools.py          # SQLite customer database tools
│   ├── action_tools.py      # Email (Gmail SMTP) & support ticket tools
│   └── complex_tools.py     # Stripe, Shopify & Calendar simulations
│
├── chroma_db/               # Persisted ChromaDB vector store
├── business_agent.db        # SQLite customer database
├── tickets.txt              # Support ticket log
└── agent.log                # Agent action audit log
```

---

## Prerequisites

- Python **3.10+**
- A [Groq API Key](https://console.groq.com/) (free tier available)
- A [Telegram Bot Token](https://t.me/BotFather)
- A [Hugging Face API Token](https://huggingface.co/settings/tokens) (free tier available)
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) configured

---

## Local Setup

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd business-agent-telegram
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_api_token

# Required for email sending
GMAIL_SENDER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
```

> **Note:** For `GMAIL_APP_PASSWORD`, you must enable 2-Factor Authentication on your Google account and then generate an [App Password](https://myaccount.google.com/apppasswords). Your regular Gmail password will not work.

### 3. Add Your Documents (Optional)

Place any `.pdf` or `.txt` files you want the agent to know about into the `rag/documents/` folder.

### 4. Start the Agent

```bash
python main.py
```

The bot will automatically initialize the database on first start. To load your documents into the knowledge base, send `/ingest` in Telegram.

---

## Telegram Commands

| Command | Description |
|---|---|
| `/start` | Initialize the agent and see the welcome message |
| `/help` | List all available commands |
| `/status` | Check system health (Database, Documents, LLM, Agent) |
| `/ingest` | Trigger a refresh of the RAG knowledge base from the `documents/` folder |
| `/refresh` | Clear the bot's conversation memory and start a fresh session |

### Example Prompts

```
"What is our refund policy?"
"Search the database for customer Alice."
"Check the Stripe payment status for bob@example.com."
"Send the payment details for bob@example.com to my email."
"Track Shopify order #10024."
"Book a meeting called 'Q3 Review' for tomorrow at 3 PM."
"Search the web for the latest AI regulations news."
"Log a support ticket: user cannot reset their password."
```

---

## Deployment on Render

This project is pre-configured for deployment on [Render](https://render.com/) as a **Web Service** using Docker.

### Steps

1. Push your code to a GitHub repository.
2. Create a new **Web Service** on Render and connect your repository.
3. Render will automatically detect the `Dockerfile` and build the image.
4. Add the following **Environment Variables** in the Render dashboard under **Environment**:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `GROQ_API_KEY` | Your Groq API key |
| `HF_TOKEN` | Your Hugging Face API token |
| `GMAIL_SENDER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Your Gmail App Password |

5. Deploy. Once the build completes and the service is live, send `/ingest` in Telegram to populate the knowledge base.

> **Important:** Document ingestion must be triggered via the `/ingest` Telegram command after deployment — do not rely on local ingestion, as the Render file system is ephemeral and the ChromaDB data must be built within the running container.

---

## Technology Stack

| Component | Technology |
|---|---|
| LLM | Groq — Llama 3.3 70B Versatile |
| Agent Framework | LangGraph |
| Embeddings | Hugging Face Inference API (`sentence-transformers/all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB |
| Bot Framework | python-telegram-bot v21 |
| Database | SQLite |
| Web Server | FastAPI + Uvicorn |
| Deployment | Render (Docker) |

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.
