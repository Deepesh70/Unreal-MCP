"""
Settings & Constants for the Unreal MCP Server.

All configurable values live here so they can be changed in one place
without touching any tool or connection logic.
"""

import os

# ── WebSocket Connection ──────────────────────────────────────────────
# The WebSocket URL that Unreal Engine's Remote Control plugin exposes.
# Default: local UE on the standard Remote Control port.
# For remote/cloud mode, set UE_WS_URL to your public tunnel address.
UE_WS_URL = os.getenv("UE_WS_URL", "ws://127.0.0.1:30020")

# ── MCP Server Transport ─────────────────────────────────────────────
# How the FastMCP server is exposed to agents (sse, stdio, etc.)
SERVER_TRANSPORT = "sse"
SERVER_HOST = "localhost"
SERVER_PORT = 8000

# ── Builder Mode — C++ File Generation ───────────────────────────────
# Directory where generated .h/.cpp files are written.
CPP_OUTPUT_DIR = os.getenv("CPP_OUTPUT_DIR", os.path.join(os.getcwd(), "generated"))

# The Unreal project API export macro (e.g., MYPROJECT_API).
# Set this in your .env to match your Unreal project name.
PROJECT_API = os.getenv("PROJECT_API", "YOURPROJECT_API")

# The Unreal project module name (derived from PROJECT_API if not set).
# Used for advanced class path construction if needed.
UE_PROJECT_MODULE = os.getenv("UE_PROJECT_MODULE", "")

