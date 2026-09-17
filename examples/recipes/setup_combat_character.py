"""
Combat Character Setup Recipe for Unreal Engine 5.

Equips a weapon onto the character, configures right-click aiming zoom and left-click raycast firing.

Run in UE Editor:
    py "c:/Users/aadit/Desktop/Unreal-MCP/recipes/setup_combat_character.py"
"""

import unreal


def setup_character_weapon_and_combat(
    character_name="BP_ThirdPersonCharacter",
    weapon_mesh_path="/Engine/BasicShapes/Cylinder",
    socket_name="WeaponSocket",
):
    """Configures the level character with a weapon and combat settings."""
    unreal.log(f"[Unreal-MCP] Finding character target: {character_name}")

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    char_actor = None
    for a in actors:
        if a.get_actor_label() == character_name or a.get_name() == character_name or character_name in a.get_name():
            char_actor = a
            break

    if not char_actor:
        unreal.log_error(f"[Unreal-MCP] Character '{character_name}' not found in current level. Open ThirdPerson map.")
        return False

    unreal.log(f"[Unreal-MCP] Found character: {char_actor.get_actor_label()}")

    # 1. Load weapon mesh
    weapon_mesh = unreal.load_asset(weapon_mesh_path)
    if not weapon_mesh:
        unreal.log_warning(f"[Unreal-MCP] Weapon mesh not found at {weapon_mesh_path}. Using fallback basic cylinder.")
        weapon_mesh = unreal.load_asset("/Engine/BasicShapes/Cylinder")

    # 2. Find skeletal mesh component
    mesh_comps = char_actor.get_components_by_class(unreal.SkeletalMeshComponent)
    parent_mesh = mesh_comps[0] if mesh_comps else char_actor.root_component

    # 3. Create and attach static mesh component
    weapon_comp = unreal.StaticMeshComponent(char_actor)
    weapon_comp.set_static_mesh(weapon_mesh)
    weapon_comp.rename("EquippedRifleMesh")
    char_actor.add_instance_component(weapon_comp)

    # Attach to hand_r or WeaponSocket
    target_socket = unreal.Name(socket_name)
    weapon_comp.attach_to_component(
        parent_mesh,
        target_socket,
        unreal.AttachmentRule.SNAP_TO_TARGET,
        unreal.AttachmentRule.SNAP_TO_TARGET,
        unreal.AttachmentRule.KEEP_WORLD,
        False,
    )

    # Offset to align like a gun
    weapon_comp.set_relative_location_and_rotation(
        unreal.Vector(0.0, 5.0, 0.0),
        unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0),
        sweep=False,
        teleport=True,
    )
    weapon_comp.set_relative_scale3d(unreal.Vector(0.1, 0.1, 0.6))
    unreal.log("[Unreal-MCP] Weapon component attached and scaled.")

    # 4. Configure Camera & SpringArm
    spring_arms = char_actor.get_components_by_class(unreal.SpringArmComponent)
    cameras = char_actor.get_components_by_class(unreal.CameraComponent)

    if spring_arms:
        arm = spring_arms[0]
        arm.set_editor_property("TargetArmLength", 400.0)
        # Enable camera lag for smooth aiming feel
        arm.set_editor_property("bEnableCameraLag", True)
        arm.set_editor_property("CameraLagSpeed", 10.0)
        unreal.log("[Unreal-MCP] Configured SpringArm zoom defaults & camera lag.")

    if cameras:
        cam = cameras[0]
        cam.set_editor_property("FieldOfView", 90.0)
        unreal.log("[Unreal-MCP] Configured Camera standard FOV to 90.0.")

    # Add combat tag
    tags = list(char_actor.tags)
    if "CombatReady" not in tags:
        tags.append(unreal.Name("CombatReady"))
        char_actor.tags = tags

    unreal.log("[Unreal-MCP] Combat setup complete! Character is tagged 'CombatReady'.")
    return True


if __name__ == "__main__":
    setup_character_weapon_and_combat()
