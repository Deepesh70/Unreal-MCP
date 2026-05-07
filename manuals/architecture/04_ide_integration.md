# 🔌 IDE Integration — How MCP Connects to IDEs

## What is MCP?

Model Context Protocol (MCP) is a standard that lets AI models in IDEs call external tools. Our server exposes Unreal Engine capabilities as MCP tools. Any IDE that supports MCP can connect and use them.

## How It Works

1. Our MCP server runs as a separate process (`python server.py`)
2. The server exposes tools via SSE (Server-Sent Events) at `http://localhost:8000/sse`
3. The IDE connects to this URL and discovers all available tools
4. When the user asks the AI to do something in Unreal, the AI calls our tools
5. Our tools send WebSocket commands to Unreal Engine
6. Results flow back through the same chain

## Supported IDEs

| IDE | MCP Support | Configuration |
|-----|-------------|---------------|
| **Cursor** | ✅ Native | `.cursor/mcp.json` in project root |
| **VS Code + Copilot** | ✅ With extension | `settings.json` MCP config |
| **Antigravity** | ✅ Native | Settings panel → MCP servers |
| **Claude Desktop** | ✅ Native | `claude_desktop_config.json` |
| **Continue.dev** | ✅ Native | `.continue/config.json` |
| **Any MCP client** | ✅ Via SSE | Point to `http://localhost:8000/sse` |

## What the IDE Sees

When connected, the IDE's AI model sees 12 tools:

```
Tools available:
├── Scene Management
│   ├── get_scene_state     — Query all actors in the scene
│   ├── list_actors         — Simple actor list (legacy)
│   ├── spawn_actor         — Create any actor
│   ├── modify_actor        — Move/rotate/scale actors
│   ├── destroy_actor       — Remove actors
│   └── set_actor_scale     — Scale actors (legacy)
├── Properties
│   ├── set_actor_property  — Set ANY UE property
│   └── get_actor_property  — Read ANY UE property
├── Scripting
│   └── execute_python_in_editor — Run UE Python scripts (the superpower)
├── Capture
│   └── capture_viewport    — Screenshot for visual feedback
├── Discovery
│   └── find_assets         — Search project content
└── Engine
    └── run_console_command — Execute UE console commands
```

The AI model decides which tools to call based on the user's request. A smart model (GPT-4, Claude, Gemini Pro) will chain tools together intelligently. A simpler model will use the basic tools.

## The Model Is Not Ours

This is important: **we don't provide the AI model**. The intelligence comes from the IDE's own model. Our server just provides the hands.

| What we provide | What the IDE provides |
|----------------|----------------------|
| 12 MCP tools | AI model (GPT, Claude, Gemini, etc.) |
| WebSocket bridge to UE | Reasoning about what to build |
| Python script execution | Natural language understanding |
| Screenshot capture | Vision analysis (if model supports it) |
