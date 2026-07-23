# 🐍 The Python Gateway — processor.py and the MCP Server

> How Python validates, repairs, and routes LLM output to Unreal Engine.

---

## Python's Role (Post-Refactor)

After The Great Refactor, Python's responsibilities are dramatically reduced:

| Before (Puppet Master) | After (Gateway) |
|------------------------|-----------------|
| Parse JSON ✅ | Parse JSON ✅ |
| Repair truncated JSON ✅ | Repair truncated JSON ✅ |
| Run spatial math loops ❌ REMOVED | Validate schema ✅ NEW |
| Calculate scale factors ❌ REMOVED | Discover CityManager ✅ NEW |
| Send 26 WebSocket calls ❌ REMOVED | Send 1 WebSocket call ✅ NEW |
| Track no state | Forward receipts |
| Write C++ files ✅ | Write C++ files ✅ (unchanged) |

---

## The Processing Pipeline

```
LLM Raw Output
    │
    ▼
┌─────────────────────────────┐
│ Step 1: Strip Code Fences   │  Remove ```json ... ``` if LLM wrapped it
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│ Step 2: Repair Truncation   │  Fix unclosed brackets, strings, braces
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│ Step 3: JSON Parse          │  json.loads() — fail here = fatal error
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│ Step 4: Schema Validation   │  Check required fields, types
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│ Step 5: Route by Intent     │  CreateClass → disk  |  Everything else → Unreal
└──────┬──────────────┬───────┘
       ▼              ▼
   Write .h/.cpp   Single WebSocket Call
   to disk         to ProcessBlueprint()
```

---

## JSON Repair — The Safety Net

LLMs operating near their token limit often produce truncated JSON. The `_repair_truncated_json()` function in `processor.py` handles this:

### What It Fixes

| Problem | Example | Fix |
|---------|---------|-----|
| Unclosed string | `{"name": "Hello` | Append `"` |
| Unclosed object | `{"name": "Hello"` | Append `}` |
| Unclosed array | `[{"name": "A"}` | Append `]` |
| Nested unclosed | `{"a": [{"b": "c"` | Append `"}]}` |

### How It Works

```python
def _repair_truncated_json(raw: str) -> str:
    # 1. Track whether we're inside a string literal
    # 2. If we end inside a string → close it with "
    # 3. Track bracket/brace depth with a stack
    # 4. Append closing characters in reverse order
    
    # Example: '{"Floors": 5, "Walls": [' 
    #   Stack after parsing: ['}', ']']
    #   Append: ']}'
    #   Result: '{"Floors": 5, "Walls": []}'
```

### When Repair Happens

If `json.loads()` fails on the raw content, Python tries the repair. If the repaired version parses successfully, it continues with a warning:

```
⚠️  LLM output was truncated — repaired JSON automatically.
   The generated output may be incomplete. Use a larger model for best results.
```

---

## Schema Validation (Phase 3)

After JSON parsing succeeds, Python validates the structure:

```python
def _validate_intent_schema(data: dict) -> tuple[bool, str]:
    intent = data.get("Intent", "")
    
    if intent == "Spawn":
        if "ID" not in data:
            return False, "Spawn requires an 'ID' field"
        if "RequestedLoc" not in data:
            return False, "Spawn requires a 'RequestedLoc' field"
        loc = data["RequestedLoc"]
        if not isinstance(loc, list) or len(loc) != 3:
            return False, "RequestedLoc must be an array of 3 numbers"
        # Type checks
        params = data.get("Parameters", {})
        if "Floors" in params and not isinstance(params["Floors"], int):
            return False, "Parameters.Floors must be an integer"
        ...
    
    elif intent == "BatchSpawn":
        if "Blueprints" not in data:
            return False, "BatchSpawn requires a 'Blueprints' array"
        if not isinstance(data["Blueprints"], list):
            return False, "Blueprints must be an array"
        # Validate each blueprint in the array
        for i, bp in enumerate(data["Blueprints"]):
            if "ID" not in bp:
                return False, f"Blueprint [{i}] requires an 'ID' field"
            ...
    
    elif intent == "Modify":
        if "TargetID" not in data:
            return False, "Modify requires a 'TargetID' field"
        ...
    
    elif intent == "Destroy":
        if "TargetID" not in data:
            return False, "Destroy requires a 'TargetID' field"
    
    elif intent == "ClearAll":
        pass  # No validation needed
    
    elif intent == "ScanArea":
        if "Center" not in data:
            return False, "ScanArea requires a 'Center' field"
        ...
    
    else:
        return False, f"Unknown Intent: '{intent}'"
    
    return True, ""
```

