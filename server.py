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

import os

# Clean up broken SSL_CERT_FILE / SSL_CERT_DIR pointing to non-existent files (common on Windows Conda)
if "SSL_CERT_FILE" in os.environ and not os.path.exists(os.environ["SSL_CERT_FILE"]):
    del os.environ["SSL_CERT_FILE"]
if "SSL_CERT_DIR" in os.environ and not os.path.exists(os.environ["SSL_CERT_DIR"]):
    del os.environ["SSL_CERT_DIR"]

from unreal_mcp.cli import main

if __name__ == "__main__":
    main()
