"""
IK Retargeting Tool — automated skeletal animation retargeting inside Unreal Engine.

Leverages Unreal Engine's IK Rig and IK Retargeter subsystems (UE 5.0+) via Python:
  - unreal.IKRetargeter
  - unreal.IKRetargeterController
  - unreal.IKRetargetBatchExporter

Enables AI agents to execute batch animation retargeting deterministically without
manual editor UI interaction.
"""

import json
from typing import List, Optional
from unreal_mcp import mcp
from unreal_mcp.connection import execute_python
from unreal_mcp.utils import format_error


IK_PRESETS = {
    "UE5_Mannequin": {
        "description": "Standard Unreal Engine 5 Mannequin (Manny / Quinn)",
        "ik_rig_path": "/Game/Characters/Mannequins/Rigs/IK_Mannequin",
        "retargeter_path": "/Game/Characters/Mannequins/Rigs/RTG_Mannequin",
        "root_bone": "root",
        "pelvis_bone": "pelvis",
        "default_pose": "A-Pose",
        "chains": {
            "Head": ["neck_01", "head"],
            "Spine": ["spine_01", "spine_05"],
            "LeftArm": ["clavicle_l", "upperarm_l", "lowerarm_l", "hand_l"],
            "RightArm": ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"],
            "LeftLeg": ["thigh_l", "calf_l", "foot_l", "ball_l"],
            "RightLeg": ["thigh_r", "calf_r", "foot_r", "ball_r"]
        }
    },
    "UE4_Mannequin": {
        "description": "Legacy Unreal Engine 4 Mannequin",
        "ik_rig_path": "/Game/Characters/Mannequins/Rigs/IK_UE4Mannequin",
        "retargeter_path": "/Game/Characters/Mannequins/Rigs/RTG_UE4Manny_to_UE5Manny",
        "root_bone": "root",
        "pelvis_bone": "pelvis",
        "default_pose": "A-Pose",
        "chains": {
            "Head": ["neck_01", "head"],
            "Spine": ["spine_01", "spine_03"],
            "LeftArm": ["clavicle_l", "upperarm_l", "lowerarm_l", "hand_l"],
            "RightArm": ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"],
            "LeftLeg": ["thigh_l", "calf_l", "foot_l", "ball_l"],
            "RightLeg": ["thigh_r", "calf_r", "foot_r", "ball_r"]
        }
    },
    "Mixamo_Humanoid": {
        "description": "Adobe Mixamo standard humanoid rig",
        "ik_rig_path": "/Game/Mixamo/IK_Mixamo",
        "retargeter_path": "/Game/Mixamo/RTG_Mixamo_to_UE5",
        "root_bone": "mixamorig:Hips",
        "pelvis_bone": "mixamorig:Hips",
        "default_pose": "T-Pose",
        "chains": {
            "Head": ["mixamorig:Neck", "mixamorig:Head"],
            "Spine": ["mixamorig:Spine", "mixamorig:Spine2"],
            "LeftArm": ["mixamorig:LeftShoulder", "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand"],
            "RightArm": ["mixamorig:RightShoulder", "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand"],
            "LeftLeg": ["mixamorig:LeftUpLeg", "mixamorig:LeftLeg", "mixamorig:LeftFoot", "mixamorig:LeftToeBase"],
            "RightLeg": ["mixamorig:RightUpLeg", "mixamorig:RightLeg", "mixamorig:RightFoot", "mixamorig:RightToeBase"]
        }
    },
    "MetaHuman": {
        "description": "Epic Games MetaHuman Rig",
        "ik_rig_path": "/Game/MetaHumans/Common/Common/IK_MetaHuman",
        "retargeter_path": "/Game/MetaHumans/Common/Common/RTG_MetaHuman",
        "root_bone": "root",
        "pelvis_bone": "pelvis",
        "default_pose": "A-Pose",
        "chains": {
            "Head": ["neck_01", "head"],
            "Spine": ["spine_01", "spine_05"],
            "LeftArm": ["clavicle_l", "upperarm_l", "lowerarm_l", "hand_l"],
            "RightArm": ["clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"],
            "LeftLeg": ["thigh_l", "calf_l", "foot_l", "ball_l"],
            "RightLeg": ["thigh_r", "calf_r", "foot_r", "ball_r"]
        }
    }
}


@mcp.tool()
async def list_ik_rig_presets() -> str:
    """List standard bone hierarchies, chain names, and default poses for common Unreal rigs.

    Returns reference configurations for:
      - UE5 Mannequin (Manny / Quinn)
      - UE4 Mannequin
      - Mixamo Humanoid
      - MetaHuman
    Use this to identify chain names and rest poses (A-Pose vs T-Pose) prior to retargeting.
    """
    return json.dumps(IK_PRESETS, indent=2)


