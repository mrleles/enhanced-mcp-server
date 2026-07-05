import asyncio
import sys
import jsonfrom urllib.parse import quote
from typing import Optional, Dict, Any, List, Union
from contextLib import AsyncExitStack

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult

from anthropic import Anthropic
from dotenv import load_dotenv

MODEL_ID = "claude-sonnet-4-5-20250929"

class MCPClient:
    """MCP (Model Context Protocol) client for interacting with MCP servers and Claude.
    This client manages connections to MCP servers, handles tools execution, and provides an interactive interface for querying Claude with MCP tools."""

    def __init__(self) -> None:
        """Initialize the MCP client with session management and Anthropic API client.

        Sets up:
            - AsyncExitStack for managing async context managers
            - Anthropic client for Claude API interactions
        """
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server via stdio transport.

        Establishes a connection to an MCP server by launching the server script
        as a subprocess and communicating via stdin/stdout.

        Args:
            server_script_path: Path to the server script (.py, .js, or .ts file)

        Raises:
            ValueError: If server_script_path is not a .py, .js, or .ts file
        """
        # Determine script type based on file extension
        is_python = server_script_path.endswith('.py')
        is_ts = server_script_path.endswith('.ts')
        is_js = server_script_path.endswith('.js')

        if not (is_python or is_ts or is_js):
            raise ValueError("Server script must be a .py, .js, or .ts file")

        self.client = Client(
            server_script_path,
            elicitation_handler=self.handle_elicitation,
            progress_handler=self.handle_progress,
            message_handler=self.handle_message
        )

        await self.exit_stack.enter_async_context(self.client)

    async def handle_elicitation(self, message: str, response_type: type, params, context):
        """
        Handle elicitation request from the MCP server.
        When the server needs user input, this handler prompts the user, collects their response, and returns it in the expected format.
        Args:
            message: The question or prompt from the server
            response_type: Pydantic model defining the expected response structure
            params: Additional parameters for the elicitation
            context: Elicitation context information
        Returns:
            ElicitResult with action="decline" if no response, or response_type instance with user input
        """
        print(f"Server asks: {message}")

        user_data = {}
        for field_name, field_type in response_type.__annotations__.items():
            user_input = input(f"Enter value for '{field_name}' ({field_type.__name__}): ").strip()
            if not user_input:
                return ElicitResult(action="decline")

            user_data[field_name] = user_input

        return response_type(**user_data)

    async def handle_progress(self, progress: float, total: float | None, message: str | None) -> None:
        """
        Handle progress notifications from the MCP server.
        Displays progress updates to the user, showing percentage complete if no total is provide.
        Args:
            progress: Current progress value
            total: Total expected progress value (None if unknown)
            message: Optional descriptive message about current progress
        """
        if total is not None:
            percentage = (progress / total) * 100
            print(f"Progress: {percentage:.1f}% - {message or ''}")
        else:
            print(f"Progress: {progress} - {message or ''}")


    async def handle_message(self, message):
        """
        Handle notification messages from the MCP server.
        Processes server notifications such as tool list changes or resource updates and displays appropriate messages to the user.
        Args:
            message: MCP notification message from the server
        """
        if hasattr(message, 'root'):
            method = message.root.method
            print(f"Received: {method}")

            if method == "notifications/tools/list_changed":
                print("Tools have changed - might want to refresh tool cache")
            elif method == "notifications/resources/list_changed":
                print("Resources have changed")
