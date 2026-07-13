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

# Fetching from MCP server
async def _get_tools(self) -> List[Dict[str, Any]]:
    """Retrieve available tools from the MCP server.
    Fetches the list of tools exposed by the server and formats them for use with the Claude API.
    Returns:
    List of tool definitions with name, description, and input schema
    """
    tools_response = await self.client.list_tools()

    tools = [
        {
            "name": tool.name,
            "description": tool.description or "MCP Tool",
            "input_schema": tool.inputSchema,
        }
        for tool in tools_response
    ]

    return tools

async def _get_prompts(self):
    """Retrieve available prompts from the MCP server.
    Returns:
        PromptsResponse containing available prompt templates
    """

    prompts_response = await self.client.list_prompts()
    return prompts_response

async def _get_resources(self):
    """Retrieve available resources from the MCP server.
    Returns:
        ResourcesResponse containing available resources
    """
    resources_response = await self.client.list_resources()
    return resources_response

async def _get_resource_templates():
    """Retrieve available resource templates from the MCP server.
    Returns:
        ResourceTemplatesResponse containing available resource templates
    """
    resource_templates_response = await self.client.list_resource_templates()
    return resource_templates_response

async def process_query(self, query: str) -> str:
    """Process a query using Claude with access to MCP server tools.
    Implements an agentic loop where Claude can use MCP tools to answer the query. The loop continues until Claude provides a final response without requesting further tool use.
    Args:
        query: The user's query to process
    Returns:
        The final text response from Claude
    """

    messages = [
        {
            "role": "user",
            "content": query
        }
    ]

    available_tools = await self._get_tools()

    response = await self.anthropic.messages.create(
        model=MODEL_ID,
        max_tokens=4096,
        messages=messages,
        tools=available_tools
    )

    while response.stop_reason == "tool_use":
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        tool_results = []
        for content in response.content:
            if content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                try:
                    result = await self.client.call_tool(tool_name, tool_args)

                    if isinstance(result.content, list):
                        result_text = "\n".join([
                            c.text if hasattr(c, 'text') else str(c)
                            for c in result.content
                        ])
                    else:
                        result_text = result.content

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result_text
                    })

                except Exception as e:
                    print(f"Error calling tool {tool_name}: {e}")
                    tools_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": f"Error: {str(e)}",
                        "is_error": True
                    })

            # Add tool results to conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })

            response = self.anthropic.messages.create(
                model=MODEL_ID,
                max_tokens=4096,
                messages=messages,
                tools=available_tools
            )

        final_text = []
        for content in response.content:
            if hasattr(content, 'text'):
                final_text.append(content.text)

        return "\n".join(final_text)

async def converse(self):
    """Start an interactive conversation mode with Claude.
    Allows the user to have a multi-turn conversation with Claude, where each query can trigger tool use. Exits when user types 'quit' or 'q'
    """
    print("\nEntering conversation mode. Type 'quit' or 'q' to exit.")

    while True:
        query = input("\nQuery: ").strip()

        if query.lower() in ("quit", "q"):
            break

        if not query:
            print("Please enter query")
            continue

        try:
            response = await self.process_query(query)
            print("\n" + response)
        except Exception as e:
            print(f"Error processing query: {e}")
    return

# prompts
async def prompt(self, prompt_name: str):
    """Execute a named prompt template from the MCP server.
    Retrieves a prompt template from the server, collects required arguments from the user, generates the prompt, and processes it with Claude.
    Args:
        prompt_name: Name of the prompt template to execute
    """
    try:
        prompts_response = await self._get_prompts()
        prompt_obj = next(
            (p for p in prompts_response if p.name == prompt_name), None
        )

        if not prompt_obj:
            print(f"Prompt '{prompt_name}' not found")
            return

            # Collect arguments for the prompt template
            arguments = {}
            if prompt_obj.arguments:
                for arg in prompt_obj.arguments:
                    required = "required" if arg.required else "optional"
                    user_input = input(f"{arg.name} ({required}): ").strip()

                    if not user_input and arg.required:
                        print(f"Error: {arg.name} is required")
                        return

                    if user_input:
                        arguments[arg.name] = user_input

            # Generate the prompt with provided arguments
            prompt_result = await self.client.get_prompt(prompt_name, arguments=arguments)

            prompt = prompt_result.messages[0].content.text

            response = await self.process_query(prompt)
            print(response)
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}\n")
            return

async def read_file(self):
    """Read the contents of a file via MCP resource.
    Prompts the user for a file path and retrieves the file content through the MCP server's file resource.
    """
    try:
        file_name = input("Enter file path: ").strip()
        encoded_file_name = quote(file_name, safe="")
        resource = await self.client.read_resource(f"file://{encoded_file_name}")
        file_content = json.loads(resource[0].text)["file_content"]

        print(f"File content:\n {file_content}")
        return file_content
    except Exception as e:
        print(f"Error reading file: {e}")

    def _print_dir_listing(self, items: list[dict]):
        """Format and print a directory listing.
        Args:
            items: List of directory items with metadata(type, size, modified, name)
        """
        print("\nDirectory Listing:\n")
        print(f"{'Type':<10} {'Size':>10} {'Modified':<25} {'Name'}")
        print("-" * 70)
        for item in items:
            type_icon = "📁" if item["type"] == "directory" else "📄"
            size = f"{item['size']} B"
            print(f"{type_icon:<2} {item['type']:<8} {size:>10} {item['modified']:<25} {item['name']}")

async def read_dir(self):
    """List the contents of the current directory via MCP resource.
    Retrieves and displays directory contents through the MCP server's directory resource.
    """
    try:
        resource = await self.client.read_resource(f"dir://.")
        dir_list = json.loads(resource[0].text)["items"]
        self._print_dir_listing(dir_list)
        return

    except Exception as e:
        print(f"Error reading directory: {e}")