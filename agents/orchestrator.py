"""
Backward compatibility shim for agents.orchestrator -> unreal_mcp.agents.orchestrator.
"""
import sys
import unreal_mcp.agents.orchestrator as _target

sys.modules[__name__] = _target
