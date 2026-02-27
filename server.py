import asyncio
import json
import websockets
from fastmcp import FastMCP

# 1. Initialize the MCP Server
mcp = FastMCP("UnrealHPC_Server")
UE_WS_URL = "ws://127.0.0.1:30020"

async def send_ue_ws_command(object_path: str, function_name: str, parameters: dict = None):
    """Wraps the RC HTTP payload into the WebSocket format with strict error catching."""
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": "/remote/object/call",
            "Verb": "PUT",
            "Body": {
                "objectPath": object_path,
                "functionName": function_name
            }
        }
    }
    if parameters:
        payload["Parameters"]["Body"]["parameters"] = parameters

    try:
        async with websockets.connect(UE_WS_URL) as ws:
            await ws.send(json.dumps(payload))
            response_str = await ws.recv()
            response_data = json.loads(response_str)
            
            if "ErrorMessage" in response_data:
                raise Exception(f"WebSocket Error: {response_data['ErrorMessage']}")
            
            body = response_data.get("ResponseBody", {})
            response_code = response_data.get("ResponseCode", 200)
            
            if response_code not in [200, 202]:
                error_msg = body.get("ErrorMessage") if isinstance(body, dict) else "Unknown Error"
                raise Exception(f"Unreal API Error {response_code}: {error_msg}")
                
            if isinstance(body, dict) and body.get("ErrorMessage"):
                raise Exception(f"Execution Error: {body['ErrorMessage']}")
                
            return response_data
            
    except Exception as e:
        raise Exception(str(e))

@mcp.tool()
async def spawn_actor(actor_class_or_asset: str, x: float = 0, y: float = 0, z: float = 0) -> str:
    """
    Spawns an actor. Use 'cylinder' for pillars, 'cube' for bases, 'sphere' for caps.
    Returns the EXACT_ACTOR_PATH which is required for scaling or moving.
    """
    actor_lower = actor_class_or_asset.lower()
    asset_map = {
        "cube": "/Engine/BasicShapes/Cube.Cube",
        "sphere": "/Engine/BasicShapes/Sphere.Sphere",
        "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
        "plane": "/Engine/BasicShapes/Plane.Plane"
    }

    try:
        if actor_lower in asset_map:
            response = await send_ue_ws_command(
                object_path="/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
                function_name="SpawnActorFromObject",
                parameters={
                    "ObjectToUse": asset_map[actor_lower],
                    "Location": {"X": x, "Y": y, "Z": z}
                }
            )
        else:
            return f"Spawn Failed: Unknown asset '{actor_class_or_asset}'. Use cylinder, cube, or sphere."
            
        actor_path = response.get("ResponseBody", {}).get("ReturnValue")
        if isinstance(actor_path, dict):
            actor_path = actor_path.get("ObjectPath", str(actor_path))
            
        if not actor_path:
            raise Exception("Unreal did not return a valid ObjectPath.")
            
        return f"Success. Spawned at ({x}, {y}, {z}). EXACT_ACTOR_PATH: {actor_path}"
        
    except Exception as e:
        return f"Spawn Failed: {str(e)}"

@mcp.tool()
async def set_actor_transform(actor_path: str, scale_x: float, scale_y: float, scale_z: float, loc_x: float, loc_y: float, loc_z: float) -> str:
    """
    Combines scaling and locating into a single atomic network call for HPC efficiency.
    You MUST provide the exact actor_path returned by the spawn tool.
    """
    try:
        await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorScale3D",
            parameters={"NewScale3D": {"X": scale_x, "Y": scale_y, "Z": scale_z}}
        )
        await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorLocation",
            parameters={"NewLocation": {"X": loc_x, "Y": loc_y, "Z": loc_z}, "bSweep": False}
        )
        return f"Successfully transformed {actor_path.split('.')[-1]}."
    except Exception as e:
        return f"Transform Failed: {str(e)}. Did you use the correct exact path?"

@mcp.tool()
async def delete_actor(actor_path: str) -> str:
    """Deletes an actor if you made a mistake. Requires the EXACT_ACTOR_PATH."""
    try:
        await send_ue_ws_command(
            object_path="/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
            function_name="DestroyActor",
            parameters={"ActorToDestroy": actor_path}
        )
        return f"Successfully deleted {actor_path}"
    except Exception as e:
        return f"Delete Failed: {str(e)}"

if __name__ == "__main__":
    print("🚀 Starting FastMCP Server on port 8000...")
    mcp.run(transport="sse", host="localhost", port=8000)