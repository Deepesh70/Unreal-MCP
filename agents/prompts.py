"""
Backward compatibility shim for agents.prompts -> unreal_mcp.agents.prompts.
"""
import sys
import unreal_mcp.agents.prompts as _target

sys.modules[__name__] = _target
