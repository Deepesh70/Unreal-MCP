# 📐 Flow: Transforming an Actor (Scale)

> Traces the complete path when the `set_actor_scale` tool is called.

---

## Sequence Diagram

```
Agent (LLM)        tools/transform.py    connection/websocket.py     Unreal Engine
    │                     │                       │                      │
    │── set_actor_scale ─►│                       │                      │
    │   (path, 5, 5, 5)   │                       │                      │
    │                     │── send_ue_ws_cmd ────►│                      │
    │                     │   SetActorScale3D     │── WebSocket PUT ────►│
    │                     │   {NewScale3D: ...}    │                      │
    │                     │                       │◄── JSON response ────│
    │                     │◄── response dict ─────│                      │
    │                     │                       │                      │
    │◄── "Successfully    │                       │                      │
    │     scaled..." ─────│                       │                      │
```

---

## Step-by-Step

### 1. MCP dispatches to `tools/transform.py`
The agent provides the full actor path (obtained from `list_actors`) and target scale values.

### 2. Send command via `connection/`
```python
await send_ue_ws_command(
    object_path=actor_path,
    function_name="SetActorScale3D",
    parameters={"NewScale3D": {"X": scale_x, "Y": scale_y, "Z": scale_z}}
)
```
Note: The `object_path` here is the **actor itself**, not a library subsystem.

### 3. Return result
Extracts the short name from the actor path and returns a confirmation string.
On error → `format_error()` from `utils/response.py` adds a troubleshooting tip.

---

## Files Involved

| File | Role |
|------|------|
| `tools/transform.py` | Entry point, orchestration |
| `connection/websocket.py` | Sends WS command to UE |
| `config/settings.py` | Provides `UE_WS_URL` |
| `utils/response.py` | Error formatting |

---

## Extending This Module

To add **move** or **rotate** tools, add them in `tools/transform.py` alongside `set_actor_scale`:

```python
@mcp.tool()
async def set_actor_location(actor_path: str, x: float, y: float, z: float) -> str:
    ...

@mcp.tool()
async def set_actor_rotation(actor_path: str, pitch: float, yaw: float, roll: float) -> str:
    ...
```
