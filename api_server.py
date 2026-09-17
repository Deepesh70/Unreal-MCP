"""
Backward compatibility launcher for Unreal-MCP API Server.
The canonical module is now `unreal_mcp.api.server`.
"""

from unreal_mcp.api.server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("unreal_mcp.api.server:app", host="0.0.0.0", port=8000, reload=True)
