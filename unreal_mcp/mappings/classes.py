"""
Actor Class Mappings — Lights & Other Actor Types.

Maps friendly lowercase names to Unreal Engine class paths.
Add new actor types here; every tool that needs class lookups
imports from this single source of truth.
"""

# ── Class Map ─────────────────────────────────────────────────────────
# Key   : lowercase friendly name
# Value : /Script/Engine class path used by SpawnActorFromClass
CLASS_MAP: dict[str, str] = {
    "pointlight":       "/Script/Engine.PointLight",
    "spotlight":        "/Script/Engine.SpotLight",
    "directional_light": "/Script/Engine.DirectionalLight",
}


def get_class_path(name: str, fallback: str | None = None) -> str:
    """
    Look up an actor class path by friendly name (case-insensitive).

    If the name is not in the map, returns the fallback (which defaults
    to the original input — letting callers pass raw class paths through).

    Args:
        name:     A friendly name like 'pointlight' or a raw class path.
        fallback: Value to return when name is not found; defaults to name itself.

    Returns:
        The resolved class path string.
    """
    if fallback is None:
        fallback = name
    return CLASS_MAP.get(name.lower(), fallback)
