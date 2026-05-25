from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from rag.retriever import query_rag
from mcp_server.db_tools import search_database, get_record
from mcp_server.action_tools import send_email, create_ticket
from mcp_server.complex_tools import get_stripe_status, get_shopify_order, schedule_calendar_event
from agent.logging_config import log_tool_use

@tool
def search_company_documents(query: str):
    """
    Search private company documents (refund policy, company info, etc.) 
    to answer questions. Use this whenever the user asks about rules, 
    policies, or internal information.
    """
    results = query_rag(query)
    log_tool_use("search_company_documents", {"query": query}, str(results))
    if not results:
        return "No relevant information found in documents."
    return "\n\n".join(results)

@tool
def search_customer_db(query: str):
    """
    Search for customer records in the database by name or email.
    """
    result = str(search_database(query))
    log_tool_use("search_customer_db", {"query": query}, result)
    return result

@tool
def get_customer_details(customer_id: str):
    """
    Get all details for a specific customer using their unique ID.
    """
    try:
        customer_id = int(customer_id)
    except ValueError:
        pass
    result = str(get_record(customer_id))
    log_tool_use("get_customer_details", {"customer_id": customer_id}, result)
    return result

@tool
def send_automated_email(to_email: str, subject: str, body: str):
    """
    Send an email to a recipient. Use this for notifications or sending 
    requested information to users.
    """
    result = str(send_email(to_email, subject, body))
    log_tool_use("send_automated_email", {"to_email": to_email, "subject": subject}, result)
    return result

@tool
def log_support_ticket(title: str, description: str):
    """
    Create a new support ticket to track an issue or request.
    """
    result = str(create_ticket(title, description))
    log_tool_use("log_support_ticket", {"title": title}, result)
    return result

@tool
def web_search(query: str):
    """
    Search the real-time internet for information not found in internal 
    company documents. Use this for current events, news, general facts, 
    or legal/tax updates.
    """
    search = DuckDuckGoSearchRun()
    result = search.run(query)
    log_tool_use("web_search", {"query": query}, result)
    return result

@tool
def check_stripe_payment(customer_email: str):
    """
    Check a customer's payment status and history on Stripe.
    """
    result = str(get_stripe_status(customer_email))
    log_tool_use("check_stripe_payment", {"email": customer_email}, result)
    return result

@tool
def track_shopify_order(order_id: str):
    """
    Retrieve the status and tracking info for a Shopify order.
    """
    result = str(get_shopify_order(order_id))
    log_tool_use("track_shopify_order", {"order_id": order_id}, result)
    return result

@tool
def book_calendar_meeting(title: str, date_time: str):
    """
    Book a new meeting in the company calendar.
    """
    result = str(schedule_calendar_event(title, date_time))
    log_tool_use("book_calendar_meeting", {"title": title, "time": date_time}, result)
    return result

# List of tools to be used by the agent
tools = [
    search_company_documents,
    search_customer_db,
    get_customer_details,
    send_automated_email,
    log_support_ticket,
    web_search,
    check_stripe_payment,
    track_shopify_order,
    book_calendar_meeting
]
