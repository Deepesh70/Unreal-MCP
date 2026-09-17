"""
Backward compatibility launcher for Unreal-MCP IDE Bridge.
The canonical module is now `unreal_mcp.api.bridge`.
"""

import sys
import asyncio
from unreal_mcp.api.bridge import (
    main,
    send_intent,
    send_intents_from_file,
    check_status,
    run_screenshot,
    run_refine,
)

if __name__ == "__main__":
    asyncio.run(main())
