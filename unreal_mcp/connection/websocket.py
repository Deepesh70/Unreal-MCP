"""
WebSocket Transport Layer for Unreal Engine Remote Control.

This module is the *only* place that opens WebSocket connections to
Unreal Engine.  Every MCP tool calls `send_ue_ws_command()` instead
of managing sockets directly.
"""

import json
import websockets
from typing import Any, Dict, Optional

from unreal_mcp.config.settings import UE_WS_URL


async def send_ue_ws_http_request(
    url: str,
    verb: str = "PUT",
    body: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Send a generic Unreal Remote Control HTTP-over-WebSocket request.

    Args:
        url:  Remote Control endpoint path (for example /remote/object/call).
        verb: HTTP verb (for example PUT, GET).
        body: JSON body for the endpoint.

    Returns:
        The full parsed JSON response from Unreal Engine.

    Raises:
        Exception: On connection failure or if Unreal reports an error.
    """
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": url,
            "Verb": verb,
            "Body": body or {},
        },
    }

    try:
        async with websockets.connect(UE_WS_URL) as ws:
            await ws.send(json.dumps(payload))

            response_str = await ws.recv()
            response_data = json.loads(response_str)

            error_msg = response_data.get("ResponseBody", {}).get("ErrorMessage")
            if error_msg:
                raise Exception(error_msg)

            return response_data

    except Exception as e:
        raise Exception(f"WebSocket Error: {str(e)}")


async def send_ue_ws_command(
    object_path: str,
    function_name: str,
    parameters: dict = None,
) -> dict:
    """
    Send a remote-control command to Unreal Engine via WebSocket.
    """
    body = {
        "objectPath": object_path,
        "functionName": function_name,
    }

    if parameters:
        body["parameters"] = parameters

    return await send_ue_ws_http_request(
        url="/remote/object/call",
        verb="PUT",
        body=body,
    )


async def send_ue_ws_property_update(
    object_path: str,
    property_name: str,
    property_value,
) -> dict:
    """
    Set a UObject property via Unreal Remote Control WebSocket.
    """
    return await send_ue_ws_http_request(
        url="/remote/object/property",
        verb="PUT",
        body={
            "objectPath": object_path,
            "propertyName": property_name,
            "access": "WRITE_ACCESS",
            "propertyValue": property_value,
        },
    )


async def send_ue_ws_property_read(
    object_path: str,
    property_name: str,
) -> dict:
    """
    Read a UObject property via Unreal Remote Control WebSocket.
    """
    return await send_ue_ws_http_request(
        url="/remote/object/property",
        verb="PUT",
        body={
            "objectPath": object_path,
            "propertyName": property_name,
            "access": "READ_ACCESS",
        },
    )


async def send_ue_ws_object_describe(object_path: str) -> dict:
    """
    Describe a UObject so tools can discover callable functions/properties.

    Unreal endpoints can vary by version/plugin, so try common options.
    """
    last_error = None
    for endpoint in ("/remote/object/describe", "/remote/object", "/remote/object/metadata"):
        try:
            return await send_ue_ws_http_request(
                url=endpoint,
                verb="PUT",
                body={"objectPath": object_path},
            )
        except Exception as e:
            last_error = e

    raise Exception(f"Could not describe object '{object_path}': {last_error}")
