"""
Spawning Tool — spawn actors and shapes in the Unreal level.

Uses the mappings layer to resolve friendly names and the connection
layer to talk to Unreal Engine.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.mappings import get_asset_path, get_class_path
from unreal_mcp.utils import format_error


# ── Editor Library path used for all spawn calls ─────────────────────
_EDITOR_LIB = "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary"


async def spawn_actor_internal(actor_class_or_asset: str, x=0, y=0, z=0):
    """
    Internal spawn helper. Returns (actor_path, display_name).
    actor_path can be used for subsequent transform calls.
    """
    asset_path = get_asset_path(actor_class_or_asset)

    if asset_path:
        response = await send_ue_ws_command(
            object_path=_EDITOR_LIB,
            function_name="SpawnActorFromObject",
            parameters={
                "ObjectToUse": asset_path,
                "Location": {"X": x, "Y": y, "Z": z},
            },
        )
        display_name = actor_class_or_asset
    else:
        resolved_class = get_class_path(actor_class_or_asset)
        response = await send_ue_ws_command(
            object_path=_EDITOR_LIB,
            function_name="SpawnActorFromClass",
            parameters={
                "ActorClass": resolved_class,
                "Location": {"X": x, "Y": y, "Z": z},
            },
        )
        display_name = actor_class_or_asset

    # Extract the actor path from the UE response
    actor_path = None
    if isinstance(response, dict):
        ret = response.get("ReturnValue", "")
        if isinstance(ret, str) and ret:
            actor_path = ret
        elif isinstance(ret, dict):
            actor_path = ret.get("ObjectPath", ret.get("Name", ""))
            
    # Fallback: Sometimes Remote Control just returns True. If so, get the newest actor.
    if not actor_path:
        try:
            from unreal_mcp.tools.actors import list_actors
            actors_str = await list_actors()
            # The last actor in the list is usually the newest
            lines = [line.strip() for line in actors_str.split('\n') if line.strip()]
            for line in reversed(lines):
                if "/" in line and ":" in line:
                    # e.g. "- Cube (Path: /Game/Map.Map:PersistentLevel.Cube_1)"
                    parts = line.split("Path: ")
                    if len(parts) > 1:
                        actor_path = parts[1].replace(")", "").strip()
                        break
        except Exception:
            pass

    return actor_path, display_name


@mcp.tool()
async def spawn_actor(
    actor_class_or_asset: str,
    x: float = 0,
    y: float = 0,
    z: float = 0,
) -> str:
    """Spawn an actor. Use: cube, sphere, cone, cylinder, plane, pointlight, spotlight."""
    try:
        actor_path, name = await spawn_actor_internal(actor_class_or_asset, x, y, z)
        path_info = f" (path: {actor_path})" if actor_path else ""
        return f"Successfully spawned {name} at {x}, {y}, {z}{path_info}"
    except Exception as e:
        return format_error(e, "Check parameter names.")
