import os
import sys
import argparse
import logging
import subprocess
from mcp.server.fastmcp import FastMCP

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

# 3. FastMCP Server Initialization
mcp = FastMCP("mcp-micro-shell")

# Determine Workspace and initialize Security Manager
WORKSPACE_PATH = os.environ.get("MCP_MICRO_SHELL_WORKSPACE", os.getcwd())
security = WorkspaceSecurityManager(WORKSPACE_PATH)

# Define Tools with @mcp.tool
@mcp.tool()
def get_current_directory() -> str:
    """
    Returns the current configured workspace directory of the shell server.
    """
    return f"Current workspace: {security.workspace}"

@mcp.tool()
def read_file(path: str) -> str:
    """
    Reads the entire text content of a file located within the allowed workspace boundary.

    Args:
        path: The path to the file (absolute or relative to the workspace).
    """
    try:
        safe_path = security.get_safe_path(path)
        if not os.path.exists(safe_path):
            return f"Error: File not found at '{path}'"
        
        if os.path.isdir(safe_path):
            return f"Error: '{path}' is a directory, not a file."

        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """
    Writes text content to a file within the allowed workspace boundary, creating parent folders if they don't exist.

    Args:
        path: The path to the file (absolute or relative to the workspace).
        content: The text content to write to the file.
    """
    try:
        safe_path = security.get_safe_path(path)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: File successfully written to '{path}'"
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def execute_command(command: str, cwd: str = None, timeout: int = 30) -> str:
    """
    Executes an operating system shell command safely inside the workspace.
    Captures and returns the complete STDOUT, STDERR, and numerical exit code.

    Args:
        command: The exact shell command line string to run.
        cwd: Optional sub-directory within the workspace to run the command. Defaults to the workspace root.
        timeout: Subprocess execution timeout in seconds. Defaults to 30.
    """
    try:
        if cwd:
            safe_cwd = security.get_safe_path(cwd)
        else:
            safe_cwd = security.workspace
    except PermissionError as pe:
        return str(pe)

    logger.info(f"Subprocess Triggered: '{command}' in CWD: '{safe_cwd}' (timeout: {timeout}s)")
    
    try:
        # Run command using the standard platform shell
        result = subprocess.run(
            command,
            shell=True,
            cwd=safe_cwd,
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
            
        return f"Exit Code: {result.returncode}\n\n" + "\n\n".join(output_blocks)
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Process timeout after {timeout}s: '{command}'")
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        logger.error(f"Process execution failed: {e}")
        return f"Error: Subprocess failed to execute.\nException: {str(e)}"

# 4. Entrypoint main
def main():
    parser = argparse.ArgumentParser(
        description="mcp-micro-shell: A lightweight, secure MCP server powered by FastMCP."
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

    logger.info(f"Initializing FastMCP mcp-micro-shell server inside workspace: {security.workspace}")

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "sse":
            # FastMCP matches host and port for SSE transport
            mcp.run(transport="sse", host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Server shut down by user.")
    except Exception as e:
        logger.critical(f"Server crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()