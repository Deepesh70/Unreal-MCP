"""
File Writer — Writes generated C++ code to the UE project Source directory.

Handles path resolution, directory creation, and backup of existing files.
"""

from __future__ import annotations
from pathlib import Path

from unreal_mcp.config.settings import UE_PROJECT_PATH, UE_PROJECT_NAME


def _get_source_dir() -> Path:
    """Get the project's Source directory."""
    return Path(UE_PROJECT_PATH) / "Source" / UE_PROJECT_NAME


def write_class_files(
    class_name: str,
    header_code: str,
    source_code: str,
    subdirectory: str = "",
) -> tuple[Path, Path]:
    """
    Write generated .h and .cpp files to the UE project.

    Args:
        class_name:   The class name (without prefix), e.g. "DynamicWeather"
        header_code:  Rendered .h content
        source_code:  Rendered .cpp content
        subdirectory: Optional subfolder inside Source/ProjectName/

    Returns:
        Tuple of (header_path, source_path) that were written.

    Raises:
        FileNotFoundError: If the UE project Source directory doesn't exist.
    """
    source_dir = _get_source_dir()

    if subdirectory:
        target_dir = source_dir / subdirectory
    else:
        target_dir = source_dir

    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    header_path = target_dir / f"{class_name}.h"
    source_path = target_dir / f"{class_name}.cpp"

    # Backup existing files
    for path in [header_path, source_path]:
        if path.exists():
            backup = path.with_suffix(path.suffix + ".bak")
            path.rename(backup)

    # Write new files
    header_path.write_text(header_code, encoding="utf-8")
    source_path.write_text(source_code, encoding="utf-8")

    return header_path, source_path


def list_source_files() -> list[dict]:
    """
    List all .h and .cpp files in the project Source directory.

    Returns a list of dicts with 'name', 'type' (.h/.cpp), and 'path'.
    """
    source_dir = _get_source_dir()

    if not source_dir.exists():
        return []

    files = []
    for ext in ("*.h", "*.cpp"):
        for path in source_dir.rglob(ext):
            files.append({
                "name": path.stem,
                "type": path.suffix,
                "path": str(path),
                "relative": str(path.relative_to(source_dir)),
            })

    return sorted(files, key=lambda f: f["relative"])
