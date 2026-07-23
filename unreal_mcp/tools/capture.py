"""
Viewport Capture Tool — takes screenshots for AI visual feedback.

This closes the feedback loop: the AI acts, captures a screenshot, analyzes
it (via a vision-capable model), and adjusts. Without this, the AI is blind.
"""

import os
import tempfile

from unreal_mcp import mcp
from unreal_mcp.connection import send_console_command, execute_python
from unreal_mcp.utils import format_error


@mcp.tool()
async def capture_viewport(
    filename: str = "ue_mcp_capture.png",
    resolution_x: int = 1920,
    resolution_y: int = 1080,
) -> str:
    """Capture the current Unreal Editor viewport as a screenshot.

    The screenshot is saved to disk. The file path is returned so the AI
    model in the IDE can analyze it (if the model supports vision/images).

    Use this after making changes to verify the scene looks correct.

    Args:
        filename: Name for the screenshot file (saved to temp directory).
        resolution_x: Width in pixels.
        resolution_y: Height in pixels.

    Returns:
        The absolute file path to the saved screenshot.
    """
    try:
        # Determine output path
        output_dir = os.path.join(tempfile.gettempdir(), "ue_mcp_captures")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename).replace("\\", "/")

        # Use a Python script inside UE to capture via automation library
        # This is more reliable than the HighResShot console command
        capture_script = f"""
import unreal
import os

output_path = r"{output_path}"
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

# Use HighResScreenshot console command
# This captures the active viewport
unreal.AutomationLibrary.take_high_res_screenshot(
    {resolution_x}, {resolution_y}, output_path
)
print(f"Screenshot saved to: {{output_path}}")
"""

        result = await execute_python(capture_script, timeout=15.0)

        if "SUCCESS" in result:
            # Verify file exists
            if os.path.exists(output_path):
                size_kb = os.path.getsize(output_path) / 1024
                return (
                    f"Screenshot captured successfully.\n"
                    f"Path: {output_path}\n"
                    f"Size: {size_kb:.1f} KB\n"
                    f"Resolution: {resolution_x}x{resolution_y}\n"
                    f"The AI model can analyze this image to verify the scene."
                )
            else:
                # Fallback: try console command approach
                await send_console_command(
                    f"HighResShot {resolution_x}x{resolution_y}"
                )
                return (
                    f"Screenshot triggered via HighResShot command.\n"
                    f"Check Unreal's Saved/Screenshots folder for the output.\n"
                    f"Note: AutomationLibrary capture did not produce a file at {output_path}."
                )
        else:
            # Fallback to console command
            await send_console_command(
                f"HighResShot {resolution_x}x{resolution_y}"
            )
            return (
                f"Python capture had an issue: {result}\n"
                f"Fallback: HighResShot console command triggered.\n"
                f"Check Unreal's Saved/Screenshots folder."
            )

    except Exception as e:
        return format_error(e, "Ensure Unreal Engine is running with an active viewport.")
