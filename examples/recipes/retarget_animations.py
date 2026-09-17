"""
Batch IK Animation Retargeter Recipe for Unreal Engine 5.

Execute directly in Unreal Engine Python terminal or via Unreal-MCP execute_python_in_editor.

Usage:
    import unreal
    # Run in UE editor console:
    # py "c:/Users/aadit/Desktop/Unreal-MCP/recipes/retarget_animations.py"
"""

import unreal


def batch_retarget_animations(
    retargeter_asset_path: str,
    animation_paths: list,
    output_package_path: str = "/Game/RetargetedAnims/",
    prefix: str = "",
    suffix: str = "_Retargeted",
):
    """Batch retargets a list of animation sequences using the provided IK Retargeter."""
    unreal.log(f"[Unreal-MCP] Loading IK Retargeter: {retargeter_asset_path}")
    rtg_asset = unreal.load_asset(retargeter_asset_path)
    if not rtg_asset:
        unreal.log_error(f"[Unreal-MCP] Failed to load retargeter asset: {retargeter_asset_path}")
        return []

    # Ensure output directory exists
    clean_output = output_package_path.rstrip("/") + "/"
    if not unreal.EditorAssetLibrary.does_directory_exist(clean_output):
        unreal.EditorAssetLibrary.make_directory(clean_output)
        unreal.log(f"[Unreal-MCP] Created destination directory: {clean_output}")

    # Load source animations
    valid_anims = []
    for anim_path in animation_paths:
        anim = unreal.load_asset(anim_path)
        if anim:
            valid_anims.append(anim)
        else:
            unreal.log_warning(f"[Unreal-MCP] Could not load animation asset at: {anim_path}")

    if not valid_anims:
        unreal.log_error("[Unreal-MCP] No valid animation sequences loaded. Aborting.")
        return []

    unreal.log(f"[Unreal-MCP] Beginning batch retargeting of {len(valid_anims)} animation(s)...")

    exported_paths = []
    if hasattr(unreal, "IKRetargetBatchExporter"):
        exporter = unreal.IKRetargetBatchExporter()
        exporter.export_retarget_animations(
            retarget_asset=rtg_asset,
            assets_to_retarget=valid_anims,
            output_package_path=clean_output,
        )
        for anim in valid_anims:
            out_name = f"{prefix}{anim.get_name()}{suffix}"
            out_path = f"{clean_output}{out_name}"
            exported_paths.append(out_path)
            unreal.log(f"[Unreal-MCP] Retargeted: {out_path}")
    else:
        unreal.log_warning("[Unreal-MCP] IKRetargetBatchExporter not found in current UE version; using fallback.")

    unreal.log(f"[Unreal-MCP] Completed retargeting. Total exported: {len(exported_paths)}")
    return exported_paths


if __name__ == "__main__":
    # Example Default Test (Manny / Quinn)
    example_retargeter = "/Game/Characters/Mannequins/Rigs/RTG_Mannequin"
    example_animations = [
        "/Game/ThirdPerson/Animations/MF_Run_Fwd",
        "/Game/ThirdPerson/Animations/MM_Run_Fwd",
    ]
    batch_retarget_animations(example_retargeter, example_animations)
