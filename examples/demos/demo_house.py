"""
=== UNREAL MCP - HOUSE BUILDER ===
Builds a small house/hut in Unreal Engine using primitive shapes.

Structure:
  - Floor slab (scaled cube)
  - 4 walls (scaled cubes)
  - Gable roof (2 angled cubes)
  - Door opening (front wall split)
  - Chimney (cylinder on roof)
  - Fence posts around the yard
  - Path to the door
  - Lights inside and outside

No LLM, no API keys. Direct tool calls.

Run:  python demo_house.py
"""
import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from unreal_mcp.tools.spawning import spawn_actor_internal
from unreal_mcp.tools.transform import set_actor_scale, set_actor_rotation


async def spawn(shape, x, y, z, label=""):
    """Spawn and return path."""
    path, _ = await spawn_actor_internal(shape, x, y, z)
    print(f"  + {label or shape}")
    await asyncio.sleep(0.12)
    return path


async def spawn_scaled(shape, x, y, z, sx, sy, sz, label=""):
    """Spawn an actor and scale it immediately."""
    path = await spawn(shape, x, y, z, label)
    if path:
        await set_actor_scale(path, sx, sy, sz)
    return path


async def spawn_rotated(shape, x, y, z, pitch, yaw, roll, label=""):
    """Spawn an actor and rotate it immediately."""
    path = await spawn(shape, x, y, z, label)
    if path:
        await set_actor_rotation(path, pitch, yaw, roll)
    return path


async def spawn_full(shape, x, y, z, sx, sy, sz, pitch=0, yaw=0, roll=0, label=""):
    """Spawn, scale, and rotate."""
    path = await spawn(shape, x, y, z, label)
    if path:
        await set_actor_scale(path, sx, sy, sz)
        if pitch or yaw or roll:
            await set_actor_rotation(path, pitch, yaw, roll)
    return path


# ── House dimensions (UE units) ──────────────────────────────────────
# Default cube is 100x100x100 units. Scale multipliers below.
BASE_X = 0       # House center X
BASE_Y = 0       # House center Y
BASE_Z = 0       # Ground level


async def build_floor():
    """Large flat floor slab."""
    print("\n[1/8] Building floor...")
    await spawn_scaled("cube", BASE_X, BASE_Y, BASE_Z,
                       8, 6, 0.2, label="FLOOR SLAB (800x600)")


async def build_walls():
    """4 walls with a door gap in the front."""
    print("\n[2/8] Building walls...")

    wall_h = 3.0   # wall height scale
    wall_t = 0.2   # wall thickness scale

    # Back wall (full width)
    await spawn_scaled("cube", BASE_X, BASE_Y - 300, 150 + BASE_Z,
                       8, wall_t, wall_h, label="BACK WALL")

    # Left wall
    await spawn_scaled("cube", BASE_X - 400, BASE_Y, 150 + BASE_Z,
                       wall_t, 6, wall_h, label="LEFT WALL")

    # Right wall
    await spawn_scaled("cube", BASE_X + 400, BASE_Y, 150 + BASE_Z,
                       wall_t, 6, wall_h, label="RIGHT WALL")

    # Front wall - LEFT section (door gap in center)
    await spawn_scaled("cube", BASE_X - 250, BASE_Y + 300, 150 + BASE_Z,
                       3, wall_t, wall_h, label="FRONT WALL (left)")

    # Front wall - RIGHT section
    await spawn_scaled("cube", BASE_X + 250, BASE_Y + 300, 150 + BASE_Z,
                       3, wall_t, wall_h, label="FRONT WALL (right)")

    # Front wall - TOP (above door)
    await spawn_scaled("cube", BASE_X, BASE_Y + 300, 250 + BASE_Z,
                       2, wall_t, 1.0, label="FRONT WALL (above door)")


async def build_roof():
    """Gable roof - two angled planes."""
    print("\n[3/8] Building roof...")

    # Left roof slope
    await spawn_full("cube", BASE_X - 200, BASE_Y, 350 + BASE_Z,
                     5, 7, 0.15,
                     pitch=0, yaw=0, roll=25,
                     label="ROOF LEFT SLOPE")

    # Right roof slope
    await spawn_full("cube", BASE_X + 200, BASE_Y, 350 + BASE_Z,
                     5, 7, 0.15,
                     pitch=0, yaw=0, roll=-25,
                     label="ROOF RIGHT SLOPE")


