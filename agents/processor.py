"""
Processor — Routes LLM JSON output to the correct action.

The LLM outputs strict JSON. Routing is based on:
  - "Intent" field (new Delegator architecture):
      Spawn / BatchSpawn / Modify / Destroy / ClearAll / ScanArea
      → forwarded to AProceduralCityManager via a SINGLE WebSocket call
  - "Action" field (legacy):
      "CreateClass" → Write .h/.cpp files to disk
      "SpawnActor"  → auto-migrated to new "Spawn" Intent

This module is the bridge between the LLM's brain and the real world.
"""

import json
import logging
import os
import re
import sys
import time

from unreal_mcp.connection import send_ue_ws_command

# ── Audit Logger — dual output: console + file ───────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "audit.log")

log = logging.getLogger("unreal_mcp.processor")
log.setLevel(logging.DEBUG)
if not log.handlers:
    _fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Console handler (INFO+)
    _ch = logging.StreamHandler(sys.stdout)
    _ch.setLevel(logging.INFO)
    _ch.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    ))
    log.addHandler(_ch)
    # File handler (DEBUG — captures everything)
    _fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(_fmt)
    log.addHandler(_fh)
    log.info("Audit log file: %s", _LOG_FILE)


# ── Editor paths ──────────────────────────────────────────────────────
_EDITOR_SUBSYSTEM = "/Script/UnrealEd.Default__EditorActorSubsystem"
_EDITOR_LIB = "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary"

# ── Module-level cache for the discovered CityManager actor path ──────
_manager_cache = None
_fallback_warned = False  # Only print the fallback warning once

# Python-side position ledger for legacy mode collision avoidance
# Each entry: {"id": str, "x": float, "y": float, "w": float, "d": float, "h": float}
_spawned_buildings = []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Legacy Fallback — Direct actor spawning (no C++ required)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_SHAPE_ASSETS = {
    "cube":     "/Engine/BasicShapes/Cube.Cube",
    "sphere":   "/Engine/BasicShapes/Sphere.Sphere",
    "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
    "cone":     "/Engine/BasicShapes/Cone.Cone",
    "plane":    "/Engine/BasicShapes/Plane.Plane",
}

_FLOOR_HEIGHT = 300.0
_BUILDING_WIDTH = 1000.0
_WALL_THICKNESS = 20.0
_CUBE_ASSET = _SHAPE_ASSETS["cube"]
_CONE_ASSET = _SHAPE_ASSETS["cone"]
_MIN_SPACING = 300.0  # Minimum gap between building edges (UU) — raised from 200

# Material colors — matched to the C++ ApplyMaterialByColor lookup
_MATERIAL_COLORS = {
    "red": {"R": 0.8, "G": 0.1, "B": 0.1, "A": 1.0},
    "blue": {"R": 0.1, "G": 0.2, "B": 0.9, "A": 1.0},
    "green": {"R": 0.1, "G": 0.8, "B": 0.2, "A": 1.0},
    "yellow": {"R": 0.9, "G": 0.85, "B": 0.1, "A": 1.0},
    "orange": {"R": 0.9, "G": 0.5, "B": 0.1, "A": 1.0},
    "purple": {"R": 0.6, "G": 0.1, "B": 0.9, "A": 1.0},
    "cyan": {"R": 0.3, "G": 0.75, "B": 0.9, "A": 1.0},
    "white": {"R": 1.0, "G": 1.0, "B": 1.0, "A": 1.0},
    "black": {"R": 0.02, "G": 0.02, "B": 0.02, "A": 1.0},
    "gray": {"R": 0.4, "G": 0.4, "B": 0.4, "A": 1.0},
    "steel": {"R": 0.5, "G": 0.55, "B": 0.6, "A": 1.0},
    "gold": {"R": 0.85, "G": 0.65, "B": 0.13, "A": 1.0},
    "concrete": {"R": 0.65, "G": 0.63, "B": 0.6, "A": 1.0},
    "wood": {"R": 0.55, "G": 0.35, "B": 0.15, "A": 1.0},
    "wood_dark": {"R": 0.35, "G": 0.2, "B": 0.1, "A": 1.0},
    "stone": {"R": 0.5, "G": 0.48, "B": 0.45, "A": 1.0},
    "glass": {"R": 0.4, "G": 0.6, "B": 0.8, "A": 0.5},
}


def _check_overlap(x, y, w, d):
    """
    Check if a building at (x,y) with footprint (w,d) overlaps any existing building.
    Uses strict AABB edge-to-edge distance with a spacing buffer.
    Returns the ID of the first overlapping building, or None.
    """
    half_w = w / 2.0
    half_d = d / 2.0
    for b in _spawned_buildings:
        bh_w = b["w"] / 2.0
        bh_d = b["d"] / 2.0
        # Distance between edges (not centers)
        dx = abs(x - b["x"]) - (half_w + bh_w)
        dy = abs(y - b["y"]) - (half_d + bh_d)
        # Overlap if BOTH edges overlap OR too close
        if dx < _MIN_SPACING and dy < _MIN_SPACING:
            log.debug("Overlap: new (%.0f,%.0f %sx%s) vs '%s' (%.0f,%.0f) — edge gap: dx=%.0f dy=%.0f",
                      x, y, w, d, b['id'], b['x'], b['y'], dx, dy)
            return b['id']
    return None


