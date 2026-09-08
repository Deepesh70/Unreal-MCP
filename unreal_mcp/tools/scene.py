"""
Scene Query Tool — gives the AI "eyes" to see what exists in the Unreal level.

This is the MOST IMPORTANT tool in the entire system. Before the AI does
anything, it must call get_scene_state() to understand what already exists.
Without this, the AI is blind and will create duplicates, spawn on top of
existing objects, or wipe things it shouldn't.

UPGRADED (v2): Returns a human-readable summary with type breakdown,
mesh name resolution, and automatic filtering of noise actors (HLOD,
LandscapeStreamingProxy). No more "200 unknown actors" — now you get
"24 static meshes (Cube, Tower, Wall), 3 lights, 1 camera".
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command, execute_python
from unreal_mcp.utils import extract_return_value, format_error

import json
from collections import Counter

# ── Editor subsystem used to enumerate actors ────────────────────────
_ACTOR_SUBSYSTEM = "/Script/UnrealEd.Default__EditorActorSubsystem"

# ── Actor types that are "environment noise" — filtered from the main list ──
_NOISE_PREFIXES = (
    "hlod", "landscapestreamingproxy", "worlddatastorage",
    "worldpartitionminimapvolume", "worldsettings",
    "abstractnavdata", "navmeshboundsvolume",
    "levelscriptactor", "gameplaydebuggerplayer",
    "brushactor", "brush", "note",
)


@mcp.tool()
async def get_scene_state(
    filter_type: str = "",
    detail: str = "full",
    near_x: float = None,
    near_y: float = None,
    near_z: float = None,
    radius: float = 10000.0,
) -> str:
    """Get a clear summary of what is in the current Unreal scene.

    Returns actor types, counts, mesh names, and locations — not just
    raw paths. Use this BEFORE making any changes.

    Args:
        filter_type: Optional type filter (e.g. "StaticMesh", "Light", "Camera").
                     Leave empty to get everything.
        detail: "quick" = counts only (fast), "full" = counts + mesh names + locations (default).
        near_x, near_y, near_z: Optional center point to filter by proximity.
        radius: Maximum distance from the center point (default: 10000 UU = 100m).

    Returns:
        A structured summary with breakdown by type, list of user-placed actors,
        and a natural-language summary sentence.
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
                "summary": "Scene is empty — no actors found.",
                "total_actors": 0,
                "actors": [],
            })

        # ── Classify every actor ─────────────────────────────────
        user_actors = []
        noise_counts = Counter()  # HLOD, Landscape, etc.

        for actor_path in raw_actors:
            if not isinstance(actor_path, str):
                continue

            parts = str(actor_path).split(".")
            name = parts[-1] if parts else str(actor_path)
            actor_type = _infer_type(name)

            # Check if this is a noise/environment actor
            if _is_noise(name):
                noise_category = _noise_category(name)
                noise_counts[noise_category] += 1
                continue

            # Apply type filter if specified
            if filter_type and filter_type.lower() not in actor_type.lower():
                continue

            user_actors.append({
                "name": name,
                "type": actor_type,
                "path": str(actor_path),
            })

        # ── Enrich user actors with locations (and mesh names in full mode) ──
        if detail == "full":
            user_actors = await _enrich_actors(user_actors, near_x, near_y, near_z, radius)

        # ── Build type breakdown ──────────────────────────────────
        type_counts = Counter(a["type"] for a in user_actors)

        # ── Build summary sentence ────────────────────────────────
        summary = _build_summary(user_actors, type_counts, noise_counts)

        # ── Assemble result ───────────────────────────────────────
        result = {
            "summary": summary,
            "total_actors": len(user_actors) + sum(noise_counts.values()),
            "user_actors_count": len(user_actors),
            "breakdown": dict(type_counts.most_common()),
            "actors": user_actors,
        }

        if noise_counts:
            result["environment"] = {
                "counts": dict(noise_counts.most_common()),
                "total": sum(noise_counts.values()),
                "note": "Auto-generated environment actors (HLOD, Landscape, etc.), hidden from main list.",
            }

        return json.dumps(result, indent=2)

    except Exception as e:
        return format_error(e, "Is Unreal Engine running with Remote Control enabled?")


