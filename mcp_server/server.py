from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio
import asyncio
import sys

# Increase recursion depth limit for complex tool calls
sys.setrecursionlimit(2000)

from mcp_server.db_tools import search_database, get_record, init_db
from mcp_server.action_tools import send_email, create_ticket
from mcp_server.complex_tools import get_stripe_status, get_shopify_order, schedule_calendar_event

# Initialize the MCP Server
server = Server("business-agent-mcp")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available business tools."""
    return [
        Tool(
            name="search_database",
            description="Search for customer records by name or email.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name or email fragment to search for."}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_record",
            description="Get a specific customer record by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "The unique ID of the customer."}
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="send_email",
            description="Send an email to a customer or team member.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "Recipient email address."},
                    "subject": {"type": "string", "description": "Email subject line."},
                    "body": {"type": "string", "description": "The message body."}
                },
                "required": ["to_email", "subject", "body"]
            }
        ),
        Tool(
            name="create_ticket",
            description="Create a support ticket or log an issue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Brief title of the issue."},
                    "description": {"type": "string", "description": "Detailed description of the issue."}
                },
                "required": ["title", "description"]
            }
        ),
        Tool(
            name="get_stripe_status",
            description="Check the payment status and history of a customer on Stripe.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_email": {"type": "string", "description": "The email of the customer to check."}
                },
                "required": ["customer_email"]
            }
        ),
        Tool(
            name="get_shopify_order",
            description="Get the status and tracking number of a Shopify order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The Shopify order ID (e.g., #1234)."}
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="schedule_calendar_event",
            description="Schedule a new meeting or event in Google Calendar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the meeting."},
                    "date_time": {"type": "string", "description": "The requested date and time."}
                },
                "required": ["title", "date_time"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Execute a tool and return the result as text."""
    if not arguments:
        return [TextContent(type="text", text="No arguments provided.")]

    try:
        if name == "search_database":
            result = search_database(arguments.get("query", ""))
            return [TextContent(type="text", text=str(result))]
        
        elif name == "get_record":
            result = get_record(arguments.get("customer_id", 0))
            return [TextContent(type="text", text=str(result))]
        
        elif name == "send_email":
            result = send_email(
                arguments.get("to_email", ""),
                arguments.get("subject", ""),
                arguments.get("body", "")
            )
            return [TextContent(type="text", text=str(result))]
        
        elif name == "create_ticket":
            result = create_ticket(
                arguments.get("title", ""),
                arguments.get("description", "")
            )
            return [TextContent(type="text", text=str(result))]
        
        elif name == "get_stripe_status":
            result = get_stripe_status(arguments.get("customer_email", ""))
            return [TextContent(type="text", text=str(result))]
        
        elif name == "get_shopify_order":
            result = get_shopify_order(arguments.get("order_id", ""))
            return [TextContent(type="text", text=str(result))]
        
        elif name == "schedule_calendar_event":
            result = schedule_calendar_event(
                arguments.get("title", ""),
                arguments.get("date_time", "")
            )
            return [TextContent(type="text", text=str(result))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    # Initialize the database before starting the server
    init_db()
    # Run server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
