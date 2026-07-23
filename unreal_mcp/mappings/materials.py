"""
Material Path Mappings — Starter Content & Engine Materials.

Maps friendly lowercase names to Unreal Engine material asset paths.
These are available when a project includes Starter Content, or when
the Engine's built-in materials are referenced.
"""

# ── Material Map ─────────────────────────────────────────────────────
# Key   : lowercase friendly name
# Value : Material asset path used by SetMaterial
MATERIAL_MAP: dict[str, str] = {
    # ── Metals ──────────────────────────────────────────────────
    "steel":     "/Game/StarterContent/Materials/M_Metal_Steel.M_Metal_Steel",
    "chrome":    "/Game/StarterContent/Materials/M_Metal_Chrome.M_Metal_Chrome",
    "gold":      "/Game/StarterContent/Materials/M_Metal_Gold.M_Metal_Gold",
    "copper":    "/Game/StarterContent/Materials/M_Metal_Copper.M_Metal_Copper",
    "rust":      "/Game/StarterContent/Materials/M_Metal_Rust.M_Metal_Rust",
    "iron":      "/Game/StarterContent/Materials/M_Metal_Burnished_Steel.M_Metal_Burnished_Steel",

    # ── Stone & Concrete ────────────────────────────────────────
    "brick":     "/Game/StarterContent/Materials/M_Brick_Clay_New.M_Brick_Clay_New",
    "stone":     "/Game/StarterContent/Materials/M_Brick_Cut_Stone.M_Brick_Cut_Stone",
    "cobble":    "/Game/StarterContent/Materials/M_CobbleStone_Rough.M_CobbleStone_Rough",
    "concrete":  "/Game/StarterContent/Materials/M_Concrete_Poured.M_Concrete_Poured",
    "slate":     "/Game/StarterContent/Materials/M_Rock_Slate.M_Rock_Slate",

    # ── Wood ────────────────────────────────────────────────────
    "wood":      "/Game/StarterContent/Materials/M_Wood_Oak.M_Wood_Oak",
    "pine":      "/Game/StarterContent/Materials/M_Wood_Pine.M_Wood_Pine",
    "walnut":    "/Game/StarterContent/Materials/M_Wood_Floor_Walnut_Polished.M_Wood_Floor_Walnut_Polished",

    # ── Ground & Nature ─────────────────────────────────────────
    "grass":     "/Game/StarterContent/Materials/M_Ground_Grass.M_Ground_Grass",
    "gravel":    "/Game/StarterContent/Materials/M_Ground_Gravel.M_Ground_Gravel",
    "water":     "/Game/StarterContent/Materials/M_Water_Lake.M_Water_Lake",
    "ocean":     "/Game/StarterContent/Materials/M_Water_Ocean.M_Water_Ocean",

    # ── Architecture ────────────────────────────────────────────
    "floor":     "/Game/StarterContent/Materials/M_Basic_Floor.M_Basic_Floor",
    "wall":      "/Game/StarterContent/Materials/M_Basic_Wall.M_Basic_Wall",
    "tile":      "/Game/StarterContent/Materials/M_Tech_Hex_Tile.M_Tech_Hex_Tile",

    # ── Engine Built-in (always available) ──────────────────────
    "default":   "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial",
    "wireframe": "/Engine/EngineMaterials/WireframeMaterial.WireframeMaterial",
}


def get_material_path(name: str) -> str | None:
    """
    Look up a material path by friendly name (case-insensitive).

    Args:
        name: A friendly name like 'steel', 'brick', 'wood'.
              If the name starts with '/' it's treated as a raw path.

    Returns:
        The full material asset path, or None if not found.
    """
    if name.startswith("/"):
        return name  # Raw path pass-through
    return MATERIAL_MAP.get(name.lower())


def list_available_materials() -> dict[str, str]:
    """Return the full material map for listing in tool descriptions."""
    return dict(MATERIAL_MAP)
