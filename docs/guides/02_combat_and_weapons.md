# Unreal-MCP: Animation Retargeting & Weapon Combat System Manual

This manual provides complete documentation for the **Deterministic Skeletal Animation Retargeting** and **Weapon Attachment & Combat Gameplay Mechanics** introduced into Unreal-MCP.

---

## 1. System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │            AI Agent / LLM Client             │
                    └──────────────────────┬───────────────────────┘
                                           │ FastMCP Protocol
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │               Unreal-MCP Server              │
                    │  (retargeting.py, character_weapon.py, etc.) │
                    └──────────────────────┬───────────────────────┘
                                           │ Web Remote Control (ws://127.0.0.1:30020)
                                           ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                            Unreal Engine 5 Editor                               │
 │                                                                                 │
 │   ┌───────────────────────────┐         ┌───────────────────────────────────┐   │
 │   │   IK Retargeter Subsystem │         │ Character Combat & Sockets        │   │
 │   │   - IKRetargetBatchExporter│         │ - WeaponSocket on hand_r          │   │
 │   │   - IKRetargeterController │         │ - Static / Skeletal Mesh Attached │   │
 │   │   - Rest-Pose Normalization│         │ - RMB Aim: SpringArm & FOV Zoom   │   │
 │   │   - Batch Export to /Game │         │ - LMB Fire: LineTrace & Damage    │   │
 │   └───────────────────────────┘         └───────────────────────────────────┘   │
 └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Animation & Skeletal IK Retargeting

### The Challenge: Rest-Pose Alignment
Standard automated retargeting often suffers from twisted limbs when:
- **Source Mesh** is in **A-Pose** (e.g. UE5 Mannequin Manny/Quinn with arms angled downward at 45°)
- **Target Mesh** is in **T-Pose** (e.g. Adobe Mixamo models with arms horizontal at 90°)

### Built-in Presets (`list_ik_rig_presets`)
Call `list_ik_rig_presets` to inspect standard bone hierarchies:
- **UE5 Mannequin:** `IK_Mannequin`, root: `root`, arms: `clavicle_l/r` -> `upperarm_l/r` -> `lowerarm_l/r` -> `hand_l/r` (A-Pose)
- **UE4 Mannequin:** `IK_UE4Mannequin`, root: `root` (A-Pose)
- **Mixamo Humanoid:** `IK_Mixamo`, root: `mixamorig:Hips` (T-Pose)
- **MetaHuman:** `IK_MetaHuman` (A-Pose)

### Executing Batch Retargeting via MCP Tool
```json
{
  "retargeter_asset_path": "/Game/Characters/Mannequins/Rigs/RTG_Mannequin",
  "animation_paths": [
    "/Game/ThirdPerson/Animations/MF_Run_Fwd",
    "/Game/ThirdPerson/Animations/MM_Run_Fwd"
  ],
  "output_package_path": "/Game/RetargetedAnims/",
  "name_prefix": "RTG_",
  "name_suffix": ""
}
```

### Standalone Recipe Execution inside Unreal Editor
Open the Unreal Editor Output Log (Python mode) or console:
```text
py "c:/Users/aadit/Desktop/Unreal-MCP/recipes/retarget_animations.py"
```

---

## 3. Weapon Attachment & Socket Management

### 1. Creating the Weapon Socket
Weapons attach to sockets parented to the character's right hand bone (`hand_r` on standard UE mannequins):
```python
# MCP Tool: setup_character_socket
{
  "skeleton_asset_path": "/Game/Characters/Mannequins/Meshes/SK_Mannequin_Skeleton",
  "socket_name": "WeaponSocket",
  "bone_name": "hand_r",
  "relative_location": [0.0, 5.0, 0.0],
  "relative_rotation": [0.0, 90.0, 0.0]
}
```

### 2. Attaching the Weapon Mesh
Equips either a Static Mesh or Skeletal Mesh weapon to an instantiated level actor or Blueprint:
```python
# MCP Tool: attach_weapon_to_character
{
  "character_name_or_path": "BP_ThirdPersonCharacter",
  "weapon_mesh_path": "/Engine/BasicShapes/Cylinder",
  "socket_name": "WeaponSocket",
  "component_name": "EquippedRifle",
  "relative_scale": [0.1, 0.1, 0.6]
}
```

---

## 4. Combat Mechanics: Aiming (RMB) and Firing (LMB)

### 1. Aiming Zoom (Right Mouse Button)
- **Idle State:** Camera Boom `TargetArmLength` = `400.0`, Camera `FieldOfView` = `90.0`
- **Aiming State:** Camera Boom `TargetArmLength` = `150.0`, Camera `FieldOfView` = `65.0`
- **Camera Lag:** Enabled with `CameraLagSpeed = 10.0` for cinematic zoom interpolation.

### 2. Raycast Firing (Left Mouse Button)
- Fires a `LineTraceByChannel` along the forward vector of the camera / weapon muzzle.
- Applies `WeaponDamage` (default: `35.0`) to hit targets.
- Spawns muzzle particles, impact decals, and plays weapon audio.

### Quick Setup Recipe
Run in the Unreal Editor console:
```text
py "c:/Users/aadit/Desktop/Unreal-MCP/recipes/setup_combat_character.py"
```

---

## 5. Live Project Verification Checklist (When Unreal Engine is Running)

1. **Launch Unreal Engine 5** and open your project (e.g., Third Person Template).
2. **Verify Plugins:**
   - Go to **Edit -> Plugins**.
   - Ensure **Remote Control API**, **Web Remote Control**, and **Python Editor Script Plugin** are enabled.
3. **Verify Port:**
   - In Unreal Editor console, check that WebSocket server is listening on port `30020`.
4. **Test via MCP:**
   - Run `check_connection` -> returns `"Connected"`.
   - Run `list_ik_rig_presets` -> returns preset schemas.
   - Run `attach_weapon_to_character` -> equips the weapon to `BP_ThirdPersonCharacter`.
   - Run `setup_combat_mechanics` -> sets camera zoom and combat parameters.
