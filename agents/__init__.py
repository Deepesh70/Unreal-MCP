"""
Backward compatibility proxy for `agents` -> `unreal_mcp.agents`.
"""
import sys
import unreal_mcp.agents

# Proxy module
sys.modules[__name__] = unreal_mcp.agents
