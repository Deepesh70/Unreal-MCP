# 🌐 WebSocket Bridge — How Python Talks to Unreal

## Overview

The WebSocket bridge (`unreal_mcp/connection/websocket.py`) is the ONLY communication channel between the MCP server and Unreal Engine. Every tool call eventually goes through one of these transport functions.

## Transport Functions

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `send_ue_ws_command()` | `/remote/object/call` | Call any UFunction on any UObject |
| `send_ue_ws_property()` | `/remote/object/property` (PUT) | Set a property on a UObject |
| `get_ue_ws_property()` | `/remote/object/property` (READ) | Read a property from a UObject |
| `send_console_command()` | `/remote/object/call` → `ExecuteConsoleCommand` | Run UE console commands |
| `execute_python()` | Console `py "script.py"` + file I/O | Run Python scripts inside UE |

## Protocol Details

All communication uses Unreal's **Remote Control WebSocket** protocol. The WebSocket server runs at `ws://localhost:30020` (default).

### Message Format

Every message follows this pattern:

```json
{
    "MessageName": "http",
    "Parameters": {
        "Url": "/remote/object/call",
        "Verb": "PUT",
        "Body": {
            "objectPath": "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
            "functionName": "SpawnActorFromClass",
            "parameters": {
                "ActorClass": "/Script/Engine.PointLight",
                "Location": {"X": 0, "Y": 0, "Z": 500}
            }
        }
    }
}
```

### Connection Lifecycle

Each command opens a **transient** WebSocket connection:
1. Connect to `ws://localhost:30020`
2. Send JSON payload
3. Receive response
4. Close connection

This is simple but means each tool call has connection overhead. For batch operations, the AI should use `execute_python_in_editor` to send one script that does multiple things.

## How `execute_python()` Works

This is the most complex transport function. It can't just "call a Python function" — it needs to:

1. **Write** the Python script to a temp file on disk
2. **Wrap** it in try/except to capture stdout and errors to an output file
3. **Execute** via the UE console command `py "path/to/script.py"`
4. **Poll** for the output file to appear (script runs async in UE's game thread)
5. **Read** the output file and return the result
6. **Clean up** temp files

```
MCP Server                          Unreal Engine
    │                                    │
    ├── Write script.py to temp dir      │
    ├── Send: py "C:/temp/script.py" ──► │
    │                                    ├── Python interpreter runs script
    │                                    ├── Script writes output.txt
    ├── Poll for output.txt ◄────────────┤
    ├── Read output.txt                  │
    ├── Clean up temp files              │
    └── Return result                    │
```

### Timeout Behavior

The default timeout is 10 seconds. If the script doesn't produce an output file within that time, the function returns a timeout message. The script may still be running in Unreal — it just means we stopped waiting.

For long-running scripts (e.g., heavy geometry operations), increase the timeout:
```python
result = await execute_python(script, timeout=30.0)
```

## Error Handling

All transport functions handle three categories of errors:

1. **Connection refused** → "Unreal Engine API is offline" message
2. **UE internal error** → ErrorMessage from response body is raised
3. **Timeout** → Script didn't complete in time

The MCP tools catch these and return user-friendly error messages via `format_error()`.
