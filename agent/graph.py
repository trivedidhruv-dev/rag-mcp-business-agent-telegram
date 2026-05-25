import os
from typing import Annotated, TypedDict, Union
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from agent.tools import tools
from agent.logging_config import log_agent_action, log_tool_use

load_dotenv()

# Define the state of the graph
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

_model_instance = None

# 1. Initialize the LLM with tool support
def get_model():
    global _model_instance
    if _model_instance is None:
        print("Initializing LLM Model (Singleton)...")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        
        llm = ChatGroq(
            api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0
        )
        _model_instance = llm.bind_tools(tools)
    return _model_instance

# 2. Define the nodes
def call_model(state: State):
    messages = state['messages']
    # Add a system prompt if it's the first message
    if not any(isinstance(m, SystemMessage) for m in messages):
        system_msg = SystemMessage(content=(
            "You are a powerful RAG + MCP Business Agent. "
            "You have access to company documents (RAG), customer databases (MCP), real-time web search, and email tools. "
            "You can also check Stripe payments, track Shopify orders, and schedule meetings in Google Calendar. "
            "Always use the appropriate tools to answer questions accurately. "
            "If a user asks about a policy, search the documents. "
            "If they ask about customers, search the database. "
            "If they ask about payments or orders, use the Stripe or Shopify tools. "
            "If they want to schedule something, use the Calendar tool. "
            "If they ask about current events, news, or general information not in documents, use the web search tool. "
            "If they want to send an email or log a ticket, use those tools. If no email address is specified, use 'defoperator28@gmail.com' as the default recipient. "
            "IMPORTANT: If the user asks you to send information (like a Stripe payment) to an email, you must FIRST use the appropriate tool to get that information, and THEN use the send_automated_email tool to send it. Make sure you actually call the email tool and tell the user when you have done so."
            "Be professional and concise."
        ))
        messages = [system_msg] + messages
    else:
        # Truncate context to save memory and speed up TTFT: keep system prompt + last 10 messages
        system_msg = next(m for m in messages if isinstance(m, SystemMessage))
        other_messages = [m for m in messages if not isinstance(m, SystemMessage)]
        messages = [system_msg] + other_messages[-10:]
        
    model = get_model()
    response = model.invoke(messages)
    
    # Log the LLM's decision
    if response.tool_calls:
        for tool_call in response.tool_calls:
            log_agent_action("LLM DECIDED TOOL USE", f"Tool: {tool_call['name']}")
    else:
        log_agent_action("LLM REPLIED DIRECTLY")
        
    return {"messages": [response]}

# 3. Define the Router (Conditional Edge)
def should_continue(state: State) -> str:
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 4. Build the Graph
workflow = StateGraph(State)

# Add Nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Set Entry Point
workflow.set_entry_point("agent")

# Add Edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
)
workflow.add_edge("tools", "agent")

# 5. Add Persistence
memory = MemorySaver()

# Compile without interrupt so it runs autonomously
agent_app = workflow.compile(
    checkpointer=memory
)

async def get_response(user_input: str, thread_id: str = "default"):
    """
    Entry point for the Telegram bot to interact with the LangGraph agent.
    """
    log_agent_action("USER MESSAGE RECEIVED", f"Thread: {thread_id} | Input: {user_input}")
    
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    config = {"configurable": {"thread_id": thread_id}}
    
    final_state = await agent_app.ainvoke(initial_state, config=config)
    
    ai_response = final_state['messages'][-1].content
    log_agent_action("AGENT RESPONSE GENERATED", f"Output length: {len(ai_response)}")
    
    # Return the content of the last AI message
    return ai_response

if __name__ == "__main__":
    # Test script for local debugging (non-async version for quick check)
    import asyncio
    
    async def test():
        print("Testing Agent Loop...")
        resp = await get_response("Who is Alice Smith?")
        print(f"Agent: {resp}")
        
    asyncio.run(test())
