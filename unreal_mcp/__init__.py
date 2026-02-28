"""
Unreal MCP — Root Package.

Creates the shared FastMCP instance and loads all tool modules so their
@mcp.tool() decorators register automatically at import time.

Usage (from server.py):
    from unreal_mcp import mcp
    mcp.run(...)
"""

from fastmcp import FastMCP

# ── Shared MCP instance ──────────────────────────────────────────────
mcp = FastMCP("UnrealMCP")

# ── Auto-register all tools by importing the tools package ───────────
from unreal_mcp import tools  # noqa: E402, F401
