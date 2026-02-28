"""
Settings & Constants for the Unreal MCP Server.

All configurable values live here so they can be changed in one place
without touching any tool or connection logic.
"""

# ── WebSocket Connection ──────────────────────────────────────────────
# The WebSocket URL that Unreal Engine's Remote Control plugin exposes.
UE_WS_URL = "ws://127.0.0.1:30020"

# ── MCP Server Transport ─────────────────────────────────────────────
# How the FastMCP server is exposed to agents (sse, stdio, etc.)
SERVER_TRANSPORT = "sse"
SERVER_HOST = "localhost"
SERVER_PORT = 8000

# ── Unreal Project ────────────────────────────────────────────────────
# Path to your UE project root (the folder containing .uproject)
# Update this to match your project location!
UE_PROJECT_PATH = "C:/Users/Jeevant/Documents/Unreal Projects/MyProject"
UE_PROJECT_NAME = "MyProject"

