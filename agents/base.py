"""
Backward compatibility shim for agents.base -> unreal_mcp.agents.base.
"""
import sys
import unreal_mcp.agents.base as _target

sys.modules[__name__] = _target
