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
