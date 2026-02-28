<p align="center">
  <h1 align="center">🎮 Unreal MCP</h1>
  <p align="center">
    <strong>Control Unreal Engine with natural language using LLM agents and the Model Context Protocol.</strong>
  </p>
  <p align="center">
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-features">Features</a> •
    <a href="#%EF%B8%8F-architecture">Architecture</a> •
    <a href="#-supported-llm-backends">LLM Backends</a> •
    <a href="#-available-tools">Tools</a> •
    <a href="#-documentation">Docs</a>
  </p>
</p>

---

## 📖 Overview

**Unreal MCP** is a Python-based bridge that connects Large Language Models (LLMs) to Unreal Engine via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It lets you spawn actors, list objects, transform geometry, and more — all through plain-English commands.

The system has two halves:

| Component | Description |
|-----------|-------------|
| **MCP Server** (`server.py`) | A FastMCP server that exposes Unreal Engine operations as MCP tools over SSE. It communicates with UE via WebSocket using the built-in Remote Control API. |
| **LLM Agent** (`agent.py`) | A LangChain-powered agent that connects to the MCP server, discovers available tools, and uses an LLM to plan & execute multi-step operations inside the Unreal Editor. |

---

## ✨ Features

- 🗣️ **Natural Language Control** — Tell the agent what to do in plain English and watch it happen in Unreal Engine.
- 🔌 **Model Context Protocol** — Clean, standardized tool interface via FastMCP.
- 🤖 **Multi-Model Support** — Swap between **Groq**, **Ollama** (local), and **Google Gemini** with a single CLI flag.
- 💬 **Interactive Mode** — Chat with your Unreal scene in a REPL-style loop.
- 🧩 **Modular & Extensible** — Adding a new tool is as simple as writing a decorated function.
- ⚡ **WebSocket Transport** — Real-time communication with Unreal Engine's Remote Control API.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Unreal Engine 5.x** with the **Remote Control API** plugin enabled
- At least one LLM provider set up (see [Supported LLM Backends](#-supported-llm-backends))

### 1. Clone & Install

```bash
git clone https://github.com/Deepesh70/Unreal-MCP.git
cd Unreal-MCP
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add the API key(s) for your chosen LLM provider:

```env
# Only fill in the provider you plan to use
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
# Ollama needs no API key — just make sure it's running locally
```

### 3. Enable Remote Control in Unreal Engine

1. Open your Unreal Engine project.
2. Go to **Edit → Plugins** and enable **Remote Control API**.
3. Restart the editor — it will start listening on `ws://127.0.0.1:30020` by default.

### 4. Start the MCP Server

```bash
python server.py
```

The server starts on `http://localhost:8000` with SSE transport.

### 5. Run the Agent

```bash
# Full demo — spawns actors, lists them, scales them
python agent.py groq

# Quick test — just lists actors (1 API call)
python agent.py gemini --test

# Interactive chat mode
python agent.py groq --interactive

# Custom prompt
python agent.py gemini --prompt "spawn a sphere at 0 0 500"
```

---

## 🤖 Supported LLM Backends

| Backend | Provider | Models | API Key Required |
|---------|----------|--------|------------------|
| `groq` | [Groq Cloud](https://console.groq.com/) | `llama-3.1-8b-instant` (default), `llama-3.3-70b-versatile` | ✅ `GROQ_API_KEY` |
| `gemini` | [Google AI Studio](https://aistudio.google.com/apikey) | `gemini-2.5-pro` (default), `gemini-2.5-flash`, `gemini-2.0-flash` | ✅ `GOOGLE_API_KEY` |
| `ollama` | [Ollama](https://ollama.com/) (local) | `llama3.3:70b` (default), `qwen2.5:72b`, `deepseek-r1:70b`, `command-r-plus:104b` | ❌ Local |

You can also run each backend directly:

```bash
python -m agents.groq_agent
python -m agents.gemini_agent --model gemini-2.5-flash
python -m agents.ollama_agent --model qwen2.5:72b

# List available models for a backend
python -m agents.gemini_agent --list-models
python -m agents.ollama_agent --list-models
```

---

## 🛠️ Available Tools

These MCP tools are automatically registered and available to the agent:

| Tool | Description | Example |
|------|-------------|---------|
| `spawn_actor` | Spawn an actor or shape at a given position | `"spawn a cube at 0 0 200"` |
| `list_actors` | List all actors in the current level | `"list all actors"` |
| `set_actor_scale` | Scale an actor using its full path | `"scale the cube to 5x"` |

**Supported spawn types:** `cube`, `sphere`, `cone`, `cylinder`, `plane`, `pointlight`, `spotlight`

---

## 🏗️ Architecture

```
Unreal-MCP/
├── server.py                  ← Entry point — starts the MCP server
├── agent.py                   ← CLI launcher for the LLM agent
├── requirements.txt
│
├── unreal_mcp/                ← Core MCP server package
│   ├── __init__.py            ← Creates shared FastMCP instance
│   ├── config/                ← Settings & constants (WebSocket URL, ports)
│   ├── connection/            ← WebSocket transport to Unreal Engine
│   ├── mappings/              ← Friendly name → UE asset/class path lookups
│   ├── tools/                 ← MCP tool definitions (spawn, list, transform)
│   └── utils/                 ← Response parsing & formatting helpers
│
├── agents/                    ← LLM backend integrations
│   ├── base.py                ← Shared agent runner (MCP connection + execution)
│   ├── groq_agent.py          ← Groq Cloud backend
│   ├── ollama_agent.py        ← Local Ollama backend
│   └── gemini_agent.py        ← Google Gemini backend
│
└── docs/                      ← Detailed documentation
    ├── ARCHITECTURE.md         ← Full architecture & dependency diagram
    ├── FLOW_SPAWN.md           ← Spawn actor flow walkthrough
    ├── FLOW_LIST.md            ← List actors flow walkthrough
    ├── FLOW_TRANSFORM.md       ← Transform flow walkthrough
    ├── AGENTS.md               ← Agent system documentation
    └── ADDING_TOOLS.md         ← Guide to adding new MCP tools
```

### Data Flow

```
┌─────────────┐    SSE/HTTP     ┌──────────────┐   WebSocket    ┌──────────────────┐
│  LLM Agent  │ ◄────────────► │  MCP Server  │ ◄────────────► │  Unreal Engine   │
│ (LangChain) │    Port 8000    │  (FastMCP)   │   Port 30020   │ (Remote Control) │
└─────────────┘                 └──────────────┘                └──────────────────┘
```

1. **Agent** receives a natural language prompt
2. **LangChain** plans which MCP tools to call
3. **MCP Server** translates tool calls into WebSocket commands
4. **Unreal Engine** executes the commands and returns results
5. **Agent** interprets the results and responds

---

## ⚙️ Configuration

All server settings are centralized in `unreal_mcp/config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `UE_WS_URL` | `ws://127.0.0.1:30020` | Unreal Engine WebSocket endpoint |
| `SERVER_HOST` | `localhost` | MCP server bind address |
| `SERVER_PORT` | `8000` | MCP server port |
| `SERVER_TRANSPORT` | `sse` | MCP transport protocol |

---

## 🧩 Adding New Tools

Adding a new tool is straightforward. Create a new file in `unreal_mcp/tools/` and use the `@mcp.tool()` decorator:

```python
# unreal_mcp/tools/my_tool.py
from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command

@mcp.tool()
async def my_new_tool(param: str) -> str:
    """Description of what this tool does."""
    response = await send_ue_ws_command(
        object_path="/Script/...",
        function_name="SomeFunction",
        parameters={"Param": param},
    )
    return f"Done: {response}"
```

Then import it in `unreal_mcp/tools/__init__.py`. See [`docs/ADDING_TOOLS.md`](docs/ADDING_TOOLS.md) for a full guide.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full project architecture & dependency diagram |
| [`FLOW_SPAWN.md`](docs/FLOW_SPAWN.md) | End-to-end spawn actor flow |
| [`FLOW_LIST.md`](docs/FLOW_LIST.md) | End-to-end list actors flow |
| [`FLOW_TRANSFORM.md`](docs/FLOW_TRANSFORM.md) | End-to-end transform/scale flow |
| [`AGENTS.md`](docs/AGENTS.md) | Agent system & multi-model setup |
| [`ADDING_TOOLS.md`](docs/ADDING_TOOLS.md) | Step-by-step guide to adding new tools |

---

## 📋 Requirements

```
fastmcp                      # MCP server framework
websockets                   # WebSocket connection to UE
langchain                    # Agent orchestration
langchain_core               # Core LangChain types
langchain_mcp_adapters       # MCP ↔ LangChain bridge
langchain_groq               # Groq Cloud provider
langchain_ollama             # Local Ollama provider
langchain_google_genai       # Google Gemini provider
python-dotenv                # Environment variable loading
```

Install everything with:

```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-tool`)
3. Add your tool following the [Adding Tools guide](docs/ADDING_TOOLS.md)
4. Commit your changes (`git commit -m 'Add amazing-tool'`)
5. Push to the branch (`git push origin feature/amazing-tool`)
6. Open a Pull Request

---

## 📝 License

This project is open source. See the repository for license details.

---

<p align="center">
  Built with ❤️ using <a href="https://modelcontextprotocol.io/">MCP</a>, <a href="https://python.langchain.com/">LangChain</a>, and <a href="https://www.unrealengine.com/">Unreal Engine</a>
</p>