async def _enrich_actors(actors: list, near_x, near_y, near_z, radius) -> list:
    """Add locations and mesh names to actors. Cap at 80 to avoid flooding."""
    enriched = []
    actors_to_process = actors[:80]

    for actor_info in actors_to_process:
        # ── Get location ──────────────────────────────────────
        try:
            loc_response = await send_ue_ws_command(
                object_path=actor_info["path"],
                function_name="GetActorLocation",
            )
            loc_data = extract_return_value(loc_response)
            if isinstance(loc_data, dict):
                loc = [
                    round(loc_data.get("X", 0), 1),
                    round(loc_data.get("Y", 0), 1),
                    round(loc_data.get("Z", 0), 1),
                ]
                actor_info["location"] = loc

                # Apply proximity filter if specified
                if near_x is not None and near_y is not None and near_z is not None:
                    dx = loc[0] - near_x
                    dy = loc[1] - near_y
                    dz = loc[2] - near_z
                    dist = (dx*dx + dy*dy + dz*dz) ** 0.5
                    if dist > radius:
                        continue  # Skip actors outside radius
        except Exception:
            pass  # Location enrichment is best-effort

        # ── Get mesh/asset name for StaticMeshActors ──────────
        if actor_info["type"] == "StaticMeshActor":
            try:
                mesh_name = await _get_mesh_name(actor_info["path"])
                if mesh_name:
                    actor_info["mesh"] = mesh_name
            except Exception:
                pass

        enriched.append(actor_info)

    # If no proximity filter, include remaining actors beyond the 80 cap
    if near_x is None:
        remaining = actors[80:]
        enriched.extend(remaining)

    return enriched


async def _get_mesh_name(actor_path: str) -> str:
    """Try to resolve the static mesh asset name for a StaticMeshActor.
    
    Uses a targeted Python script inside UE to read the actual mesh component.
    Falls back to extracting from the actor name if Python isn't available.
    """
    try:
        # Quick approach: read the StaticMeshComponent's mesh via Remote Control
        # The component is usually at actor_path + ".StaticMeshComponent0"
        component_path = actor_path + ".StaticMeshComponent0"
        from unreal_mcp.connection import get_ue_ws_property
        response = await get_ue_ws_property(
            object_path=component_path,
            property_name="StaticMesh",
        )
        body = response.get("ResponseBody", {})
        mesh_ref = body.get("StaticMesh", "")
        
        if isinstance(mesh_ref, str) and mesh_ref:
            # Extract the asset name from the full path
            # e.g. "/Engine/BasicShapes/Cube.Cube" → "Cube"
            mesh_name = mesh_ref.split("/")[-1].split(".")[0]
            return mesh_name
        elif isinstance(mesh_ref, dict):
            # Some versions return {"ObjectName": "...", "ObjectPath": "..."}
            obj_path = mesh_ref.get("ObjectPath", mesh_ref.get("objectPath", ""))
            if obj_path:
                return obj_path.split("/")[-1].split(".")[0]
    except Exception:
        pass
    
    return ""


def _build_summary(actors: list, type_counts: Counter, noise_counts: Counter) -> str:
    """Build a one-sentence natural-language summary of the scene."""
    if not actors and not noise_counts:
        return "Scene is empty — no actors found."

    parts = []
    for actor_type, count in type_counts.most_common():
        # Add mesh details if available
        if actor_type == "StaticMeshActor":
            mesh_names = set()
            for a in actors:
                if a["type"] == "StaticMeshActor" and "mesh" in a:
                    mesh_names.add(a["mesh"])
            if mesh_names:
                meshes_str = ", ".join(sorted(mesh_names)[:5])
                if len(mesh_names) > 5:
                    meshes_str += f" +{len(mesh_names) - 5} more"
                parts.append(f"{count} static meshes ({meshes_str})")
            else:
                parts.append(f"{count} static meshes")
        elif actor_type == "PointLight":
            parts.append(f"{count} point light{'s' if count > 1 else ''}")
        elif actor_type == "SpotLight":
            parts.append(f"{count} spot light{'s' if count > 1 else ''}")
        elif actor_type == "DirectionalLight":
            parts.append(f"{count} directional light{'s' if count > 1 else ''}")
        elif actor_type == "CineCameraActor":
            parts.append(f"{count} cine camera{'s' if count > 1 else ''}")
        elif actor_type == "CameraActor":
            parts.append(f"{count} camera{'s' if count > 1 else ''}")
        else:
            parts.append(f"{count} {actor_type}")

    total_noise = sum(noise_counts.values())
    if total_noise:
        noise_detail = ", ".join(f"{v} {k}" for k, v in noise_counts.most_common(3))
        parts.append(f"{total_noise} environment actors ({noise_detail})")

    total = len(actors) + total_noise
    items_str = ", ".join(parts)
    return f"Scene has {total} actors: {items_str}."


def _is_noise(name: str) -> bool:
    """Check if an actor name is environment noise (HLOD, Landscape, etc.)."""
    name_lower = name.lower()
    for prefix in _NOISE_PREFIXES:
        if prefix in name_lower:
            return True
    return False


def _noise_category(name: str) -> str:
    """Categorize a noise actor for the environment counts."""
    name_lower = name.lower()
    if "hlod" in name_lower:
        return "HLOD"
    elif "landscape" in name_lower:
        return "Landscape"
    elif "worlddata" in name_lower or "worldsetting" in name_lower:
        return "WorldSettings"
    elif "nav" in name_lower:
        return "Navigation"
    elif "volume" in name_lower:
        return "Volume"
    else:
        return "Other"


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
