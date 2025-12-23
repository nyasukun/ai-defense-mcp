
import asyncio
import argparse
import sys
import logging
from typing import Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response
import uvicorn

from src.tools.guardrails import setup_ai_defense_guardrails
from src.tools.events import get_ai_defense_events, get_ai_defense_event_details
from src.tools.validation import start_ai_validation, get_ai_validation_status

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("ai-defense-mcp")

# Initialize MCP Server
# This server exposes tools to manage AI Defense resources and run validations.
app = Server("ai-defense-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="setup_ai_defense_guardrails",
            description="Sets up AI Defense guardrails (Application, Connection, Policies) for an application.",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_name": {"type": "string", "description": "Name of the application to protect."},
                    "description": {"type": "string", "description": "Description of the application."},
                    "target_system_description": {"type": "string", "description": "Optional description of the target system."},
                    "policy_name": {"type": "string", "description": "Name of the Policy to associate. If not provided, lists available policies."}
                },
                "required": ["application_name"]
            }
        ),
        Tool(
            name="get_ai_defense_events",
            description="Lists security events from AI Defense.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20, "description": "Number of events to retrieve."},
                    "offset": {"type": "integer", "default": 0, "description": "Pagination offset."}
                }
            }
        ),
        Tool(
            name="get_ai_defense_event_details",
            description="Retrieves details of a specific security event, optionally with conversation history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The ID of the event."},
                    "include_conversation": {"type": "boolean", "default": False, "description": "Whether to include conversation history."}
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="start_ai_validation",
            description="Starts an AI validation/compliance scan against a model endpoint. Please provide any necessary headers (e.g., authentication) required to access the model endpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "validation_scan_name": {"type": "string", "description": "Name for the validation scan."},
                    "model_endpoint": {"type": "string", "description": "The full URL of the model endpoint to test."},
                    "application_id": {"type": "string", "description": "Optional Application ID to associate with."},
                    "headers": {
                        "type": "object", 
                        "additionalProperties": {"type": "string"},
                        "description": "Headers required for the model endpoint (e.g. {'Authorization': 'Bearer <OpenAI Key>'})."
                    },
                    "model_request_template": {"type": "string", "description": "Optional: JSON template for model request. Auto-configured for OpenAI if omitted. Use {{prompt}} as placeholder."},
                    "model_provider": {"type": "string", "description": "Optional: Name of the model provider (e.g. 'OpenAI'). Auto-configured for OpenAI."},
                    "model_response_json_path": {"type": "string", "description": "Optional: JSONPath to extract text from response. Auto-configured for OpenAI (e.g. 'choices.0.message.content')."},
                    "system_prompt": {"type": "string", "description": "Optional: If you can find the system prompt used in the user's application code, provide it here. It will be used in the validation request template."}
                },
                "required": ["validation_scan_name", "model_endpoint"]
            }
        ),
        Tool(
            name="get_ai_validation_status",
            description="Checks the status of a running AI validation job.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The Task ID returned by start_ai_validation."}
                },
                "required": ["task_id"]
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    try:
        if name == "setup_ai_defense_guardrails":
            result = await setup_ai_defense_guardrails(
                application_name=arguments["application_name"],
                description=arguments.get("description", "Protecting AI Chat Application"),
                target_system_description=arguments.get("target_system_description"),
                policy_name=arguments.get("policy_name")
            )
        elif name == "get_ai_defense_events":
            result = await get_ai_defense_events(
                limit=arguments.get("limit", 20),
                offset=arguments.get("offset", 0)
            )
        elif name == "get_ai_defense_event_details":
            result = await get_ai_defense_event_details(
                event_id=arguments["event_id"],
                include_conversation=arguments.get("include_conversation", False)
            )
        elif name == "start_ai_validation":
            result = await start_ai_validation(
                validation_scan_name=arguments["validation_scan_name"],
                model_endpoint=arguments["model_endpoint"],
                application_id=arguments.get("application_id"),
                headers=arguments.get("headers"),
                model_request_template=arguments.get("model_request_template"),
                model_provider=arguments.get("model_provider"),
                model_response_json_path=arguments.get("model_response_json_path"),
                system_prompt=arguments.get("system_prompt")
            )
        elif name == "get_ai_validation_status":
            result = await get_ai_validation_status(
                task_id=arguments["task_id"]
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def run_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

async def run_sse():
    from mcp.server.sse import SseServerTransport
    
    sse = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
            
    async def handle_messages(request: Request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )
    
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def main():
    parser = argparse.ArgumentParser(description="AI Defense MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport mode: stdio or sse")
    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio())
    else:
        asyncio.run(run_sse())

if __name__ == "__main__":
    main()
