"""
Asset Path Mappings — Basic Shapes.

Maps friendly lowercase names to their Unreal Engine asset paths.
Add new shapes here; every tool that needs shape lookups imports
from this single source of truth.
"""

# ── Asset Map ─────────────────────────────────────────────────────────
# Key   : lowercase friendly name
# Value : Engine asset path used by SpawnActorFromObject
ASSET_MAP: dict[str, str] = {
    "cube":     "/Engine/BasicShapes/Cube.Cube",
    "sphere":   "/Engine/BasicShapes/Sphere.Sphere",
    "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
    "cone":     "/Engine/BasicShapes/Cone.Cone",
    "plane":    "/Engine/BasicShapes/Plane.Plane",
}


def get_asset_path(name: str) -> str | None:
    """
    Look up an asset path by friendly name (case-insensitive).

    Args:
        name: A friendly name like 'cube', 'Sphere', etc.

    Returns:
        The full asset path string, or None if not found.
    """
    return ASSET_MAP.get(name.lower())
