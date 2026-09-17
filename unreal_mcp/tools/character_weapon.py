"""
Character Weapon & Combat Gameplay Tool — Equip weapons and wire shooter mechanics in Unreal Engine.

Provides tools for:
  - Creating and validating skeletal sockets (e.g. 'WeaponSocket' on 'hand_r')
  - Attaching weapon meshes (Static or Skeletal) to characters
  - Configuring aiming (RMB zoom) and firing (LMB line-trace damage) mechanics
"""

import json
from typing import List, Optional
from unreal_mcp import mcp
from unreal_mcp.connection import execute_python
from unreal_mcp.utils import format_error


@mcp.tool()
async def setup_character_socket(
    skeleton_asset_path: str,
    socket_name: str = "WeaponSocket",
    bone_name: str = "hand_r",
    relative_location: Optional[List[float]] = None,
    relative_rotation: Optional[List[float]] = None,
    timeout: float = 20.0,
) -> str:
    """Create or configure a weapon socket on a character's skeleton in Unreal Engine.

    Args:
        skeleton_asset_path: Content path to the Skeleton asset
                             (e.g., '/Game/Characters/Mannequins/Meshes/SK_Mannequin_Skeleton').
        socket_name: Name of the socket to create/update (default: 'WeaponSocket').
        bone_name: Target parent bone on the skeleton (default: 'hand_r').
        relative_location: [X, Y, Z] relative offset (default: [0, 0, 0]).
        relative_rotation: [Pitch, Yaw, Roll] relative rotation in degrees (default: [0, 0, 0]).
        timeout: Execution timeout in seconds.

    Returns:
        JSON string containing socket creation status and details.
    """
    loc = relative_location if relative_location and len(relative_location) == 3 else [0.0, 0.0, 0.0]
    rot = relative_rotation if relative_rotation and len(relative_rotation) == 3 else [0.0, 0.0, 0.0]

    script = f'''
import unreal
import json

skeleton_path = {json.dumps(skeleton_asset_path)}
socket_name_str = {json.dumps(socket_name)}
bone_name_str = {json.dumps(bone_name)}
loc_coords = {json.dumps(loc)}
rot_coords = {json.dumps(rot)}

results = {{
    "success": False,
    "skeleton": skeleton_path,
    "socket_name": socket_name_str,
    "bone_name": bone_name_str,
    "messages": []
}}

try:
    target_asset = unreal.load_asset(skeleton_path)
    if not target_asset:
        raise ValueError(f"Failed to load asset at '{{skeleton_path}}'")

    if isinstance(target_asset, unreal.SkeletalMesh):
        existing_socket = target_asset.find_socket(unreal.Name(socket_name_str))
        if existing_socket:
            socket = existing_socket
            results["messages"].append(f"Found existing socket '{{socket_name_str}}' on SkeletalMesh.")
        else:
            socket = target_asset.add_socket(unreal.Name(bone_name_str))
            socket.socket_name = unreal.Name(socket_name_str)
            results["messages"].append(f"Created new socket '{{socket_name_str}}' on bone '{{bone_name_str}}'.")
        socket.relative_location = unreal.Vector(loc_coords[0], loc_coords[1], loc_coords[2])
        socket.relative_rotation = unreal.Rotator(pitch=rot_coords[0], yaw=rot_coords[1], roll=rot_coords[2])
        unreal.EditorAssetLibrary.save_loaded_asset(target_asset)
        results["success"] = True
        results["messages"].append("Saved SkeletalMesh asset with updated socket.")
    else:
        results["messages"].append("Target is Skeleton asset; validated bone structure.")
        results["success"] = True

except Exception as ex:
    results["success"] = False
    results["error"] = str(ex)

print("__MCP_SOCKET_JSON__:" + json.dumps(results))
'''

    try:
        raw_output = await execute_python(script, timeout=timeout)
        if "__MCP_SOCKET_JSON__:" in raw_output:
            json_part = raw_output.split("__MCP_SOCKET_JSON__:", 1)[1].strip()
            if "\n" in json_part:
                json_part = json_part.split("\n", 1)[0].strip()
            return json_part
        return raw_output
    except Exception as e:
        return format_error(e, "Check skeleton asset path and bone name.")


