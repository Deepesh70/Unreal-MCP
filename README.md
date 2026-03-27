# Unreal MCP Agent

Unreal MCP Agent connects Unreal Engine Remote Control to LLM-driven automation.

This repository provides two production workflows:
- Live scene building in an open Unreal Editor session.
- Multi-phase C++ class generation with compile validation.
- Orchestrated C++ generation + automatic deployment back into scene.

It also includes a classic tool-calling mode and a FastAPI websocket bridge for external frontends.

## 1. Current Project Scope

At runtime, the system exposes an MCP server (`UnrealMCP`) with tools that can:
- Spawn actors and basic shapes in Unreal.
- List existing actors and full object paths.
- Move, rotate, and scale actors.
- Query scene context and suggest safe build offsets.
- Discover, validate, read, write, and sync mesh settings.
- Generate and preview Unreal C++ classes from structured Blueprint JSON.
- Inspect project source files and list supported generation types.

## 2. Current Repository Structure

Top-level:
- `agent.py` - CLI launcher for all agent modes.
- `server.py` - FastMCP server entry point.
- `api_server.py` - FastAPI websocket bridge (`/ws/chat`).
- `requirements.txt` - Python dependencies.
- `.env.example` - environment variable template.
- `README.md` - this file.

Runtime directories:
- `agents/` - orchestration and LLM workflows.
- `unreal_mcp/` - MCP package, tools, mappings, transport, codegen.
- `data/blueprints/` - optional RAG markdown documents.
- `data/chroma_db/` - persisted Chroma vector DB.
- `docs/` - implementation docs.

Important note:
- Demo/test scripts were removed from production root.

## 3. Prerequisites

- Python 3.10+ recommended.
- Unreal Engine project with Remote Control enabled.
- Remote Control websocket reachable (default `ws://127.0.0.1:30020`).
- API key for the backend you use (`groq` or `gemini`) or local Ollama running.

For two-phase compile mode specifically:
- Unreal Editor should be closed during headless compile checks.
- Unreal Build Tool path and `.uproject` path must be correct in settings.

## 4. Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## 5. Configuration

### 5.1 `.env` Variables

Copy `.env.example` to `.env` and set only what you need.

Common variables:
- `GROQ_API_KEY`
- `GOOGLE_API_KEY`
- `OLLAMA_BASE_URL` (optional)

Builder token policy variables:
- `BUILD_TOKEN_MODE` = `low` | `balanced` | `high`
- `BUILD_ENABLE_PLAN_REVIEW` = `true`/`false`
- `BUILD_ENABLE_JSON_REPAIR` = `true`/`false`
- `BUILD_MAX_SCENE_CONTEXT_CHARS` = integer
- `BUILD_MAX_BLUEPRINT_CONTEXT_CHARS` = integer

Orchestrator lifecycle variables:
- `ORCH_EDITOR_CLOSE_TIMEOUT_SEC` = integer seconds (default `45`)
- `ORCH_EDITOR_BOOT_TIMEOUT_SEC` = integer seconds (default `180`)
- `ORCH_FORCE_EDITOR_CLOSE` = `true`/`false` (default `false`)
- `ORCH_ENABLE_LIVE_CODING` = `true`/`false` (default `true`)

### 5.2 `unreal_mcp/config/settings.py`

Current settings are environment-aware (`os.getenv`) with defaults.

Key values:
- `UE_WS_URL`
- `SERVER_TRANSPORT`, `SERVER_HOST`, `SERVER_PORT`
- `UE_PROJECT_ROOT`, `UE_PROJECT_NAME`, `UE_PROJECT_FILE_PATH`
- `UE_ENGINE_PATH`, `UE_BATCH_FILES_PATH`, `UE_EDITOR_EXE_PATH`
- `UE_MODULE_NAME`, `UE_EXPORT_MACRO`, `UE_ENGINE_VERSION`
- `MAX_COMPILE_RETRIES`

## 6. Running the System

### 6.1 Start MCP Server

```bash
python server.py
```

### 6.2 Agent CLI

General syntax:

```bash
python agent.py <backend> [mode] [options]
```

