# Unreal MCP Agent

Unreal MCP Agent connects Unreal Engine Remote Control to LLM-driven automation.

It supports:
- Live scene building from natural language.
- Scene-aware planning with optional RAG blueprint retrieval.
- Tool-calling agent mode for direct Unreal operations.
- Two-phase C++ class generation for Unreal projects.
- Mesh settings discovery, validation, read, write, and sync operations.

This README is a full, current reference for the repository state.

## 1. What This Project Does

At runtime, the system exposes an MCP server (`UnrealMCP`) with tools that can:
- Spawn actors and basic shapes in Unreal.
- List existing actors and their full object paths.
- Move, rotate, and scale actors.
- Query scene context and recommend safe build offsets.
- Generate and preview Unreal C++ classes from structured JSON blueprints.
- Inspect source files and supported C++ generation types.
- Manage mesh properties for specific mesh components with discovery and validation.

On the agent side, there are multiple workflows:
- Classic tool-calling mode (`agents/base.py`).
- Live builder pipeline (`agents/builder.py`) for scene construction.
- Two-phase codegen pipeline (`agents/pipeline.py`) for C++ classes.

## 2. Current Architecture

### 2.1 High-Level Flow

1. User runs `agent.py` with a backend (`groq`, `ollama`, or `gemini`).
2. Agent connects to MCP server (`server.py`) via SSE.
3. MCP server exposes tools from `unreal_mcp/tools/*`.
4. Tools call Unreal through Remote Control WebSocket transport in `unreal_mcp/connection/websocket.py`.
5. Unreal executes object calls/property operations and returns responses.

### 2.2 Runtime Layers

- Entry points:
  - `server.py`: starts FastMCP server.
  - `agent.py`: CLI launcher and mode selection.
- Agent workflows:
  - `agents/base.py`
  - `agents/builder.py`
  - `agents/pipeline.py`
- MCP package:
  - `unreal_mcp/__init__.py` (creates shared FastMCP instance)
  - `unreal_mcp/tools/*` (tool registration and tool logic)
  - `unreal_mcp/connection/*` (UE transport)
  - `unreal_mcp/config/settings.py` (host, port, UE path, WS URL)
- Codegen:
  - `unreal_mcp/codegen/*`
- Mappings:
  - `unreal_mcp/mappings/assets.py`
  - `unreal_mcp/mappings/classes.py`

## 3. Repository Structure

Top-level important files and folders:

- `agent.py`: CLI launcher for all agent modes.
- `server.py`: FastMCP server launcher.
- `api_server.py`: FastAPI websocket bridge for external clients.
- `requirements.txt`: Python dependencies.
- `.env.example`: environment variable template.
- `agents/`: orchestration logic and LLM adapters.
- `unreal_mcp/`: MCP package and tools.
- `data/blueprints/`: markdown blueprint documents for RAG.
- `data/chroma_db/`: persisted Chroma vectorstore.
- `docs/`: internal developer docs.

## 4. Prerequisites

- Python 3.8+
- Unreal Engine with Remote Control plugin available
- Remote Control Web Interface running in editor
- Network access to UE Remote Control websocket endpoint

## 5. Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Core dependencies include:
- `fastmcp`
- `websockets`
- `langchain` and adapters
- `langchain_groq`, `langchain_ollama`, `langchain_google_genai`
- `langchain_chroma`, `langchain_huggingface`
- `python-dotenv`

## 6. Configuration

### 6.1 Environment Variables (`.env`)

Copy `.env.example` to `.env` and set only the provider keys you use.

Typical variables:
- `GROQ_API_KEY`
- `GOOGLE_API_KEY`
- `OLLAMA_BASE_URL` (optional, defaults to localhost)

Builder token optimization variables:
- `BUILD_TOKEN_MODE` = `low` | `balanced` | `high`
- `BUILD_ENABLE_PLAN_REVIEW` = `true`/`false`
- `BUILD_ENABLE_JSON_REPAIR` = `true`/`false`
- `BUILD_MAX_SCENE_CONTEXT_CHARS` = integer
- `BUILD_MAX_BLUEPRINT_CONTEXT_CHARS` = integer

