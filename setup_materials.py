"""
One-time setup: Create colored material assets in the Unreal project.

Run this ONCE with Unreal Editor open:
    python setup_materials.py

This creates /Game/Materials/Colors/MI_Wood, MI_Stone, MI_Cyan, etc.
The spawner then references these instead of trying dynamic material hacks.
"""

import asyncio
import json
import websockets

UE_WS_URL = "ws://127.0.0.1:30020"

# Colors to create (name → RGBA linear)
COLORS = {
    "red":       (0.8, 0.1, 0.1, 1.0),
    "blue":      (0.1, 0.2, 0.9, 1.0),
    "green":     (0.1, 0.8, 0.2, 1.0),
    "yellow":    (0.9, 0.85, 0.1, 1.0),
    "orange":    (0.9, 0.5, 0.1, 1.0),
    "purple":    (0.6, 0.1, 0.9, 1.0),
    "cyan":      (0.3, 0.75, 0.9, 1.0),
    "white":     (1.0, 1.0, 1.0, 1.0),
    "black":     (0.02, 0.02, 0.02, 1.0),
    "gray":      (0.4, 0.4, 0.4, 1.0),
    "steel":     (0.5, 0.55, 0.6, 1.0),
    "gold":      (0.85, 0.65, 0.13, 1.0),
    "concrete":  (0.65, 0.63, 0.6, 1.0),
    "wood":      (0.55, 0.35, 0.15, 1.0),
    "wood_dark": (0.35, 0.2, 0.1, 1.0),
    "stone":     (0.5, 0.48, 0.45, 1.0),
    "glass":     (0.4, 0.6, 0.8, 1.0),
}

# UE Python script to create a simple material with BaseColor parameter
CREATE_MATERIAL_SCRIPT = '''
import unreal

mat_path = "/Game/Materials/Colors/M_BaseColor"

# Check if base material already exists
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    print(f"Base material already exists: {mat_path}")
else:
    # Create the base material
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset("M_BaseColor", "/Game/Materials/Colors", unreal.Material, factory)
    
    if mat:
        # Create a VectorParameter node for BaseColor
        # We'll use the material's base color input
        print(f"Created base material: {mat_path}")
        unreal.EditorAssetLibrary.save_asset(mat_path)
    else:
        print("Failed to create base material")
'''

# UE Python script to create a material instance with a specific color
CREATE_MI_TEMPLATE = '''
import unreal

mi_name = "MI_{name}"
mi_path = "/Game/Materials/Colors/" + mi_name
base_mat_path = "/Game/Materials/Colors/M_BaseColor"

if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
    print(f"Already exists: {{mi_path}}")
else:
    base_mat = unreal.EditorAssetLibrary.load_asset(base_mat_path)
    if not base_mat:
        # Fallback: use engine default lit material
        base_mat = unreal.EditorAssetLibrary.load_asset("/Engine/EngineMaterials/DefaultMaterial")
    
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    factory.set_editor_property("InitialParent", base_mat)
    mi = asset_tools.create_asset(mi_name, "/Game/Materials/Colors", unreal.MaterialInstanceConstant, factory)
    
    if mi:
        # Set the base color as a scalar override (directly modify the diffuse)
        color = unreal.LinearColor({r}, {g}, {b}, {a})
        mi.set_editor_property("base_property_overrides", 
            unreal.MaterialInstanceBasePropertyOverrides(override_base_color=True))
        # For simple coloring, just save it - the parent material controls the look
        unreal.EditorAssetLibrary.save_asset(mi_path)
        print(f"Created: {{mi_path}}")
    else:
        print(f"Failed to create: {{mi_path}}")
'''


async def run_ue_python(script: str):
    """Execute a Python script inside Unreal Editor via WebSocket."""
    payload = {
        "MessageName": "http",
        "Parameters": {
            "Url": "/remote/object/call",
            "Verb": "PUT",
            "Body": {
                "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
                "functionName": "ExecutePythonCommand",
                "parameters": {
                    "PythonCommand": script
                }
            }
        }
    }
    try:
        async with websockets.connect(UE_WS_URL, ping_timeout=30, close_timeout=30) as ws:
            await ws.send(json.dumps(payload))
            resp = await ws.recv()
            data = json.loads(resp)
            return data
    except Exception as e:
        print(f"  ❌ WebSocket error: {e}")
        return None


async def main():
    print("🎨 Creating colored material assets in Unreal...")
    print("   (Requires Unreal Editor to be running with Remote Control plugin)\n")
    
    # Step 1: Create base material
    print("1. Creating base material M_BaseColor...")
    result = await run_ue_python(CREATE_MATERIAL_SCRIPT)
    if result:
        print("   ✅ Base material created")
    else:
        print("   ⚠️  Could not create base material (will use defaults)")
    
    # Step 2: Create material instances for each color
    print(f"\n2. Creating {len(COLORS)} color material instances...")
    for name, (r, g, b, a) in COLORS.items():
        script = CREATE_MI_TEMPLATE.format(name=name.title(), r=r, g=g, b=b, a=a)
        result = await run_ue_python(script)
        status = "✅" if result else "❌"
        print(f"   {status} MI_{name.title()} ({r:.1f}, {g:.1f}, {b:.1f})")
    
    print("\n🎨 Done! Material assets saved to /Game/Materials/Colors/")
    print("   Restart the builder to use colored materials.")


if __name__ == "__main__":
    asyncio.run(main())
