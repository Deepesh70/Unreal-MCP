"""
Backward compatibility shim for agents.vision -> unreal_mcp.agents.vision.
"""
import sys
import unreal_mcp.agents.vision as _target

sys.modules[__name__] = _target
