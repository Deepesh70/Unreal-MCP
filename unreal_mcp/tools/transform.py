"""
Transform Tools — set location, rotation, and scale of actors.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.utils import format_error


@mcp.tool()
async def set_actor_scale(
    actor_path: str,
    scale_x: float,
    scale_y: float,
    scale_z: float,
) -> str:
    """Scale an actor. Use the full actor_path from list_actors."""
    try:
        response = await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorScale3D",
            parameters={"NewScale3D": {"X": scale_x, "Y": scale_y, "Z": scale_z}},
        )
        return f"Scaled {actor_path} to ({scale_x}, {scale_y}, {scale_z})"
    except Exception as e:
        return format_error(e, "Check actor path.")


@mcp.tool()
async def set_actor_rotation(
    actor_path: str,
    pitch: float = 0,
    yaw: float = 0,
    roll: float = 0,
) -> str:
    """Rotate an actor. Pitch=up/down, Yaw=left/right, Roll=tilt."""
    try:
        response = await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorRotation",
            parameters={"NewRotation": {"Pitch": pitch, "Yaw": yaw, "Roll": roll}, "bTeleportPhysics": False},
        )
        return f"Rotated {actor_path} to (Pitch={pitch}, Yaw={yaw}, Roll={roll})"
    except Exception as e:
        return format_error(e, "Check actor path.")


@mcp.tool()
async def set_actor_location(
    actor_path: str,
    x: float,
    y: float,
    z: float,
) -> str:
    """Move an actor to a new position."""
    try:
        response = await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorLocation",
            parameters={"NewLocation": {"X": x, "Y": y, "Z": z}, "bSweep": False},
        )
        return f"Moved {actor_path} to ({x}, {y}, {z})"
    except Exception as e:
        return format_error(e, "Check actor path.")
