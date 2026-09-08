"""
Spawning Tool — spawn actors and shapes in the Unreal level.

Uses the mappings layer to resolve friendly names and the connection
layer to talk to Unreal Engine.

UPGRADED: Now returns the actor's full path so subsequent tools (modify_actor,
destroy_actor, set_actor_property) can reference it. Also supports rotation.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.mappings import get_asset_path, get_class_path
from unreal_mcp.utils import extract_return_value, format_error


# ── Editor Library path used for all spawn calls ─────────────────────
_EDITOR_LIB = "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary"


@mcp.tool()
async def spawn_actor(
    actor_class_or_asset: str,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    rotation_pitch: float = 0,
    rotation_yaw: float = 0,
    rotation_roll: float = 0,
) -> str:
    """Spawn an actor in the Unreal scene.

    Supports friendly names: cube, sphere, cone, cylinder, plane,
    pointlight, spotlight, directionallight, cinecameraactor, etc.

    Args:
        actor_class_or_asset: What to spawn (e.g. "cube", "PointLight", "CineCameraActor").
        x, y, z: World position to spawn at.
        rotation_pitch, rotation_yaw, rotation_roll: Initial rotation in degrees.

    Returns:
        The spawned actor's name and full path (use this path with modify_actor, destroy_actor, etc.)
    """
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
            display_name = actor_class_or_asset
        else:
            # ── Spawn from Class (lights, cameras, custom actors) ─
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

        # ── Try to extract the spawned actor's path from the response ──
        actor_path = _extract_actor_path(response)

        # ── Apply rotation if non-zero ──────────────────────────
        if actor_path and (rotation_pitch != 0 or rotation_yaw != 0 or rotation_roll != 0):
            try:
                await send_ue_ws_command(
                    object_path=actor_path,
                    function_name="SetActorRotation",
                    parameters={
                        "NewRotation": {
                            "Pitch": rotation_pitch,
                            "Yaw": rotation_yaw,
                            "Roll": rotation_roll,
                        },
                        "bTeleportPhysics": False,
                    },
                )
            except Exception:
                pass  # Rotation is best-effort, don't fail the spawn

        if actor_path:
            short_name = actor_path.split(".")[-1]
            return (
                f"Spawned {display_name} at ({x}, {y}, {z}).\n"
                f"Actor name: {short_name}\n"
                f"Actor path: {actor_path}\n"
                f"Use this path with modify_actor, destroy_actor, or set_actor_property."
            )
        else:
            return f"Spawned {display_name} at ({x}, {y}, {z}). (Could not extract actor path from response.)"

    except Exception as e:
        return format_error(e, "Check parameter names.")


def _extract_actor_path(response: dict) -> str:
    """Try to extract the spawned actor's path from UE's response."""
    if not response:
        return ""

    # The response structure depends on the Remote Control version.
    # Common patterns:
    body = response.get("ResponseBody", {})

    # Pattern 1: ReturnValue is the actor path string
    ret_val = body.get("ReturnValue", "")
    if isinstance(ret_val, str) and ret_val:
        return ret_val

    # Pattern 2: ReturnValue is an object with path
    if isinstance(ret_val, dict):
        return ret_val.get("ObjectPath", ret_val.get("objectPath", ""))

    return ""