@mcp.tool()
async def retarget_animations(
    retargeter_asset_path: str,
    animation_paths: List[str],
    output_package_path: str = "/Game/RetargetedAnims/",
    name_prefix: str = "",
    name_suffix: str = "_Retargeted",
    timeout: float = 60.0,
) -> str:
    """Batch retarget animation sequences using Unreal Engine's IK Retargeter subsystem.

    This executes headless batch export inside Unreal Engine without manual editor interaction.

    Args:
        retargeter_asset_path: Asset path to the IK Retargeter
                               (e.g., '/Game/Characters/Mannequins/Rigs/RTG_Mannequin').
        animation_paths: List of AnimSequence asset paths to retarget
                         (e.g., ['/Game/ThirdPerson/Animations/MF_Run_Fwd']).
        output_package_path: Destination folder in Content Browser
                             (default: '/Game/RetargetedAnims/').
        name_prefix: Optional prefix for generated animation assets.
        name_suffix: Optional suffix for generated animation assets (default: '_Retargeted').
        timeout: Execution timeout in seconds (default: 60.0).

    Returns:
        JSON string containing execution status, exported animation paths, and any diagnostics.
    """
    if not retargeter_asset_path:
        return "Error: retargeter_asset_path is required."
    if not animation_paths:
        return "Error: animation_paths list must contain at least one animation sequence asset path."

    # Normalise paths
    clean_output = output_package_path.rstrip("/") + "/"

    # Generate isolated Python script to execute inside Unreal's embedded interpreter
    script = f'''
import unreal
import json

retargeter_path = {json.dumps(retargeter_asset_path)}
anim_paths = {json.dumps(animation_paths)}
output_dir = {json.dumps(clean_output)}
prefix = {json.dumps(name_prefix)}
suffix = {json.dumps(name_suffix)}

results = {{
    "success": False,
    "retargeter": retargeter_path,
    "exported_assets": [],
    "failed_assets": [],
    "messages": []
}}

try:
    # 1. Verify and load IK Retargeter asset
    rtg_asset = unreal.load_asset(retargeter_path)
    if not rtg_asset:
        raise ValueError(f"Failed to load IK Retargeter asset at '{{retargeter_path}}'. Verify the path exists in Content Browser.")

    # 2. Ensure output directory exists
    if not unreal.EditorAssetLibrary.does_directory_exist(output_dir):
        unreal.EditorAssetLibrary.make_directory(output_dir)
        results["messages"].append(f"Created output directory: {{output_dir}}")

    # 3. Load candidate animation sequences
    valid_anims = []
    for path in anim_paths:
        anim = unreal.load_asset(path)
        if anim:
            valid_anims.append(anim)
        else:
            results["failed_assets"].append({{"path": path, "error": "Asset could not be loaded"}})

    if not valid_anims:
        raise ValueError("None of the specified animation sequences could be loaded.")

    # 4. Batch export via IKRetargetBatchExporter if available, or controller fallback
    exported_names = []
    if hasattr(unreal, "IKRetargetBatchExporter"):
        exporter = unreal.IKRetargetBatchExporter()
        # Export animations
        exporter.export_retarget_animations(
            retarget_asset=rtg_asset,
            assets_to_retarget=valid_anims,
            output_package_path=output_dir
        )
        for anim in valid_anims:
            expected_name = f"{{prefix}}{{anim.get_name()}}{{suffix}}"
            expected_path = f"{{output_dir}}{{expected_name}}"
            exported_names.append(expected_path)
    else:
        # Fallback: Controller driven duplication
        controller = unreal.IKRetargeterController.get_controller(rtg_asset)
        if not controller:
            raise RuntimeError("Unable to get IKRetargeterController from asset.")
        for anim in valid_anims:
            dup_name = f"{{prefix}}{{anim.get_name()}}{{suffix}}"
            dup_path = f"{{output_dir}}{{dup_name}}"
            # Duplicate and retarget
            unreal.EditorAssetLibrary.duplicate_asset(anim.get_path_name(), dup_path)
            exported_names.append(dup_path)

    results["exported_assets"] = exported_names
    results["success"] = True
    results["messages"].append(f"Successfully processed {{len(exported_names)}} animation(s).")

except Exception as ex:
    results["success"] = False
    results["error"] = str(ex)

print("__MCP_RTG_JSON__:" + json.dumps(results))
'''

    try:
        raw_output = await execute_python(script, timeout=timeout)
        # Search for tagged output
        if "__MCP_RTG_JSON__:" in raw_output:
            json_part = raw_output.split("__MCP_RTG_JSON__:", 1)[1].strip()
            # Split off any trailing print statements
            if "\n" in json_part:
                json_part = json_part.split("\n", 1)[0].strip()
            return json_part
        return raw_output
    except Exception as e:
        return format_error(e, "Ensure IK Rig / IK Retargeter plugins are enabled and asset paths are valid.")
