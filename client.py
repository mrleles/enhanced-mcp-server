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
