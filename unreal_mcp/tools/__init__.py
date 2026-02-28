"""
Tools package — MCP tool registration.

Importing this package triggers all tool modules to load, which
registers their @mcp.tool() decorated functions with the FastMCP
instance.

To add a new tool:
  1. Create a new .py file in this folder
  2. Import `mcp` from `unreal_mcp` and decorate your function
  3. Add an import line below so the module loads at startup
"""

# Each import causes the @mcp.tool() decorators inside to fire,
# registering the tools on the shared `mcp` instance.
from . import spawning   # noqa: F401  – spawn_actor
from . import actors     # noqa: F401  – list_actors
from . import transform  # noqa: F401  – set_actor_scale