If validation fails, Python rejects the command and asks the LLM to fix it — the malformed data never reaches Unreal.

---

## City Manager Discovery

Python discovers the `AProceduralCityManager` actor at runtime:

```python
_manager_cache = None  # Module-level cache

async def _discover_city_manager() -> str:
    global _manager_cache
    if _manager_cache:
        return _manager_cache
    
    # Call GetAllLevelActors
    response = await send_ue_ws_command(
        object_path="/Script/UnrealEd.Default__EditorActorSubsystem",
        function_name="GetAllLevelActors",
    )
    actors = response.get("ResponseBody", {}).get("ReturnValue", [])
    
    # Find the city manager
    for actor_path in actors:
        if "ProceduralCityManager" in actor_path:
            _manager_cache = actor_path
            return actor_path
    
    raise Exception(
        "❌ No AProceduralCityManager found in the level.\n"
        "   Please place one in your map (drag from Content Browser)."
    )
```

The cache is module-level, so the discovery happens once per session. If the user reloads the level, restarting the Python server resets the cache.

---

## The Forwarding Call

Once the manager is discovered and the JSON is validated:

```python
async def _handle_unreal_intent(validated_json: str) -> str:
    manager_path = await _discover_city_manager()
    
    response = await send_ue_ws_command(
        object_path=manager_path,
        function_name="ProcessBlueprint",
        parameters={"JsonPayload": validated_json},
    )
    
    # C++ returns a JSON receipt string
    receipt = response.get("ResponseBody", {}).get("ReturnValue", "")
    return receipt
```

**That's it.** One call. The entire spatial math, HISM management, overlap detection, and auto-nudge happens inside Unreal C++.

---

## Legacy Compatibility

The old `"Action": "SpawnActor"` format is auto-migrated:

```python
# Old format
{"Action": "SpawnActor", "ClassToSpawn": "Building", 
 "Parameters": {"NumberOfFloors": 5, "X": 0, "Y": 0, "Z": 0}}

# Auto-migrated to
{"Intent": "Spawn", "ID": f"Legacy_{timestamp}", "Style": "Default",
 "RequestedLoc": [0, 0, 0], "Parameters": {"Floors": 5}}
```

This ensures that the old `BUILDER_SYSTEM_PROMPT` (which some cached LLM sessions might still use) continues to work during the transition.

---

## The MCP Server (server.py)

The MCP server is the transport layer that makes tools available to LLM agents:

```python
from unreal_mcp import mcp
mcp.run(transport="sse", host="localhost", port=8000)
```

The server exposes tools via Server-Sent Events (SSE) at `http://localhost:8000/sse`. Any MCP-compatible agent can connect and use the registered tools (spawn_actor, list_actors, set_actor_scale).

In Builder mode (`-b` flag), the agent bypasses the MCP tool-calling loop entirely and calls the LLM directly with the builder system prompt. The JSON output is processed by `processor.py`, which either writes C++ files to disk or forwards to Unreal via WebSocket.

---

## File Map

| File | What It Does |
|------|-------------|
| `server.py` | Starts the FastMCP server on port 8000 |
| `agent.py` | CLI launcher — picks the LLM backend and mode |
| `agents/base.py` | Agent runner + system prompts + REPL |
| `agents/processor.py` | JSON repair, validation, routing, C++ file writing |
| `agents/orchestrator.py` | (Phase 3) Token-aware complexity routing |
| `unreal_mcp/__init__.py` | Creates the shared FastMCP instance |
| `unreal_mcp/config/settings.py` | All configurable values (URLs, paths, macros) |
| `unreal_mcp/connection/websocket.py` | WebSocket transport to Unreal |
| `unreal_mcp/tools/` | MCP tool registrations (spawn, list, transform) |
| `unreal_mcp/mappings/` | Asset/class name-to-path lookups |
| `unreal_mcp/utils/response.py` | Response parsing helpers |