def _find_clear_position(x, y, w, d, max_attempts=80):
    """
    Spiral outward from (x,y) until a non-overlapping position is found.
    Returns (new_x, new_y, was_nudged).

    Uses a true spiral with 12 directions per ring for denser coverage.
    """
    if not _check_overlap(x, y, w, d):
        return x, y, False

    # Step size = building footprint + buffer so each ring clears the previous
    step = max(w, d) + _MIN_SPACING
    import math
    directions = 12  # Check 12 directions per ring (every 30 degrees)

    for ring in range(1, max_attempts):
        offset = ring * step
        for i in range(directions):
            angle = (2 * math.pi * i) / directions
            cx = x + math.cos(angle) * offset
            cy = y + math.sin(angle) * offset
            if not _check_overlap(cx, cy, w, d):
                log.info("Auto-nudge: ring %d, angle %.0f deg, offset %.0f UU -> (%.0f, %.0f)",
                         ring, math.degrees(angle), offset, cx, cy)
                return cx, cy, True

    # Radius exhausted
    log.warning("RADIUS EXHAUSTED: could not find clear position in %d rings (%.0f UU radius)",
                max_attempts, max_attempts * step)
    final_x = x + max_attempts * step
    return final_x, y, True


async def _spawn_and_scale(x, y, z, sx, sy, sz, asset=None):
    """Spawn a shape at (x,y,z) then scale it to (sx,sy,sz). Returns actor path or None."""
    if asset is None:
        asset = _CUBE_ASSET
    resp = await send_ue_ws_command(
        object_path=_EDITOR_LIB,
        function_name="SpawnActorFromObject",
        parameters={
            "ObjectToUse": asset,
            "Location": {"X": x, "Y": y, "Z": z},
        },
    )
    actor_path = resp.get("ResponseBody", {}).get("ReturnValue", "")
    if actor_path:
        await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetActorScale3D",
            parameters={"NewScale3D": {"X": sx, "Y": sy, "Z": sz}},
        )
    return actor_path


async def _handle_spawn_fallback(data: dict) -> str:
    """
    Build a procedural structure using individual actors (legacy mode).
    Routes to the correct template based on StructureType.

    Supported StructureTypes:
      - "Building"   — multi-floor box (floor slabs + 4 walls + roof)
      - "Solid"      — single primitive shape (cube, sphere, cylinder, cone)
      - "Bridge"     — deck + support pillars
      - "Composite"  — LLM provides a "Parts" array of individual primitives
    """
    params = data.get("Parameters", {})
    loc = data.get("RequestedLoc", [0, 0, 0])
    building_id = data.get("ID", "Structure")
    structure_type = params.get("StructureType", "Building")

    raw_x = float(loc[0]) if len(loc) > 0 else 0
    raw_y = float(loc[1]) if len(loc) > 1 else 0
    base_z = float(loc[2]) if len(loc) > 2 else 0

    # Determine footprint for collision check
    bldg_width = float(params.get("BuildingWidth", params.get("Width", _BUILDING_WIDTH)))
    bldg_depth = float(params.get("BuildingDepth", params.get("Depth", _BUILDING_WIDTH)))

    # Auto-nudge to prevent overlap
    base_x, base_y, was_nudged = _find_clear_position(
        raw_x, raw_y, bldg_width, bldg_depth
    )

    # Route to the correct template
    log.info("Spawn '%s' [%s] at (%.0f, %.0f, %.0f)%s",
             building_id, structure_type, base_x, base_y, base_z,
             " (NUDGED)" if was_nudged else "")
    if structure_type == "Composite" and "Parts" in data:
        result_str = await _build_composite(data, base_x, base_y, base_z)
    elif structure_type == "Solid":
        result_str = await _build_solid(params, base_x, base_y, base_z)
    elif structure_type == "Bridge":
        result_str = await _build_bridge(params, base_x, base_y, base_z)
    else:
        # Default: Building template
        result_str = await _build_building(params, base_x, base_y, base_z)

    # Record in ledger IMMEDIATELY so the next building in a batch sees this one
    entry = {
        "id": building_id, "x": base_x, "y": base_y,
        "w": bldg_width, "d": bldg_depth,
    }
    _spawned_buildings.append(entry)
    log.debug("Ledger updated: %d buildings tracked. Latest: %s at (%.0f, %.0f)",
              len(_spawned_buildings), building_id, base_x, base_y)

    result = f"✅ Built '{building_id}' [{structure_type}] (legacy mode)\n{result_str}\n   Location: X={base_x:.0f}, Y={base_y:.0f}, Z={base_z:.0f}"
    if was_nudged:
        result += f"\n   ↪ Auto-nudged from X:{raw_x:.0f}, Y:{raw_y:.0f} (overlap detected)"
    return result


# ── Template: Building (multi-floor box) ─────────────────────────────

