"""
Python Scripting Tool — the superpower that gives the AI infinite capability.

Instead of building 50 narrow tools for every UE feature, this single tool
lets the AI write and execute arbitrary Python scripts inside Unreal Engine's
embedded interpreter. The AI has full access to `import unreal` and every
UE Python API.

Examples of what the AI can do with this:
  - Create Level Sequences with keyframes for cinematics
  - Set up camera rigs on splines
  - Fracture meshes into GeometryCollections
  - Spawn and configure Niagara VFX systems
  - Sculpt landscape terrain
  - Create and apply dynamic materials
  - Animate characters via Animation Blueprints/Montages
  - Query detailed actor/component properties
  - Anything the unreal Python API supports

Prerequisites:
  - Python Editor Script Plugin must be enabled in the UE project
    (Edit → Plugins → search "Python")
"""

from unreal_mcp import mcp
from unreal_mcp.connection import execute_python
from unreal_mcp.utils import format_error


@mcp.tool()
async def execute_python_in_editor(
    script: str,
    timeout: float = 10.0,
) -> str:
    """Execute a Python script inside Unreal Engine's embedded Python interpreter.

    The script has full access to `import unreal` and all UE Python APIs.
    Use this for complex operations that the basic tools don't cover:
    creating Level Sequences, setting up cameras, fracturing meshes,
    spawning VFX, sculpting terrain, creating materials, etc.

    The script's stdout is captured and returned. Use print() for output.
    Errors are caught and returned with full tracebacks.

    Args:
        script: Python source code to execute. Must be valid Python.
                The `unreal` module is available for import.
        timeout: Max seconds to wait for completion (default: 10).

    Returns:
        "SUCCESS" followed by any stdout output, or "ERROR" with traceback.

    Example scripts:
        # Spawn a CineCameraActor and set focal length
        import unreal
        camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor, unreal.Vector(0, -1000, 200))
        camera.camera_component.set_editor_property('CurrentFocalLength', 35.0)
        print(f"Camera spawned: {camera.get_name()}")

        # List all static meshes in the scene
        import unreal
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for a in actors:
            if isinstance(a, unreal.StaticMeshActor):
                print(f"{a.get_name()} at {a.get_actor_location()}")
    """
    if not script or not script.strip():
        return "Error: Empty script. Provide Python code to execute."

    try:
        result = await execute_python(script, timeout=timeout)
        return result
    except Exception as e:
        return format_error(e, "Ensure the Python Editor Script Plugin is enabled in Unreal.")
