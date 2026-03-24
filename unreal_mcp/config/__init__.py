# # Configuration package for Unreal MCP Server
# from .settings import UE_WS_URL, SERVER_HOST, SERVER_PORT, SERVER_TRANSPORT
# from .settings import UE_PROJECT_PATH, UE_PROJECT_NAME

# unreal_mcp/config/__init__.py

# Only import what we actually defined in settings.py
from .settings import (
    UE_PROJECT_NAME, 
    UE_PROJECT_ROOT,     # New name
    UE_PROJECT_FILE_PATH, 
    SERVER_HOST, 
    SERVER_PORT,
    UE_WS_URL
)