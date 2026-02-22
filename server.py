import asyncio
import json
import websockets
from fastmcp import FastMCP

# 1. Initialize the MCP Server
mcp = FastMCP("UnrealToyWebSocket")

# 2. Configuration - The "Telephone Line" to Unreal
UE_WS_URL = "ws://127.0.0.1:30020"

async def send_ue_ws_command(object_path: str, function_name: str, parameters: dict = None):
    """
    Helper function that wraps the standard Remote Control HTTP payload 
    into the format Unreal's WebSocket server expects.
    """
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
    
    # Inject parameters into the Body if they exist
    if parameters:
        payload["Parameters"]["Body"]["parameters"] = parameters

    try:
        # Open a transient WebSocket connection for the tool call
        async with websockets.connect(UE_WS_URL) as ws:
            await ws.send(json.dumps(payload))
            
            # Wait for Unreal's real-time response
            response_str = await ws.recv()
            response_data = json.loads(response_str)
            
            # Check if Unreal threw an internal error
            if response_data.get("ResponseBody", {}).get("ErrorMessage"):
                raise Exception(response_data["ResponseBody"]["ErrorMessage"])
                
            return response_data
            
    except Exception as e:
        raise Exception(f"WebSocket Error: {str(e)}")


@mcp.tool()
async def spawn_actor(actor_class_or_asset: str, x: float = 0, y: float = 0, z: float = 0) -> str:
    """
    Spawns an actor or basic shape in the Unreal level at the specified coordinates.
    Example: 'pointlight', 'cube', 'sphere', '/Script/Engine.PointLight'
    """
    actor_lower = actor_class_or_asset.lower()
    
    # Map friendly names to asset paths (for basic shapes)
    asset_map = {
        "cube": "/Engine/BasicShapes/Cube.Cube",
        "sphere": "/Engine/BasicShapes/Sphere.Sphere",
        "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
        "cone": "/Engine/BasicShapes/Cone.Cone",
        "plane": "/Engine/BasicShapes/Plane.Plane"
    }
    
    # Map friendly names to actor classes
    class_map = {
        "pointlight": "/Script/Engine.PointLight",
        "spotlight": "/Script/Engine.SpotLight",
        "directional_light": "/Script/Engine.DirectionalLight"
    }

    try:
        if actor_lower in asset_map:
            # Spawn from Object (Asset)
            response = await send_ue_ws_command(
                object_path="/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
                function_name="SpawnActorFromObject",
                parameters={
                    "ObjectToUse": asset_map[actor_lower],
                    "Location": {"X": x, "Y": y, "Z": z}
                }
            )
            name = asset_map[actor_lower]
        else:
            # Spawn from Class
            resolved_class = class_map.get(actor_lower, actor_class_or_asset)
            response = await send_ue_ws_command(
                object_path="/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
                function_name="SpawnActorFromClass",
                parameters={
                    "ActorClass": resolved_class,
                    "Location": {"X": x, "Y": y, "Z": z}
                }
            )
            name = resolved_class
            
        return f"Successfully spawned {name} at {x}, {y}, {z}"
    except Exception as e:
        return f"Connection Failed: {str(e)}. Tip: Check parameter names in Unreal version."


@mcp.tool()
async def list_actors() -> str:
    """
    List all actors currently in the Unreal level, returning their names and full paths.
    """
    try:
        response = await send_ue_ws_command(
            object_path="/Script/UnrealEd.Default__EditorActorSubsystem",
            function_name="GetAllLevelActors"
        )
        
        # Extract the ReturnValue from the nested WebSocket response body
        actors = response.get("ResponseBody", {}).get("ReturnValue", [])
        
        if not actors:
            return "No actors found or list is empty."
            
        # Provide both the Short Name and the Full Object Path
        actor_info = [f"{a.split('.')[-1]} (Path: {a})" for a in actors]
        return "Actors in level:\n" + "\n".join(actor_info)
        
    except Exception as e:
        return f"Analysis Failed: {str(e)}. Tip: Is the Editor Actor Subsystem accessible?"


@mcp.tool()
async def set_actor_scale(actor_path: str, scale_x: float, scale_y: float, scale_z: float) -> str:
    """
    Sets the 3D scale of an actor. 
    You MUST provide the full actor_path (e.g. from the list_actors output).
    """
    try:
        response = await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorScale3D",
            parameters={
                "NewScale3D": {"X": scale_x, "Y": scale_y, "Z": scale_z}
            }
        )
        return f"Successfully scaled {actor_path.split('.')[-1]} to ({scale_x}, {scale_y}, {scale_z})"
    except Exception as e:
        return f"Scale Failed: {str(e)}. Tip: Ensure you used the exact full path."


if __name__ == "__main__":
    # Start the FastMCP server on a local network port instead of stdio
    mcp.run(transport="sse", host="localhost", port=8000)