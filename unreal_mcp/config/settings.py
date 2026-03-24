"""
Settings & Constants for the Unreal MCP Server.
Modernized for CI/CD Headless Compilation.
"""
import os

# ── WebSocket Connection ──────────────────────────────────────────────
# The WebSocket URL that Unreal Engine's Remote Control plugin exposes.
UE_WS_URL = "ws://127.0.0.1:30020"

# ── MCP Server Transport ─────────────────────────────────────────────
SERVER_TRANSPORT = "sse"
SERVER_HOST = "localhost"
SERVER_PORT = 8000

# ── Unreal Project Configuration ──────────────────────────────────────
# PROJECT_NAME must match the folder name in your 'Source' directory.
UE_PROJECT_NAME = "Automator"

# The root directory of your Unreal Project.
# Based on your previous logs, this is your current path:
UE_PROJECT_ROOT = r"C:\Users\Deepesh\Desktop\Abhishekyadav0210-project\Automator"

# Path to the actual .uproject file (Needed for UBT)
UE_PROJECT_FILE_PATH = os.path.join(UE_PROJECT_ROOT, f"{UE_PROJECT_NAME}.uproject")

# ── Unreal Build Tool (UBT) Paths ─────────────────────────────────────
# This is the 'BatchFiles' directory inside your Unreal Engine installation.
# Adjust the drive letter 'E:' if your UE5.6 is installed elsewhere!
UE_ENGINE_PATH = r"E:\Unreal Engine\UE_5.6"
UE_BATCH_FILES_PATH = os.path.join(UE_ENGINE_PATH, r"Engine\Build\BatchFiles\Build.bat")

# ── Codegen Settings ──────────────────────────────────────────────────
# Max retries for the self-healing compiler loop
MAX_COMPILE_RETRIES = 3