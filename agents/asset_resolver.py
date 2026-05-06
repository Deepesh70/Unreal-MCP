"""
Asset Resolver — Feature 7: Dynamic Asset Loading.

Provides a cache layer and placeholder API integration for resolving
style tags to actual mesh/material assets. When a Style key is unknown,
this module can search for matching assets and update the cache.

Currently implements:
  - Local asset cache (data/asset_cache.json)
  - Search stub for Fab/Quixel API (ready for integration)
  - Cache read/write for cross-session persistence

Usage:
    from agents.asset_resolver import resolve_style, search_assets
"""

import json
import os
from pathlib import Path


# ── Cache Paths ──────────────────────────────────────────────────────

CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "asset_cache.json"


def _load_cache() -> dict:
    """Load the asset cache from disk."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_cache(cache: dict):
    """Save the asset cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# ── Style Resolution ────────────────────────────────────────────────

def resolve_style(style_key: str) -> dict | None:
    """
    Check if a style key has cached asset paths.

    Returns:
        A dict with mesh/material paths if found, None otherwise.
        Example: {"WallMesh": "/Game/Meshes/WoodWall", "FloorMesh": "/Game/Meshes/WoodFloor"}
    """
    cache = _load_cache()
    return cache.get(style_key)


def cache_style(style_key: str, assets: dict):
    """
    Cache asset paths for a style key.

    Args:
        style_key: The semantic style tag (e.g., "Rustic_Stone_Cottage")
        assets:    Dict of asset paths {WallMesh, FloorMesh, RoofMesh, etc.}
    """
    cache = _load_cache()
    cache[style_key] = assets
    _save_cache(cache)
    print(f"💾 Cached assets for style '{style_key}'")


def list_cached_styles() -> list:
    """Return all cached style keys."""
    cache = _load_cache()
    return list(cache.keys())


# ── Asset Search (Fab/Quixel Integration Stub) ──────────────────────

async def search_assets(query: str, max_results: int = 5) -> list:
    """
    Search for assets matching a query.

    Currently returns a stub response. When Fab API integration is added,
    this will search the Fab (formerly Quixel Megascans) marketplace.

    Args:
        query:       Natural language search query.
        max_results: Maximum number of results to return.

    Returns:
        A list of dicts with asset info:
        [{"id": "...", "name": "...", "preview_url": "...", "category": "..."}]
    """
    # Stub: Return suggestions based on common keywords
    suggestions = _get_builtin_suggestions(query)

    if suggestions:
        return suggestions[:max_results]

    return [{
        "id": "stub_not_found",
        "name": f"No assets found for '{query}'",
        "preview_url": "",
        "category": "unknown",
        "note": "Fab API integration not yet configured. "
                "Set FAB_API_KEY environment variable to enable.",
    }]


def _get_builtin_suggestions(query: str) -> list:
    """
    Return built-in mesh/material suggestions for common style queries.
    These map to Unreal Engine's built-in or commonly available assets.
    """
    query_lower = query.lower()

    # Built-in engine meshes that are always available
    builtin_db = {
        "cube":     {"WallMesh": "/Engine/BasicShapes/Cube"},
        "sphere":   {"WallMesh": "/Engine/BasicShapes/Sphere"},
        "cylinder": {"WallMesh": "/Engine/BasicShapes/Cylinder"},
        "cone":     {"WallMesh": "/Engine/BasicShapes/Cone"},
    }

    # Style preset mappings
    style_presets = {
        "wood":     {"style": "Wood",     "note": "Use Cube with brown material override"},
        "stone":    {"style": "Stone",    "note": "Use Cube with gray material override"},
        "concrete": {"style": "Concrete", "note": "Use Cube with concrete material override"},
        "glass":    {"style": "Glass",    "note": "Use Cube with translucent material override"},
        "metal":    {"style": "Metal",    "note": "Use Cube with steel material override"},
        "brick":    {"style": "Brick",    "note": "Use Cube with red/brown material override"},
        "modern":   {"style": "Modern",   "note": "Use Composite with glass + steel elements"},
        "medieval": {"style": "Medieval", "note": "Use Building template with pointed roof"},
        "rustic":   {"style": "Rustic",   "note": "Use Building template with wood style"},
        "gothic":   {"style": "Gothic",   "note": "Use Building template with pointed roof, tall"},
    }

    results = []
    for keyword, info in style_presets.items():
        if keyword in query_lower:
            results.append({
                "id": f"preset_{keyword}",
                "name": info["style"],
                "preview_url": "",
                "category": "style_preset",
                "note": info["note"],
            })

    return results


# ── Pre-Spawn Resolution ────────────────────────────────────────────

async def pre_spawn_resolve(style_key: str) -> str | None:
    """
    Called before a Spawn intent is forwarded to C++.
    Checks if the style exists in cache, tries to resolve if not.

    Returns:
        The resolved style key to use, or None if no resolution needed.
    """
    if not style_key or style_key == "Default":
        return None

    # Check cache first
    cached = resolve_style(style_key)
    if cached:
        print(f"✅ Style '{style_key}' found in asset cache.")
        return style_key

    # Try to search for assets
    print(f"🔍 Style '{style_key}' unknown — searching for matching assets...")
    results = await search_assets(style_key)

    if results and results[0].get("category") == "style_preset":
        preset = results[0]
        cache_style(style_key, {"resolved_from": preset["name"], "note": preset.get("note", "")})
        print(f"   Found preset: {preset['name']} — {preset.get('note', '')}")
        return style_key

    print(f"   ⚠️  No match found for '{style_key}'. Using default shapes.")
    return None
