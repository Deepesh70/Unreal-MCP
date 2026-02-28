"""
Actors Tool — list all actors in the current Unreal level.

Uses the connection layer to query Unreal and the utils layer
to parse and format the response.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.utils import extract_return_value, format_actor_list, format_error


# ── Editor subsystem used to enumerate actors ────────────────────────
_ACTOR_SUBSYSTEM = "/Script/UnrealEd.Default__EditorActorSubsystem"


@mcp.tool()
async def list_actors() -> str:
    """List all actors in the level with names and paths."""
    try:
        response = await send_ue_ws_command(
            object_path=_ACTOR_SUBSYSTEM,
            function_name="GetAllLevelActors",
        )

        actors = extract_return_value(response)
        return format_actor_list(actors)

    except Exception as e:
        return format_error(e, "Is the Editor Actor Subsystem accessible?")
