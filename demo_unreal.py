"""
=== UNREAL ENGINE LIVE DEMO ===
No LLM needed! Directly calls MCP tools to spawn objects in UE.

Requirements:
  1. Unreal Engine must be open with Remote Control plugin enabled
  2. python server.py must be running in another terminal

Run:  python demo_unreal.py
"""
import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from unreal_mcp.tools.spawning import spawn_actor
from unreal_mcp.tools.actors import list_actors
from unreal_mcp.tools.transform import set_actor_scale


async def main():
    print("=" * 60)
    print("  UNREAL MCP - Live Engine Demo (No LLM Required)")
    print("=" * 60)

    # Step 1: Spawn a Cube
    print("\n[1/5] Spawning a CUBE at (0, 0, 200)...")
    result = await spawn_actor("cube", x=0, y=0, z=200)
    print(f"  -> {result}")

    # Step 2: Spawn a Sphere
    print("\n[2/5] Spawning a SPHERE at (500, 0, 200)...")
    result = await spawn_actor("sphere", x=500, y=0, z=200)
    print(f"  -> {result}")

    # Step 3: Spawn a Cone
    print("\n[3/5] Spawning a CONE at (1000, 0, 200)...")
    result = await spawn_actor("cone", x=1000, y=0, z=200)
    print(f"  -> {result}")

    # Step 4: List all actors to find the cube path
    print("\n[4/5] Listing all actors in the level...")
    actors = await list_actors()
    print(f"  -> {actors[:300]}...")

    # Step 5: Scale the cube to be HUGE
    # Try to find the cube path from the actor list
    cube_path = None
    for line in actors.split("\n"):
        if "Cube" in line or "cube" in line:
            # Extract the path (usually after "Path: " or similar)
            if "/" in line:
                parts = line.split()
                for part in parts:
                    if "/" in part and "Cube" in part:
                        cube_path = part.strip()
                        break

    if cube_path:
        print(f"\n[5/5] Scaling cube ({cube_path}) to 5x size...")
        result = await set_actor_scale(cube_path, 5.0, 5.0, 5.0)
        print(f"  -> {result}")
    else:
        print("\n[5/5] Could not find cube path to scale. Check Unreal Editor!")

    print("\n" + "=" * 60)
    print("  Check your Unreal viewport - you should see 3 shapes!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
