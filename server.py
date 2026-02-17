import requests
from fastmcp import FastMCP
#ali ne bhi kam kiya
# 1. Initialize the MCP Server
mcp = FastMCP("UnrealToy")

# 2. Configuration - The "Door" to Unreal
UE_API_URL = "http://localhost:30010/remote/object/call"

@mcp.tool()
def spawn_actor(actor_class: str, x: float = 0, y: float = 0, z: float = 0):
    """
    Spawns an actor in the Unreal level at the specified coordinates.
    Example actor_class: '/Script/Engine.PointLight'
    """
    # class_map = {
    #     "pointlight": "/Script/Engine.PointLight",
    #     "cube": "/Script/Engine.StaticMeshActor",
    #     "sphere": "/Script/Engine.StaticMeshActor",
    #     "spotlight": "/Script/Engine.SpotLight"
    # }

    # actor_class = class_map.get(actor_class.lower(), actor_class)

    payload = {
        "objectPath": "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
        "functionName": "SpawnActorFromClass",
        "parameters": {
            "ActorClass": actor_class,
            "Location": {"X": x, "Y": y, "Z": z}
        }
    }


    
    try:
        # We use PUT because the Remote Control API requires it for 'calls'
        response = requests.put(UE_API_URL, json=payload, timeout=5)
        response.raise_for_status()
        return f"Successfully spawned {actor_class} at {x}, {y}, {z}"
    except Exception as e:
        return f"Connection Failed: {str(e)}. Is WebControl.StartServer running in UE?"
    
    
# implement all the tools below with similar structure to spawn_actor, making sure to handle any necessary parameters and API calls to Unreal Engine's Remote Control API.

@mcp.tool()
def list_actors():
    """
    List all actors currently in the Unreal level.
    """
    # Using the simpler GetAllLevelActors which takes NO parameters
    payload = {
        "objectPath": "/Script/UnrealEd.Default__EditorActorSubsystem",
        "functionName": "GetAllLevelActors"
    }
    
    try:
        # Note: We use PUT for all 'calls'
        response = requests.put(UE_API_URL, json=payload, timeout=5)
        response.raise_for_status()
        
        # Unreal returns the list in a key called "ReturnValue"
        actors = response.json().get("ReturnValue", [])
        
        # Clean up the output so Claude can read it easily
        actor_names = [a.split('.')[-1] for a in actors]
        return f"Actors in level: {', '.join(actor_names)}"
        
    except Exception as e:
        return f"Connection Failed: {str(e)}. Ensure WebControl.StartServer is active."    


# @mcp.toop()
# def inspect_blueprint(blueprint_path: str):
#     """
#     Reads the meradata and variables of a specified Blueprint asset.
#     Use this to analyze exiting Blueprints logic.
#     """
#     clean_path = f"{blueprint_path}.{blueprint_path.split('/')[-1]}_C"

#     payload = {
#         "objectPath": "/Script/EditorScriptingUtilities.Default__EditorBlueprintLibrary",
#         "functionName": "GetBlueprintVariableDefaultValue",
#         "parameters": {
#             "Blueprint": blueprint_path,
#             # This is tricky: to get ALL variables, we usually 
#             # have to iterate or use the 'GetClass' reflection.
#         }
#     }

# @mcp.tool()
# def get_actor_components(actor_name: str):
#     """
#     Lists all components within a specific actor and their 'bCanEverTick' status.
#     Use this to find performance bottlenecks in your Blueprints.
#     """
#     # 1. We first need to find the actual actor object path from its name
#     # Logic: We use the Subsystem to get the actor reference
#     payload = {
#         "objectPath": f"/Project/CurrentLevel.{actor_name}", # Simplified path logic
#         "functionName": "GetComponentsByClass",
#         "parameters": {
#             "ComponentClass": "/Script/Engine.ActorComponent"
#         }
#     }
    
#     try:
#         # Note: In the 'Toy' version, it's often easier to 'GetClass' 
#         # then 'GetDescriptor' to see what the Blueprint is made of.
#         response = requests.put(UE_API_URL, json=payload, timeout=5)
#         response.raise_for_status()
        
#         components = response.json().get("ReturnValue", [])
#         return f"Components in {actor_name}: {', '.join([c.split('.')[-1] for c in components])}"
#     except Exception as e:
#         return f"Analysis Failed: {str(e)}. Tip: Make sure the actor is spawned in the level first."

if __name__ == "__main__":
    # Start the server using the standard transport for Claude/Cursor
    mcp.run()