async def _build_building(params, base_x, base_y, base_z):
    """The original floors + walls + roof template."""
    num_floors = max(1, int(params.get("Floors", 3)))
    floor_height = float(params.get("FloorHeight", _FLOOR_HEIGHT))
    bldg_width = float(params.get("BuildingWidth", _BUILDING_WIDTH))
    bldg_depth = float(params.get("BuildingDepth", _BUILDING_WIDTH))
    wall_thick = float(params.get("WallThickness", _WALL_THICKNESS))
    roof_type = params.get("RoofType", "flat")

    half_w = bldg_width / 2.0
    half_d = bldg_depth / 2.0

    slab_sx = bldg_width / 100.0
    slab_sy = bldg_depth / 100.0
    slab_sz = 0.2

    wall_fb_sx = bldg_width / 100.0
    wall_fb_sy = wall_thick / 100.0
    wall_fb_sz = floor_height / 100.0

    wall_lr_sx = wall_thick / 100.0
    wall_lr_sy = bldg_depth / 100.0
    wall_lr_sz = floor_height / 100.0

    spawned = 0
    errors = []

    for f in range(num_floors):
        floor_z = base_z + (f * floor_height)
        try:
            await _spawn_and_scale(base_x, base_y, floor_z, slab_sx, slab_sy, slab_sz)
            spawned += 1
            wall_z = floor_z + floor_height / 2.0
            await _spawn_and_scale(base_x, base_y + half_d, wall_z, wall_fb_sx, wall_fb_sy, wall_fb_sz)
            spawned += 1
            await _spawn_and_scale(base_x, base_y - half_d, wall_z, wall_fb_sx, wall_fb_sy, wall_fb_sz)
            spawned += 1
            await _spawn_and_scale(base_x - half_w, base_y, wall_z, wall_lr_sx, wall_lr_sy, wall_lr_sz)
            spawned += 1
            await _spawn_and_scale(base_x + half_w, base_y, wall_z, wall_lr_sx, wall_lr_sy, wall_lr_sz)
            spawned += 1
        except Exception as e:
            errors.append(f"Floor {f}: {e}")
            break

    if not errors:
        try:
            roof_z = base_z + (num_floors * floor_height)
            if roof_type == "pointed":
                await _spawn_and_scale(base_x, base_y, roof_z, bldg_width / 100.0, bldg_depth / 100.0, (floor_height * 0.5) / 100.0, _CONE_ASSET)
            else:
                await _spawn_and_scale(base_x, base_y, roof_z, slab_sx, slab_sy, slab_sz)
            spawned += 1
        except Exception as e:
            errors.append(f"Roof: {e}")

    total_h = num_floors * floor_height
    info = (
        f"   {num_floors} floors × (1 slab + 4 walls) + 1 roof = {spawned} actors\n"
        f"   Size: {bldg_width:.0f} × {bldg_depth:.0f} × {total_h:.0f} UU"
    )
    if errors:
        info += f"\n   ⚠️  {len(errors)} part(s) failed: {errors[0]}"
    return info


# ── Template: Solid (single primitive) ───────────────────────────────

async def _build_solid(params, base_x, base_y, base_z):
    """Spawn a single scaled primitive shape."""
    shape = params.get("Shape", "cube").lower()
    width = float(params.get("Width", 200))
    depth = float(params.get("Depth", 200))
    height = float(params.get("Height", 200))

    asset = _SHAPE_ASSETS.get(shape, _CUBE_ASSET)
    sx = width / 100.0
    sy = depth / 100.0
    sz = height / 100.0

    # Center the shape vertically (base of UE cube is at its center)
    spawn_z = base_z + (height / 2.0)

    try:
        await _spawn_and_scale(base_x, base_y, spawn_z, sx, sy, sz, asset)
        return f"   Shape: {shape} — {width:.0f} × {depth:.0f} × {height:.0f} UU (1 actor)"
    except Exception as e:
        return f"   ❌ Failed to spawn {shape}: {e}"


# ── Template: Bridge (deck + pillars) ────────────────────────────────

async def _build_bridge(params, base_x, base_y, base_z):
    """Build a bridge: horizontal deck on support pillars."""
    span = float(params.get("Span", params.get("BuildingWidth", 3000)))
    deck_width = float(params.get("DeckWidth", params.get("BuildingDepth", 500)))
    deck_thick = float(params.get("DeckThickness", 30))
    deck_height = float(params.get("DeckHeight", params.get("Height", 500)))
    pillar_width = float(params.get("PillarWidth", 150))
    num_pillars = max(2, int(params.get("NumPillars", 2)))
    has_railings = params.get("Railings", True)

    spawned = 0
    errors = []

    # Pillar spacing
    pillar_spacing = span / max(1, num_pillars - 1)
    start_x = base_x - span / 2.0

    # Spawn pillars (vertical cubes)
    for i in range(num_pillars):
        px = start_x + (i * pillar_spacing)
        pillar_z = base_z + deck_height / 2.0
        try:
            await _spawn_and_scale(
                px, base_y, pillar_z,
                pillar_width / 100.0, pillar_width / 100.0, deck_height / 100.0
            )
            spawned += 1
        except Exception as e:
            errors.append(f"Pillar {i}: {e}")

    # Spawn deck (horizontal slab on top of pillars)
    try:
        await _spawn_and_scale(
            base_x, base_y, base_z + deck_height,
            span / 100.0, deck_width / 100.0, deck_thick / 100.0
        )
        spawned += 1
    except Exception as e:
        errors.append(f"Deck: {e}")

    # Optional railings (thin tall cubes along each side of deck)
    if has_railings and not errors:
        railing_height = 100.0
        railing_thick = 10.0
        railing_z = base_z + deck_height + deck_thick + railing_height / 2.0
        half_dw = deck_width / 2.0
        try:
            # Left railing
            await _spawn_and_scale(
                base_x, base_y - half_dw, railing_z,
                span / 100.0, railing_thick / 100.0, railing_height / 100.0
            )
            spawned += 1
            # Right railing
            await _spawn_and_scale(
                base_x, base_y + half_dw, railing_z,
                span / 100.0, railing_thick / 100.0, railing_height / 100.0
            )
            spawned += 1
        except Exception as e:
            errors.append(f"Railings: {e}")

    info = (
        f"   Bridge: {span:.0f} UU span, {num_pillars} pillars, {deck_width:.0f} UU wide = {spawned} actors\n"
        f"   Deck height: {deck_height:.0f} UU above ground"
    )
    if errors:
        info += f"\n   ⚠️  {len(errors)} part(s) failed: {errors[0]}"
    return info


