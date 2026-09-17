# 🔧 MCP Tools Reference — Every Tool Documented

## Current Tool Inventory (6 tools as of Phase 1)

---

### `get_scene_state` — The AI's Eyes

**File:** `unreal_mcp/tools/scene.py`
**Phase:** 1 (Foundation)
**Purpose:** Query all actors in the scene before making changes.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `filter_type` | string | `""` | Filter by actor type (e.g. "StaticMesh", "Light", "Camera") |
| `near_x` | float | None | Center X for proximity filter |
| `near_y` | float | None | Center Y for proximity filter |
| `near_z` | float | None | Center Z for proximity filter |
| `radius` | float | 10000 | Max distance from center (in Unreal Units) |

**Returns:** JSON with all actors, their names, types, paths, and locations.

**Example response:**
```json
{
  "total_actors": 3,
  "actors": [
    {"name": "StaticMeshActor_5", "type": "StaticMeshActor", "path": "/Game/...", "location": [500, 0, 0]},
    {"name": "PointLight_1", "type": "PointLight", "path": "/Game/...", "location": [200, 100, 300]}
  ]
}
```

**When to use:** ALWAYS call this first before spawning, modifying, or destroying anything. The AI should never act without knowing what's in the scene.

---

### `spawn_actor` — Create Anything

**File:** `unreal_mcp/tools/spawning.py`
**Phase:** 1 (upgraded from original)
**Purpose:** Spawn any actor type in the scene.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `actor_class_or_asset` | string | required | What to spawn (e.g. "cube", "PointLight", "CineCameraActor") |
| `x`, `y`, `z` | float | 0 | World position |
| `rotation_pitch/yaw/roll` | float | 0 | Initial rotation in degrees |

**Returns:** Actor name and full path (use the path for modify/destroy/property tools).

**Friendly names supported:** cube, sphere, cone, cylinder, plane, pointlight, spotlight, directionallight, cinecameraactor

---

### `modify_actor` — Change Anything That Exists

**File:** `unreal_mcp/tools/modify.py`
**Phase:** 1
**Purpose:** Move, rotate, or scale an existing actor.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `actor_path` | string | required | Full path from get_scene_state or spawn_actor |
| `location_x/y/z` | float | None | New position (set all 3 to move) |
| `rotation_pitch/yaw/roll` | float | None | New rotation (set all 3 to rotate) |
| `scale_x/y/z` | float | None | New scale (set all 3 to scale) |

Only specify what you want to change — omitted values stay unchanged.

---

### `destroy_actor` — Remove Anything

**File:** `unreal_mcp/tools/modify.py`
**Phase:** 1
**Purpose:** Remove an actor from the scene.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `actor_path` | string | required | Full path to the actor to destroy |

---

### `list_actors` — Simple Actor List (Legacy)

**File:** `unreal_mcp/tools/actors.py`
**Phase:** Original
**Purpose:** List all actors with names and paths. Simpler than get_scene_state.

---

### `set_actor_scale` — Scale Only (Legacy)

**File:** `unreal_mcp/tools/transform.py`
**Phase:** Original
**Purpose:** Scale an actor. Superseded by modify_actor but kept for backward compatibility.

---

## Planned Tools (Phase 2+)

| Tool | Phase | Purpose |
|------|-------|---------|
| `execute_python_in_editor` | 2 | Run arbitrary UE Python scripts — infinite capability |
| `set_actor_property` | 2 | Set any UE property on any actor |
| `get_actor_property` | 2 | Read any UE property from any actor |
| `capture_viewport` | 3 | Take screenshots for visual feedback |
| `run_console_command` | 3 | Execute UE console commands |
| `find_assets` | 3 | Search project content for assets |
