"""
Backward compatibility shim for agents.groq_agent -> unreal_mcp.agents.groq_agent.
"""
import sys
import unreal_mcp.agents.groq_agent as _target

sys.modules[__name__] = _target
