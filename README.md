# 🛠️ mcp-micro-shell

A modular, lightweight, and high-performance **Model Context Protocol (MCP)** server that exposes system shell capabilities to AI agents (like Claude Desktop, Cursor, cl0w, etc.).

Powered by [**`uv`**](https://github.com/astral-sh/uv), the ultra-fast Python package installer and runner.

---

## 🌟 Key Features

- **⚡ Fast Execution:** Scaled and executed instantly with `uv` virtual environments.
- **🧱 Modular Tools Design:** Separated tool modules (e.g., `tools/shell.py`) make it clean and easy to add new capabilities.
- **🛡️ Embedded Security:** Restricts directory paths, protects against directory escapes, and facilitates command filtering.
- **🔌 Multi-Transport Mode:** 
  - **Stdio (Default):** Ultra-fast stdio JSON-RPC transport for local integrations (e.g. Claude Desktop).
  - **SSE (Server-Sent Events):** High-performance HTTP server built on Starlette and Uvicorn for remote integrations.
- **⚙️ Clean Logging:** Logs are redirected entirely to `stderr` or a log stream, keeping standard output (`stdout`) clear for JSON-RPC messages.

---

## 📂 Project Architecture

```
mcp-micro-shell/
├── .python-version
├── pyproject.toml              # Project metadata, dependencies, and script entry points
├── README.md                   # Instructions and Client configuration
├── src/
│   └── mcp_micro_shell/
│       ├── __init__.py         # Package version declaration
│       ├── __main__.py        # Python module run entry (-m)
│       ├── main.py            # CLI argument parser and transport router
│       ├── server.py          # Central MCP Server initialization
│       ├── tools/             # Modular tool registries
│       │   ├── __init__.py    # Dynamic tool loader
│       │   └── shell.py       # Core shell execution tools
│       └── utils/             # Core internal helpers
│           ├── __init__.py
│           ├── logging.py     # Stderr-exclusive logging utility
│           └── security.py    # Directory-traversal & validation manager
└── tests/                     # Automated unit test suite
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have `uv` installed. If you don't, you can install it using one command:

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🏃 Run the Server

### 1. Stdio Mode (Default)
This mode communicates over standard I/O streams and is perfect for client integrations.

```bash
uv run mcp-micro-shell
```

### 2. SSE Mode (Web API)
This mode runs a web server that accepts client connections over standard HTTP endpoints.

```bash
uv run mcp-micro-shell --transport sse --host 127.0.0.1 --port 8000
```

### 3. Check CLI Options
To inspect available arguments:

```bash
uv run mcp-micro-shell --help
```

---

## 🔌 Integrating with MCP Clients

### 1. Claude Desktop Integration
Add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-micro-shell": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\SKTelecom\\Documents\\mcp-micro-shell",
        "run",
        "mcp-micro-shell"
      ]
    }
  }
}
```
*(Remember to replace the directory path with your actual absolute path if it is placed elsewhere.)*

---

### 2. cl0w Integration
Add `mcp-micro-shell` to your `mcp.json` file inside the `cl0w` project directory:

```json
{
  "mcpServers": {
    "mcp-micro-shell": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\SKTelecom\\Documents\\mcp-micro-shell",
        "run",
        "mcp-micro-shell"
      ]
    }
  }
}
```

---

## 🛠️ Provided Tools

### 1. `execute_command`
Runs standard operating system shell commands safely in a subprocess.

**Arguments:**
- `command` (string, **required**): The command string to run.
- `cwd` (string, optional): The directory where the command will execute.
- `timeout` (integer, optional): Maximum execution time in seconds (defaults to `30`).

---

### 2. `get_current_directory`
Returns the current working directory of the shell environment.
