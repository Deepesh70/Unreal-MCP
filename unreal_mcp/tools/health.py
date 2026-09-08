"""
Health Check Tool — instant connection verification.

Checks every link in the chain:
  1. MCP Server itself (always passes — you're calling it)
  2. Unreal Engine WebSocket (can we reach ws://127.0.0.1:30020?)
  3. Remote Control API (can we call a function on UE?)
  4. Python Editor Plugin (can we execute Python inside UE?)

Returns a clear ✅/❌ status board so the user knows exactly what's
working and what needs fixing.
"""

import json
import asyncio
import websockets

from unreal_mcp import mcp
from unreal_mcp.config import UE_WS_URL, SERVER_PORT


@mcp.tool()
async def check_connection() -> str:
    """Check if the MCP server is connected to Unreal Engine and everything is working.

    Call this before doing any work to verify the full pipeline is operational.

    Returns:
        A status board showing ✅/❌ for each system component.
    """
    results = []
    all_ok = True

    # ── 1. MCP Server (always passes) ─────────────────────────────────
    results.append(f"✅ MCP Server     → Running (port {SERVER_PORT})")

    # ── 2. WebSocket Connection ───────────────────────────────────────
    ws_ok = False
    try:
        async with websockets.connect(UE_WS_URL, open_timeout=5) as ws:
            ws_ok = True
            results.append(f"✅ UE WebSocket   → Connected to {UE_WS_URL}")
    except ConnectionRefusedError:
        results.append(f"❌ UE WebSocket   → Connection refused on {UE_WS_URL}")
        results.append(f"   Fix: Open Unreal Engine and enable the Remote Control Web Interface plugin")
        all_ok = False
    except asyncio.TimeoutError:
        results.append(f"❌ UE WebSocket   → Timeout connecting to {UE_WS_URL}")
        results.append(f"   Fix: Verify Unreal Engine is running and Remote Control plugin is enabled")
        all_ok = False
    except Exception as e:
        error_str = str(e)
        if "1225" in error_str or "10061" in error_str or "refused" in error_str.lower():
            results.append(f"❌ UE WebSocket   → Connection refused on {UE_WS_URL}")
            results.append(f"   Fix: Open Unreal Engine and enable the Remote Control Web Interface plugin")
        else:
            results.append(f"❌ UE WebSocket   → {error_str}")
        all_ok = False

    # ── 3. Remote Control API (call a function) ───────────────────────
    if ws_ok:
        try:
            from unreal_mcp.connection import send_ue_ws_command
            from unreal_mcp.utils import extract_return_value

            response = await send_ue_ws_command(
                object_path="/Script/UnrealEd.Default__EditorActorSubsystem",
                function_name="GetAllLevelActors",
            )
            actors = extract_return_value(response)
            actor_count = len(actors) if isinstance(actors, list) else 0
            results.append(f"✅ Remote Control → Responding ({actor_count} actors in level)")
        except Exception as e:
            results.append(f"❌ Remote Control → API call failed: {e}")
            all_ok = False

    # ── 4. Python Editor Plugin ───────────────────────────────────────
    if ws_ok:
        try:
            from unreal_mcp.connection import execute_python

            py_result = await execute_python('print("MCP_HEALTH_OK")', timeout=5.0)
            if "MCP_HEALTH_OK" in py_result:
                results.append(f"✅ Python Plugin  → Available (execute_python works)")
            elif "not enabled" in py_result.lower():
                results.append(f"⚠️  Python Plugin  → Console execution disabled")
                results.append(f"   Fix: Edit → Project Settings → Remote Control → Enable 'Allow Remote Console Execution'")
            else:
                results.append(f"⚠️  Python Plugin  → Uncertain response: {py_result[:100]}")
        except Exception as e:
            results.append(f"⚠️  Python Plugin  → Could not verify: {e}")

    # ── Summary ───────────────────────────────────────────────────────
    status_line = "READY — All systems operational." if all_ok else "NOT READY — See issues above."
    status_emoji = "🟢" if all_ok else "🔴"

    output = "\n".join(results)
    output += f"\n\n{status_emoji} Status: {status_line}"

    if all_ok:
        output += "\n\nYou can now spawn actors, modify the scene, capture screenshots, and more."

    return output
