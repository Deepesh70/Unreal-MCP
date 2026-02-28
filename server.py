"""
Unreal MCP Server — Entry Point.

This file is now a thin launcher.  All logic lives inside the
`unreal_mcp` package.  Run this to start the FastMCP server:

    python server.py
"""

from unreal_mcp import mcp
from unreal_mcp.config import SERVER_HOST, SERVER_PORT

if __name__ == "__main__":
    try:
        # FastMCP v3.x — supports host/port as transport kwargs
        mcp.run(transport="sse", host=SERVER_HOST, port=SERVER_PORT)
    except TypeError:
        try:
            # FastMCP v2.x — has sse_app() method
            import uvicorn
            app = mcp.sse_app()
            uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
        except AttributeError:
            # FastMCP v1.x / other — run with http transport
            import uvicorn
            app = mcp.http_app(transport="sse")
            uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)