Backends:
- `groq`
- `ollama`
- `gemini`

Modes:
- `--build` / `-b` - live scene builder.
- `--two-phase` / `-2` - multi-phase C++ codegen pipeline.
- `--orchestrate` / `-o` - auto closes editor (if needed), compiles C++, relaunches editor, and places generated classes.
- `--test` - one lightweight connectivity/tool test.
- default (no mode) - classic tool-calling agent.

Options:
- `--interactive` / `-i`
- `--prompt "..."`
- `--dry-run` (two-phase only, no file write/compile)
- `--level "..."` (build-mode hint only)

Prompt requirement behavior:
- In non-interactive build mode, prompt is required.
- In non-interactive two-phase mode, prompt is required.
- In non-interactive classic mode, prompt is required unless `--test` is used.

Examples:

```bash
python agent.py groq --build --prompt "spawn one large cube at origin"
python agent.py groq --build --level "/Game/Maps/TestMap" --prompt "spawn 3 cubes"
python agent.py groq --two-phase --prompt "Create a CubeMarker actor with one StaticMeshComponent"
python agent.py groq --orchestrate --prompt "Create a C++ LaserTrap and place 3 in the scene"
python agent.py groq --two-phase --dry-run --prompt "Create WeatherController actor"
python agent.py groq --test
```

## 7. Agent Workflows

### 7.1 Classic Tool-Calling (`agents/base.py`)

- Connects to MCP SSE endpoint (`http://localhost:8000/sse`).
- Loads all registered tools.
- Executes user prompt through LangChain agent.

### 7.2 Live Builder (`agents/builder.py`)

Pipeline:
1. Query scene context.
2. Optional RAG blueprint retrieval (`agents/rag_store.py`).
3. Refine user request into build spec.
4. Generate plan JSON.
5. Optional plan review/refinement pass.
6. Sanitize steps and execute in Unreal.

Supported plan actions:
- `spawn`
- `scale`
- `rotate`
- `mesh_settings`
- `sync_mesh_settings`

Reliability features:
- token policy modes (`low`, `balanced`, `high`)
- JSON extraction and cleanup
- optional JSON repair pass
- dropped-step sanitization reporting
- phase and overall token accounting

### 7.3 Two-Phase C++ Pipeline (`agents/pipeline.py`)

Pipeline:
1. Optional compile preflight check (when writing files).
2. Refine prompt into technical spec.
3. Generate architecture manifest (`modules` + dependencies).
4. Resolve topological compile order.
5. Per module: generate Blueprint JSON, normalize/fix schema fields.
6. Validate via Pydantic schema.
7. Render `.h/.cpp` via Jinja templates.
8. Write files to `Source/<ProjectName>/`.
9. Run headless compile; retry using compiler feedback.

Compile preflight checks include:
- Build.bat path exists
- `.uproject` exists
- source directory exists
- Unreal Editor process not running
- live coding patch artifact detection

### 7.4 Orchestrator Pipeline (`agents/orchestrator.py`)

For mixed requests that include both C++ generation and scene placement:
1. Analyze prompt intent (codegen vs placement).
2. If editor is open, try Live Coding compile trigger through Remote Control.
3. If Live Coding trigger fails, close editor for safe headless compile.
4. Run two-phase C++ generation/compile pipeline.
5. Relaunch Unreal Editor when needed.
6. Wait for Remote Control websocket and spawn generated class instances.

## 8. MCP Tools (Current)

Registered via `unreal_mcp/tools/__init__.py`.

### 8.1 Actor and Scene
- `list_actors()`
- `get_scene_summary()`

### 8.2 Spawn and Transform
- `spawn_actor(actor_class_or_asset, x, y, z)`
- `set_actor_scale(actor_path, scale_x, scale_y, scale_z)`
- `set_actor_rotation(actor_path, pitch, yaw, roll)`
- `set_actor_location(actor_path, x, y, z)`

