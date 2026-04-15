"""
Alignment Tools — deterministic spatial math and snapping.
Moves the "intelligence" of geometry from the LLM to Python/Unreal.
"""

import math
from typing import Dict, Any, Tuple
from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command, send_ue_ws_property_update
from unreal_mcp.utils import extract_return_value, format_error

@mcp.tool()
async def get_actor_bounds(actor_path: str) -> str:
    """
    Get the exact world-space center and extents (bounding box) of an actor.
    Returns: {center: {x,y,z}, extents: {x,y,z}}
    """
    try:
        # Call AActor::GetActorBounds
        response = await send_ue_ws_command(
            object_path=actor_path,
            function_name="GetActorBounds",
            parameters={
                "bOnlyCollidingComponents": False,
                "bIncludeFromChildActors": False
            }
        )
        
        body = response.get("ResponseBody", {})
        origin = body.get("Origin", {"X": 0, "Y": 0, "Z": 0})
        extent = body.get("BoxExtent", {"X": 0, "Y": 0, "Z": 0})
        
        return (
            f"Bounds for {actor_path}:\n"
            f"  Center:  X={origin.get('X')}, Y={origin.get('Y')}, Z={origin.get('Z')}\n"
            f"  Extents: X={extent.get('X')}, Y={extent.get('Y')}, Z={extent.get('Z')}"
        )
    except Exception as e:
        return format_error(e, f"Could not get bounds for {actor_path}")

async def _get_raw_bounds(actor_path: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    response = await send_ue_ws_command(
        object_path=actor_path,
        function_name="GetActorBounds",
        parameters={
            "bOnlyCollidingComponents": False,
            "bIncludeFromChildActors": False
        }
    )
    body = response.get("ResponseBody", {})
    origin = body.get("Origin", {"X": 0, "Y": 0, "Z": 0})
    extent = body.get("BoxExtent", {"X": 0, "Y": 0, "Z": 0})
    return origin, extent

@mcp.tool()
async def snap_to_actor(
    subject_path: str,
    target_path: str,
    direction: str,
    padding: float = 0.0
) -> str:
    """
    Deterministically snap one actor to the edge of another.
    Directions: top, bottom, north, south, east, west.
    'north' is +Y, 'south' is -Y, 'east' is +X, 'west' is -X (Unreal defaults).
    """
    try:
        # 1. Get bounds for both
        s_origin, s_extent = await _get_raw_bounds(subject_path)
        t_origin, t_extent = await _get_raw_bounds(target_path)
        
        new_x = t_origin["X"]
        new_y = t_origin["Y"]
        new_z = t_origin["Z"]
        new_yaw = 0.0

        d = direction.lower().strip()
        
        if d == "top":
            new_z = t_origin["Z"] + t_extent["Z"] + s_extent["Z"] + padding
        elif d == "bottom":
            new_z = t_origin["Z"] - t_extent["Z"] - s_extent["Z"] - padding
        elif d == "north": # +Y
            new_y = t_origin["Y"] + t_extent["Y"] + s_extent["X"] + padding # assuming wall depth is X
            new_yaw = 0.0
        elif d == "south": # -Y
            new_y = t_origin["Y"] - t_extent["Y"] - s_extent["X"] - padding
            new_yaw = 180.0
        elif d == "east": # +X
            new_x = t_origin["X"] + t_extent["X"] + s_extent["X"] + padding
            new_yaw = 90.0
        elif d == "west": # -X
            new_x = t_origin["X"] - t_extent["X"] - s_extent["X"] - padding
            new_yaw = 270.0
        elif d == "northwest":
            new_x = t_origin["X"] - t_extent["X"] - s_extent["X"] - padding
            new_y = t_origin["Y"] + t_extent["Y"] + s_extent["Y"] + padding
            new_yaw = 315.0
        elif d == "northeast":
            new_x = t_origin["X"] + t_extent["X"] + s_extent["X"] + padding
            new_y = t_origin["Y"] + t_extent["Y"] + s_extent["Y"] + padding
            new_yaw = 45.0
        elif d == "southwest":
            new_x = t_origin["X"] - t_extent["X"] - s_extent["X"] - padding
            new_y = t_origin["Y"] - t_extent["Y"] - s_extent["Y"] - padding
            new_yaw = 225.0
        elif d == "southeast":
            new_x = t_origin["X"] + t_extent["X"] + s_extent["X"] + padding
            new_y = t_origin["Y"] - t_extent["Y"] - s_extent["Y"] - padding
            new_yaw = 135.0
        else:
            return f"Unknown direction '{direction}'. Use: top, bottom, north, south, east, west, northwest, northeast, southwest, southeast."

        # 2. Apply Location
        await send_ue_ws_command(
            object_path=subject_path,
            function_name="K2_SetActorLocation",
            parameters={
                "NewLocation": {"X": new_x, "Y": new_y, "Z": new_z},
                "bSweep": False,
                "bTeleport": True
            }
        )
        
        # 3. Apply Rotation (if applicable for walls/stairs)
        if d in ["north", "south", "east", "west", "northwest", "northeast", "southwest", "southeast"]:
             await send_ue_ws_command(
                object_path=subject_path,
                function_name="K2_SetActorRotation",
                parameters={
                    "NewRotation": {"Pitch": 0, "Yaw": new_yaw, "Roll": 0},
                    "bTeleport": True
                }
            )

        return (
            f"Successfully snapped {subject_path} to {direction} of {target_path}.\n"
            f"New Location: X={new_x:.1f}, Y={new_y:.1f}, Z={new_z:.1f}\n"
            f"New Rotation (Yaw): {new_yaw:.1f}"
        )

    except Exception as e:
        return format_error(e, f"Check if both actors exist: {subject_path}, {target_path}")
