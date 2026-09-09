"""
Tool Discovery & Toolset Meta-Tools.

Provides on-demand toolset discovery matching the pattern introduced in
Epic Games' official Unreal MCP (UE 5.8):
  - list_toolsets: Returns list of available toolsets and descriptions.
  - describe_toolset: Returns detailed parameter schemas for a chosen toolset.
  - call_tool: Dispatches a tool call dynamically.

This keeps initial LLM system prompts and tool lists token-lean.
"""

import json
from typing import Dict, Any, List
from unreal_mcp import mcp
from unreal_mcp.utils import format_error

# Registered toolsets grouping existing tools into logical modules
TOOLSET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ProceduralBuildingTools": {
        "description": "Procedural architecture generation, HISM buildings, and city structures via AProceduralCityManager.",
        "tools": {
            "get_scene_summary": "Get a spatial summary of all actors in the scene to find clear coordinates.",
        }
    },
    "ActorTools": {
        "description": "Inspect, list, and modify actors and transforms in the active Unreal level.",
        "tools": {
            "list_actors": "List all actors currently placed in the Unreal level.",
            "spawn_actor": "Spawn a primitive actor (cube, sphere, cylinder, cone, plane) at (x, y, z).",
            "set_actor_scale": "Scale a named actor to target (sx, sy, sz).",
            "modify_actor": "Translate, rotate, or scale an existing actor.",
            "destroy_actor": "Delete an actor from the active level.",
        }
    },
    "SceneTools": {
        "description": "Query scene state with intelligent noise filtering (filters HLODs, LandscapeProxies).",
        "tools": {
            "get_scene_state": "Retrieve structured list of actors with noise filtering applied.",
        }
    },
    "MaterialTools": {
        "description": "List and apply color and starter content materials by friendly name.",
        "tools": {
            "list_materials": "List all 24 available friendly material presets (wood, concrete, gold, glass, etc.).",
            "set_material": "Apply a friendly material name or asset path to a specific actor.",
        }
    },
    "ScriptingTools": {
        "description": "Execute arbitrary Python scripts and console commands live in Unreal Editor.",
        "tools": {
            "execute_python_in_editor": "Run arbitrary Python code inside Unreal Engine's embedded Python interpreter.",
            "run_console_command": "Execute an Unreal Engine console command (e.g. Stat FPS, HighResShot).",
            "get_actor_property": "Read a reflection property value from an actor.",
            "set_actor_property": "Modify a reflection property value on an actor.",
        }
    },
    "InspectionTools": {
        "description": "Viewport screenshots, health diagnostics, and asset discovery.",
        "tools": {
            "capture_viewport": "Take a high-resolution viewport screenshot and return the saved image file path.",
            "check_connection": "Diagnose MCP, WebSocket, Remote Control, and Python plugin health.",
            "find_assets": "Search the Unreal project Content directory for assets by class or name pattern.",
            "import_asset": "Import an external FBX/OBJ or image asset into the project.",
            "add_starter_content": "Add standard Starter Content pack to the active project.",
        }
    },
    "CodeGenTools": {
        "description": "Generate and preview Unreal Engine C++ classes (.h / .cpp) from structured JSON specifications.",
        "tools": {
            "generate_ue_class": "Generate full C++ class (.h/.cpp) with variables, functions, and tick implementation.",
            "preview_ue_class": "Preview C++ code in memory without writing to disk.",
            "get_project_info": "Inspect the active Unreal project name and source path.",
            "list_project_files": "List existing C++ headers and source files in the project.",
            "list_supported_types": "List supported variable types mapped to Unreal C++ types.",
        }
    },
}


@mcp.tool()
async def list_toolsets() -> str:
    """List all available toolsets with summary descriptions (low-token discovery)."""
    lines = ["Available Unreal MCP Toolsets:"]
    for name, info in sorted(TOOLSET_REGISTRY.items()):
        tool_count = len(info.get("tools", {}))
        lines.append(f"  • {name} ({tool_count} tools): {info.get('description')}")
    lines.append("\nUse 'describe_toolset(name)' to view tools and schemas for any toolset.")
    return "\n".join(lines)


@mcp.tool()
async def describe_toolset(toolset_name: str) -> str:
    """Get the schemas and tool list for a named toolset."""
    if toolset_name not in TOOLSET_REGISTRY:
        valid = ", ".join(TOOLSET_REGISTRY.keys())
        return f"Unknown toolset '{toolset_name}'. Valid toolsets: {valid}"

    info = TOOLSET_REGISTRY[toolset_name]
    lines = [
        f"Toolset: {toolset_name}",
        f"Description: {info['description']}",
        "Tools in this set:"
    ]
    for tool, desc in info.get("tools", {}).items():
        lines.append(f"  - {tool}: {desc}")
    return "\n".join(lines)
