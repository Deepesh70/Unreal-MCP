"""
Scene Query Tool — gives the AI "eyes" to see what exists in the Unreal level.

This is the MOST IMPORTANT tool in the entire system. Before the AI does
anything, it must call get_scene_state() to understand what already exists.
Without this, the AI is blind and will create duplicates, spawn on top of
existing objects, or wipe things it shouldn't.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.utils import extract_return_value, format_error

import json

# ── Editor subsystem used to enumerate actors ────────────────────────
_ACTOR_SUBSYSTEM = "/Script/UnrealEd.Default__EditorActorSubsystem"


@mcp.tool()
async def get_scene_state(
    filter_type: str = "",
    near_x: float = None,
    near_y: float = None,
    near_z: float = None,
    radius: float = 10000.0,
) -> str:
    """Get all actors in the current Unreal scene with their names, types, and locations.

    Use this BEFORE making any changes to understand what already exists.

    Args:
        filter_type: Optional type filter (e.g. "StaticMesh", "Light", "Camera").
                     Leave empty to get all actors.
        near_x, near_y, near_z: Optional center point to filter by proximity.
        radius: Maximum distance from the center point (default: 10000 UU = 100m).

    Returns:
        A structured summary of all actors the AI can reason about.
    """
    try:
        # Get all actors in the level
        response = await send_ue_ws_command(
            object_path=_ACTOR_SUBSYSTEM,
            function_name="GetAllLevelActors",
        )

        raw_actors = extract_return_value(response)

        if not raw_actors or not isinstance(raw_actors, list):
            return json.dumps({
                "total_actors": 0,
                "actors": [],
                "note": "Scene is empty or could not query actors."
            })

        # Build actor summaries
        actors = []
        for actor_path in raw_actors:
            if not isinstance(actor_path, str):
                continue

            # Extract readable name and type from the path
            # Typical path: "/Game/Level.Level:PersistentLevel.StaticMeshActor_5"
            parts = str(actor_path).split(".")
            name = parts[-1] if parts else str(actor_path)

            # Determine type from the name pattern
            actor_type = _infer_type(name)

            # Apply type filter if specified
            if filter_type and filter_type.lower() not in actor_type.lower():
                continue

            actors.append({
                "name": name,
                "type": actor_type,
                "path": str(actor_path),
            })

        # Try to get location for each actor (best effort — limited to avoid
        # overwhelming the WebSocket with too many calls for large scenes)
        enriched_actors = []
        actors_to_enrich = actors[:50]  # Cap at 50 to avoid flooding

        for actor_info in actors_to_enrich:
            try:
                loc_response = await send_ue_ws_command(
                    object_path=actor_info["path"],
                    function_name="GetActorLocation",
                )
                loc_data = extract_return_value(loc_response)
                if isinstance(loc_data, dict):
                    actor_info["location"] = [
                        loc_data.get("X", 0),
                        loc_data.get("Y", 0),
                        loc_data.get("Z", 0),
                    ]

                    # Apply proximity filter if specified
                    if near_x is not None and near_y is not None and near_z is not None:
                        dx = actor_info["location"][0] - near_x
                        dy = actor_info["location"][1] - near_y
                        dz = actor_info["location"][2] - near_z
                        dist = (dx*dx + dy*dy + dz*dz) ** 0.5
                        if dist > radius:
                            continue  # Skip actors outside radius

                enriched_actors.append(actor_info)
            except Exception:
                # If we can't get location, include without it
                enriched_actors.append(actor_info)

        # If no proximity filter, include all (even non-enriched ones beyond 50)
        if near_x is None:
            remaining = actors[50:]
            enriched_actors.extend(remaining)

        result = {
            "total_actors": len(enriched_actors),
            "actors": enriched_actors,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return format_error(e, "Is Unreal Engine running with Remote Control enabled?")


def _infer_type(name: str) -> str:
    """Infer actor type from its name pattern."""
    name_lower = name.lower()

    if "staticmesh" in name_lower:
        return "StaticMeshActor"
    elif "pointlight" in name_lower:
        return "PointLight"
    elif "spotlight" in name_lower:
        return "SpotLight"
    elif "directionallight" in name_lower:
        return "DirectionalLight"
    elif "cinecamera" in name_lower:
        return "CineCameraActor"
    elif "camera" in name_lower:
        return "CameraActor"
    elif "skeletalmesh" in name_lower:
        return "SkeletalMeshActor"
    elif "landscape" in name_lower:
        return "Landscape"
    elif "playerstart" in name_lower:
        return "PlayerStart"
    elif "skylight" in name_lower:
        return "SkyLight"
    elif "sky" in name_lower:
        return "Sky"
    elif "fog" in name_lower:
        return "ExponentialHeightFog"
    elif "volume" in name_lower:
        return "Volume"
    elif "niagara" in name_lower:
        return "NiagaraActor"
    elif "geometrycollection" in name_lower:
        return "GeometryCollectionActor"
    elif "citymanager" in name_lower or "proceduralcity" in name_lower:
        return "ProceduralCityManager"
    else:
        return "Actor"
