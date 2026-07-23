# 🏗️ System Overview — How Everything Connects

## The Big Picture

```
┌───────────────────────────────────────────────────────────┐
│  USER'S IDE                                               │
│  (Cursor / VS Code Copilot / Antigravity / any MCP IDE)   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  AI MODEL (the user's model — GPT, Claude, Gemini,  │  │
│  │  Groq, local Ollama — whatever the IDE provides)    │  │
│  │                                                     │  │
│  │  The model sees our MCP tools in its tool list.     │  │
│  │  When the user says "build a castle", the model     │  │
│  │  decides which tools to call and in what order.     │  │
│  └────────────────────┬────────────────────────────────┘  │
│                       │ MCP Protocol (tool calls + results)│
└───────────────────────┼───────────────────────────────────┘
                        │
          ┌─────────────┼─────────────────┐
          │ SSE Connection                │
          │ http://localhost:8000/sse      │
          └─────────────┼─────────────────┘
                        │
┌───────────────────────┼───────────────────────────────────┐
│  UNREAL-MCP SERVER    │    (our code)                     │
│                       ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  FastMCP Server (server.py)                         │  │
│  │                                                     │  │
│  │  Registered Tools:                                  │  │
│  │    get_scene_state    → Query what's in the scene   │  │
│  │    spawn_actor        → Create any actor            │  │
│  │    modify_actor       → Move/rotate/scale           │  │
│  │    destroy_actor      → Remove an actor             │  │
│  │    set_actor_property → Set any UE property         │  │
│  │    get_actor_property → Read any UE property        │  │
│  │    execute_python_in_editor → Run UE Python scripts │  │
│  │    capture_viewport   → Take screenshot             │  │
│  │    run_console_command→ Execute UE console commands  │  │
│  │    find_assets        → Search project assets       │  │
│  └────────────────────┬────────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┼────────────────────────────────┐  │
│  │  WebSocket Bridge   │  (websocket.py)               │  │
│  │                     │                               │  │
│  │  send_ue_ws_command(object_path, function, params)  │  │
│  │  send_ue_ws_property(object_path, prop, value)      │  │
│  │  execute_python(script)                             │  │
│  └────────────────────┬────────────────────────────────┘  │
│                       │                                   │
└───────────────────────┼───────────────────────────────────┘
                        │
          ┌─────────────┼─────────────────┐
          │ WebSocket Connection          │
          │ ws://localhost:30020           │
          └─────────────┼─────────────────┘
                        │
┌───────────────────────┼───────────────────────────────────┐
│  UNREAL ENGINE        ▼                                   │
│                                                           │
│  Remote Control Web Interface Plugin (enabled)            │
│  Python Editor Script Plugin (enabled)                    │
│                                                           │
│  Receives commands, executes them, returns results.       │
│  Works with ANY project — no hardcoded paths.             │
└───────────────────────────────────────────────────────────┘
```

## What Each Layer Does

### Layer 1: The User's IDE
- The user types natural language in their IDE's chat sidebar
- The IDE's AI model (GPT, Claude, Gemini, etc.) processes the request
- The model sees our MCP tools and decides which ones to call
- **We don't control this layer — the user chooses their IDE and model**

### Layer 2: The MCP Server (Our Code)
- A Python process running `server.py`
- Exposes ~10 generalized tools via FastMCP on SSE
- Receives tool calls from the IDE, translates them to WebSocket commands
- Returns results back to the IDE
- **No AI logic inside — pure tool execution**

### Layer 3: The WebSocket Bridge
- `websocket.py` handles all communication with Unreal Engine
- Uses Unreal's Remote Control API protocol (JSON over WebSocket)
- Single connection point: `ws://localhost:30020`
- **Works with any Unreal project running on the same machine**

### Layer 4: Unreal Engine
- Receives and executes commands via the Remote Control plugin
- Can execute Python scripts via the Python Editor Script plugin
- Returns results (actor lists, property values, receipts)
- **The actual 3D work happens here**

## The Data Flow (Example)

User types: *"Move the house 500 units north"*

```
1. IDE AI model calls: modify_actor(actor_name="House_01", location=[500, 500, 0])
2. MCP server receives the tool call
3. websocket.py sends: SetActorLocation(NewLocation={X:500, Y:500, Z:0})
4. Unreal moves the actor
5. Unreal returns: success
6. MCP server returns: "House_01 moved to (500, 500, 0)"
7. IDE shows the result to the user
```