# ── Template: Composite (LLM-defined parts) ─────────────────────────

async def _build_composite(data, base_x, base_y, base_z):
    """
    The LLM provides a 'Parts' array where each part is an individual
    primitive with a shape, offset, and scale. This allows building
    any complex structure from basic shapes.

    Each part: {"Shape": "cube", "Offset": [dx, dy, dz], "Scale": [sx, sy, sz]}
    """
    parts = data.get("Parts", [])
    if not parts:
        return "   ⚠️  Composite structure has no Parts array."

    spawned = 0
    errors = []

    for i, part in enumerate(parts):
        shape = part.get("Shape", "cube").lower()
        offset = part.get("Offset", [0, 0, 0])
        scale = part.get("Scale", [1, 1, 1])
        label = part.get("Label", f"Part_{i}")

        asset = _SHAPE_ASSETS.get(shape, _CUBE_ASSET)

        # Absolute position = base + offset
        px = base_x + float(offset[0]) if len(offset) > 0 else base_x
        py = base_y + float(offset[1]) if len(offset) > 1 else base_y
        pz = base_z + float(offset[2]) if len(offset) > 2 else base_z

        sx = float(scale[0]) if len(scale) > 0 else 1. 
        sy = float(scale[1]) if len(scale) > 1 else 1.0
        sz = float(scale[2]) if len(scale) > 2 else 1.0

        material_name = part.get("material", part.get("Material", "")).lower()

        try:
            actor_path = await _spawn_and_scale(px, py, pz, sx, sy, sz, asset)
            spawned += 1
            # Apply material color if specified
            if actor_path and material_name and material_name in _MATERIAL_COLORS:
                color = _MATERIAL_COLORS[material_name]
                try:
                    await send_ue_ws_command(
                        object_path=actor_path,
                        function_name="SetActorLabel",
                        parameters={"NewActorLabel": f"{label}_{material_name}"},
                    )
                except Exception:
                    pass  # Label setting is non-critical
        except Exception as e:
            errors.append(f"{label}: {e}")

    info = f"   Composite: {spawned}/{len(parts)} parts spawned"
    if errors:
        info += f"\n   ⚠️  {len(errors)} part(s) failed: {errors[0]}"
    return info


async def _handle_batch_spawn_fallback(data: dict) -> str:
    """Handle BatchSpawn by iterating over Blueprints and spawning each one."""
    blueprints = data.get("Blueprints", [])
    results = []
    for bp in blueprints:
        # Each blueprint in the array looks like a Spawn intent
        bp["Intent"] = "Spawn"
        result = await _handle_spawn_fallback(bp)
        results.append(result)
    return "\n".join(results)


