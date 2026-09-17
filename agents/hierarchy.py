"""
Backward compatibility shim for agents.hierarchy -> unreal_mcp.agents.hierarchy.
"""
import sys
import unreal_mcp.agents.hierarchy as _target

sys.modules[__name__] = _target
