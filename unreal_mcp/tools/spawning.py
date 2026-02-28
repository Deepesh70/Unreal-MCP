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


@mcp.tool()
async def spawn_actor(
    actor_class_or_asset: str,
    x: float = 0,
    y: float = 0,
    z: float = 0,
) -> str:
    """Spawn an actor. Use: cube, sphere, cone, cylinder, plane, pointlight, spotlight."""
    asset_path = get_asset_path(actor_class_or_asset)

    try:
        if asset_path:
            # ── Spawn from Asset (basic shapes) ──────────────────
            response = await send_ue_ws_command(
                object_path=_EDITOR_LIB,
                function_name="SpawnActorFromObject",
                parameters={
                    "ObjectToUse": asset_path,
                    "Location": {"X": x, "Y": y, "Z": z},
                },
            )
            name = asset_path
        else:
            # ── Spawn from Class (lights, custom actors) ─────────
            resolved_class = get_class_path(actor_class_or_asset)
            response = await send_ue_ws_command(
                object_path=_EDITOR_LIB,
                function_name="SpawnActorFromClass",
                parameters={
                    "ActorClass": resolved_class,
                    "Location": {"X": x, "Y": y, "Z": z},
                },
            )
            name = resolved_class

        return f"Successfully spawned {name} at {x}, {y}, {z}"

    except Exception as e:
        return format_error(e, "Check parameter names.")
