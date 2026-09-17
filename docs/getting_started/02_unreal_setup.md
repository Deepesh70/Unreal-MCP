# 🔌 Unreal Engine Plugins — What to Enable

## Required Plugins

Both plugins must be enabled in your Unreal project for the full tool set to work.

### 1. Remote Control Web Interface (REQUIRED)

**What it does:** Opens a WebSocket server on port 30020 that accepts JSON commands. This is how Python talks to Unreal.

**How to enable:**
1. Open Unreal Engine with your project
2. Go to `Edit → Plugins`
3. Search for "Remote Control"
4. Enable **"Remote Control API"** (the base plugin)
5. Enable **"Remote Control Web Interface"** (the WebSocket server)
6. Restart the editor when prompted

**Verify it's working:**
- After restart, open a browser and go to: `http://localhost:30010`
- You should see the Remote Control web panel
- The WebSocket is on: `ws://localhost:30020`

**If the port is different:**
Edit `unreal_mcp/config/settings.py` and update `UE_WS_URL`:
```python
UE_WS_URL = "ws://localhost:30020"  # Change port if needed
```

### 2. Python Editor Script Plugin (REQUIRED for full capability)

**What it does:** Embeds a Python 3 interpreter inside the Unreal Editor. This is what `execute_python_in_editor` uses to run arbitrary Python scripts with full `import unreal` access.

**How to enable:**
1. Go to `Edit → Plugins`
2. Search for "Python"
3. Enable **"Python Editor Script Plugin"**
4. Restart the editor when prompted

**Verify it's working:**
1. Open the Output Log: `Window → Developer Tools → Output Log`
2. At the bottom, switch the dropdown from "Cmd" to "Python"
3. Type: `print("Hello from Python!")` and press Enter
4. You should see `Hello from Python!` in the log

**Without this plugin:**
The following tools still work (they only use the Remote Control WebSocket):
- `get_scene_state` ✅
- `spawn_actor` ✅
- `modify_actor` ✅
- `destroy_actor` ✅
- `list_actors` ✅
- `set_actor_scale` ✅
- `set_actor_property` ✅
- `get_actor_property` ✅
- `run_console_command` ✅

The following tools REQUIRE the Python plugin:
- `execute_python_in_editor` ❌ (needs Python interpreter)
- `capture_viewport` ❌ (uses Python internally for AutomationLibrary)
- `find_assets` ❌ (uses Python internally for EditorAssetLibrary)

## Optional Plugins

These are NOT required but enhance capabilities if you want specific features:

| Plugin | What It Enables |
|--------|----------------|
| **Geometry Scripting** | Runtime boolean modeling (used by ProceduralCityManager.cpp) |
| **Chaos Destruction** | Physics-based destruction with GeometryCollections |
| **Niagara** | Particle VFX (usually enabled by default) |
| **Level Sequencer** | Cinematic timeline (usually enabled by default) |