async def build_chimney():
    """Chimney on the roof."""
    print("\n[4/8] Building chimney...")
    await spawn_scaled("cylinder", BASE_X + 250, BASE_Y - 150, 400 + BASE_Z,
                       0.5, 0.5, 2.5, label="CHIMNEY")


async def build_door_step():
    """Small step at the door entrance."""
    print("\n[5/8] Building door step and path...")

    # Door step
    await spawn_scaled("cube", BASE_X, BASE_Y + 350, BASE_Z,
                       1.5, 0.8, 0.15, label="DOOR STEP")

    # Walkway - series of flat cubes leading to the door
    for i in range(4):
        await spawn_scaled("cube", BASE_X, BASE_Y + 450 + i * 120, BASE_Z - 5,
                           1.2, 1, 0.1, label=f"PATH STONE {i+1}")


async def build_fence():
    """Fence posts around the front yard."""
    print("\n[6/8] Building fence...")

    fence_y_start = BASE_Y + 400
    fence_y_end = BASE_Y + 900

    # Left fence posts
    for i in range(4):
        y = fence_y_start + i * (fence_y_end - fence_y_start) / 3
        await spawn_scaled("cylinder", BASE_X - 500, y, 50 + BASE_Z,
                           0.15, 0.15, 1.0, label=f"FENCE POST L{i+1}")

    # Right fence posts
    for i in range(4):
        y = fence_y_start + i * (fence_y_end - fence_y_start) / 3
        await spawn_scaled("cylinder", BASE_X + 500, y, 50 + BASE_Z,
                           0.15, 0.15, 1.0, label=f"FENCE POST R{i+1}")

    # Front fence (with gate gap)
    await spawn_scaled("cylinder", BASE_X - 500, fence_y_end, 50 + BASE_Z,
                       0.15, 0.15, 1.0, label="FENCE CORNER L")
    await spawn_scaled("cylinder", BASE_X + 500, fence_y_end, 50 + BASE_Z,
                       0.15, 0.15, 1.0, label="FENCE CORNER R")


async def build_lights():
    """Interior and exterior lights."""
    print("\n[7/8] Placing lights...")

    # Interior light
    await spawn("pointlight", BASE_X, BASE_Y, 250 + BASE_Z, label="INTERIOR LIGHT")

    # Porch light
    await spawn("pointlight", BASE_X, BASE_Y + 320, 250 + BASE_Z, label="PORCH LIGHT")

    # Yard lights
    await spawn("pointlight", BASE_X - 500, BASE_Y + 700, 150 + BASE_Z, label="YARD LIGHT L")
    await spawn("pointlight", BASE_X + 500, BASE_Y + 700, 150 + BASE_Z, label="YARD LIGHT R")


async def build_decorations():
    """Small decorative elements."""
    print("\n[8/8] Adding decorations...")

    # Sphere bushes near the door
    await spawn_scaled("sphere", BASE_X - 200, BASE_Y + 380, 40 + BASE_Z,
                       0.8, 0.8, 0.8, label="BUSH LEFT")
    await spawn_scaled("sphere", BASE_X + 200, BASE_Y + 380, 40 + BASE_Z,
                       0.8, 0.8, 0.8, label="BUSH RIGHT")

    # Cone trees in the yard
    await spawn_scaled("cone", BASE_X - 400, BASE_Y + 700, 100 + BASE_Z,
                       1.0, 1.0, 3.0, label="TREE LEFT")
    await spawn_scaled("cone", BASE_X + 400, BASE_Y + 700, 100 + BASE_Z,
                       1.0, 1.0, 3.0, label="TREE RIGHT")


async def main():
    print("=" * 60)
    print("      UNREAL MCP - House Builder")
    print("      Building a complete house with yard")
    print("=" * 60)

    await build_floor()
    await build_walls()
    await build_roof()
    await build_chimney()
    await build_door_step()
    await build_fence()
    await build_lights()
    await build_decorations()

    print("\n" + "=" * 60)
    print("  HOUSE COMPLETE!")
    print()
    print("  What you should see:")
    print("    - Floor slab with 4 walls and door opening")
    print("    - Gable roof with chimney")
    print("    - Front path with stepping stones")
    print("    - Fence posts around the yard")
    print("    - Interior + exterior lighting")
    print("    - Bush and tree decorations")
    print()
    print("  ~40 objects, all placed programmatically!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
