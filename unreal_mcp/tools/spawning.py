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
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    scale_z: float = 1.0,
) -> str:
    """Spawn an actor in the Unreal scene with optional rotation and scale.

    Supports friendly names: cube, sphere, cone, cylinder, plane,
    pointlight, spotlight, directionallight, cinecameraactor, etc.

    Args:
        actor_class_or_asset: What to spawn (e.g. "cube", "PointLight", "CineCameraActor").
        x, y, z: World position to spawn at.
        rotation_pitch, rotation_yaw, rotation_roll: Initial rotation in degrees.
        scale_x, scale_y, scale_z: Initial scale factor (default 1.0).

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

        # ── Apply scale if non-default ──────────────────────────
        if actor_path and (scale_x != 1.0 or scale_y != 1.0 or scale_z != 1.0):
            try:
                await send_ue_ws_command(
                    object_path=actor_path,
                    function_name="SetActorScale3D",
                    parameters={
                        "NewScale3D": {
                            "X": scale_x,
                            "Y": scale_y,
                            "Z": scale_z,
                        },
                    },
                )
            except Exception:
                pass  # Scale is best-effort

        if actor_path:
            short_name = actor_path.split(".")[-1]
            return (
                f"Spawned {display_name} at ({x}, {y}, {z}) with scale ({scale_x}, {scale_y}, {scale_z}).\n"
                f"Actor name: {short_name}\n"
                f"Actor path: {actor_path}\n"
                f"Use this path with modify_actor, destroy_actor, or set_actor_property."
            )
        else:
            return f"Spawned {display_name} at ({x}, {y}, {z}). (Could not extract actor path from response.)"

    except Exception as e:
        return format_error(e, "Check parameter names.")


@mcp.tool()
async def spawn_actors_batch(
    actors: list[dict],
) -> str:
    """Spawn multiple actors in a single tool call without writing scripts.

    Each entry in `actors` is a dict with:
        - "actor": Friendly name or class (e.g. "cube", "cylinder", "PointLight")
        - "x", "y", "z": Position (floats, optional, default 0)
        - "pitch", "yaw", "roll": Rotation (floats, optional, default 0)
        - "scale_x", "scale_y", "scale_z": Scale (floats, optional, default 1.0)

    Returns:
        Summary of all spawned actors with their paths.
    """
    results = []
    for item in actors:
        actor_name = item.get("actor", "cube")
        x = float(item.get("x", 0))
        y = float(item.get("y", 0))
        z = float(item.get("z", 0))
        pitch = float(item.get("pitch", 0))
        yaw = float(item.get("yaw", 0))
        roll = float(item.get("roll", 0))
        sx = float(item.get("scale_x", 1.0))
        sy = float(item.get("scale_y", 1.0))
        sz = float(item.get("scale_z", 1.0))

        res = await spawn_actor(
            actor_class_or_asset=actor_name,
            x=x, y=y, z=z,
            rotation_pitch=pitch, rotation_yaw=yaw, rotation_roll=roll,
            scale_x=sx, scale_y=sy, scale_z=sz,
        )
        first_line = res.split("\n")[0]
        results.append(first_line)

    return f"Batch spawned {len(results)} actors:\n" + "\n".join(f"  • {r}" for r in results)


async def spawn_actor_internal(
    actor_class_or_asset: str,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    rotation_pitch: float = 0,
    rotation_yaw: float = 0,
    rotation_roll: float = 0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    scale_z: float = 1.0,
) -> tuple[str, str]:
    """Internal spawn helper that returns (actor_path, display_name)."""
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

    actor_path = _extract_actor_path(response)
    return actor_path, display_name


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