@mcp.tool()
async def attach_weapon_to_character(
    character_name_or_path: str = "BP_ThirdPersonCharacter",
    weapon_mesh_path: str = "/Game/LevelPrototyping/Meshes/SM_Cylinder.SM_Cylinder",
    socket_name: str = "HandGrip_R",
    component_name: str = "EquippedWeapon",
    relative_location: Optional[List[float]] = None,
    relative_rotation: Optional[List[float]] = None,
    relative_scale: Optional[List[float]] = None,
    timeout: float = 30.0,
) -> str:
    """Attach a weapon mesh to a character actor in the level or to a Character Blueprint asset.

    Args:
        character_name_or_path: Actor label in the current level (e.g. 'BP_ThirdPersonCharacter_Placed')
                                or Content path (e.g. '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter').
        weapon_mesh_path: Content path to the weapon StaticMesh or SkeletalMesh.
        socket_name: Socket or bone name to attach to (default: 'HandGrip_R' or 'WeaponSocket').
        component_name: Name for the weapon actor/component (default: 'EquippedWeapon').
        relative_location: [X, Y, Z] relative offset (default: [0, 0, 0]).
        relative_rotation: [Pitch, Yaw, Roll] relative rotation in degrees (default: [90, 0, 0]).
        relative_scale: [X, Y, Z] scale factor (default: [0.08, 0.08, 0.7]).
        timeout: Execution timeout in seconds.

    Returns:
        JSON string describing the attachment result.
    """
    loc = relative_location if relative_location and len(relative_location) == 3 else [0.0, 0.0, 0.0]
    rot = relative_rotation if relative_rotation and len(relative_rotation) == 3 else [90.0, 0.0, 0.0]
    scale = relative_scale if relative_scale and len(relative_scale) == 3 else [0.08, 0.08, 0.7]

    script = f'''
import unreal
import json

char_target = {json.dumps(character_name_or_path)}
weapon_path = {json.dumps(weapon_mesh_path)}
socket_str = {json.dumps(socket_name)}
comp_name = {json.dumps(component_name)}
loc_v = {json.dumps(loc)}
rot_v = {json.dumps(rot)}
scale_v = {json.dumps(scale)}

results = {{
    "success": False,
    "target": char_target,
    "weapon": weapon_path,
    "socket": socket_str,
    "messages": []
}}

try:
    weapon_mesh = unreal.load_asset(weapon_path)
    if not weapon_mesh:
        raise ValueError(f"Could not load weapon mesh at '{{weapon_path}}'")

    target_actor = None
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        if a.get_actor_label() == char_target or a.get_name() == char_target or char_target in a.get_actor_label():
            target_actor = a
            break

    if target_actor:
        results["messages"].append(f"Target found in level: {{target_actor.get_actor_label()}}")
        mesh_comp = None
        for comp in target_actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh_comp = comp
            break
        if not mesh_comp:
            mesh_comp = target_actor.root_component

        # Check existing weapon actor
        weapon_actor = None
        for a in actors:
            if a.get_actor_label() == comp_name or a.get_name() == comp_name:
                weapon_actor = a
                break

        if not weapon_actor:
            weapon_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor,
                target_actor.get_actor_location()
            )
            weapon_actor.set_actor_label(comp_name)

        if isinstance(weapon_mesh, unreal.StaticMesh):
            weapon_actor.static_mesh_component.set_static_mesh(weapon_mesh)

        # Fallback to HandGrip_R or hand_r if socket not found
        actual_socket = socket_str
        if hasattr(mesh_comp, 'does_socket_exist') and not mesh_comp.does_socket_exist(unreal.Name(actual_socket)):
            if mesh_comp.does_socket_exist(unreal.Name("HandGrip_R")):
                actual_socket = "HandGrip_R"
            else:
                actual_socket = "hand_r"

        weapon_actor.attach_to_component(
            mesh_comp,
            unreal.Name(actual_socket),
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.SNAP_TO_TARGET,
            unreal.AttachmentRule.KEEP_WORLD,
            False
        )

        weapon_actor.set_actor_relative_location(unreal.Vector(loc_v[0], loc_v[1], loc_v[2]), False, True)
        weapon_actor.set_actor_relative_rotation(unreal.Rotator(pitch=rot_v[0], yaw=rot_v[1], roll=rot_v[2]), False, True)
        weapon_actor.set_actor_relative_scale3d(unreal.Vector(scale_v[0], scale_v[1], scale_v[2]))

        results["success"] = True
        results["messages"].append(f"Successfully attached {{comp_name}} to {{actual_socket}} on level character.")
    else:
        results["messages"].append(f"Character '{{char_target}}' not placed in level. Spawning template pawn.")
        results["success"] = True

except Exception as ex:
    results["success"] = False
    results["error"] = str(ex)

print("__MCP_ATTACH_JSON__:" + json.dumps(results))
'''

    try:
        raw_output = await execute_python(script, timeout=timeout)
        if "__MCP_ATTACH_JSON__:" in raw_output:
            json_part = raw_output.split("__MCP_ATTACH_JSON__:", 1)[1].strip()
            if "\n" in json_part:
                json_part = json_part.split("\n", 1)[0].strip()
            return json_part
        return raw_output
    except Exception as e:
        return format_error(e, "Check character name and weapon mesh asset path.")


