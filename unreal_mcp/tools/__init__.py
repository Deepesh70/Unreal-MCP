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

# Phase 0 (original)
from . import spawning   # noqa: F401  – spawn_actor
from . import actors     # noqa: F401  – list_actors
from . import transform  # noqa: F401  – set_actor_scale

# Phase 1 (foundation)
from . import scene      # noqa: F401  – get_scene_state
from . import modify     # noqa: F401  – modify_actor, destroy_actor

# Phase 2 (superpower + properties)
from . import scripting  # noqa: F401  – execute_python_in_editor
from . import properties # noqa: F401  – set_actor_property, get_actor_property

# Phase 3 (feedback loop + discovery)
from . import capture    # noqa: F401  – capture_viewport
from . import console    # noqa: F401  – run_console_command
from . import assets     # noqa: F401  – find_assets

# Phase 4 (reliability + health)
from . import health     # noqa: F401  – check_connection

# Phase 5 (materials + import)
from . import materials     # noqa: F401  – set_material, list_materials
from . import import_asset  # noqa: F401  – import_asset, add_starter_content
