# 📋 Flow: Listing Actors

> Traces the complete path when the `list_actors` tool is called.

---

## Sequence Diagram

```
Agent (LLM)        tools/actors.py       connection/websocket.py     utils/response.py     Unreal Engine
    │                     │                       │                        │                      │
    │── list_actors() ───►│                       │                        │                      │
    │                     │                       │                        │                      │
    │                     │── send_ue_ws_cmd ────►│                        │                      │
    │                     │   GetAllLevelActors    │── WebSocket PUT ──────►│                      │
    │                     │                       │                        │                      │
    │                     │                       │◄── JSON response ──────│                      │
    │                     │◄── response dict ─────│                        │                      │
    │                     │                       │                        │                      │
    │                     │── extract_return_value ──────────────────────►│                      │
    │                     │◄── actor list ───────────────────────────────│                      │
    │                     │                       │                        │                      │
    │                     │── format_actor_list ─────────────────────────►│                      │
    │                     │◄── formatted string ────────────────────────│                      │
    │                     │                       │                        │                      │
    │◄── "Actors in..." ──│                       │                        │                      │
```

---

## Step-by-Step

### 1. MCP dispatches to `tools/actors.py`
The `@mcp.tool()` decorator routes the `list_actors` call.

### 2. Query Unreal via `connection/`
```python
response = await send_ue_ws_command(
    object_path="/Script/UnrealEd.Default__EditorActorSubsystem",
    function_name="GetAllLevelActors",
)
```

### 3. Parse response via `utils/response.py`
```python
actors = extract_return_value(response)
# → ["/Game/Level...:StaticMeshActor_0", "/Game/Level...:PointLight_1", ...]
```

### 4. Format output via `utils/response.py`
```python
return format_actor_list(actors)
# → "Actors in level:\nStaticMeshActor_0 (Path: /Game/...)\n..."
```

---

## Files Involved

| File | Role |
|------|------|
| `tools/actors.py` | Entry point, orchestration |
| `connection/websocket.py` | Sends WS command to UE |
| `utils/response.py` | Parses ReturnValue + formats output |
| `config/settings.py` | Provides `UE_WS_URL` |