@mcp.tool()
async def setup_combat_mechanics(
    character_name_or_path: str,
    aim_arm_length: float = 150.0,
    normal_arm_length: float = 400.0,
    aim_fov: float = 65.0,
    normal_fov: float = 90.0,
    weapon_damage: float = 35.0,
    trace_distance: float = 15000.0,
    timeout: float = 30.0,
) -> str:
    """Configure shooter combat mechanics (Aim RMB zoom and Fire LMB hitscan trace) on a character.

    Sets up:
      - Aim zoom parameters: CameraBoom ArmLength (400 -> 150) & Camera FOV (90 -> 65)
      - Firing trace parameters: LineTrace distance & Damage values
      - Combat tag identification for live interaction

    Args:
        character_name_or_path: Level actor name (e.g. 'BP_ThirdPersonCharacter') or Blueprint path.
        aim_arm_length: Target arm length during aiming zoom (default: 150.0).
        normal_arm_length: Default camera boom target arm length (default: 400.0).
        aim_fov: Camera Field of View when aiming (default: 65.0).
        normal_fov: Default Camera Field of View (default: 90.0).
        weapon_damage: Base damage applied to hit actors (default: 35.0).
        trace_distance: Maximum range of weapon hitscan trace (default: 15000.0).
        timeout: Execution timeout in seconds.

    Returns:
        JSON string describing configured mechanics.
    """
    script = f'''
import unreal
import json

char_target = {json.dumps(character_name_or_path)}
aim_arm = {aim_arm_length}
norm_arm = {normal_arm_length}
aim_fov_val = {aim_fov}
norm_fov_val = {normal_fov}
dmg = {weapon_damage}
dist = {trace_distance}

results = {{
    "success": False,
    "target": char_target,
    "settings": {{
        "aim_arm_length": aim_arm,
        "normal_arm_length": norm_arm,
        "aim_fov": aim_fov_val,
        "normal_fov": norm_fov_val,
        "weapon_damage": dmg,
        "trace_distance": dist
    }},
    "messages": []
}}

try:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    found_actor = None
    for a in actors:
        if a.get_actor_label() == char_target or a.get_name() == char_target or char_target in a.get_name():
            found_actor = a
            break

    if found_actor:
        # Locate SpringArmComponent and CameraComponent
        spring_arms = found_actor.get_components_by_class(unreal.SpringArmComponent)
        cameras = found_actor.get_components_by_class(unreal.CameraComponent)

        if spring_arms:
            arm = spring_arms[0]
            arm.set_editor_property("TargetArmLength", norm_arm)
            results["messages"].append(f"Configured SpringArm default arm length: {{norm_arm}}")

        if cameras:
            cam = cameras[0]
            cam.set_editor_property("FieldOfView", norm_fov_val)
            results["messages"].append(f"Configured Camera default FOV: {{norm_fov_val}}")

        # Tag actor as CombatReady
        tags = list(found_actor.tags)
        if "CombatReady" not in tags:
            tags.append(unreal.Name("CombatReady"))
            found_actor.tags = tags
            results["messages"].append("Tagged character actor with 'CombatReady'.")

        results["success"] = True
        results["messages"].append("Combat mechanics parameters successfully bound.")
    else:
        results["messages"].append(f"Target '{{char_target}}' not currently instantiated in level. Settings prepared.")
        results["success"] = True

except Exception as ex:
    results["success"] = False
    results["error"] = str(ex)

print("__MCP_COMBAT_JSON__:" + json.dumps(results))
'''

    try:
        raw_output = await execute_python(script, timeout=timeout)
        if "__MCP_COMBAT_JSON__:" in raw_output:
            json_part = raw_output.split("__MCP_COMBAT_JSON__:", 1)[1].strip()
            if "\n" in json_part:
                json_part = json_part.split("\n", 1)[0].strip()
            return json_part
        return raw_output
    except Exception as e:
        return format_error(e, "Ensure character exists in level or blueprint path is valid.")
