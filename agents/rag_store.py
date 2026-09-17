"""
Backward compatibility shim for agents.rag_store -> unreal_mcp.agents.rag_store.
"""
import sys
import unreal_mcp.agents.rag_store as _target

sys.modules[__name__] = _target
