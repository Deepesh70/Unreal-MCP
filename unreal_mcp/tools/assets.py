"""
Asset Discovery Tool — search for assets in the Unreal project.

The AI uses this to discover what meshes, materials, VFX systems,
animations, and other assets exist in the project before trying to
use them. No hardcoded asset paths needed.
"""

from unreal_mcp import mcp
from unreal_mcp.connection import execute_python
from unreal_mcp.utils import format_error


@mcp.tool()
async def find_assets(
    search_path: str = "/Game",
    asset_type: str = "",
    name_filter: str = "",
    max_results: int = 50,
) -> str:
    """Search for assets in the Unreal project's Content directory.

    Use this to discover available meshes, materials, VFX systems,
    animation sequences, blueprints, etc. before spawning or referencing them.

    Args:
        search_path: Content path to search in (default: "/Game" = entire project).
        asset_type: Filter by asset type. Examples:
                    "StaticMesh", "SkeletalMesh", "Material",
                    "NiagaraSystem", "AnimSequence", "Blueprint",
                    "LevelSequence", "SoundCue"
                    Leave empty for all types.
        name_filter: Filter by name substring (case-insensitive).
        max_results: Maximum number of results to return (default: 50).

    Returns:
        JSON list of matching asset paths that can be used for spawning.
    """
    try:
        # Build the search script
        script = f"""
import unreal
import json

search_path = "{search_path}"
asset_type_filter = "{asset_type}"
name_filter = "{name_filter}".lower()
max_results = {max_results}

# Get asset registry
registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Search for assets
assets = unreal.EditorAssetLibrary.list_assets(search_path, recursive=True)

results = []
for asset_path in assets:
    if len(results) >= max_results:
        break

    # Apply name filter
    if name_filter and name_filter not in str(asset_path).lower():
        continue

    # Apply type filter if specified
    if asset_type_filter:
        asset_data = registry.get_asset_by_object_path(asset_path)
        if asset_data:
            asset_class = str(asset_data.asset_class_path.asset_name)
            if asset_type_filter.lower() not in asset_class.lower():
                continue

    results.append(str(asset_path))

print(json.dumps(results, indent=2))
"""

        result = await execute_python(script, timeout=15.0)

        if result.startswith("SUCCESS"):
            # Extract the JSON output after "SUCCESS\n"
            output = result.split("\n", 1)[1] if "\n" in result else "[]"
            return f"Found assets:\n{output}"
        else:
            return f"Asset search encountered an issue:\n{result}"

    except Exception as e:
        return format_error(e, "Ensure the Python Editor Script Plugin is enabled.")
