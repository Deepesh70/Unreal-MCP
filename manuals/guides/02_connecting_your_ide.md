# 🔌 Connecting Your IDE — Setup for Every Major IDE

## Quick Start (3 steps)

1. **Install the MCP server** (one time):
   ```bash
   cd d:\Desktop\Unreal-MCP
   pip install .
   ```
   This installs the `unreal-mcp` command globally.

2. **Add MCP config** to your IDE (see sections below)

3. **Open Unreal Engine** with the Remote Control Web Interface plugin enabled

That's it. Your IDE now has full control over Unreal Engine.

---

## Prerequisites

- **Python 3.10+** installed
- **Unreal Engine running** with your project open
- **Remote Control Web Interface plugin** enabled in UE (see [Unreal Plugins](03_unreal_plugins.md))

---

## VS Code with GitHub Copilot (MCP-enabled)

The server launches automatically when you open VS Code — no manual terminal needed.

Open VS Code settings (`settings.json`) and add:

```json
{
  "mcp.servers": {
    "unreal-engine": {
      "command": "unreal-mcp",
      "args": ["--stdio"],
      "env": {
        "UE_WS_URL": "ws://127.0.0.1:30020"
      }
    }
  }
}
```

Restart VS Code. Copilot Chat now has access to all Unreal tools.

**Test it:** Type "check my connection to Unreal" → Should show ✅ status for all systems.

---

## Cursor

Create a file at your project root: `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "unreal-engine": {
      "command": "unreal-mcp",
      "args": ["--stdio"],
      "env": {
        "UE_WS_URL": "ws://127.0.0.1:30020"
      }
    }
  }
}
```

Restart Cursor. The AI now has access to all Unreal MCP tools.

**Test it:** Type "What actors are in my Unreal scene?" → The AI should call `get_scene_state` and return a meaningful summary.

> **Note:** You can also use SSE mode if you prefer running the server manually:
> ```json
> {
>   "mcpServers": {
>     "unreal-engine": {
>       "url": "http://localhost:8000/sse"
>     }
>   }
> }
> ```
> Then run `unreal-mcp` in a terminal first.

---

## Antigravity

Antigravity supports MCP server connections. You can configure it in two ways:

**Option A — SSE mode** (requires running the server manually):
1. Start the server: `unreal-mcp` (in a terminal)
2. Configure Antigravity to connect to: `http://localhost:8000/sse`

**Option B — stdio mode** (Antigravity launches the server):
Configure the command as `unreal-mcp` with args `["--stdio"]`.

The exact configuration location depends on Antigravity's settings panel.

---

## Claude Desktop

Add to `claude_desktop_config.json` (usually at `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "unreal-engine": {
      "command": "unreal-mcp",
      "args": ["--stdio"],
      "env": {
        "UE_WS_URL": "ws://127.0.0.1:30020"
      }
    }
  }
}
```

Claude Desktop launches the server itself. You don't need to run it separately.

---

## Any Other MCP-Compatible IDE

**stdio mode** (recommended — IDE auto-launches):
```json
{
  "command": "unreal-mcp",
  "args": ["--stdio"],
  "env": {
    "UE_WS_URL": "ws://127.0.0.1:30020"
  }
}
```

**SSE mode** (manual — you run the server):
1. Run `unreal-mcp` (or `unreal-mcp --port 9000` for a custom port)
2. Connect your IDE to `http://localhost:8000/sse`

---

## Environment Variables

You can customize the connection via the `env` block in your MCP config:

| Variable | Default | Description |
|----------|---------|-------------|
| `UE_WS_URL` | `ws://127.0.0.1:30020` | WebSocket URL to Unreal Engine's Remote Control |
| `SERVER_PORT` | `8000` | Port for SSE mode (auto-fallback if taken) |

For remote Unreal Engine (e.g., on another machine or via ngrok):
```json
"env": {
  "UE_WS_URL": "ws://192.168.1.50:30020"
}
```

---

## First Things to Try

After connecting, try these prompts in your IDE's AI chat:

1. **"Check my connection to Unreal"** — Verifies the full pipeline (MCP → WebSocket → UE → Python)
2. **"What's in my scene?"** — Gets a summary of all actors with types and mesh names
3. **"Spawn a cube at 0, 0, 100"** — Creates a basic shape in the level
4. **"Take a screenshot"** — Captures the viewport for visual verification

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `unreal-mcp` command not found | Run `pip install .` from the Unreal-MCP directory |
| "Connection refused" | Is Unreal Engine running? Is the Remote Control Web Interface plugin enabled? |
| "No tools found" | Restart the IDE after adding the MCP config |
| Tools work but nothing happens in UE | Check that Unreal's Remote Control is on port 30020 (default) |
| Port 8000 already in use | Use `unreal-mcp --port 9000` or let it auto-fallback |
