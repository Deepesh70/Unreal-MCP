# 📊 Phase Tracking — Implementation Progress

## Phase Overview

| Phase | Name | Status | Tools Added | Files Changed |
|-------|------|--------|-------------|---------------|
| **1** | Eyes & Hands | 🔄 In Progress | `get_scene_state`, `modify_actor`, `destroy_actor`, `spawn_actor` upgrade | 3 new, 1 modified |
| **2** | The Superpower | ⬜ Not Started | `execute_python_in_editor`, `set_actor_property`, `get_actor_property` | 2 new, 1 modified |
| **3** | Feedback Loop | ⬜ Not Started | `capture_viewport`, `run_console_command`, `find_assets` | 3 new |
| **4** | Legacy Merge | ⬜ Not Started | Refactor `agent.py` to use MCP tools internally | 4 modified |

---

## Phase 1: Eyes & Hands (Foundation)

### Goal
Give the AI the ability to SEE what's in the scene and MANIPULATE existing actors.

### Checklist
- [ ] Create `unreal_mcp/tools/scene.py` with `get_scene_state`
- [ ] Create `unreal_mcp/tools/modify.py` with `modify_actor` and `destroy_actor`
- [ ] Upgrade `unreal_mcp/tools/spawning.py` — return actor path, add rotation support
- [ ] Update `unreal_mcp/tools/__init__.py` to import new modules
- [ ] Test: `get_scene_state` returns actors from a running UE instance
- [ ] Test: `modify_actor` successfully moves an actor
- [ ] Test: `destroy_actor` removes an actor
- [ ] Test: `spawn_actor` returns the spawned actor's path

### Validation
- Tool registration verified (FastMCP lists all tools on startup)
- WebSocket commands are correctly formatted
- Return values are useful to an LLM (clear names, locations, types)

---

## Phase 2: The Superpower

### Goal
Enable the AI to write and execute arbitrary Unreal Python scripts.

### Checklist
- [ ] Add `execute_python()` to `websocket.py`
- [ ] Create `unreal_mcp/tools/scripting.py` with `execute_python_in_editor`
- [ ] Create `unreal_mcp/tools/properties.py` with `set_actor_property`, `get_actor_property`
- [ ] Test: Execute a simple Python script that spawns an actor
- [ ] Test: Execute a Sequencer creation script
- [ ] Test: Set a light's intensity via `set_actor_property`

### Validation
- Scripts execute inside UE's Python interpreter
- Output/errors are returned to the caller
- Property changes reflect immediately in the UE viewport

---

## Phase 3: Feedback Loop

### Goal
Enable the AI to see the results of its work via screenshots.

### Checklist
- [ ] Create `unreal_mcp/tools/capture.py` with `capture_viewport`
- [ ] Create `unreal_mcp/tools/console.py` with `run_console_command`
- [ ] Create `unreal_mcp/tools/assets.py` with `find_assets`
- [ ] Test: Screenshot is saved and path is returned
- [ ] Test: Console command executes successfully
- [ ] Test: Asset search returns valid results

### Validation
- Screenshots are readable image files
- The path returned can be used by a vision-capable model

---

## Phase 4: Legacy Merge

### Goal
Refactor the standalone `agent.py` CLI to use MCP tools internally, so there's one code path.

### Checklist
- [ ] Refactor `agent.py` to start the MCP server internally
- [ ] Refactor `agents/base.py` to call MCP tools instead of `processor.py` directly
- [ ] Fix bridge paralysis (semantic routing via LLM)
- [ ] Add recipe jitter/randomization
- [ ] Verify backward compatibility: `python agent.py groq -b -i` still works

### Validation
- Old CLI commands produce the same results as before
- No duplicate WebSocket connections
- Recipe matching uses LLM, not substring
