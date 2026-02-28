"""
Transform Tool — modify actor transforms (scale, position, rotation).

Currently implements scaling; extend this module for future movement
and rotation tools.
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
            parameters={
                "NewScale3D": {"X": scale_x, "Y": scale_y, "Z": scale_z}
            },
        )
        short_name = actor_path.split(".")[-1]
        return f"Successfully scaled {short_name} to ({scale_x}, {scale_y}, {scale_z})"

    except Exception as e:
        return format_error(e, "Ensure you used the exact full path.")
