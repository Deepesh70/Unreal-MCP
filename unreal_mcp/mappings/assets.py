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
    # ── Engine Basic Shapes ─────────────────────────────────────
    "cube":     "/Engine/BasicShapes/Cube.Cube",
    "sphere":   "/Engine/BasicShapes/Sphere.Sphere",
    "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
    "cone":     "/Engine/BasicShapes/Cone.Cone",
    "plane":    "/Engine/BasicShapes/Plane.Plane",

    # ── Starter Content Props ───────────────────────────────────
    "chair":        "/Game/StarterContent/Props/SM_Chair.SM_Chair",
    "couch":        "/Game/StarterContent/Props/SM_Couch.SM_Couch",
    "door":         "/Game/StarterContent/Props/SM_Door.SM_Door",
    "table_round":  "/Game/StarterContent/Props/SM_TableRound.SM_TableRound",
    "table_square": "/Game/StarterContent/Props/SM_TableSquare.SM_TableSquare",
    "pillar":       "/Game/StarterContent/Props/SM_PillarFrame.SM_PillarFrame",
    "rock":         "/Game/StarterContent/Props/SM_Rock.SM_Rock",
    "shelf":        "/Game/StarterContent/Props/SM_Shelf.SM_Shelf",
    "lamp_ceiling": "/Game/StarterContent/Props/SM_Lamp_Ceiling.SM_Lamp_Ceiling",
    "lamp_desk":    "/Game/StarterContent/Props/SM_Lamp_Desk.SM_Lamp_Desk",
    "frame":        "/Game/StarterContent/Props/SM_Frame.SM_Frame",
    "statue":       "/Game/StarterContent/Props/SM_Statue.SM_Statue",
    "mat_preview":  "/Game/StarterContent/Props/SM_MatPreviewMesh_02.SM_MatPreviewMesh_02",

    # ── Starter Content Architecture ────────────────────────────
    "wall_piece":   "/Game/StarterContent/Architecture/Wall_400x300.Wall_400x300",
    "floor_piece":  "/Game/StarterContent/Architecture/Floor_400x400.Floor_400x400",
    "stairs":       "/Game/StarterContent/Architecture/SM_AssetPlatform.SM_AssetPlatform",
    "pillar_50":    "/Game/StarterContent/Architecture/Pillar_50x500.Pillar_50x500",
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
