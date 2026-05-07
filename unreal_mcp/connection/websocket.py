"""
WebSocket Transport Layer for Unreal Engine Remote Control.

This module is the *only* place that opens WebSocket connections to
Unreal Engine.  Every MCP tool calls `send_ue_ws_command()` instead
of managing sockets directly.

Transport functions:
  - send_ue_ws_command()   — Call any UFunction on any UObject
  - send_ue_ws_property()  — Set a property on a UObject
  - get_ue_ws_property()   — Read a property from a UObject
  - send_console_command() — Execute UE console commands
  - execute_python()       — Run Python scripts inside UE's interpreter
"""

import json
import os
import asyncio
import tempfile
import textwrap
import websockets

from unreal_mcp.config.settings import UE_WS_URL


async def send_ue_ws_command(
    object_path: str,
    function_name: str,
    parameters: dict = None,
) -> dict:
    """
    Send a remote-control command to Unreal Engine via WebSocket.

    Wraps the standard Remote Control HTTP payload into the format
    Unreal's WebSocket server expects, opens a transient connection,
    and returns the parsed JSON response.

    Args:
        object_path:   The UObject path to call the function on.
        function_name: The name of the UFunction to invoke.
        parameters:    Optional dict of function parameters.

    Returns:
        The full parsed JSON response from Unreal Engine.

    Raises:
        Exception: On connection failure or if Unreal reports an error.
    """
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": "/remote/object/call",
            "Verb": "PUT",
            "Body": {
                "objectPath": object_path,
                "functionName": function_name,
            },
        },
    }

    # Inject parameters into the Body if they exist
    if parameters:
        payload["Parameters"]["Body"]["parameters"] = parameters

    try:
        async with websockets.connect(UE_WS_URL, ping_timeout=120, close_timeout=120) as ws:
            await ws.send(json.dumps(payload))

            # Wait for Unreal's real-time response
            response_str = await ws.recv()
            response_data = json.loads(response_str)

            # Check if Unreal threw an internal error
            error_msg = response_data.get("ResponseBody", {}).get("ErrorMessage")
            if error_msg:
                raise Exception(error_msg)

            return response_data

    except ConnectionRefusedError:
        raise Exception("Unreal Engine API is offline. Please start Unreal Engine and ensure the Remote Control Web Interface plugin is enabled.")
    except OSError as e:
        error_str = str(e)
        if "1225" in error_str or "10061" in error_str or "Connection refused" in error_str:
            raise Exception("Unreal Engine API is offline. Please start Unreal Engine and ensure the Remote Control Web Interface plugin is enabled.")
        raise Exception(f"WebSocket Error: {error_str}")
    except Exception as e:
        error_str = str(e)
        if "1225" in error_str or "10061" in error_str or "refused" in error_str.lower():
            raise Exception("Unreal Engine API is offline. Please start Unreal Engine and ensure the Remote Control Web Interface plugin is enabled.")
        raise Exception(f"WebSocket Error: {error_str}")


async def send_ue_ws_property(
    object_path: str,
    property_name: str,
    property_value,
) -> dict:
    """
    Set a property on a UObject via Unreal's Remote Control WebSocket.
    Uses /remote/object/property endpoint.
    """
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": "/remote/object/property",
            "Verb": "PUT",
            "Body": {
                "objectPath": object_path,
                "propertyName": property_name,
                "propertyValue": property_value,
            },
        },
    }

    try:
        async with websockets.connect(UE_WS_URL, ping_timeout=120, close_timeout=120) as ws:
            await ws.send(json.dumps(payload))
            response_str = await ws.recv()
            return json.loads(response_str)
    except Exception:
        return {}  # Property setting is non-critical


async def get_ue_ws_property(
    object_path: str,
    property_name: str,
) -> dict:
    """
    Read a property from a UObject via Unreal's Remote Control WebSocket.
    Uses /remote/object/property endpoint.
    """
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": "/remote/object/property",
            "Verb": "PUT",
            "Body": {
                "objectPath": object_path,
                "propertyName": property_name,
                "access": "READ_ACCESS",
            },
        },
    }

    try:
        async with websockets.connect(UE_WS_URL, ping_timeout=120, close_timeout=120) as ws:
            await ws.send(json.dumps(payload))
            response_str = await ws.recv()
            return json.loads(response_str)
    except Exception:
        return {}


