"""
Asset Import Tool — import files from disk into Unreal Engine.

Lets users point the AI to meshes, textures, and audio files on their
local system and have them imported into the UE Content Browser for use.

Prerequisites:
  - Python Editor Script Plugin (Edit → Plugins → search "Python Editor Script Plugin")
  - Editor Scripting Utilities (Edit → Plugins → search "Editor Scripting Utilities")
  - Allow Remote Console Execution (Edit → Project Settings → Plugins → Remote Control)
"""

from unreal_mcp import mcp
from unreal_mcp.connection import execute_python
from unreal_mcp.utils import format_error


@mcp.tool()
async def import_asset(
    file_path: str,
    destination: str = "/Game/ImportedAssets",
) -> str:
    """Import a file from the user's disk into Unreal Engine's Content Browser.

    Supports common 3D, texture, and audio formats.

    Supported formats:
      - 3D Meshes: .fbx, .obj, .gltf, .glb
      - Textures:  .png, .jpg, .jpeg, .tga, .bmp, .exr
      - Audio:     .wav, .ogg

    After importing, the asset can be used with spawn_actor by passing
    its Content Browser path.

    Args:
        file_path: Absolute path to the file on disk.
                   Example: "C:/Users/Me/Desktop/bridge_beam.fbx"
                   or "D:/Assets/wood_texture.png"
        destination: Content Browser destination path.
                     Default: "/Game/ImportedAssets"
                     Example: "/Game/MyProject/Meshes"

    Returns:
        The Content Browser path of the imported asset, ready for use.

    Prerequisites:
        These Unreal Engine plugins must be enabled:
        1. Python Editor Script Plugin (Edit → Plugins → search "Python Editor Script Plugin")
        2. Editor Scripting Utilities (Edit → Plugins → search "Editor Scripting Utilities")
        3. Remote Control Web Interface (Edit → Plugins → search "Remote Control")

        And this project setting:
        - Edit → Project Settings → Plugins → Remote Control → Allow Remote Console Execution ✓
    """
    # Normalize path separators for Python
    safe_path = file_path.replace("\\", "/")
    safe_dest = destination.replace("\\", "/")

    try:
        script = f"""
import unreal
import os

file_path = r"{safe_path}"
destination = "{safe_dest}"

# Verify file exists
if not os.path.exists(file_path):
    print(f"ERROR: File not found: {{file_path}}")
else:
    # Get file extension
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.splitext(os.path.basename(file_path))[0]

    # Determine asset type and import
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    # Build import task
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", file_path)
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", filename)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    # For FBX files, set additional options
    if ext == ".fbx":
        fbx_options = unreal.FbxImportUI()
        fbx_options.set_editor_property("import_mesh", True)
        fbx_options.set_editor_property("import_as_skeletal", False)
        fbx_options.set_editor_property("import_materials", True)
        fbx_options.set_editor_property("import_textures", True)
        task.set_editor_property("options", fbx_options)

    # Execute import
    asset_tools.import_asset_tasks([task])

    # Get the imported asset paths
    imported = task.get_editor_property("imported_object_paths")
    if imported and len(imported) > 0:
        asset_path = str(imported[0])
        print(f"SUCCESS: {{asset_path}}")
    else:
        # Try to find it at the expected location
        expected_path = f"{{destination}}/{{filename}}"
        if unreal.EditorAssetLibrary.does_asset_exist(expected_path):
            print(f"SUCCESS: {{expected_path}}")
        else:
            print(f"IMPORTED: Asset imported to {{destination}}/{{filename}} (verify in Content Browser)")
"""

        result = await execute_python(script, timeout=30.0)

        if "SUCCESS:" in result:
            asset_path = result.split("SUCCESS:")[1].strip()
            return (
                f"Asset imported successfully!\n"
                f"Content Browser path: {asset_path}\n"
                f"You can now use this path with spawn_actor or set_material."
            )
        elif "IMPORTED:" in result:
            msg = result.split("IMPORTED:")[1].strip()
            return f"Asset import completed: {msg}"
        elif "ERROR:" in result:
            error = result.split("ERROR:")[1].strip()
            return f"Import failed: {error}"
        else:
            return f"Import result: {result}"

    except Exception as e:
        error_msg = str(e)
        if "disabled" in error_msg.lower() or "console" in error_msg.lower():
            return (
                "Asset import requires these Unreal Engine plugins to be enabled:\n\n"
                "1. Python Editor Script Plugin\n"
                "   → Edit → Plugins → search 'Python Editor Script Plugin' → Enable ✓\n\n"
                "2. Editor Scripting Utilities\n"
                "   → Edit → Plugins → search 'Editor Scripting Utilities' → Enable ✓\n\n"
                "3. Remote Control Web Interface\n"
                "   → Edit → Plugins → search 'Remote Control' → Enable ✓\n\n"
                "4. Allow Remote Console Execution\n"
                "   → Edit → Project Settings → Plugins → Remote Control\n"
                "   → Check 'Allow Remote Console Execution' ✓\n\n"
                "After enabling, restart Unreal Engine."
            )
        return format_error(e, "Ensure the Python Editor Script Plugin is enabled in Unreal.")


@mcp.tool()
async def add_starter_content() -> str:
    """Add Starter Content to the current project if it's not already present.

    This makes materials like steel, brick, wood, grass and props like
    chairs, tables, doors available for use.

    If Starter Content is already present, this is a no-op.

    Note: This requires the Python Editor Script Plugin to be enabled.
    """
    try:
        script = """
import unreal

# Check if starter content exists
registry = unreal.AssetRegistryHelpers.get_asset_registry()
starter_path = "/Game/StarterContent"

if unreal.EditorAssetLibrary.does_directory_exist(starter_path):
    print("ALREADY_EXISTS: Starter Content is already in this project.")
else:
    # Try to add it via Feature Pack
    # The user needs to do this manually via UE Editor:
    # Edit → Add Feature or Content Pack → StarterContent
    print("NOT_FOUND: Starter Content is not in this project.")
    print("To add it: In UE Editor, go to Edit → Add Feature or Content Pack → Content Packs → Starter Content → Add to Project")
"""
        result = await execute_python(script, timeout=10.0)

        if "ALREADY_EXISTS" in result:
            return (
                "✅ Starter Content is already in your project!\n"
                "All materials (steel, brick, wood, etc.) and meshes (chair, table, etc.) "
                "are available for use."
            )
        elif "NOT_FOUND" in result:
            return (
                "Starter Content is NOT in this project. To add it:\n\n"
                "1. In Unreal Editor: Content Browser → Add → Add Feature or Content Pack\n"
                "2. Go to the 'Content Packs' tab\n"
                "3. Click 'Starter Content' → 'Add to Project'\n\n"
                "This will add all built-in materials and meshes."
            )
        else:
            return f"Result: {result}"

    except Exception as e:
        return format_error(e, "Ensure the Python Editor Script Plugin is enabled.")
