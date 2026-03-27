"""
Safe stdio encoding setup for Windows terminals.

This avoids repeatedly wrapping sys.stdout/sys.stderr, which can lead to
"I/O operation on closed file" when wrappers are replaced multiple times.
"""

from __future__ import annotations

import io
import sys


def configure_windows_stdio_utf8() -> None:
    """Configure stdout/stderr to UTF-8 once per process on Windows."""
    if sys.platform != "win32":
        return

    if getattr(sys, "_unreal_mcp_stdio_utf8_configured", False):
        return

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue

        try:
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8", errors="replace")
                continue
        except Exception:
            pass

        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            continue

        try:
            setattr(sys, stream_name, io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"))
        except Exception:
            # Last-resort fallback failed; keep original stream.
            continue

    setattr(sys, "_unreal_mcp_stdio_utf8_configured", True)