async def send_console_command(command: str) -> dict:
    """
    Execute a console command in Unreal Engine.

    NOTE: Requires "Enable Remote Console Execution" to be ON in
    Project Settings → Remote Control. If not enabled, this will return
    an error.

    Args:
        command: The console command string to execute.

    Returns:
        The response from Unreal Engine.
    """
    # Try via the HTTP batch endpoint first (more broadly supported)
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": "/remote/object/call",
            "Verb": "PUT",
            "Body": {
                "objectPath": "/Script/Engine.Default__KismetSystemLibrary",
                "functionName": "ExecuteConsoleCommand",
                "parameters": {
                    "WorldContextObject": "",
                    "Command": command,
                },
            },
        },
    }

    try:
        async with websockets.connect(UE_WS_URL, ping_timeout=120, close_timeout=120) as ws:
            await ws.send(json.dumps(payload))
            response_str = await ws.recv()
            result = json.loads(response_str)

            # Check if console execution is disabled
            error_msg = result.get("ResponseBody", {}).get("errorMessage", "")
            if "not enabled" in error_msg.lower():
                raise Exception(
                    "Remote console execution is disabled in Unreal Engine.\n"
                    "To enable: Edit → Project Settings → search 'Remote Control' → "
                    "Enable 'Allow Remote Console Execution'"
                )

            return result
    except Exception as e:
        if "not enabled" in str(e).lower() or "console" in str(e).lower():
            raise  # Re-raise the informative error
        raise Exception(f"Console command failed: {e}")


async def execute_python(script: str, timeout: float = 10.0) -> str:
    """
    Execute a Python script inside Unreal Engine's embedded interpreter.

    The script has full access to `import unreal` and all UE Python APIs.

    Tries two approaches:
    1. Write script to temp file + execute via `py` console command
    2. If console commands are disabled, returns instructions to enable them

    Args:
        script: Python source code to execute inside UE.
        timeout: Max seconds to wait for script completion.

    Returns:
        The captured output or error message from the script execution.
    """
    # Create temp paths (use forward slashes for UE compatibility)
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "ue_mcp_script.py").replace("\\", "/")
    output_path = os.path.join(temp_dir, "ue_mcp_output.txt").replace("\\", "/")

    # Clean up old output file
    if os.path.exists(output_path):
        os.remove(output_path)

    # Wrap the user's script to capture output and errors
    wrapped_script = (
        'import sys, io, traceback\n'
        f'_ue_mcp_output_path = r"{output_path}"\n'
        '_ue_mcp_stdout = io.StringIO()\n'
        '_ue_mcp_old_stdout = sys.stdout\n'
        'sys.stdout = _ue_mcp_stdout\n'
        'try:\n'
        f'{textwrap.indent(script, "    ")}\n'
        '    _result = _ue_mcp_stdout.getvalue()\n'
        '    with open(_ue_mcp_output_path, "w", encoding="utf-8") as _f:\n'
        '        _f.write("SUCCESS\\n" + _result)\n'
        'except Exception as _e:\n'
        '    with open(_ue_mcp_output_path, "w", encoding="utf-8") as _f:\n'
        '        _f.write("ERROR\\n" + traceback.format_exc())\n'
        'finally:\n'
        '    sys.stdout = _ue_mcp_old_stdout\n'
    )

    # Write the wrapped script to temp file
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(wrapped_script)

    # Execute via UE console command: py "path/to/script.py"
    try:
        await send_console_command(f'py "{script_path}"')
    except Exception as e:
        error_msg = str(e)
        if "not enabled" in error_msg.lower():
            return (
                "ERROR: Remote console execution is disabled in Unreal Engine.\n"
                "To enable: Edit > Project Settings > search 'Remote Control' > "
                "Enable 'Allow Remote Console Execution'\n"
                "After enabling, restart the test."
            )
        return f"Failed to send script to Unreal: {e}"

    # Poll for the output file (script runs async in UE's game thread)
    elapsed = 0.0
    poll_interval = 0.3
    while elapsed < timeout:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Clean up temp files
                try:
                    os.remove(script_path)
                    os.remove(output_path)
                except OSError:
                    pass
                return content
            except Exception:
                continue  # File might still be being written

    return f"Timeout: Script did not produce output within {timeout}s. It may still be running in Unreal."
