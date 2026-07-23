"""
Unreal MCP — Root Package.

Creates the shared FastMCP instance and loads all tool modules so their
@mcp.tool() decorators register automatically at import time.

Usage (from server.py):
    from unreal_mcp import mcp
    mcp.run(...)
"""

from fastmcp import FastMCP

# ── Shared MCP instance ──────────────────────────────────────────────
mcp = FastMCP(
    "UnrealMCP",
    instructions="""You are connected to a LIVE Unreal Engine editor via MCP tools.
You control the 3D editor by calling the tools below — that is your ONLY interface.

⚠️  CRITICAL RULES:
• DO NOT create, edit, or modify any files on the user's disk.
• DO NOT write Python scripts, JavaScript, or any code files.
• DO NOT touch files like modify.py, server.py, or anything in unreal_mcp/.
• You work ENTIRELY through the MCP tools listed below. Just call them.

🔧 WORKFLOW:
1. check_connection — verify Unreal Engine is reachable
2. get_scene_state  — see what already exists before changing anything
3. spawn_actor / modify_actor / set_material / destroy_actor — build and edit
4. get_scene_state  — verify your changes worked

🎨 SPAWNABLE SHAPES: cube, sphere, cylinder, cone, plane
💡 SPAWNABLE LIGHTS: pointlight, spotlight, directional_light
🏠 STARTER CONTENT MESHES: chair, couch, door, table_round, table_square, pillar, 
   rock, shelf, wall, floor, stairs, lamp_ceiling, lamp_desk, frame, statue, mat_preview

🎨 MATERIALS (use with set_material tool, friendly names):
  Metals:  steel, chrome, gold, copper, rust, iron
  Stone:   brick, stone, cobble, concrete, slate
  Wood:    wood, pine, walnut
  Ground:  grass, gravel, water, ocean
  Walls:   floor, wall, tile

📐 UNITS: 1 Unreal Unit = 1 centimeter. A person is ~180 UU tall.
   A standard cube is 100x100x100 UU (1 meter).
""",
)

# ── Auto-register all tools by importing the tools package ───────────
from unreal_mcp import tools  # noqa: E402, F401
