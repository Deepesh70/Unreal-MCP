"""
WebSocket Transport Layer for Unreal Engine Remote Control.

This module is the *only* place that opens WebSocket connections to
Unreal Engine.  Every MCP tool calls `send_ue_ws_command()` instead
of managing sockets directly.
"""

import json
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
        async with websockets.connect(UE_WS_URL) as ws:
            await ws.send(json.dumps(payload))

            # Wait for Unreal's real-time response
            response_str = await ws.recv()
            response_data = json.loads(response_str)

            # Check if Unreal threw an internal error
            error_msg = response_data.get("ResponseBody", {}).get("ErrorMessage")
            if error_msg:
                raise Exception(error_msg)

            return response_data

    except Exception as e:
        raise Exception(f"WebSocket Error: {str(e)}")
