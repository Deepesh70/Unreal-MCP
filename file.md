# 🎮 GEP Worldwide Interview Masterclass: Unreal-MCP Code-by-Code Deep Mastery
## Complete Internal Architecture, Every Module Explained, MCP Protocol Internals, WebSocket Transport, Tool Registration, and Interviewer Defense

> **Directory**: `study/15_Unreal_MCP_Code_By_Code_Mastery.md`  
> **Scope**: Line-by-line internal mastery of the entire `Unreal-MCP` codebase — What MCP is, how FastMCP works, WebSocket transport to UE5's Remote Control API, tool registration lifecycle, scene querying, actor spawning, material application, Python script injection into UE5's embedded interpreter, and asset import pipeline.

---

# 1. WHAT IS MCP (MODEL CONTEXT PROTOCOL)?

**MCP** is an open protocol created by Anthropic that standardizes how AI agents (LLMs) connect to external tools and data sources. Think of it as **USB-C for AI** — a universal interface that lets any AI model call functions on any external system.

```
=====================================================================================
                         MCP PROTOCOL ARCHITECTURE
=====================================================================================

[ AI AGENT (LLM Client) ]
        |
        | MCP Protocol Layer (JSON-RPC 2.0 Messages)
        | Transport: SSE (Server-Sent Events) or stdio (Standard I/O Pipes)
        v
[ MCP SERVER (Your Python Code) ]
  |-- Exposes "Tools" (functions the AI can call)
  |-- Exposes "Resources" (data the AI can read)
  |-- Exposes "Prompts" (templates the AI can use)
        |
        v (Your server calls external systems)
[ EXTERNAL SYSTEM (Unreal Engine, Database, API, etc.) ]
=====================================================================================
```

### Why MCP Matters (Interview Answer):
> "Before MCP, every AI integration was a custom one-off — you'd write a specific plugin for Claude, another for GPT, another for Gemini. MCP standardizes this into a single protocol. I write ONE MCP server, and ANY MCP-compatible client can use it. It's like how REST standardized web APIs — MCP standardizes AI-to-tool communication."

---

# 2. FASTMCP FRAMEWORK & TOOL REGISTRATION LIFECYCLE

**FastMCP** is a Python framework that handles all MCP protocol boilerplate — JSON-RPC serialization, transport management, tool schema generation from Python type hints.

### How Your `__init__.py` Works:

```python
# File: unreal_mcp/__init__.py

from fastmcp import FastMCP

# Step 1: Create a SINGLE shared FastMCP instance for the entire server
mcp = FastMCP(
    "UnrealMCP",
    instructions="You are connected to a LIVE Unreal Engine editor via MCP tools..."
)

# Step 2: Import the tools package — this triggers ALL @mcp.tool() decorators to fire
from unreal_mcp import tools  # noqa: E402, F401
```

### The Decorator Registration Pattern:

When Python imports a module containing `@mcp.tool()`, the decorator **immediately registers** the function as an MCP tool on the shared `mcp` instance. This is a **side-effect import pattern** — the import itself causes registration.

```python
# File: unreal_mcp/tools/__init__.py
# Each import causes @mcp.tool() decorators to register tools

from . import spawning     # Registers spawn_actor tool
from . import actors       # Registers list_actors tool
from . import scene        # Registers get_scene_state tool
from . import modify       # Registers modify_actor, destroy_actor tools
from . import scripting    # Registers execute_python_in_editor tool
from . import health       # Registers check_connection tool
from . import materials    # Registers set_material, list_materials tools
from . import import_asset # Registers import_asset, add_starter_content tools
# ... etc.
```

### Interview Defense: "How does @mcp.tool() work internally?"
> "FastMCP's `@mcp.tool()` is a Python decorator that inspects the function's type hints and docstring at import time. It auto-generates a JSON Schema describing the tool's parameters (name, type, description, required/optional) and registers it on the FastMCP instance. When an AI client requests the tool list, FastMCP serves these schemas. When the AI calls a tool, FastMCP deserializes the JSON arguments, calls my Python function, and serializes the return value back as a JSON-RPC response."

---

# 3. WEBSOCKET TRANSPORT LAYER (connection/websocket.py)

This is the **ONLY module that talks to Unreal Engine**. Every tool calls functions from here.