async def _handle_intent_with_fallback(data: dict) -> str:
    """
    Try the new C++ Delegator path first.
    If no CityManager found, fall back to legacy direct spawning.
    """
    global _fallback_warned
    intent = data.get("Intent", "")

    try:
        return await _handle_unreal_intent(data)
    except Exception as e:
        error_str = str(e)
        if "No AProceduralCityManager found" not in error_str:
            raise  # Re-raise if it's a different error

    # CityManager not found — use legacy fallback
    if not _fallback_warned:
        print("⚠️  No CityManager actor found — using legacy direct-spawn mode.")
        print("   Buildings will appear as individual actors (not HISM-batched).")
        print("   To enable full performance: run 'python setup_unreal.py'\n")
        _fallback_warned = True

    if intent == "Spawn":
        return await _handle_spawn_fallback(data)
    elif intent == "BatchSpawn":
        return await _handle_batch_spawn_fallback(data)
    elif intent == "Destroy":
        return f"⚠️  Destroy is not available in legacy mode (no ledger). Delete actors manually in UE."
    elif intent == "Modify":
        return f"⚠️  Modify is not available in legacy mode (no ledger). Edit actors manually in UE."
    elif intent == "ClearAll":
        return f"⚠️  ClearAll is not available in legacy mode. Select all and delete manually in UE."
    elif intent == "ScanArea":
        return f"⚠️  ScanArea is not available in legacy mode (no spatial awareness)."
    elif intent == "GenerateGeometry":
        return f"⚠️  GenerateGeometry requires C++ Geometry Scripting (no legacy fallback). Place a CityManager in your level."
    else:
        return f"⚠️  Unknown intent '{intent}' in legacy fallback mode."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  JSON Repair (kept from original — battle-tested)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _repair_truncated_json(raw: str) -> str:
    """
    Attempt to repair JSON that was truncated mid-stream by the LLM
    hitting its max_tokens limit.

    Strategy: walk the string tracking open brackets/braces/quotes,
    then append the necessary closing characters.
    """
    # If it looks like the string was cut inside a JSON string value,
    # close the string first, then close any open structures.
    repaired = raw.rstrip()

    # Close an unclosed string literal (odd number of unescaped quotes)
    in_string = False
    i = 0
    while i < len(repaired):
        ch = repaired[i]
        if ch == '\\' and in_string:
            i += 2  # skip escaped char
            continue
        if ch == '"':
            in_string = not in_string
        i += 1

    if in_string:
        # We're inside an unclosed string — close it
        repaired += '"'

    # Now close any unclosed brackets/braces
    stack = []
    in_string = False
    i = 0
    while i < len(repaired):
        ch = repaired[i]
        if ch == '\\' and in_string:
            i += 2
            continue
        if ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch in ('{', '['):
                stack.append('}' if ch == '{' else ']')
            elif ch in ('}', ']'):
                if stack:
                    stack.pop()
        i += 1

    # Close everything in reverse order
    while stack:
        repaired += stack.pop()

    return repaired


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Schema Validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _validate_intent_schema(data: dict) -> tuple:
    """
    Validate that the JSON payload has the required fields for its Intent.

    Returns:
        (True, "") on success, or (False, "error message") on failure.
    """
    intent = data.get("Intent", "")

    if intent == "Spawn":
        if "ID" not in data or not data["ID"]:
            return False, "Spawn requires a non-empty 'ID' field"
        loc = data.get("RequestedLoc")
        if loc is not None:
            if not isinstance(loc, list) or len(loc) < 3:
                return False, "RequestedLoc must be an array of 3 numbers [X, Y, Z]"
            for i, v in enumerate(loc):
                if not isinstance(v, (int, float)):
                    return False, f"RequestedLoc[{i}] must be a number, got {type(v).__name__}"
        params = data.get("Parameters", {})
        if "Floors" in params and not isinstance(params["Floors"], (int, float)):
            return False, "Parameters.Floors must be a number"
        if "RoofType" in params and params["RoofType"] not in ("flat", "pointed"):
            return False, f"Parameters.RoofType must be 'flat' or 'pointed', got '{params['RoofType']}'"

    elif intent == "BatchSpawn":
        bps = data.get("Blueprints")
        if not isinstance(bps, list):
            return False, "BatchSpawn requires a 'Blueprints' array"
        if len(bps) == 0:
            return False, "BatchSpawn 'Blueprints' array is empty"
        for i, bp in enumerate(bps):
            if not isinstance(bp, dict):
                return False, f"Blueprints[{i}] must be an object"
            if "ID" not in bp or not bp["ID"]:
                return False, f"Blueprints[{i}] requires a non-empty 'ID' field"

    elif intent == "Modify":
        if "TargetID" not in data or not data["TargetID"]:
            return False, "Modify requires a non-empty 'TargetID' field"
        if "NewBlueprint" not in data:
            return False, "Modify requires a 'NewBlueprint' object"

    elif intent == "Destroy":
        if "TargetID" not in data or not data["TargetID"]:
            return False, "Destroy requires a non-empty 'TargetID' field"

    elif intent == "ClearAll":
        pass  # No fields required

    elif intent == "ScanArea":
        center = data.get("Center")
        if center is not None:
            if not isinstance(center, list) or len(center) < 3:
                return False, "ScanArea.Center must be an array of 3 numbers"

    elif intent == "GenerateGeometry":
        if "ID" not in data or not data["ID"]:
            return False, "GenerateGeometry requires a non-empty 'ID' field"
        base_shape = data.get("BaseShape")
        if not isinstance(base_shape, dict):
            return False, "GenerateGeometry requires a 'BaseShape' object"
        if "Type" not in base_shape:
            return False, "BaseShape must have a 'Type' field (Box, Cylinder, Sphere)"
        dims = base_shape.get("Dimensions")
        if dims is not None:
            if not isinstance(dims, list) or len(dims) < 3:
                return False, "BaseShape.Dimensions must be an array of 3 numbers"
        ops = data.get("Operations", [])
        if not isinstance(ops, list):
            return False, "Operations must be an array"
        for i, op in enumerate(ops):
            if not isinstance(op, dict):
                return False, f"Operations[{i}] must be an object"
            if "Action" not in op:
                return False, f"Operations[{i}] requires an 'Action' field"
            if "ToolShape" not in op:
                return False, f"Operations[{i}] requires a 'ToolShape' field"

    else:
        return False, f"Unknown Intent: '{intent}'"

    return True, ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Legacy Format Migration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _migrate_legacy_format(data: dict) -> dict:
    """
    Convert the old SpawnActor format to the new Spawn Intent format.

    Old: {"Action":"SpawnActor","ClassToSpawn":"Building",
          "Parameters":{"NumberOfFloors":5,"X":0,"Y":0,"Z":0}}

    New: {"Intent":"Spawn","ID":"Legacy_<timestamp>","Style":"Default",
          "RequestedLoc":[0,0,0],"Parameters":{"Floors":5}}
    """
    params = data.get("Parameters", {})
    floors = max(1, int(params.get("NumberOfFloors", params.get("Floors", 3))))
    x = float(params.get("X", 0))
    y = float(params.get("Y", 0))
    z = float(params.get("Z", 0))

    migrated = {
        "Intent": "Spawn",
        "ID": f"Legacy_{int(time.time())}",
        "Style": "Default",
        "RequestedLoc": [x, y, z],
        "Parameters": {
            "Floors": floors,
        },
    }

    # Carry over any dimension overrides
    for key in ("FloorHeight", "BuildingWidth", "BuildingDepth", "WallThickness"):
        if key in params:
            migrated["Parameters"][key] = float(params[key])

    print("⚠️  Auto-migrated legacy SpawnActor format → new Spawn Intent.")
    return migrated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  City Manager Discovery
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _discover_city_manager(force_refresh: bool = False) -> str:
    """
    Find the AProceduralCityManager actor in the current Unreal level.

    Uses GetAllLevelActors via the EditorActorSubsystem, filters for
    actors with 'ProceduralCityManager' in their path, and caches the
    result for subsequent calls.

    Args:
        force_refresh: If True, bypass the cache and re-discover.

    Returns:
        The full UObject path of the CityManager actor.

    Raises:
        Exception: If no CityManager is found in the level.
    """
    global _manager_cache

    if _manager_cache and not force_refresh:
        # Validate cached path still exists
        try:
            await send_ue_ws_command(
                object_path=_manager_cache,
                function_name="GetActorLocation",
            )
            return _manager_cache
        except Exception:
            _manager_cache = None  # Cache busted — actor gone

    # Full discovery
    response = await send_ue_ws_command(
        object_path=_EDITOR_SUBSYSTEM,
        function_name="GetAllLevelActors",
    )

    # The return value is an array of actor object paths
    actors = response.get("ResponseBody", {}).get("ReturnValue", [])

    for actor_path in actors:
        actor_str = str(actor_path)
        if "ProceduralCityManager" in actor_str:
            _manager_cache = actor_str
            return actor_str

    raise Exception(
        "❌ No AProceduralCityManager found in the level.\n"
        "   Please place one in your map:\n"
        "   1. Compile the generated C++ files in your Unreal project\n"
        "   2. In the Content Browser, search for 'ProceduralCityManager'\n"
        "   3. Drag it into your level and save"
    )


