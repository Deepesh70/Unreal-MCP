"""
Test module imports and backward-compatibility layers.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_core_modules():
    """Ensure core Unreal-MCP modules and FastMCP load correctly."""
    import unreal_mcp
    from unreal_mcp import cli
    assert hasattr(unreal_mcp, "__version__") or unreal_mcp is not None
    assert cli is not None


def test_import_server():
    """Verify server module imports without side effects."""
    import server
    assert server is not None


def test_import_agents_and_facade():
    """Verify canonical unreal_mcp.agents and root agents facade import cleanly."""
    import unreal_mcp.agents
    import unreal_mcp.agents.builder
    import unreal_mcp.agents.base
    import unreal_mcp.agents.processor
    import unreal_mcp.agents.hierarchy
    import unreal_mcp.agents.vision

    # Test backward-compatibility facade
    import agents
    import agents.builder
    import agents.processor
    assert unreal_mcp.agents.builder is not None
    assert agents.builder is not None


def test_import_api_and_bridge():
    """Verify unreal_mcp.api, api_server shim, and ide_bridge shim import cleanly."""
    import unreal_mcp.api
    import unreal_mcp.api.server
    import unreal_mcp.api.bridge
    import api_server
    import ide_bridge
    assert unreal_mcp.api.server.app is not None
    assert api_server.app is not None


def test_import_codegen_and_tools():
    """Verify codegen schemas, renderer, and domain tools import cleanly."""
    from unreal_mcp.codegen.schema import Blueprint, Variable, Function
    from unreal_mcp.codegen.renderer import render_header, render_source
    import unreal_mcp.tools.spawning
    import unreal_mcp.tools.transform
    import unreal_mcp.tools.character_weapon
    import unreal_mcp.tools.retargeting
    import unreal_mcp.tools.mesh_settings

    assert render_header is not None
    assert render_source is not None


if __name__ == "__main__":
    test_import_core_modules()
    test_import_server()
    test_import_agents_and_facade()
    test_import_api_and_bridge()
    test_import_codegen_and_tools()
    print("All import tests passed successfully!")
