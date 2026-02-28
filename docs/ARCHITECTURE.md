# 📂 Project Architecture — Unreal MCP

> A modular Python package that lets an LLM agent control Unreal Engine
> through the Model Context Protocol (MCP) over WebSocket.

---

## Folder Structure

```
Unreal-MCP/
├── server.py                  ← Thin entry point (starts the MCP server)
├── agent.py                   ← LLM agent that connects to the MCP server
├── requirements.txt
│
├── unreal_mcp/                ← Root package
│   ├── __init__.py            ← Creates shared FastMCP instance
│   │
│   ├── config/                ← ⚙️  Settings & constants
│   │   ├── __init__.py
│   │   └── settings.py        ← UE_WS_URL, host, port, transport
│   │
│   ├── connection/            ← 🔌 WebSocket transport
│   │   ├── __init__.py
│   │   └── websocket.py       ← send_ue_ws_command()
│   │
│   ├── mappings/              ← 🗺️  Name-to-path lookups
│   │   ├── __init__.py
│   │   ├── assets.py          ← Basic shapes (cube, sphere, …)
│   │   └── classes.py         ← Actor classes (pointlight, …)
│   │
│   ├── tools/                 ← 🛠️  MCP tool definitions
│   │   ├── __init__.py        ← Auto-registers all tools
│   │   ├── spawning.py        ← spawn_actor tool
│   │   ├── actors.py          ← list_actors tool
│   │   └── transform.py       ← set_actor_scale tool
│   │
│   └── utils/                 ← 🧰 Shared response helpers
│       ├── __init__.py
│       └── response.py        ← extract_return_value, format helpers
│
└── docs/                      ← 📖 Flow documentation
    ├── ARCHITECTURE.md         ← This file
    ├── FLOW_SPAWN.md           ← Spawn actor flow
    ├── FLOW_LIST.md            ← List actors flow
    ├── FLOW_TRANSFORM.md       ← Transform (scale) flow
    └── ADDING_TOOLS.md         ← How to add new tools
```

---

## Layer Dependency Diagram

```
┌──────────────────────────────────────────────────────┐
│                  server.py  (entry point)             │
│              imports mcp from unreal_mcp              │
└──────────────────────┬───────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   unreal_mcp/__init__   │
          │   Creates FastMCP mcp   │
          │   Imports tools package │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │     tools/__init__      │
          │  imports spawning,      │
          │  actors, transform      │
          └──┬────────┬─────────┬──┘
             │        │         │
      ┌──────▼──┐  ┌──▼───┐  ┌─▼──────────┐
      │spawning │  │actors│  │ transform  │
      └──┬──┬───┘  └──┬───┘  └──┬─────────┘
         │  │         │         │
         │  │    ┌────▼────┐    │
         │  └───►│  utils  │◄───┘
         │       │response │
         │       └─────────┘
         │
    ┌────▼─────┐      ┌────────────┐
    │ mappings │      │ connection │
    │assets.py │      │websocket.py│◄──── all tools
    │classes.py│      └──────┬─────┘
    └──────────┘             │
                      ┌──────▼──────┐
                      │   config    │
                      │ settings.py │
                      └─────────────┘
```

---

## How It Works (High Level)

1. **`server.py`** imports `mcp` from `unreal_mcp`
2. `unreal_mcp/__init__.py` creates the FastMCP instance and imports `tools/`
3. `tools/__init__.py` imports each tool module (`spawning`, `actors`, `transform`)
4. Each tool module uses `@mcp.tool()` decorators to register functions
5. The tools call `send_ue_ws_command()` from `connection/` to talk to UE
6. `connection/websocket.py` reads the UE URL from `config/settings.py`
7. `server.py` calls `mcp.run()` — agents connect via SSE at port 8000
