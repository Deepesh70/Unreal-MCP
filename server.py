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
async def spawn_actor(actor_class: str, x: float = 0, y: float = 0, z: float = 0) -> str:
    """
    Spawns an actor in the Unreal level at the specified coordinates.
    Example actor_class: '/Script/Engine.PointLight'
    """
    # Optional friendly name mapping
    class_map = {
        "pointlight": "/Script/Engine.PointLight",
        "cube": "/Script/Engine.StaticMeshActor",
        "sphere": "/Script/Engine.StaticMeshActor",
        "spotlight": "/Script/Engine.SpotLight"
    }
    actor_class = class_map.get(actor_class.lower(), actor_class)

    try:
        response = await send_ue_ws_command(
            object_path="/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
            function_name="SpawnActorFromClass",
            parameters={
                "ActorClass": actor_class,
                "Location": {"X": x, "Y": y, "Z": z}
            }
        )
        return f"Successfully spawned {actor_class} at {x}, {y}, {z}"
    except Exception as e:
        return f"Connection Failed: {str(e)}. Is WebControl.StartServer running in UE?"


@mcp.tool()
async def list_actors() -> str:
    """
    List all actors currently in the Unreal level.
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
            
        # Clean up the output so Claude can read it easily
        actor_names = [a.split('.')[-1] for a in actors]
        return f"Actors in level: {', '.join(actor_names)}"
        
    except Exception as e:
        return f"Analysis Failed: {str(e)}. Tip: Is the Editor Actor Subsystem accessible?"


if __name__ == "__main__":
    # Start the FastMCP server
    mcp.run()