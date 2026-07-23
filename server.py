"""
Unreal MCP Server — Entry Point.

This file is a backward-compatible launcher. The real logic is now in
`unreal_mcp.cli`. Prefer using the `unreal-mcp` command after pip install.

    python server.py            # SSE mode (default, port 8000)
    python server.py --stdio    # stdio mode (for VS Code / IDE integration)

Or after `pip install .`:
    unreal-mcp                  # Same as python server.py
    unreal-mcp --stdio          # Same as python server.py --stdio
"""

from unreal_mcp.cli import main

if __name__ == "__main__":
    main()