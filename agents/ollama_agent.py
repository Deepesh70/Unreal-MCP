"""
Backward compatibility shim for agents.ollama_agent -> unreal_mcp.agents.ollama_agent.
"""
import sys
import unreal_mcp.agents.ollama_agent as _target

sys.modules[__name__] = _target