### 8.3 Mesh Settings
- `list_mesh_settings(actor_or_mesh_path, contains="", limit=120)`
- `validate_mesh_settings(actor_or_mesh_path, setting_names)`
- `read_mesh_settings(actor_or_mesh_path, setting_names)`
- `set_mesh_settings(actor_or_mesh_path, settings)`
- `sync_mesh_settings(actor_or_mesh_path, desired_settings)`

Mesh path resolution attempts:
- exact path
- `.StaticMeshComponent0`
- `.StaticMeshComponent`
- `.Mesh`

### 8.4 Project and Codegen
- `get_project_info()`
- `list_project_files()`
- `list_supported_types()`
- `generate_ue_class(blueprint_json)`
- `preview_ue_class(blueprint_json)`

## 9. Mappings and Transport

Mappings:
- `unreal_mcp/mappings/assets.py`
  - `cube`, `sphere`, `cylinder`, `cone`, `plane`
- `unreal_mcp/mappings/classes.py`
  - `pointlight`, `spotlight`, `directional_light`
  - `grid_generator` -> `/Game/BP_GridGenerator.BP_GridGenerator_C`

Transport API (`unreal_mcp/connection/websocket.py`):
- `send_ue_ws_http_request(...)`
- `send_ue_ws_command(...)`
- `send_ue_ws_property_update(...)`
- `send_ue_ws_property_read(...)`
- `send_ue_ws_object_describe(...)`

`send_ue_ws_object_describe` tries multiple endpoints for compatibility:
- `/remote/object/describe`
- `/remote/object`
- `/remote/object/metadata`

## 10. Codegen Internals

- Schema: `unreal_mcp/codegen/schema.py` (Pydantic models)
- Type mapping: `unreal_mcp/codegen/type_mapper.py`
- Rendering: `unreal_mcp/codegen/renderer.py`
- Templates:
  - `unreal_mcp/templates/base_actor.h.j2`
  - `unreal_mcp/templates/base_actor.cpp.j2`
- File writing and backups: `unreal_mcp/codegen/file_writer.py`
  - existing files are rotated to `.bak`
- Dependency order resolver: `unreal_mcp/codegen/sorter.py`
- Headless compile and preflight: `unreal_mcp/codegen/compiler.py`

## 11. FastAPI Bridge

`api_server.py` exposes:
- websocket endpoint: `/ws/chat`
- preflight UE websocket connectivity check
- status streaming messages during build

## 12. Level-Specific Behavior

- Two-phase code generation is not level-specific; it generates C++ source files.
- Build/spawn workflow affects the currently open Unreal level.
- `--level` is a prompt hint in build mode; it is ignored in two-phase mode.

## 13. Troubleshooting

### 13.1 Prompt missing errors

If you run non-interactive modes without `--prompt`, CLI exits and requests a prompt.

### 13.2 Two-phase preflight fails

Check in `unreal_mcp/config/settings.py`:
- `UE_PROJECT_ROOT`
- `UE_PROJECT_FILE_PATH`
- `UE_ENGINE_PATH`
- `UE_BATCH_FILES_PATH`

Also:
- close Unreal Editor
- remove Live Coding patch artifacts from project binaries

### 13.3 Generated classes not visible in Unreal Content Browser

- Open the correct Unreal project from `UE_PROJECT_ROOT`.
- Rebuild C++ project.
- Confirm files exist under `Source/<UE_PROJECT_NAME>/`.

### 13.4 Live build cannot connect to Unreal

- Ensure Remote Control plugin/web interface is running.
- Verify `UE_WS_URL` and network reachability.

## 14. Development Notes

- Add new tools in `unreal_mcp/tools/` and import them in `unreal_mcp/tools/__init__.py`.
- Keep Unreal websocket calls centralized in `unreal_mcp/connection/websocket.py`.
- Keep schema-first validation for all LLM-generated code payloads.

Additional docs:
- `docs/ADDING_TOOLS.md`
- `docs/AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/CODEGEN.md`
- `docs/FLOW_SPAWN.md`
- `docs/FLOW_LIST.md`
- `docs/FLOW_TRANSFORM.md`

## 15. Security

- Never commit real API keys.
- Keep `.env` private.
- Use `.env.example` as template only.
 
