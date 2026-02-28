"""
Scene Awareness Tool - Query existing actors and find empty positions.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.utils import format_error


# ── Actor subsystem for queries ──────────────────────────────────────
_ACTOR_SUBSYSTEM = "/Script/EditorScriptingUtilities.Default__EditorActorSubsystem"


async def get_scene_state() -> dict:
    """
    Get a summary of the current scene for LLM context.
    Returns dict with actor names, positions, and suggested empty area.
    """
    try:
        response = await send_ue_ws_command(
            object_path=_ACTOR_SUBSYSTEM,
            function_name="GetAllLevelActors",
            params={},
        )

        actors = []
        occupied = []

        if isinstance(response, dict):
            actor_list = response.get("ReturnValue", [])
            if isinstance(actor_list, list):
                for actor in actor_list:
                    name = actor if isinstance(actor, str) else str(actor)
                    actors.append(name)

        return {
            "actor_count": len(actors),
            "actors": actors[:30],  # Limit to 30 for token savings
            "summary": f"{len(actors)} actors in scene",
        }

    except Exception:
        return {
            "actor_count": 0,
            "actors": [],
            "summary": "Could not query scene (UE may not be running)",
        }


def format_scene_for_prompt(scene: dict) -> str:
    """Format scene state into a compact string for the LLM prompt."""
    if scene["actor_count"] == 0:
        return "Empty scene (no existing actors)"

    lines = [f"Scene has {scene['actor_count']} actors:"]
    for actor in scene["actors"][:15]:  # Even more compact
        # Extract just the actor name from the full path
        name = actor.split(".")[-1] if "." in actor else actor
        lines.append(f"  - {name}")

    if scene["actor_count"] > 15:
        lines.append(f"  ... and {scene['actor_count'] - 15} more")

    return "\n".join(lines)


@mcp.tool()
async def get_scene_summary() -> str:
    """Get a summary of all actors in the scene with positions."""
    scene = await get_scene_state()
    return format_scene_for_prompt(scene)