def reset_manager_cache():
    """Force-clear the cached CityManager path and building ledger. Called by the 'refresh' command."""
    global _manager_cache, _fallback_warned, _spawned_buildings, _used_ids
    _manager_cache = None
    _fallback_warned = False
    _spawned_buildings = []
    _used_ids = set()
    print("   Also cleared the building position ledger and ID tracker.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Unreal Intent Handler — The Single WebSocket Call
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _handle_unreal_intent(data: dict) -> str:
    """
    Forward a validated intent to the AProceduralCityManager in Unreal.

    This is the Delegator pattern in action: Python sends a single
    WebSocket call with the full JSON payload. C++ does all the work
    (math, HISM, collision, ledger management) and returns a receipt.
    """
    # Discover the CityManager actor
    manager_path = await _discover_city_manager()

    # Serialize the validated data to a JSON string
    json_payload = json.dumps(data, separators=(",", ":"))
    log.info("WS → UE | Function: ProcessBlueprint | Payload size: %d bytes", len(json_payload))
    log.debug("WS → UE | Payload: %s", json_payload[:500])

    # Single WebSocket call to ProcessBlueprint
    response = await send_ue_ws_command(
        object_path=manager_path,
        function_name="ProcessBlueprint",
        parameters={"JsonPayload": json_payload},
    )

    # Extract the receipt JSON from the return value
    receipt_str = response.get("ResponseBody", {}).get("ReturnValue", "")
    log.info("WS ← UE | Receipt: %s", receipt_str[:300] if receipt_str else "(empty)")

    if not receipt_str:
        return "⚠️  No receipt returned from Unreal. Check the Output Log in UE."

    # Parse and pretty-print the receipt
    try:
        receipt = json.loads(receipt_str)
        return _format_receipt(receipt)
    except json.JSONDecodeError:
        return f"📦 Raw receipt from Unreal:\n   {receipt_str}"


def _format_receipt(receipt: dict) -> str:
    """Format a C++ receipt into a human-readable string."""
    action = receipt.get("Action", "")
    status = receipt.get("Status", "")

    if action == "BuildResult":
        building_id = receipt.get("ID", "")
        reason = receipt.get("Reason", "")

        if status == "Cleared":
            count = receipt.get("BuildingsRemoved", 0)
            return f"🗑️  ClearAll complete — {count} building(s) removed."

        if status == "Destroyed":
            return f"🗑️  Destroyed '{building_id}'"

        if status in ("Success", "Success_Nudged"):
            actual = receipt.get("ActualLoc", [0, 0, 0])
            loc_str = f"X:{actual[0]:.0f}, Y:{actual[1]:.0f}, Z:{actual[2]:.0f}"
            result = f"✅ Built '{building_id}' at {loc_str}"
            if status == "Success_Nudged":
                requested = receipt.get("RequestedLoc", [0, 0, 0])
                req_str = f"X:{requested[0]:.0f}, Y:{requested[1]:.0f}, Z:{requested[2]:.0f}"
                result += f"\n   ↪ Auto-nudged from {req_str} (obstacle detected)"
            return result

        if status == "Failed":
            return f"❌ Failed to build '{building_id}': {reason}"

        return f"📦 {status}: {building_id} — {reason}"

    elif action == "BatchResult":
        results = receipt.get("Results", [])
        lines = [f"📦 BatchSpawn complete — {len(results)} building(s):"]
        for r in results:
            rid = r.get("ID", "?")
            rstatus = r.get("Status", "?")
            if rstatus in ("Success", "Success_Nudged"):
                loc = r.get("ActualLoc", [0, 0, 0])
                lines.append(f"   ✅ {rid} at X:{loc[0]:.0f}, Y:{loc[1]:.0f}, Z:{loc[2]:.0f}")
            else:
                lines.append(f"   ❌ {rid}: {r.get('Reason', rstatus)}")
        return "\n".join(lines)

    elif action == "ScanResult":
        ground_z = receipt.get("GroundZ", 0)
        ext = receipt.get("ExternalCollisions", [])
        internal = receipt.get("InternalCollisions", [])
        lines = [f"👁️  ScanArea Result — GroundZ: {ground_z:.1f}"]
        if ext:
            lines.append(f"   External obstacles ({len(ext)}): {', '.join(ext[:10])}")
        else:
            lines.append("   External obstacles: None")
        if internal:
            lines.append(f"   Procedural buildings ({len(internal)}): {', '.join(internal[:10])}")
        else:
            lines.append("   Procedural buildings: None")
        lines.append(f"   Status: {status}")
        return "\n".join(lines)

    return f"📦 Receipt: {json.dumps(receipt, indent=2)}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main Router
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_agent_output(raw_content: str, output_dir: str, project_api: str,
                               user_prompt: str = "") -> str:
    """
    Parse the LLM's JSON output and execute the appropriate action.

    Args:
        raw_content:  The raw string from the LLM (should be valid JSON).
        output_dir:   Directory to write generated C++ files into.
        project_api:  The PROJECT_API macro name to substitute.
        user_prompt:  The original user prompt (for audit logging).

    Returns:
        A human-readable status string describing what happened.
    """
    # ── AUDIT: Log user prompt and raw LLM output ────────────────────
    log.info("=" * 60)
    log.info("USER PROMPT: %s", user_prompt or "(not provided)")
    log.info("LLM RAW OUTPUT (%d chars): %s", len(raw_content), raw_content[:500])
    if len(raw_content) > 500:
        log.debug("LLM FULL OUTPUT: %s", raw_content)

    # ── 1. Clean the raw string ─────────────────────────────────────
    content = raw_content.strip()

    # Strip markdown code fences if the LLM wrapped it anyway
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)

    # ── 2. Parse JSON ───────────────────────────────────────────────
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        repaired = _repair_truncated_json(content)
        try:
            data = json.loads(repaired)
            log.warning("LLM output was truncated — repaired JSON automatically.")
        except json.JSONDecodeError as e2:
            log.error("JSON PARSE FAILED: %s | Raw: %s", e2, content[:200])
            return (
                f"❌ JSON Parse Error (even after repair): {e2}\n"
                f"   Raw output (first 300 chars): {content[:300]}\n"
                f"   TIP: The Llama 3.1 8B model often truncates long output.\n"
                f"        Try: python agent.py gemini -b -i"
            )

    # ── 3. Determine routing ────────────────────────────────────────
    action = data.get("Action", "").strip()
    intent = data.get("Intent", "").strip()

    # ── Legacy format: SpawnActor → migrate to new Spawn intent ─────
    if action == "SpawnActor" and not intent:
        data = _migrate_legacy_format(data)
        intent = data.get("Intent", "")

    # ── Legacy format: no Action but has Files → CreateClass ────────
    if not action and not intent and "Files" in data:
        action = "CreateClass"
        data["Action"] = action

    # ── Auto-deduplicate IDs (prevent "already exists" rejections) ──
    if intent in ("Spawn", "BatchSpawn", "GenerateGeometry"):
        _deduplicate_ids(data)

    # ── 4. Route to the correct handler ─────────────────────────────
    if action == "CreateClass":
        return _handle_create_class(data, output_dir, project_api)

    if intent in ("Spawn", "BatchSpawn", "Modify", "Destroy", "ClearAll", "ScanArea", "GenerateGeometry"):
        # Validate the schema before forwarding
        valid, error = _validate_intent_schema(data)
        if not valid:
            return f"❌ Schema Validation Error: {error}"
        # Try C++ delegator, fall back to legacy if no CityManager
        return await _handle_intent_with_fallback(data)

    return (
        f"⚠️  Unknown Action/Intent: '{action or intent}'.\n"
        f"   Expected: CreateClass, Spawn, BatchSpawn, Modify, Destroy, ClearAll, or ScanArea."
    )