### 6.2 Static Settings (`unreal_mcp/config/settings.py`)

Adjust as needed:
- `UE_WS_URL` (default `ws://127.0.0.1:30020`)
- `SERVER_HOST`, `SERVER_PORT`
- `UE_PROJECT_PATH`, `UE_PROJECT_NAME`

## 7. Running the System

### 7.1 Start MCP Server

```bash
python server.py
```

### 7.2 Start Agent

Interactive live builder:

```bash
python agent.py groq -b -i
```

Other modes:

```bash
python agent.py groq --test
python agent.py groq --two-phase
python agent.py ollama -b -i
python agent.py gemini -b -i
```

## 8. Agent Modes

### 8.1 Classic Tool-Calling Mode

File: `agents/base.py`

Behavior:
- Connects to SSE MCP endpoint at `http://localhost:8000/sse`.
- Loads all FastMCP tools.
- Executes user requests via LangChain agent.

### 8.2 Live Builder Mode

File: `agents/builder.py`

Pipeline phases:
1. Phase 0: scene query + safe-offset context.
2. Phase 0.5: optional blueprint retrieval from RAG store.
3. Phase 1: prompt refinement.
4. Phase 2: build-plan JSON generation.
5. Phase 2b: optional geometry review/refinement pass.
6. Phase 3: execute plan step-by-step in Unreal.

Key reliability features:
- Token policy modes (`low`/`balanced`/`high`).
- Context truncation for token control.
- JSON extraction + cleanup.
- Optional JSON repair LLM pass.
- Plan sanitization (`spawn`, `scale`, `rotate`, `mesh_settings`, `sync_mesh_settings`).
- Dropped invalid step reporting.

Token accounting:
- Per-phase token logging:
  - Phase 1 Refine
  - Phase 2 Plan
  - Phase 2 Review (if enabled)
  - Phase 2 Repair (if triggered)
- Overall token totals at build completion.

### 8.3 Two-Phase Codegen Mode

File: `agents/pipeline.py`

Flow:
1. Refine request into technical specification.
2. Generate Blueprint JSON.
3. Render `.h/.cpp` from templates.
4. Optionally write files to Unreal project source path.

## 9. MCP Tools (Current)

Registered through `unreal_mcp/tools/__init__.py`.

### 9.1 Actor/Scene Tools

- `list_actors()`
  - Lists actor names and object paths.
- `get_scene_summary()`
  - Summarizes current scene and provides safe build origin guidance.

### 9.2 Spawn/Transform Tools

- `spawn_actor(actor_class_or_asset, x, y, z)`
- `set_actor_scale(actor_path, scale_x, scale_y, scale_z)`
- `set_actor_rotation(actor_path, pitch, yaw, roll)`
- `set_actor_location(actor_path, x, y, z)`

Supported basic shapes (asset map):
- `cube`, `sphere`, `cylinder`, `cone`, `plane`

Supported mapped classes (class map):
- `pointlight`, `spotlight`, `directional_light`

### 9.3 Mesh Settings Tools

File: `unreal_mcp/tools/mesh_settings.py`

- `list_mesh_settings(actor_or_mesh_path, contains="", limit=120)`
  - Discover available property names.
- `validate_mesh_settings(actor_or_mesh_path, setting_names)`
  - Validate names and suggest close matches.
- `read_mesh_settings(actor_or_mesh_path, setting_names)`
  - Read current values.
- `set_mesh_settings(actor_or_mesh_path, settings)`
  - Write one or many properties.
- `sync_mesh_settings(actor_or_mesh_path, desired_settings)`
  - Read current values and write only changed ones.

Path resolution behavior:
- Tries provided path first, then common mesh component suffixes:
  - `.StaticMeshComponent0`
  - `.StaticMeshComponent`
  - `.Mesh`

