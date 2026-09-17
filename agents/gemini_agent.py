"""
Backward compatibility shim for agents.gemini_agent -> unreal_mcp.agents.gemini_agent.
"""
import sys
import unreal_mcp.agents.gemini_agent as _target

sys.modules[__name__] = _target
