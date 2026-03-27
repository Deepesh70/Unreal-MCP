"""
Settings & Constants for the Unreal MCP Server.
Modernized for CI/CD Headless Compilation.
"""
import os


def _env_int(name: str, default: int) -> int:
    """Read an integer env var with a safe fallback."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

# ── WebSocket Connection ──────────────────────────────────────────────
# The WebSocket URL that Unreal Engine's Remote Control plugin exposes.
UE_WS_URL = os.getenv("UE_WS_URL", "ws://127.0.0.1:30020")

# ── MCP Server Transport ─────────────────────────────────────────────
SERVER_TRANSPORT = os.getenv("SERVER_TRANSPORT", "sse")
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = _env_int("SERVER_PORT", 8000)

# ── Unreal Project Configuration ──────────────────────────────────────
# PROJECT_NAME must match the folder name in your 'Source' directory.
UE_PROJECT_NAME = os.getenv("UE_PROJECT_NAME", "Automator")

# Optional module name for prompts and category labels. Defaults to project name.
UE_MODULE_NAME = os.getenv("UE_MODULE_NAME", UE_PROJECT_NAME)

# The root directory of your Unreal Project.
# Based on your previous logs, this is your current path:
UE_PROJECT_ROOT = os.getenv(
    "UE_PROJECT_ROOT",
    r"C:\Users\Deepesh\Desktop\Abhishekyadav0210-project\Automator",
)

# Path to the actual .uproject file (Needed for UBT)
UE_PROJECT_FILE_PATH = os.path.join(UE_PROJECT_ROOT, f"{UE_PROJECT_NAME}.uproject")

# Version label used in LLM prompt instructions.
UE_ENGINE_VERSION = os.getenv("UE_ENGINE_VERSION", "5.6")

# Explicit export macro override. Defaults to <MODULE>_API.
UE_EXPORT_MACRO = os.getenv("UE_EXPORT_MACRO", f"{UE_MODULE_NAME.upper()}_API")

# ── Unreal Build Tool (UBT) Paths ─────────────────────────────────────
# This is the 'BatchFiles' directory inside your Unreal Engine installation.
# Adjust the drive letter 'E:' if your UE5.6 is installed elsewhere!
UE_ENGINE_PATH = os.getenv("UE_ENGINE_PATH", r"E:\Unreal Engine\UE_5.6")
UE_BATCH_FILES_PATH = os.path.join(UE_ENGINE_PATH, r"Engine\Build\BatchFiles\Build.bat")
UE_EDITOR_EXE_PATH = os.path.join(UE_ENGINE_PATH, r"Engine\Binaries\Win64\UnrealEditor.exe")

# ── Codegen Settings ──────────────────────────────────────────────────
# Max retries for the self-healing compiler loop
MAX_COMPILE_RETRIES = _env_int("MAX_COMPILE_RETRIES", 3)

# Orchestrator lifecycle options
ORCH_EDITOR_CLOSE_TIMEOUT_SEC = _env_int("ORCH_EDITOR_CLOSE_TIMEOUT_SEC", 45)
ORCH_EDITOR_BOOT_TIMEOUT_SEC = _env_int("ORCH_EDITOR_BOOT_TIMEOUT_SEC", 180)
ORCH_FORCE_EDITOR_CLOSE = os.getenv("ORCH_FORCE_EDITOR_CLOSE", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
    "y",
}
ORCH_ENABLE_LIVE_CODING = os.getenv("ORCH_ENABLE_LIVE_CODING", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
    "y",
}