### 9.4 Project/Codegen Tools

- `get_project_info()`
- `list_project_files()`
- `list_supported_types()`
- `generate_ue_class(blueprint_json)`
- `preview_ue_class(blueprint_json)`

## 10. Unreal Transport API

File: `unreal_mcp/connection/websocket.py`

Functions:
- `send_ue_ws_http_request(url, verb="PUT", body=None)`
- `send_ue_ws_command(object_path, function_name, parameters=None)`
- `send_ue_ws_property_update(object_path, property_name, property_value)`
- `send_ue_ws_property_read(object_path, property_name)`
- `send_ue_ws_object_describe(object_path)`

`send_ue_ws_object_describe` tries multiple endpoints for compatibility:
- `/remote/object/describe`
- `/remote/object`
- `/remote/object/metadata`

## 11. RAG Blueprint Retrieval

File: `agents/rag_store.py`

Behavior:
- Loads markdown files from `data/blueprints/*.md`.
- Embeds text with `all-MiniLM-L6-v2`.
- Stores/reloads vectors in Chroma at `data/chroma_db`.
- Retrieves top semantic match with relevance check before injection.

## 12. Prompting Guidelines for Better Builds

For reliable geometry:
- Use two-pass prompting:
  - Pass 1: structural shell (floor/walls/openings).
  - Pass 2: roof/details/decor.
- Keep each pass bounded (for example, under 30-40 steps).
- Use explicit numeric coordinates and labels.
- Keep roof instructions deterministic with fixed rotations and centers.

For lower token usage:
- Set `BUILD_TOKEN_MODE=low`.
- Disable review for draft runs.
- Re-enable review for final quality runs.

## 13. Troubleshooting

### 13.1 `python agent.py ... -b -i` exits with error

Check:
- MCP server is running on expected host/port.
- Correct Python environment has all requirements installed.
- LLM API key for selected provider is configured.

### 13.2 Build output has detached roofs or bad openings

Common causes:
- Center-pivot rotation not compensated.
- Overly long prompt leading to malformed/approximate coordinates.
- Review pass disabled in low token mode.

Actions:
- Use deterministic two-pass prompts.
- Keep `BUILD_ENABLE_PLAN_REVIEW=true` for final builds.
- Keep JSON repair enabled.

### 13.3 JSON decode failures in Phase 2

The pipeline includes:
- JSON extraction/cleanup.
- Optional auto-repair pass.

If still failing:
- Reduce prompt complexity.
- Split build into multiple prompts.

### 13.4 No actors or mesh paths resolve

Check:
- Unreal editor running with Remote Control enabled.
- Correct object path from `list_actors`.
- Mesh settings tool path fallback may still fail for custom component names.

## 14. Development Notes

- Add new MCP tools in `unreal_mcp/tools/` and import them in `unreal_mcp/tools/__init__.py`.
- Keep all UE websocket logic in `unreal_mcp/connection/websocket.py`.
- Prefer explicit schema validation and sanitization before executing LLM outputs.

Useful docs:
- `docs/ADDING_TOOLS.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENTS.md`
- `docs/CODEGEN.md`

## 15. Security and Secrets

- Never commit real API keys to version control.
- Keep `.env` private.
- Use `.env.example` as the public template.

## 16. Quick Command Reference

Start server:

```bash
python server.py
```

Run live builder (Groq):

```bash
python agent.py groq -b -i
```

Run tool-calling test:

```bash
python agent.py groq --test
```

Run two-phase codegen:

```bash
python agent.py groq --two-phase
```

## 17. Current Status Summary

This repository currently includes:
- Multi-backend LLM integration.
- Live Unreal build pipeline with token-aware controls.
- Robust JSON handling and optional review/repair passes.
- Mesh settings introspection and diff-based sync.
- Code generation pipeline for Unreal C++ classes.
- RAG-assisted architectural prompting from local blueprint docs.

