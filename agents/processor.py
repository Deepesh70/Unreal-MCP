"""
Processor — Routes LLM JSON output to the correct action.

The LLM outputs strict JSON with an "Action" field:
  - "CreateClass" → Write .h/.cpp files to disk
  - "SpawnActor" → Send spawn command to Unreal via WebSocket

This module is the bridge between the LLM's brain and the real world.
"""

import json
import os
import re

from unreal_mcp.connection import send_ue_ws_command


# ── Editor Library path used for spawn calls ─────────────────────────
_EDITOR_LIB = "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary"


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


async def process_agent_output(raw_content: str, output_dir: str, project_api: str) -> str:
    """
    Parse the LLM's JSON output and execute the appropriate action.

    Args:
        raw_content:  The raw string from the LLM (should be valid JSON).
        output_dir:   Directory to write generated C++ files into.
        project_api:  The PROJECT_API macro name to substitute.

    Returns:
        A human-readable status string describing what happened.
    """
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
        # The LLM may have hit its token limit and truncated the JSON.
        # Try to repair it before giving up.
        repaired = _repair_truncated_json(content)
        try:
            data = json.loads(repaired)
            print("⚠️  LLM output was truncated — repaired JSON automatically.")
            print("   The generated C++ files may be incomplete. Use a larger model for best results.")
        except json.JSONDecodeError as e2:
            return (
                f"❌ JSON Parse Error (even after repair): {e2}\n"
                f"   Raw output (first 300 chars): {content[:300]}\n"
                f"   TIP: The Llama 3.1 8B model often truncates long output.\n"
                f"        Try: python agent.py gemini -b -i"
            )

    action = data.get("Action", "").strip()

    # ── Legacy format (no Action field, but has Files) → treat as CreateClass
    if not action and "Files" in data:
        action = "CreateClass"
        data["Action"] = action

    # ── 3. Route to the correct handler ─────────────────────────────
    if action == "CreateClass":
        return _handle_create_class(data, output_dir, project_api)
    elif action == "SpawnActor":
        return await _handle_spawn_actor(data)
    else:
        return f"⚠️  Unknown Action: '{action}'. Expected 'CreateClass' or 'SpawnActor'."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CreateClass Handler — Write C++ files to disk
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _handle_create_class(data: dict, output_dir: str, project_api: str) -> str:
    """Write the generated .h and .cpp files to the output directory."""
    class_name = data.get("ClassName", "UnknownClass")
    files = data.get("Files", [])

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

    paths_str = "\n   ".join(written)
    return (
        f"✅ CreateClass: '{class_name}'\n"
        f"   Wrote {len(written)} file(s) to {output_dir}:\n"
        f"   {paths_str}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SpawnActor Handler — Build real structures from basic shapes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Basic shape assets available in every UE project
_SHAPE_ASSETS = {
    "cube":     "/Engine/BasicShapes/Cube.Cube",
    "sphere":   "/Engine/BasicShapes/Sphere.Sphere",
    "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
    "cone":     "/Engine/BasicShapes/Cone.Cone",
    "plane":    "/Engine/BasicShapes/Plane.Plane",
}

# ── Building dimensions (UE units; default cube = 100x100x100) ───────
# Each "floor" is 300 UU tall (3 meters).  Walls are thin slabs on
# the perimeter; floor slabs are flat cubes at the base of each storey.
_FLOOR_HEIGHT = 300.0       # wall height per storey  (100 * 3.0)
_BUILDING_WIDTH = 1000.0    # width/depth of the building (100 * 10)
_WALL_THICKNESS = 20.0      # thickness of each wall  (100 * 0.2)

_CUBE_ASSET = _SHAPE_ASSETS["cube"]


async def _spawn_and_scale(x, y, z, sx, sy, sz, asset=_CUBE_ASSET):
    """Spawn a shape at (x,y,z) then scale it to (sx,sy,sz). Returns actor path or None."""
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


async def _handle_spawn_actor(data: dict) -> str:
    """
    Build a procedural structure in Unreal Engine.

    For each floor the handler spawns:
      • 1 floor slab   (flat cube at the base of the storey)
      • 4 walls         (thin cubes on the front/back/left/right edges)
    Plus 1 roof slab on top.

    A 5-floor building ≈ 26 actors — and it actually looks like a building.
    """
    class_to_spawn = data.get("ClassToSpawn", "Building")
    parameters = data.get("Parameters", {})

    num_floors = max(1, int(parameters.get("NumberOfFloors", 1)))
    base_x = float(parameters.get("X", 0))
    base_y = float(parameters.get("Y", 0))
    base_z = float(parameters.get("Z", 0))

    # Allow the LLM to override dimensions
    floor_height = float(parameters.get("FloorHeight", _FLOOR_HEIGHT))
    bldg_width = float(parameters.get("BuildingWidth", _BUILDING_WIDTH))
    bldg_depth = float(parameters.get("BuildingDepth", _BUILDING_WIDTH))
    wall_thick = float(parameters.get("WallThickness", _WALL_THICKNESS))

    half_w = bldg_width / 2.0
    half_d = bldg_depth / 2.0

    # Scale factors (cube base = 100 UU)
    slab_sx = bldg_width / 100.0
    slab_sy = bldg_depth / 100.0
    slab_sz = 0.2                       # thin floor slab

    wall_fb_sx = bldg_width / 100.0     # front/back wall: full width
    wall_fb_sy = wall_thick / 100.0     # thin
    wall_fb_sz = floor_height / 100.0   # full storey height

    wall_lr_sx = wall_thick / 100.0     # left/right wall: thin
    wall_lr_sy = bldg_depth / 100.0     # full depth
    wall_lr_sz = floor_height / 100.0   # full storey height

    spawned = 0
    errors = []

    for f in range(num_floors):
        floor_z = base_z + (f * floor_height)

        try:
            # ── Floor slab ──────────────────────────────────────
            await _spawn_and_scale(
                base_x, base_y, floor_z,
                slab_sx, slab_sy, slab_sz,
            )
            spawned += 1

            # ── Front wall (Y + half_d) ────────────────────────
            wall_z = floor_z + floor_height / 2.0  # center of wall
            await _spawn_and_scale(
                base_x, base_y + half_d, wall_z,
                wall_fb_sx, wall_fb_sy, wall_fb_sz,
            )
            spawned += 1

            # ── Back wall (Y - half_d) ─────────────────────────
            await _spawn_and_scale(
                base_x, base_y - half_d, wall_z,
                wall_fb_sx, wall_fb_sy, wall_fb_sz,
            )
            spawned += 1

            # ── Left wall (X - half_w) ─────────────────────────
            await _spawn_and_scale(
                base_x - half_w, base_y, wall_z,
                wall_lr_sx, wall_lr_sy, wall_lr_sz,
            )
            spawned += 1

            # ── Right wall (X + half_w) ────────────────────────
            await _spawn_and_scale(
                base_x + half_w, base_y, wall_z,
                wall_lr_sx, wall_lr_sy, wall_lr_sz,
            )
            spawned += 1

        except Exception as e:
            errors.append(f"Floor {f}: {e}")
            break  # UE probably offline

    # ── Roof slab ───────────────────────────────────────────────
    if not errors:
        try:
            roof_z = base_z + (num_floors * floor_height)
            await _spawn_and_scale(
                base_x, base_y, roof_z,
                slab_sx, slab_sy, slab_sz,
            )
            spawned += 1
        except Exception as e:
            errors.append(f"Roof: {e}")

    # ── Report ──────────────────────────────────────────────────
    if spawned == 0 and errors:
        return (
            f"❌ SpawnActor failed — could not spawn any shapes:\n"
            f"   {errors[0]}\n"
            f"   Is Unreal Engine running with the Remote Control plugin?"
        )

    total_h = num_floors * floor_height
    result = (
        f"✅ Built '{class_to_spawn}' in Unreal Editor!\n"
        f"   {num_floors} floors × (1 slab + 4 walls) + 1 roof = {spawned} actors\n"
        f"   Building: {bldg_width:.0f} × {bldg_depth:.0f} × {total_h:.0f} UU "
        f"({bldg_width/100:.0f} × {bldg_depth/100:.0f} × {total_h/100:.0f} m)\n"
        f"   Location: X={base_x}, Y={base_y}, Z={base_z}"
    )
    if errors:
        result += f"\n   ⚠️  {len(errors)} part(s) failed: {errors[0]}"

    return result
