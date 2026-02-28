"""
Project Info Tools — inspect the UE project structure.
"""

from unreal_mcp import mcp
from unreal_mcp.config.settings import UE_PROJECT_PATH, UE_PROJECT_NAME
from unreal_mcp.codegen.file_writer import list_source_files
from unreal_mcp.codegen.type_mapper import TYPE_MAP
from unreal_mcp.utils import format_error


@mcp.tool()
async def get_project_info() -> str:
    """Get the configured Unreal project name and path."""
    return (
        f"Project: {UE_PROJECT_NAME}\n"
        f"Path: {UE_PROJECT_PATH}\n"
        f"Source: {UE_PROJECT_PATH}/Source/{UE_PROJECT_NAME}"
    )


@mcp.tool()
async def list_project_files() -> str:
    """List all .h and .cpp files in the UE project Source directory."""
    try:
        files = list_source_files()
        if not files:
            return "No source files found (check UE_PROJECT_PATH in settings)."

        lines = [f"  {f['relative']} ({f['type']})" for f in files]
        return f"Source files ({len(files)}):\n" + "\n".join(lines)
    except Exception as e:
        return format_error(e, "Check UE_PROJECT_PATH in config/settings.py")


@mcp.tool()
async def list_supported_types() -> str:
    """List all supported variable types for code generation."""
    lines = []
    for friendly, ue in sorted(TYPE_MAP.items()):
        inc = f" (needs: {ue.include})" if ue.include else ""
        lines.append(f"  {friendly:15s} → {ue.cpp_type}{inc}")
    return "Supported types:\n" + "\n".join(lines)
