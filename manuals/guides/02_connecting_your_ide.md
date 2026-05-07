# 🔌 Connecting Your IDE — Setup for Every Major IDE

## Prerequisites

Before connecting any IDE, you need:

1. **Unreal Engine running** with your project open
2. **Remote Control Web Interface plugin** enabled in UE (see [Unreal Plugins](03_unreal_plugins.md))
3. **MCP Server running** — open a terminal and run:
   ```bash
   cd d:\Desktop\Unreal-MCP
   python server.py
   ```
   You should see: `Server running on http://localhost:8000`

---

## Cursor

Create a file at your project root: `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "unreal-engine": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

Restart Cursor. Open the chat sidebar. The AI now has access to all Unreal MCP tools.

**Test it:** Type "What actors are in my Unreal scene?" → The AI should call `get_scene_state` and return a list.

---

## VS Code with GitHub Copilot (MCP-enabled)

Open VS Code settings (`settings.json`) and add:

```json
{
  "mcp.servers": {
    "unreal-engine": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

Restart VS Code. Copilot Chat now has access to the tools.

---

## Antigravity

Antigravity supports MCP server connections. Configure it to point to:

```
http://localhost:8000/sse
```

The exact configuration location depends on Antigravity's settings panel. Once connected, the AI in Antigravity can directly call all Unreal tools.

---

## Claude Desktop

Add to `claude_desktop_config.json` (usually at `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "unreal-engine": {
      "command": "python",
      "args": ["d:\\Desktop\\Unreal-MCP\\server.py"],
      "env": {}
    }
  }
}
```

Note: Claude Desktop launches the server itself. You don't need to run `python server.py` separately.

---

## Any Other MCP-Compatible IDE

The MCP server uses **SSE (Server-Sent Events)** transport. Any IDE or tool that supports the MCP protocol can connect to:

```
http://localhost:8000/sse
```

If the IDE supports `stdio` transport instead, you can run the server as:
```bash
python server.py --transport stdio
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Is `python server.py` running? Check the terminal. |
| "No tools found" | Restart the IDE after adding the MCP config. |
| "Unreal Engine API is offline" | Open Unreal Engine and ensure the Remote Control Web Interface plugin is enabled. |
| Tools work but nothing happens in Unreal | Check that Unreal's Remote Control is on port 30020 (default). |
