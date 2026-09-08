"""
Material Tool — apply materials and colors to actors.

Gives the AI the ability to make scenes look realistic by applying
Starter Content materials (steel, brick, wood, etc.) or custom materials
to any actor in the scene. Works via Remote Control property setter
(no Python plugin needed).
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command, send_ue_ws_property
from unreal_mcp.mappings.materials import get_material_path, list_available_materials
from unreal_mcp.utils import format_error


@mcp.tool()
async def set_material(
    actor_path: str,
    material: str,
    slot_index: int = 0,
) -> str:
    """Apply a material to an actor to change its appearance.

    Makes scenes look realistic by applying real materials like steel, brick,
    wood, gold, concrete, etc. instead of the plain white default.

    Supports friendly names that map to Starter Content materials.

    Args:
        actor_path: Full path to the actor (from get_scene_state or spawn_actor).
        material: Friendly name ('steel', 'brick', 'wood', 'gold', 'chrome',
                  'concrete', 'grass', 'water', etc.) or a full UE material path
                  starting with '/'.

                  Available materials:
                    Metals:  steel, chrome, gold, copper, rust, iron
                    Stone:   brick, stone, cobble, concrete, slate
                    Wood:    wood, pine, walnut
                    Ground:  grass, gravel, water, ocean
                    Walls:   floor, wall, tile
                    Engine:  default, wireframe
        slot_index: Material slot index (default 0). Most actors only have slot 0.

    Returns:
        Confirmation of the material change, or an error with available options.
    """
    # Resolve friendly name to full path
    mat_path = get_material_path(material)

    if not mat_path:
        available = ", ".join(sorted(list_available_materials().keys()))
        return (
            f"Unknown material '{material}'. Available friendly names:\n"
            f"{available}\n\n"
            f"Or pass a full UE material path like '/Game/MyProject/Materials/M_Custom'."
        )

    try:
        # The StaticMeshComponent is usually the first component on the actor
        component_path = actor_path + ".StaticMeshComponent0"

        # Use SetMaterial via UFunction call on the PrimitiveComponent
        await send_ue_ws_command(
            object_path=component_path,
            function_name="SetMaterial",
            parameters={
                "ElementIndex": slot_index,
                "Material": mat_path,
            },
        )

        short_name = actor_path.split(".")[-1]
        return (
            f"Applied material '{material}' ({mat_path.split('/')[-1].split('.')[0]}) "
            f"to {short_name} (slot {slot_index})."
        )

    except Exception as e:
        error_msg = str(e)

        # If the component path didn't work, try alternative component names
        alternative_components = [
            ".StaticMeshComponent",
            ".SkeletalMeshComponent0",
            ".MeshComponent",
        ]

        for alt_comp in alternative_components:
            try:
                alt_path = actor_path + alt_comp
                await send_ue_ws_command(
                    object_path=alt_path,
                    function_name="SetMaterial",
                    parameters={
                        "ElementIndex": slot_index,
                        "Material": mat_path,
                    },
                )

                short_name = actor_path.split(".")[-1]
                return (
                    f"Applied material '{material}' to {short_name} "
                    f"(via {alt_comp}, slot {slot_index})."
                )
            except Exception:
                continue

        return format_error(
            e,
            f"Could not apply material to this actor. "
            f"The actor may not have a mesh component. "
            f"Try calling get_scene_state first to verify the actor type."
        )


@mcp.tool()
async def list_materials() -> str:
    """List all available material friendly names and their UE paths.

    Use this to discover what materials you can apply with set_material.

    Returns:
        A categorized list of all available materials.
    """
    mats = list_available_materials()

    categories = {
        "Metals": ["steel", "chrome", "gold", "copper", "rust", "iron"],
        "Stone & Concrete": ["brick", "stone", "cobble", "concrete", "slate"],
        "Wood": ["wood", "pine", "walnut"],
        "Ground & Nature": ["grass", "gravel", "water", "ocean"],
        "Architecture": ["floor", "wall", "tile"],
        "Engine Built-in": ["default", "wireframe"],
    }

    lines = ["Available materials for set_material:\n"]
    for category, names in categories.items():
        lines.append(f"\n{category}:")
        for name in names:
            if name in mats:
                short_path = mats[name].split("/")[-1].split(".")[0]
                lines.append(f"  {name:12s} → {short_path}")

    lines.append(
        "\n\nNote: Starter Content materials require the project to include "
        "Starter Content. You can also pass any full UE material path "
        "starting with '/' to set_material."
    )

    return "\n".join(lines)
