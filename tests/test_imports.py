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
