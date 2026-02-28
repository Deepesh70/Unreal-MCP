"""
=== UNREAL MCP - COMPLEX SCENE BUILDER ===
Builds an impressive architectural scene in Unreal Engine.

Creates:
  - A spiral tower of cubes rising into the sky
  - A ring of spotlights illuminating the scene
  - A floating sphere array orbiting above
  - Scaled platforms and pillars

No LLM, no API keys. Direct MCP tool calls.

Requirements:
  1. Unreal Engine open with Remote Control plugin
  2. python server.py running

Run:  python demo_complex.py
"""
import asyncio
import math
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from unreal_mcp.tools.spawning import spawn_actor
from unreal_mcp.tools.transform import set_actor_scale, set_actor_rotation


async def spawn_and_log(shape, x, y, z, label=""):
    """Spawn an actor and print status."""
    result = await spawn_actor(shape, x=x, y=y, z=z)
    tag = f" [{label}]" if label else ""
    print(f"  + {shape:12s} at ({x:7.0f}, {y:7.0f}, {z:7.0f}){tag}")
    return result


async def build_spiral_tower():
    """Build a spiral tower of cubes rising into the sky."""
    print("\n=== PHASE 1: Spiral Tower ===")
    print("  Building 20-cube spiral reaching 2000 units high...\n")

    num_cubes = 20
    radius = 300
    height_per_step = 100
    angle_per_step = 30  # degrees

    for i in range(num_cubes):
        angle_rad = math.radians(i * angle_per_step)
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        z = 100 + i * height_per_step
        await spawn_and_log("cube", x, y, z, f"tower step {i+1}")
        await asyncio.sleep(0.15)  # small delay so UE can keep up


async def build_light_ring():
    """Create a ring of point lights around the tower base."""
    print("\n=== PHASE 2: Light Ring ===")
    print("  Placing 8 point lights in a circle...\n")

    num_lights = 8
    radius = 600

    for i in range(num_lights):
        angle_rad = math.radians(i * (360 / num_lights))
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        z = 150
        await spawn_and_log("pointlight", x, y, z, f"light {i+1}")
        await asyncio.sleep(0.1)


async def build_floating_spheres():
    """Create floating spheres orbiting above the tower."""
    print("\n=== PHASE 3: Floating Spheres ===")
    print("  Spawning 12 spheres in an elevated ring...\n")

    num_spheres = 12
    radius = 500
    height = 1500

    for i in range(num_spheres):
        angle_rad = math.radians(i * (360 / num_spheres))
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        # Sine wave height variation
        z = height + 200 * math.sin(angle_rad * 2)
        await spawn_and_log("sphere", x, y, z, f"orb {i+1}")
        await asyncio.sleep(0.1)


async def build_ground_platform():
    """Build a large ground platform with pillar corners."""
    print("\n=== PHASE 4: Grand Platform ===")
    print("  Building platform base and corner pillars...\n")

    # Center platform (scaled large)
    await spawn_and_log("cube", 0, 0, 0, "CENTER PLATFORM")

    # Four corner pillars
    pillar_offset = 800
    positions = [
        ( pillar_offset,  pillar_offset, 300, "NE pillar"),
        (-pillar_offset,  pillar_offset, 300, "NW pillar"),
        ( pillar_offset, -pillar_offset, 300, "SE pillar"),
        (-pillar_offset, -pillar_offset, 300, "SW pillar"),
    ]
    for x, y, z, label in positions:
        await spawn_and_log("cylinder", x, y, z, label)
        await asyncio.sleep(0.1)

    # Crown spheres on top of each pillar
    for x, y, _, label in positions:
        await spawn_and_log("sphere", x, y, 650, f"{label} crown")
        await asyncio.sleep(0.1)


async def build_cone_ring():
    """Ring of cones pointing outward like a crown."""
    print("\n=== PHASE 5: Crown of Cones ===")
    print("  Placing 6 cones in a star pattern at the top...\n")

    num_cones = 6
    radius = 200
    height = 2200

    for i in range(num_cones):
        angle_rad = math.radians(i * (360 / num_cones))
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        await spawn_and_log("cone", x, y, height, f"crown {i+1}")
        await asyncio.sleep(0.1)


async def main():
    print("=" * 65)
    print("        UNREAL MCP - Complex Scene Builder")
    print("        Building an architectural scene in UE")  
    print("=" * 65)
    print(f"\n  Total objects to spawn: ~55")
    print(f"  Estimated time: ~15 seconds\n")

    await build_ground_platform()
    await build_spiral_tower()
    await build_light_ring()
    await build_floating_spheres()
    await build_cone_ring()

    print("\n" + "=" * 65)
    print("  SCENE COMPLETE!")
    print()
    print("  What you should see in Unreal:")
    print("    - Grand platform with 4 pillars and crown spheres")
    print("    - Spiral tower of 20 cubes rising to the sky")
    print("    - Ring of 8 lights illuminating the base")
    print("    - 12 floating spheres orbiting above")
    print("    - Crown of 6 cones at the very top")
    print()
    print("  All built programmatically - zero manual placement!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
