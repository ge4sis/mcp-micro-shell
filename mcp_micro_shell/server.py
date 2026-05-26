import os
import sys
import argparse
import asyncio
import logging
import subprocess
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types

# Define module logger
logger = logging.getLogger("mcp-micro-shell")

# 1. Stderr-Exclusive Logging setup
def setup_logging(level: int = logging.INFO):
    """
    Configures logging to write exclusively to stderr so that it doesn't
    interfere with the stdout communication channel of the MCP JSON-RPC server.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True
    )
    logging.getLogger("asyncio").setLevel(logging.WARNING)

# 2. Path security manager
class WorkspaceSecurityManager:
    def __init__(self, workspace_path: str):
        self.workspace = os.path.abspath(workspace_path)
        # Ensure workspace exists
        os.makedirs(self.workspace, exist_ok=True)
        logger.info(f"WorkspaceSecurityManager initialized with workspace: {self.workspace}")

    def is_safe_path(self, path: str) -> bool:
        """
        Checks if the resolved path is located within the allowed workspace.
        Prevents directory traversal attacks.
        """
        try:
            target_path = os.path.abspath(path)
            # Use os.path.commonpath to verify target_path is inside self.workspace
            return os.path.commonpath([self.workspace]) == os.path.commonpath([self.workspace, target_path])
        except Exception as e:
            logger.error(f"Error validating path safety for '{path}': {e}")
            return False

    def get_safe_path(self, path: str) -> str:
        """
        Resolves relative/absolute path against the workspace and ensures safety.
        """
        # If relative, resolve it relative to workspace
        if not os.path.isabs(path):
            resolved = os.path.abspath(os.path.join(self.workspace, path))
        else:
            resolved = os.path.abspath(path)

        if self.is_safe_path(resolved):
            return resolved
        raise PermissionError(f"Access denied: Path '{path}' is outside the authorized workspace '{self.workspace}'")

# 3. Server Initialization
server = Server("mcp-micro-shell")

# Determine Workspace and initialize Security Manager
WORKSPACE_PATH = os.environ.get("MCP_MICRO_SHELL_WORKSPACE", os.getcwd())
security = WorkspaceSecurityManager(WORKSPACE_PATH)

# Define Tools
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    Exposes shell execution and file operations tools to the MCP Client.
    """
    return [
        types.Tool(
            name="execute_command",
            description=(
                "Executes an operating system shell command safely inside the workspace. "
                "Captures and returns the complete STDOUT, STDERR, and numerical exit code."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The exact shell command line string to run."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Optional sub-directory within the workspace to run the command. Defaults to the workspace root."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Subprocess execution timeout in seconds. Defaults to 30.",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="get_current_directory",
            description="Returns the current configured workspace directory of the shell server.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="read_file",
            description="Reads the entire text content of a file located within the allowed workspace boundary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file (absolute or relative to the workspace)."
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="write_file",
            description="Writes text content to a file within the allowed workspace boundary, creating parent folders if they don't exist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file (absolute or relative to the workspace)."
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write to the file."
                    }
                },
                "required": ["path", "content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """
    Handles tool execution requests from the client.
    """
    if name == "execute_command":
        if not arguments or "command" not in arguments:
            raise ValueError("Missing required parameter: 'command'")
            
        command = arguments["command"]
        cwd_arg = arguments.get("cwd")
        timeout = arguments.get("timeout", 30)

        # Resolve command execution directory
        try:
            if cwd_arg:
                cwd = security.get_safe_path(cwd_arg)
            else:
                cwd = security.workspace
        except PermissionError as pe:
            return [types.TextContent(type="text", text=str(pe))]

        logger.info(f"Subprocess Triggered: '{command}' in CWD: '{cwd}' (timeout: {timeout}s)")
        
        try:
            # Run command using the standard platform shell
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output_blocks = []
            if result.stdout:
                output_blocks.append(f"--- STDOUT ---\n{result.stdout}")
            if result.stderr:
                output_blocks.append(f"--- STDERR ---\n{result.stderr}")
                
            if not output_blocks:
                output_blocks.append("[Success: No output produced]")
                
            response_text = f"Exit Code: {result.returncode}\n\n" + "\n\n".join(output_blocks)
            return [types.TextContent(type="text", text=response_text)]
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Process timeout after {timeout}s: '{command}'")
            return [types.TextContent(type="text", text=f"Error: Command timed out after {timeout} seconds.")]
        except Exception as e:
            logger.error(f"Process execution failed: {e}")
            return [types.TextContent(type="text", text=f"Error: Subprocess failed to execute.\nException: {str(e)}")]

    elif name == "get_current_directory":
        return [types.TextContent(type="text", text=f"Current workspace: {security.workspace}")]

    elif name == "read_file":
        if not arguments or "path" not in arguments:
            raise ValueError("Missing required parameter: 'path'")
        
        raw_path = arguments["path"]
        try:
            safe_path = security.get_safe_path(raw_path)
            if not os.path.exists(safe_path):
                return [types.TextContent(type="text", text=f"Error: File not found at '{raw_path}'")]
            
            if os.path.isdir(safe_path):
                return [types.TextContent(type="text", text=f"Error: '{raw_path}' is a directory, not a file.")]

            with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return [types.TextContent(type="text", text=content)]
        except PermissionError as pe:
            return [types.TextContent(type="text", text=str(pe))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]

    elif name == "write_file":
        if not arguments or "path" not in arguments or "content" not in arguments:
            raise ValueError("Missing required parameters: 'path' and 'content'")
            
        raw_path = arguments["path"]
        content = arguments["content"]
        try:
            safe_path = security.get_safe_path(raw_path)
            
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            return [types.TextContent(type="text", text=f"Success: File successfully written to '{raw_path}'")]
        except PermissionError as pe:
            return [types.TextContent(type="text", text=str(pe))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error writing file: {str(e)}")]

    else:
        raise ValueError(f"Unknown tool identifier: {name}")

# 4. Transport Runners
async def run_stdio():
    from mcp.server.stdio import stdio_server
    logger.info("Starting MCP stdio server transport...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=server.name,
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

async def run_sse(host: str, port: int):
    try:
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from mcp.server.sse import SseServerTransport
    except ImportError:
        logger.error("SSE dependencies (starlette, uvicorn) are not installed.")
        sys.exit(1)
        
    import uvicorn
    logger.info(f"Starting MCP SSE server transport on http://{host}:{port} ...")
    
    app = Starlette()
    sse = SseServerTransport("/messages")

    async def sse_handler(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=server.name,
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    async def messages_handler(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    app.add_route("/sse", sse_handler, methods=["GET"])
    app.add_route("/messages", messages_handler, methods=["POST"])
    
    @app.route("/")
    async def index(request):
        return JSONResponse({"status": "running", "server": server.name})

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    uvicorn_server = uvicorn.Server(config)
    await uvicorn_server.serve()

def main():
    parser = argparse.ArgumentParser(
        description="mcp-micro-shell: A lightweight, secure MCP server for file ops and shell command execution."
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="SSE server host binding (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="SSE server port binding (default: 8000)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug/verbose log output",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)

    logger.info(f"Initializing mcp-micro-shell server inside workspace: {security.workspace}")

    try:
        if args.transport == "stdio":
            asyncio.run(run_stdio())
        elif args.transport == "sse":
            asyncio.run(run_sse(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server shut down by user.")
    except Exception as e:
        logger.critical(f"Server crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()