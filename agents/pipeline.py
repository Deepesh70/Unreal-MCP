"""
Backward compatibility shim for agents.pipeline -> unreal_mcp.agents.pipeline.
"""
import sys
import unreal_mcp.agents.pipeline as _target

sys.modules[__name__] = _target
