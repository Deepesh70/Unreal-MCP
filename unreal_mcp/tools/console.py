"""
Console Command Tool — execute any Unreal Engine console command.

Provides raw access to UE's console for commands like:
  - stat fps, stat unit (performance monitoring)
  - r.SetRes 1920x1080 (resolution changes)
  - HighResShot 2 (screenshot multiplier)
  - t.MaxFPS 60 (frame rate cap)
  - obj list (object debugging)
"""

from unreal_mcp import mcp
from unreal_mcp.connection import send_console_command
from unreal_mcp.utils import format_error


@mcp.tool()
async def run_console_command(command: str) -> str:
    """Execute an Unreal Engine console command.

    Provides raw access to UE's command line for engine configuration,
    debugging, and advanced operations.

    Args:
        command: The console command to execute.
                 Examples: 'stat fps', 'r.SetRes 1920x1080', 'obj list'

    Returns:
        Confirmation that the command was sent. Note: most console commands
        are fire-and-forget and don't return output.
    """
    try:
        await send_console_command(command)
        return f"Console command executed: {command}"
    except Exception as e:
        return format_error(e, "Ensure Unreal Engine is running.")
