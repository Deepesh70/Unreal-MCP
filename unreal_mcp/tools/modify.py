"""
Modify & Destroy Tools — manipulate existing actors in the Unreal level.

These tools work WITH get_scene_state: the AI first queries what exists,
then uses modify_actor/destroy_actor to change or remove specific actors
by name.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.utils import format_error


@mcp.tool()
async def modify_actor(
    actor_path: str,
    location_x: float = None,
    location_y: float = None,
    location_z: float = None,
    rotation_pitch: float = None,
    rotation_yaw: float = None,
    rotation_roll: float = None,
    scale_x: float = None,
    scale_y: float = None,
    scale_z: float = None,
) -> str:
    """Move, rotate, or scale an existing actor.

    Use get_scene_state first to find the actor's full path.
    Only specify the properties you want to change — omitted values are unchanged.

    Args:
        actor_path: Full path to the actor (from get_scene_state or spawn_actor).
        location_x/y/z: New world position. Set all three to move.
        rotation_pitch/yaw/roll: New rotation in degrees. Set all three to rotate.
        scale_x/y/z: New scale factors. Set all three to scale.
    """
    results = []

    try:
        # ── Location ────────────────────────────────────────────
        if location_x is not None and location_y is not None and location_z is not None:
            await send_ue_ws_command(
                object_path=actor_path,
                function_name="SetActorLocation",
                parameters={
                    "NewLocation": {"X": location_x, "Y": location_y, "Z": location_z},
                    "bSweep": False,
                    "bTeleport": True,
                },
            )
            results.append(f"moved to ({location_x}, {location_y}, {location_z})")

        # ── Rotation ────────────────────────────────────────────
        if rotation_pitch is not None and rotation_yaw is not None and rotation_roll is not None:
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
            results.append(f"rotated to (P:{rotation_pitch}, Y:{rotation_yaw}, R:{rotation_roll})")

        # ── Scale ───────────────────────────────────────────────
        if scale_x is not None and scale_y is not None and scale_z is not None:
            await send_ue_ws_command(
                object_path=actor_path,
                function_name="SetActorScale3D",
                parameters={
                    "NewScale3D": {"X": scale_x, "Y": scale_y, "Z": scale_z},
                },
            )
            results.append(f"scaled to ({scale_x}, {scale_y}, {scale_z})")

        if not results:
            return "No changes specified. Provide location, rotation, or scale values."

        short_name = actor_path.split(".")[-1]
        return f"Successfully modified {short_name}: {', '.join(results)}"

    except Exception as e:
        return format_error(e, "Ensure the actor path is correct (use get_scene_state to find it).")


@mcp.tool()
async def destroy_actor(actor_path: str) -> str:
    """Remove an actor from the scene.

    Use get_scene_state first to find the actor's full path.

    Args:
        actor_path: Full path to the actor to destroy.
    """
    _EDITOR_LIB = "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary"

    try:
        # We must call DestroyActor on the EditorLevelLibrary and pass the actor as a parameter
        await send_ue_ws_command(
            object_path=_EDITOR_LIB,
            function_name="DestroyActor",
            parameters={
                "Actor": actor_path
            }
        )

        short_name = actor_path.split(".")[-1]
        return f"Successfully destroyed {short_name}"

    except Exception as e:
        return format_error(e, "Ensure the actor path is correct (use get_scene_state to find it).")

