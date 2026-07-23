"""
Unreal MCP CLI — the single entry point for the server.

Usage:
    unreal-mcp              # SSE mode on port 8000 (or next available)
    unreal-mcp --stdio      # stdio mode (IDE auto-launch)
    unreal-mcp --port 9000  # SSE on a specific port

After `pip install .`, this is available as the `unreal-mcp` command.
"""

import sys
import socket
import argparse

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _find_available_port(start: int = 8000, max_tries: int = 20) -> int:
    """Find the first available port starting from `start`."""
    for offset in range(max_tries):
        port = start + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    return start  # Fallback to original — let the server error naturally


def main():
    """Entry point for the `unreal-mcp` CLI command."""
    parser = argparse.ArgumentParser(
        prog="unreal-mcp",
        description="MCP server for Unreal Engine — AI-powered level editing",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport (IDE auto-launch mode)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for SSE transport (default: 8000, auto-fallback if taken)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost)",
    )

    args = parser.parse_args()

    # Import here (after arg parse) so --help is fast
    from unreal_mcp import mcp
    from unreal_mcp.config import SERVER_HOST, SERVER_PORT

    if args.stdio:
        mcp.run(transport="stdio")
    else:
        host = args.host or SERVER_HOST
        requested_port = args.port or SERVER_PORT

        # Try the requested port, auto-fallback if taken
        port = _find_available_port(requested_port)
        if port != requested_port:
            print(f"⚠  Port {requested_port} is in use, using port {port} instead.")

        print(f"🚀 Unreal MCP Server starting on http://{host}:{port}")
        print(f"   SSE endpoint: http://{host}:{port}/sse")
        print(f"   Unreal WS:    {_get_ue_url()}")
        print(f"   Press Ctrl+C to stop.\n")

        try:
            # FastMCP v3.x
            mcp.run(transport="sse", host=host, port=port)
        except TypeError:
            try:
                # FastMCP v2.x
                import uvicorn
                app = mcp.sse_app()
                uvicorn.run(app, host=host, port=port)
            except AttributeError:
                # FastMCP v1.x
                import uvicorn
                app = mcp.http_app(transport="sse")
                uvicorn.run(app, host=host, port=port)


def _get_ue_url() -> str:
    """Get the configured Unreal WebSocket URL for display."""
    try:
        from unreal_mcp.config import UE_WS_URL
        return UE_WS_URL
    except Exception:
        return "ws://127.0.0.1:30020 (default)"


if __name__ == "__main__":
    main()
