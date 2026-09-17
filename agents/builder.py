"""
Backward compatibility shim for agents.builder -> unreal_mcp.agents.builder.
"""
import sys
import unreal_mcp.agents.builder as _target

sys.modules[__name__] = _target
