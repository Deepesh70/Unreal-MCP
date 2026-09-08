# 🚀 Setup Guide — How to Install and Run

## Prerequisites

1. **Python 3.10+** installed
2. **Unreal Engine 5.x** installed and a project open
3. **pip** for installing Python dependencies

## Step 1: Install Python Dependencies

Open a terminal in the project root:

```bash
cd d:\Desktop\Unreal-MCP
pip install -r requirements.txt
```

If there's no `requirements.txt`, install manually:

```bash
pip install fastmcp websockets
```

## Step 2: Enable Unreal Engine Plugins

In your Unreal project, enable these plugins via `Edit → Plugins`:

1. **Remote Control Web Interface** — REQUIRED (this is how Python talks to UE)
2. **Python Editor Script Plugin** — REQUIRED for `execute_python_in_editor`

See [Unreal Plugins Guide](03_unreal_plugins.md) for detailed instructions.

## Step 3: Start Unreal Engine

Open your project in Unreal Engine. The Remote Control plugin will start listening on `ws://localhost:30020` by default.

## Step 4: Start the MCP Server

In a terminal:

```bash
cd d:\Desktop\Unreal-MCP
python server.py
```

You should see:
```
Server running on http://localhost:8000
```

The server will list all registered tools (should be 12 as of Phase 3).

## Step 5: Connect Your IDE

See [Connecting Your IDE](02_connecting_your_ide.md) for setup instructions for Cursor, VS Code Copilot, Antigravity, and other MCP-compatible IDEs.

## Step 6: Test the Connection

In your IDE's chat, type:

> "What actors are in my Unreal scene?"

The AI should call `get_scene_state` and return a list of actors. If this works, everything is connected.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `python server.py` fails | Missing dependencies | Run `pip install fastmcp websockets` |
| "Unreal Engine API is offline" | UE not running or plugin disabled | Open UE, enable Remote Control Web Interface |
| Tools show but nothing happens | Wrong WebSocket port | Check `unreal_mcp/config/settings.py` for `UE_WS_URL` |
| `execute_python_in_editor` returns timeout | Python plugin not enabled | Enable Python Editor Script Plugin in UE |
| IDE doesn't see tools | MCP config missing | See IDE-specific config in [Connecting Your IDE](02_connecting_your_ide.md) |

## Running the Standalone Agent (Legacy Mode)

The old terminal-based agent still works alongside the MCP server:

```bash
python agent.py groq -b -i     # Builder mode with Groq
python agent.py gemini -b -i   # Builder mode with Gemini
python agent.py ollama -b -i   # Builder mode with local Ollama
```

This mode runs its own LLM and sends commands directly. It's being merged to use MCP tools internally (Phase 4).
