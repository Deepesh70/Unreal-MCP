"""
Backward compatibility shim for agents.builder_prompts -> unreal_mcp.agents.builder_prompts.
"""
import sys
import unreal_mcp.agents.builder_prompts as _target

sys.modules[__name__] = _target
