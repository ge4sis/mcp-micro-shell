# 🛠️ mcp-micro-shell

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/MCP-1.27.1+-orange.svg?style=for-the-badge&logo=modelcontextprotocol&logoColor=white" alt="MCP Version">
  <img src="https://img.shields.io/badge/powered%20by-uv-purple.svg?style=for-the-badge&logo=astral&logoColor=white" alt="Powered by UV">
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License">
</p>

<p align="center">
  <strong>An ultra-lightweight, secure, and high-performance MCP server providing isolated file operations and shell execution capabilities.</strong>
</p>

<p align="center">
  Fully optimized with a flat python layout, powered by <a href="https://github.com/astral-sh/uv"><b>uv</b></a>, and ready for global execution via <code>uvx</code>.
</p>

---

## 🌟 Key Features

* **⚡ Lightning Fast Startup:** Built entirely with a simplified flat package structure, executing instantly with `uv` virtual environments.
* **🛡️ Hardened Sandboxed Security:** All terminal runs and file read/writes are strictly sandboxed inside your designated workspace directory (`MCP_MICRO_SHELL_WORKSPACE`), robustly defending against directory traversal (`../`) attacks.
* **🔌 Multi-Transport System:**
  * **Stdio (Default):** High-speed JSON-RPC stdio transport for local desktop clients (Cursor, Claude Desktop, cl0w, etc.).
  * **SSE (Server-Sent Events):** High-performance SSE HTTP server using Starlette and Uvicorn for remote connections.
* **⚙️ Zero Stdout Pollution:** Redirects all internal engine logs exclusively to `stderr`, keeping the `stdout` channel completely pristine for JSON-RPC messages.

---

## 📂 Simplified Architecture

Optimized down to a minimalist, highly cohesive Python package layout:
```text
mcp-micro-shell/
├── pyproject.toml              # Build backend configuration (Hatchling)
├── README.md                   # English Documentation
├── README.ko.md                # Korean Documentation
├── uv.lock                     # Lock file
└── mcp_micro_shell/            # Primary python package
    ├── __init__.py             # Version declaration
    ├── __main__.py            # Module runner (python -m)
    └── server.py              # Unified server engine & tool bindings
```

---

## 🛠️ Provided Tools

All tools automatically resolve relative paths against the designated workspace root and validate boundaries.

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| **`execute_command`** | `command` (str, **req**),<br>`cwd` (str, opt),<br>`timeout` (int, opt) | Safely executes terminal commands inside the workspace (or a sub-folder inside it). Inherits system PATH for full CLI tool access. |
| **`get_current_directory`** | None | Returns the active workspace path boundary. |
| **`read_file`** | `path` (str, **req**) | Reads text files safely, verifying boundary constraints. Blocks out-of-boundary paths. |
| **`write_file`** | `path` (str, **req**),<br>`content` (str, **req**) | Writes text files safely, auto-creating subfolders inside the workspace boundary. Blocks out-of-boundary paths. |

---

## 🚀 Getting Started

### Prerequisites
Make sure you have `uv` installed. If you don't, run:

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🏃 Running the Server

### 1. Stdio Mode (Default)
Ideal for standard JSON-RPC desktop AI integrations.
```bash
uv run mcp-micro-shell
```

### 2. SSE Mode (Web API)
Ideal for remote integrations. Runs an HTTP SSE server.
```bash
uv run mcp-micro-shell --transport sse --host 127.0.0.1 --port 8000
```

---

## 🔌 Integrating with MCP Clients (`mcp.json`)

To use this server inside AI clients (like Claude Desktop, Cursor, cl0w), configure your client config as follows:

```json
{
  "mcpServers": {
    "mcp-micro-shell": {
      "command": "uvx",
      "args": [
        "--from",
        "C:\\Users\\SKTelecom\\Documents\\mcp-micro-shell",
        "mcp-micro-shell"
      ],
      "env": {
        "MCP_MICRO_SHELL_WORKSPACE": "C:\\Users\\SKTelecom\\Documents\\mcp-micro-shell\\workspace"
      }
    }
  }
}
```
*(Once published to PyPI, the `--from` local path argument can be omitted to pull directly from PyPI).*