### 3.1 `send_ue_ws_command()` — The Core Transport Function

```python
async def send_ue_ws_command(
    object_path: str,        # UObject path (e.g. "/Script/UnrealEd.Default__EditorActorSubsystem")
    function_name: str,      # UFunction name (e.g. "GetAllLevelActors")
    parameters: dict = None, # Optional function arguments
) -> dict:
```

**How it works internally:**

1. **Constructs a JSON payload** wrapping UE5's Remote Control HTTP format inside a WebSocket message:
   ```json
   {
     "MessageName": "http",
     "Parameters": {
       "Url": "/remote/object/call",
       "Verb": "PUT",
       "Body": {
         "objectPath": "/Script/UnrealEd.Default__EditorActorSubsystem",
         "functionName": "GetAllLevelActors",
         "parameters": {}
       }
     }
   }
   ```

2. **Opens a transient WebSocket connection** to `ws://127.0.0.1:30020` (UE5's Remote Control port).

3. **Sends the JSON payload** and **awaits the response** from UE5's C++ Reflection System.

4. **Parses the response** and returns the JSON data. Checks for `ErrorMessage` in the response body.

### Interview Defense: "Why WebSocket and not REST?"
> "UE5's Remote Control plugin exposes both HTTP and WebSocket interfaces. I chose WebSocket because it supports real-time bidirectional communication — essential for operations like `execute_python()` where the script runs asynchronously on UE5's game thread and I need to poll for completion. WebSocket also avoids HTTP connection setup overhead for rapid sequential tool calls during a build session."

### 3.2 `execute_python()` — Running Python Inside UE5's Interpreter

This is the most sophisticated transport function. UE5 has an **embedded CPython interpreter** (`import unreal`) that can manipulate the editor:

```python
async def execute_python(script: str, timeout: float = 10.0) -> str:
```

**How it works step-by-step:**

1. **Writes the Python script** to a temporary file on disk (`ue_mcp_script.py`).
2. **Wraps the script** with stdout capture and error handling (redirects `sys.stdout` to `StringIO`, catches exceptions to a file).
3. **Sends a UE console command** (`py "path/to/script.py"`) via WebSocket, which triggers UE5's embedded Python interpreter to execute the script on the **game thread**.
4. **Polls for the output file** (`ue_mcp_output.txt`) with 0.3s intervals up to the timeout. UE5's Python execution is async relative to the MCP server process.
5. **Reads the output file** (prefixed with `SUCCESS` or `ERROR`) and returns the result.
6. **Cleans up** temporary files.

### Interview Defense: "Why temp file polling instead of direct response?"
> "UE5's Python interpreter runs on the game thread, which is separate from the WebSocket handler thread. There's no direct callback mechanism from UE5's Python back to my WebSocket connection. The temp file acts as a cross-process communication channel — my MCP server writes the script, UE5's game thread executes it and writes the output, and my server polls for the result. It's similar to how Unix inter-process communication uses files as shared state."

---

# 4. SCENE QUERYING: `get_scene_state()` — THE AI'S EYES

This is the **most important tool** in the system. Before the AI does anything, it must see what exists.

**What it does:**
1. Calls `GetAllLevelActors` on UE5's `EditorActorSubsystem` to get all actor paths.
2. **Filters noise actors** (HLOD, Landscape, WorldSettings, Navigation) — these are auto-generated UE5 environment actors that would confuse the AI.
3. **Classifies each actor** by inferring type from name patterns (StaticMeshActor, PointLight, CameraActor, etc.).
4. **Enriches with location data** (calls `GetActorLocation` per actor, applies proximity filtering if requested).
5. **Resolves mesh names** for StaticMeshActors by reading the `StaticMesh` property from the `StaticMeshComponent0`.
6. **Builds a natural-language summary**: "Scene has 24 actors: 15 static meshes (Cube, Wall, Table), 3 point lights, 1 camera."

### Interview Defense: "Why filter noise actors?"
> "A typical UE5 level contains 50-200+ auto-generated actors (HLOD proxies, landscape streaming proxies, world settings, navigation volumes) that the AI doesn't need to know about. Without filtering, the AI would see '200 unknown actors' and waste tokens processing irrelevant data. By filtering noise and classifying user-placed actors, I give the AI a clean, actionable scene description."

---

# 5. MAPPINGS LAYER: FRIENDLY NAMES → UE5 ASSET PATHS

### `mappings/assets.py` — ASSET_MAP

```python
ASSET_MAP = {
    "cube":     "/Engine/BasicShapes/Cube.Cube",
    "sphere":   "/Engine/BasicShapes/Sphere.Sphere",
    "chair":    "/Game/StarterContent/Props/SM_Chair.SM_Chair",
    "table_round": "/Game/StarterContent/Props/SM_TableRound.SM_TableRound",
    # ... 15+ mappings
}
```

### `mappings/materials.py` — MATERIAL_MAP

```python
MATERIAL_MAP = {
    "steel":    "/Game/StarterContent/Materials/M_Metal_Steel.M_Metal_Steel",
    "brick":    "/Game/StarterContent/Materials/M_Brick_Clay_New.M_Brick_Clay_New",
    "wood":     "/Game/StarterContent/Materials/M_Wood_Oak.M_Wood_Oak",
    "grass":    "/Game/StarterContent/Materials/M_Ground_Grass.M_Ground_Grass",
    # ... 20+ mappings
}
```

### Interview Defense: "Why a mapping layer instead of raw paths?"
> "Unreal Engine asset paths are long, error-prone strings like `/Game/StarterContent/Materials/M_Metal_Steel.M_Metal_Steel`. An AI agent can't reliably generate these. The mapping layer provides a single source of truth — the AI says 'steel' and gets the exact UE5 path. This also decouples the AI's vocabulary from UE5's internal asset structure, so if Epic renames a path in a future engine version, I change it in one place."

---

# 6. HEALTH CHECK SYSTEM (`health.py`)

The `check_connection()` tool verifies **every link in the chain** before the AI starts working:

1. **MCP Server** — Always passes (you're calling it).
2. **UE5 WebSocket** — Can we reach `ws://127.0.0.1:30020`?
3. **Remote Control API** — Can we call a UFunction and get a response?
4. **Python Editor Plugin** — Can we execute Python inside UE5?

Returns a clear ✅/❌ status board with specific fix instructions for each failure point.

---

# 7. CLI ENTRY POINT (`cli.py`)

```python
def main():
    # Supports 3 launch modes:
    # 1. `unreal-mcp`           → SSE mode on port 8000
    # 2. `unreal-mcp --stdio`   → stdio mode (IDE auto-launch)
    # 3. `unreal-mcp --port 9000` → SSE on specific port

    # Auto port fallback: If port 8000 is taken, tries 8001, 8002, etc.
    port = _find_available_port(requested_port)

    # Version compatibility: Handles FastMCP v1.x, v2.x, and v3.x APIs
    try:
        mcp.run(transport="sse", host=host, port=port)  # v3.x
    except TypeError:
        uvicorn.run(mcp.sse_app(), host=host, port=port)  # v2.x
```

### Interview Defense: "Why support multiple FastMCP versions?"
> "FastMCP evolved its API significantly between v1, v2, and v3. Since this is an open-source project used by the community, I needed backward compatibility. The try/except chain detects the installed version at runtime and uses the appropriate API — v3.x's native `mcp.run()`, v2.x's `sse_app()`, or v1.x's `http_app()`. This prevents breaking installations when users have different FastMCP versions."

---

# 8. COMPLETE MODULE DEPENDENCY MAP

```
=====================================================================================
                     UNREAL-MCP MODULE DEPENDENCY GRAPH
=====================================================================================

cli.py ──────────────────────────> __init__.py (mcp instance)
                                        |
                                        v
                                   tools/__init__.py
                                   (imports all tool modules)
                                        |
            ┌───────────┬───────────┬───┴───┬──────────┬──────────┐
            v           v           v       v          v          v
        spawning.py  scene.py  modify.py  health.py  materials.py  scripting.py
            |           |           |       |          |          |
            └───────────┴───────────┴───┬───┴──────────┴──────────┘
                                        |
                                        v
                              connection/websocket.py
                        (send_ue_ws_command, execute_python)
                                        |
                                        v
                              config/settings.py (UE_WS_URL)
                                        |
                                        v
                              mappings/ (assets.py, materials.py)
                                        |
                                        v
                              utils/response.py (extract_return_value)
=====================================================================================
```