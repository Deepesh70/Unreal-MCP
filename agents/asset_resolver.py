"""
Backward compatibility shim for agents.asset_resolver -> unreal_mcp.agents.asset_resolver.
"""
import sys
import unreal_mcp.agents.asset_resolver as _target

sys.modules[__name__] = _target
