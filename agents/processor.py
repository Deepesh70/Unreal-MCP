"""
Backward compatibility shim for agents.processor -> unreal_mcp.agents.processor.
"""
import sys
import unreal_mcp.agents.processor as _target

sys.modules[__name__] = _target
