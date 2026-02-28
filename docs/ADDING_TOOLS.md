# ➕ Adding New Tools — Developer Guide

> Step-by-step guide for extending Unreal MCP with new tools.

------

## Quick Checklist

1. **Pick the right module** or create a new one in `unreal_mcp/tools/`
2. **Import `mcp`** from `unreal_mcp`
3. **Decorate** your function with `@mcp.tool()`
4. **Register** the module in `tools/__init__.py`
5. **Add mappings** (if needed) in `mappings/`
6. **Test** with `python -c "from unreal_mcp import mcp"`

---

## Detailed Steps

### Step 1 — Decide Where the Tool Goes

| If the tool… | Put it in… |
|---|---|
| Spawns / creates actors | `tools/spawning.py` |
| Queries / lists actors/info | `tools/actors.py` |
| Moves / scales / rotates | `tools/transform.py` |
| Does something entirely new | Create a new `tools/<category>.py` |

### Step 2 — Write the Tool Function

Create or edit the file in `unreal_mcp/tools/`:

```python
# tools/materials.py  (example new tool module)

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_command
from unreal_mcp.utils import format_error


@mcp.tool()
async def set_actor_material(actor_path: str, material_path: str) -> str:
    """
    Applies a material to the given actor.
    Provide the full actor_path from list_actors output.
    """
    try:
        response = await send_ue_ws_command(
            object_path=actor_path,
            function_name="SetMaterial",
            parameters={"MaterialPath": material_path},
        )
        return f"Applied material {material_path} to {actor_path.split('.')[-1]}"
    except Exception as e:
        return format_error(e, "Check that the material path is valid.")
```

### Step 3 — Register in `tools/__init__.py`

Add one import line:

```python
from . import materials  # noqa: F401  – set_actor_material
```

### Step 4 — Add Mappings (Optional)

If your tool needs friendly-name lookups, add them to `mappings/`:

- **New shape?** → Add to `ASSET_MAP` in `mappings/assets.py`
- **New actor class?** → Add to `CLASS_MAP` in `mappings/classes.py`
- **Entirely new category?** → Create `mappings/materials.py` with its own dict + lookup helper

### Step 5 — Add Utils (Optional)

If you need shared parsing logic, add helpers to `utils/response.py` or create a new utils file.

### Step 6 — Verify

```bash
# Quick import check (no UE needed)
python -c "from unreal_mcp import mcp; print('Tools:', [t.name for t in mcp._tools.values()])"

# Full server start
python server.py
```

---

## File Naming Conventions

| Layer | Convention | Examples |
|---|---|---|
| `tools/` | Verb or category name | `spawning.py`, `actors.py`, `transform.py`, `materials.py` |
| `mappings/` | Noun (what is being mapped) | `assets.py`, `classes.py`, `materials.py` |
| `utils/` | Noun (what it helps with) | `response.py`, `validation.py` |
| `config/` | Always `settings.py` | `settings.py` |
| `connection/` | Transport type | `websocket.py` |
