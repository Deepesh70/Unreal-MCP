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
    Wraps the RC HTTP payload into the WebSocket format and aggressively 
    parses the response for silent Unreal Engine errors.
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
    
    if parameters:
        payload["Parameters"]["Body"]["parameters"] = parameters

    try:
        async with websockets.connect(UE_WS_URL) as ws:
            await ws.send(json.dumps(payload))
            response_str = await ws.recv()
            response_data = json.loads(response_str)
            
            # 1. Catch Top-Level WebSocket Errors
            if "ErrorMessage" in response_data:
                raise Exception(f"WebSocket Layer Error: {response_data['ErrorMessage']}")
            
            body = response_data.get("ResponseBody", {})
            response_code = response_data.get("ResponseCode", 200)
            
            # 2. Catch Internal HTTP Errors (e.g., 400 Bad Request, 404 Not Found)
            if response_code not in [200, 202]:
                error_msg = body.get("ErrorMessage") if isinstance(body, dict) else "Unknown Error"
                raise Exception(f"Unreal API Error {response_code}: {error_msg}")
                
            # 3. Catch Silent Blueprint/C++ Execution Errors
            if isinstance(body, dict) and body.get("ErrorMessage"):
                raise Exception(f"Execution Error: {body['ErrorMessage']}")
                
            return response_data
            
    except Exception as e:
        # Pass the exact error string up the chain so the LLM can read it
        raise Exception(str(e))
    

    
@mcp.tool()
async def spawn_actor(actor_class_or_asset: str, x: float = 0, y: float = 0, z: float = 0) -> str:
    """
    Spawns an actor/shape. Returns a success message containing the EXACT_ACTOR_PATH.
    Example: 'cube', 'sphere'
    """
    actor_lower = actor_class_or_asset.lower()
    
    asset_map = {
        "cube": "/Engine/BasicShapes/Cube.Cube",
        "sphere": "/Engine/BasicShapes/Sphere.Sphere"
    }
    class_map = {
        "pointlight": "/Script/Engine.PointLight"
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
            resolved_class = class_map.get(actor_lower, actor_class_or_asset)
            response = await send_ue_ws_command(
                object_path="/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
                function_name="SpawnActorFromClass",
                parameters={
                    "ActorClass": resolved_class,
                    "Location": {"X": x, "Y": y, "Z": z}
                }
            )
            
        # EXTRACTION: Grab the explicit path Unreal generated for this specific actor
        actor_path = response.get("ResponseBody", {}).get("ReturnValue")
        if isinstance(actor_path, dict):
            actor_path = actor_path.get("ObjectPath", str(actor_path))
            
        if not actor_path:
            actor_path = "ERROR_PATH_NOT_RETURNED"
            
        return f"Successfully spawned at {x}, {y}, {z}. EXACT_ACTOR_PATH: {actor_path}"
        
    except Exception as e:
        return f"Spawn Failed: {str(e)}"

@mcp.tool()
async def list_actors(search_term: str = "") -> str:
    """
    List actors currently in the Unreal level. 
    CRITICAL: You MUST provide a 'search_term' (e.g., 'Cube' or 'Sphere') to filter the results. 
    If you do not filter, you will be overwhelmed by background actors.
    """
    try:
        response = await send_ue_ws_command(
            object_path="/Script/UnrealEd.Default__EditorActorSubsystem",
            function_name="GetAllLevelActors"
        )
        
        actors = response.get("ResponseBody", {}).get("ReturnValue", [])
        
        if not actors:
            return "No actors found or list is empty."
            
        if search_term:
            actors = [a for a in actors if search_term.lower() in a.lower()]
            
        if not actors:
            return f"No actors found matching '{search_term}'."

        max_results = 25
        actor_info = [f"{a.split('.')[-1]} (Path: {a})" for a in actors[:max_results]]
        
        result_string = f"Found {len(actors)} matching actors. Showing top {len(actor_info)}:\n"
        result_string += "\n".join(actor_info)
        
        return result_string
        
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
    print("🚀 Starting FastMCP Server on port 8000...")
    mcp.run(transport="sse", host="localhost", port=8000)