# ── Used IDs tracker (survives across commands in a session) ──────
_used_ids = set()


def _deduplicate_ids(data: dict):
    """
    Ensure every Spawn ID is unique across the entire session.
    If the LLM reuses an ID (e.g. 'WatchTower_01'), auto-suffix it
    with a short timestamp to make it unique.
    """
    global _used_ids

    if data.get("Intent") == "ClearAll":
        _used_ids.clear()
        return

    def _make_unique(original_id: str) -> str:
        if original_id not in _used_ids:
            _used_ids.add(original_id)
            return original_id
        # Append timestamp suffix
        suffix = int(time.time() * 1000) % 100000
        new_id = f"{original_id}_{suffix}"
        while new_id in _used_ids:
            suffix += 1
            new_id = f"{original_id}_{suffix}"
        _used_ids.add(new_id)
        log.info("ID dedup: '%s' → '%s'", original_id, new_id)
        return new_id

    if data.get("Intent") == "Spawn":
        old_id = data.get("ID", "")
        if old_id:
            data["ID"] = _make_unique(old_id)

    elif data.get("Intent") == "BatchSpawn":
        for bp in data.get("Blueprints", []):
            old_id = bp.get("ID", "")
            if old_id:
                bp["ID"] = _make_unique(old_id)

    elif data.get("Intent") == "GenerateGeometry":
        old_id = data.get("ID", "")
        if old_id:
            data["ID"] = _make_unique(old_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CreateClass Handler — Write C++ files to disk (Jinja2 + fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _handle_create_class(data: dict, output_dir: str, project_api: str) -> str:
    """
    Write generated .h and .cpp files to the output directory.

    Two modes:
    1. Jinja2 mode: If the LLM provides structured data (Properties, Functions),
       render via .j2 templates for clean, properly formatted C++.
    2. Raw mode: If the LLM provides a 'Files' array with Content strings,
       write them directly (legacy behavior).
    """
    class_name = data.get("ClassName", "UnknownClass")
    files = data.get("Files", [])

    log.info("CreateClass: '%s' — %d file(s)", class_name, len(files))

    # Try Jinja2 structured rendering first
    if not files and data.get("Properties") is not None or data.get("Functions") is not None:
        return _render_class_jinja(data, output_dir, project_api)

    if not files:
        return f"⚠️  CreateClass for '{class_name}' but no Files array was provided."

    os.makedirs(output_dir, exist_ok=True)

    written = []
    for file_entry in files:
        file_name = file_entry.get("FileName", "unknown.txt")
        content = file_entry.get("Content", "")

        # Substitute {{PROJECT_API}} with the actual macro
        content = content.replace("{{PROJECT_API}}", project_api)

        # Unescape \\n → actual newlines, \\t → actual tabs (LLM often double-escapes)
        content = content.replace("\\n", "\n").replace("\\t", "\t")

        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        written.append(file_path)
        log.info("CreateClass: wrote %s (%d bytes)", file_name, len(content))

    paths_str = "\n   ".join(written)
    return (
        f"✅ CreateClass: '{class_name}'\n"
        f"   Wrote {len(written)} file(s) to {output_dir}:\n"
        f"   {paths_str}"
    )


def _render_class_jinja(data: dict, output_dir: str, project_api: str) -> str:
    """Render C++ files using Jinja2 templates for clean output."""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        log.warning("Jinja2 not installed — falling back to raw CreateClass")
        return "⚠️  Jinja2 not installed. Run: pip install Jinja2"

    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    if not os.path.isdir(templates_dir):
        return f"⚠️  Templates directory not found: {templates_dir}"

    env = Environment(loader=FileSystemLoader(templates_dir), keep_trailing_newline=True)

    class_name = data.get("ClassName", "AMyActor")
    display_name = class_name.lstrip("A")  # Remove A prefix for display

    from datetime import datetime
    context = {
        "class_name": class_name,
        "display_name": display_name,
        "project_api": project_api,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tickable": data.get("Tickable", False),
        "properties": data.get("Properties", []),
        "functions": data.get("Functions", []),
        "extra_includes": data.get("ExtraIncludes", []),
        "begin_play_body": data.get("BeginPlayBody", ""),
        "tick_body": data.get("TickBody", ""),
    }

    os.makedirs(output_dir, exist_ok=True)
    written = []

    # Render header
    try:
        header_tmpl = env.get_template("ActorHeader.h.j2")
        header_content = header_tmpl.render(**context)
        header_path = os.path.join(output_dir, f"{class_name}.h")
        with open(header_path, "w", encoding="utf-8") as f:
            f.write(header_content)
        written.append(header_path)
        log.info("Jinja2: rendered %s.h (%d bytes)", class_name, len(header_content))
    except Exception as e:
        log.error("Jinja2 header render failed: %s", e)

    # Render source
    try:
        source_tmpl = env.get_template("ActorSource.cpp.j2")
        source_content = source_tmpl.render(**context)
        source_path = os.path.join(output_dir, f"{class_name}.cpp")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_content)
        written.append(source_path)
        log.info("Jinja2: rendered %s.cpp (%d bytes)", class_name, len(source_content))
    except Exception as e:
        log.error("Jinja2 source render failed: %s", e)

    if not written:
        return f"❌ Jinja2 rendering failed for '{class_name}'"

    paths_str = "\n   ".join(written)
    return (
        f"✅ CreateClass (Jinja2): '{class_name}'\n"
        f"   Rendered {len(written)} file(s) to {output_dir}:\n"
        f"   {paths_str}\n"
        f"   💡 Press Ctrl+Alt+F11 in Unreal to trigger Live Coding."
    )
