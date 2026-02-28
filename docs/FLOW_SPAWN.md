# 🏗️ Flow: Spawning an Actor

> Traces the complete path from agent prompt → Unreal Engine when the
> `spawn_actor` tool is called.

---

## Sequence Diagram

```
Agent (LLM)           server.py           tools/spawning.py       mappings/        connection/websocket.py     Unreal Engine
    │                     │                       │                    │                      │                      │
    │── SSE call ────────►│                       │                    │                      │                      │
    │  spawn_actor        │                       │                    │                      │                      │
    │  ("cube", 0,0,100)  │                       │                    │                      │                      │
    │                     │──mcp dispatches──────►│                    │                      │                      │
    │                     │                       │                    │                      │                      │
    │                     │                       │──get_asset_path──►│                      │                      │
    │                     │                       │  ("cube")          │                      │                      │
    │                     │                       │◄─ returns path ───│                      │                      │
    │                     │                       │  "/Engine/..."     │                      │                      │
    │                     │                       │                    │                      │                      │
    │                     │                       │──send_ue_ws_cmd──────────────────────────►│                      │
    │                     │                       │  SpawnActorFromObject                     │                      │
    │                     │                       │  {ObjectToUse, Location}                  │──WebSocket PUT──────►│
    │                     │                       │                    │                      │                      │
    │                     │                       │                    │                      │◄─ JSON response ─────│
    │                     │                       │◄─ response dict ──────────────────────────│                      │
    │                     │                       │                    │                      │                      │
    │                     │◄─ "Successfully..." ──│                    │                      │                      │
    │◄── result  ─────────│                       │                    │                      │                      │
```

---

## Step-by-Step

### 1. Agent sends tool call
The LLM agent (via `agent.py`) calls `spawn_actor("cube", x=0, y=0, z=100)` over the SSE transport.

### 2. MCP dispatches to `tools/spawning.py`
The `@mcp.tool()` decorator routes the call to `spawn_actor()` in `tools/spawning.py`.

### 3. Resolve the name via `mappings/`
```python
asset_path = get_asset_path("cube")
# → "/Engine/BasicShapes/Cube.Cube"
```
If the name is a shape, `mappings/assets.py` returns the asset path.
If not found, it falls through to `mappings/classes.py` for class-based spawning.

### 4. Send command via `connection/websocket.py`
```python
await send_ue_ws_command(
    object_path=_EDITOR_LIB,
    function_name="SpawnActorFromObject",
    parameters={"ObjectToUse": asset_path, "Location": {"X": 0, "Y": 0, "Z": 100}}
)
```

### 5. WebSocket transport
`websocket.py` wraps the call in an `"http"` message, opens a transient WS connection to `UE_WS_URL`, sends JSON, and waits for the response.

### 6. Return result
On success → `"Successfully spawned /Engine/BasicShapes/Cube.Cube at 0, 0, 100"`
On failure → `format_error()` from `utils/response.py` produces a helpful message.

---

## Files Involved

| File | Role |
|------|------|
| `tools/spawning.py` | Entry point, orchestration |
| `mappings/assets.py` | Name → asset path lookup |
| `mappings/classes.py` | Name → class path lookup (fallback) |
| `connection/websocket.py` | Sends WS command to UE |
| `config/settings.py` | Provides `UE_WS_URL` |
| `utils/response.py` | Error formatting |
