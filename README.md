# Unreal Editor MCP Agent

Unreal MCP is a Python project that connects LLM agents to Unreal Engine through Model Context Protocol (MCP) tools over Unreal Remote Control WebSocket endpoints.

The repository supports three practical workflows:
- Live scene building in an open editor (`--build`)
- Multi-phase Unreal C++ generation with compile validation (`--two-phase`)
- End-to-end orchestration: generate code, compile, relaunch editor if needed, and spawn generated classes (`--orchestrate`)

## Table of Contents

- [Quick Start](#quick-start)
- [What This Project Does](#what-this-project-does)
- [Repository Layout](#repository-layout)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Run Modes](#run-modes)
- [FastAPI WebSocket Bridge](#fastapi-websocket-bridge)
- [Available MCP Tools](#available-mcp-tools)
- [Troubleshooting](#troubleshooting)
- [Development Notes](#development-notes)
- [Best Practice: Semantic Blueprints](#best-practice-semantic-blueprints)
- [RAG-Driven Code Generation (Ground Truth)](#rag-driven-code-generation-ground-truth)
- [Security Notes](#security-notes)

## Quick Start

1.  **Install dependencies**: `pip install -r requirements.txt`
2.  **Configure paths**: Copy `.env.example` to `.env` and set your `UE_ENGINE_PATH` and `UE_PROJECT_ROOT`.
3.  **Build RAG Database**: `python -m agents.rag_store`
4.  **Run Agent**: `python agent.py groq --build -i` (best for scene building)
5.  **Run C++ Generation**: `python agent.py groq --two-phase --prompt "Create a health component"`

## What This Project Does

This project gives an LLM controlled access to Unreal Editor operations through strongly scoped tools. Instead of directly emitting arbitrary code or editor actions, the model can call MCP tools such as:
- List actors
- Spawn actors
- Move/rotate/scale actors
- Read and update mesh settings
- Generate Unreal C++ class files

It also includes agent pipelines that add higher-level behavior around those tools:
- Prompt refinement
- JSON plan generation/repair
- Dependency ordering for generated modules
- Optional compile-feedback retry loops

## Repository Layout

Main entry points:
- `server.py`: Starts the MCP server
- `agent.py`: CLI launcher for Groq/Ollama/Gemini backends and mode selection
- `api_server.py`: FastAPI websocket bridge for web UIs

Core package:
- `unreal_mcp/__init__.py`: Creates shared `FastMCP` instance and auto-registers tools
- `unreal_mcp/config/settings.py`: Runtime settings (UE paths, ports, orchestrator behavior)
- `unreal_mcp/connection/websocket.py`: Unreal Remote Control transport wrappers
- `unreal_mcp/tools/`: MCP tool modules
- `unreal_mcp/codegen/`: C++ schema/render/write/sort/compile helpers
- `unreal_mcp/templates/`: Jinja2 templates for generated `.h` and `.cpp`

Agent logic:
- `agents/base.py`: Common tool-calling loop
- `agents/builder.py`: Live build pipeline
- `agents/pipeline.py`: Two-phase C++ pipeline
- `agents/orchestrator.py`: Hybrid generation + deployment flow (with robust intent analysis)
- `agents/groq_agent.py`, `agents/ollama_agent.py`, `agents/gemini_agent.py`: backend factories

Project assets:
- `unreal_mcp/mappings/`: Friendly-name to Unreal path mappings for common assets.
- `data/ue_api_knowledge.md`: Ground-truth C++ rules for Unreal components (includes, constructors, pointer patterns).

## How It Works

### MCP runtime path
1. `server.py` imports `mcp` from `unreal_mcp`.
2. `unreal_mcp/__init__.py` creates `FastMCP("UnrealMCP")` and imports `unreal_mcp.tools`.
3. `unreal_mcp/tools/__init__.py` imports each tool module so every `@mcp.tool()` function is registered.
4. Tool functions call Unreal through `unreal_mcp/connection/websocket.py` using HTTP-over-WebSocket messages.

### Unreal transport details
- Default WebSocket URL: `ws://127.0.0.1:30020`
- Typical endpoint call used by tools: `/remote/object/call`
- Property reads/writes use: `/remote/object/property`
- Metadata/describe uses fallback chain:
  - `/remote/object/describe`
  - `/remote/object`
  - `/remote/object/metadata`

### Agent run path
`agent.py` picks one backend (`groq`, `ollama`, `gemini`) and one mode:
- `--build`: scene plan + live execution
- `--two-phase`: C++ generation with optional headless compile validation
- `--orchestrate`: intent analysis + compile strategy + placement
- `data/ue_api_knowledge.md`: Dynamic RAG injection of C++ API facts.
- default mode: classic tool-calling agent

## Prerequisites

- Python 3.10+
- Unreal Engine project with C++ source enabled
- Unreal Remote Control plugins enabled in Editor:
  - Remote Control API
  - Remote Control Web Interface
- LLM provider access for at least one backend:
  - Groq API key
  - Google API key
  - or local Ollama server

For two-phase and orchestration compile flows (Windows-oriented defaults), ensure:
- `Build.bat` exists for your UE installation
- Project `.uproject` and `Source/<ProjectName>` paths are correct
- Unreal Editor can be closed/reopened by the process when required

## Installation

```bash
pip install -r requirements.txt
```

Create environment file from template:

```bash
copy .env.example .env
```

Then fill keys/settings in `.env`.

## Configuration

Configuration comes from both `.env` and `unreal_mcp/config/settings.py`.

### `.env` variables (from `.env.example`)

Provider keys:
- `GROQ_API_KEY`
- `GOOGLE_API_KEY`
- `OLLAMA_BASE_URL` (optional; defaults to `http://localhost:11434`)

Builder token controls:
- `BUILD_TOKEN_MODE` (`low`, `balanced`, `high`)
- `BUILD_ENABLE_PLAN_REVIEW`
- `BUILD_ENABLE_JSON_REPAIR`
- `BUILD_MAX_SCENE_CONTEXT_CHARS`
- `BUILD_MAX_BLUEPRINT_CONTEXT_CHARS`

### Runtime settings in `unreal_mcp/config/settings.py`

Server and transport:
- `UE_WS_URL` (default `ws://127.0.0.1:30020`)
- `SERVER_TRANSPORT` (default `sse`)
- `SERVER_HOST` (default `localhost`)
- `SERVER_PORT` (default `8000`)

Project/build paths:
- `UE_PROJECT_NAME`
- `UE_MODULE_NAME`
- `UE_PROJECT_ROOT`
- `UE_PROJECT_FILE_PATH` (derived)
- `UE_ENGINE_VERSION`
- `UE_EXPORT_MACRO`
- `UE_ENGINE_PATH`
- `UE_BATCH_FILES_PATH` (derived)
- `UE_EDITOR_EXE_PATH` (derived)

Compile/orchestrator controls:
- `MAX_COMPILE_RETRIES` (default `3`)
- `ORCH_EDITOR_CLOSE_TIMEOUT_SEC` (default `45`)
- `ORCH_EDITOR_BOOT_TIMEOUT_SEC` (default `180`)
- `ORCH_FORCE_EDITOR_CLOSE` (bool)
- `ORCH_ENABLE_LIVE_CODING` (bool, default `true`)

Semantic Build Policy:
- `BUILD_TOKEN_MODE`: Controls token usage strategy (`low`, `balanced`, `high`).
- `BUILD_ENABLE_PLAN_REVIEW`: Enables an LLM-based QA pass for geometry refinement.

Important: the checked-in defaults for project and engine paths are machine-specific placeholders. Set them to your local environment before using code generation/compile flows.

## Run Modes

### 1) Start MCP server

```bash
python server.py
```

`server.py` tries compatible run paths for different `fastmcp` versions:
- `mcp.run(transport="sse", host=..., port=...)`
- fallback to `mcp.sse_app()` + `uvicorn`
- fallback to `mcp.http_app(transport="sse")` + `uvicorn`

### 2) Launch agent CLI

```bash
python agent.py <backend> [mode] [options]
```

Backends:
- `groq`
- `ollama`
- `gemini`

Modes:
- `--build` / `-b`: Live builder
- `--two-phase` / `-2`: C++ generation pipeline
- `--orchestrate` / `-o`: Unified generation + placement  
- `--test`: Quick test prompt in classic mode
- default: classic tool-calling mode

Options:
- `--interactive` / `-i`
- `--prompt "..."`
- `--dry-run` (for `--two-phase`; ignored in `--orchestrate`)
- `--no-compile` (Write C++ files but skip Unreal Build Tool)
- `--level "..."` (Target level hint for --build/--orchestrate)

Examples:

```bash
# Live scene build
python agent.py groq --build --prompt "spawn 3 cubes at origin"

# Interactive build session
python agent.py groq --build -i

# Two-phase C++ generation with compile validation
python agent.py groq --two-phase --prompt "Create a WeatherController actor"

# Two-phase preview only (no writes/compile)
python agent.py groq --two-phase --dry-run --prompt "Create a health component"

# Full orchestrated code + placement
python agent.py groq --orchestrate --prompt "Create a C++ LaserTrap actor and place 3 in scene"

# Classic agent smoke test
python agent.py gemini --test
```

### 3) Backend-specific entry points (optional)

```bash
python -m agents.groq_agent
python -m agents.ollama_agent
python -m agents.gemini_agent
```

Useful backend options:

```bash
python -m agents.ollama_agent --list-models
python -m agents.gemini_agent --list-models
```

## FastAPI WebSocket Bridge

Run bridge:

```bash
uvicorn api_server:app --port 8080
```

WebSocket route:
- `/ws/chat`

Payloads accepted:
- Raw text prompt
- JSON object with prompt and config

Example JSON payload:

```json
{
  "prompt": "Build a small hut with a door and windows",
  "config": {
    "backend": "groq",
    "mode": "build"
  }
}
```

Supported `mode` values in bridge:
- `build` (default)
- `two_phase`
- `classic`
- `orchestrate` (Natively supported via `orchestrate_in_ue`)

## Available MCP Tools

The server currently auto-registers tools from these modules:
- `unreal_mcp/tools/spawning.py`
- `unreal_mcp/tools/actors.py`
- `unreal_mcp/tools/transform.py`
- `unreal_mcp/tools/mesh_settings.py`
- `unreal_mcp/tools/codegen_tool.py`
- `unreal_mcp/tools/project_tool.py`
- `unreal_mcp/tools/scene_tool.py`
- `unreal_mcp/tools/alignment.py` (New: Semantic Snapping)

Tool summary:

- Scene/actor tools:
  - `list_actors()`
  - `spawn_actor(actor_class_or_asset, x, y, z)`
  - `set_actor_scale(actor_path, scale_x, scale_y, scale_z)`
  - `set_actor_rotation(actor_path, pitch, yaw, roll)`
  - `set_actor_location(actor_path, x, y, z)`
  - `get_scene_summary()`

- Alignment/Snapping tools (Deterministic Math):
  - `get_actor_bounds(actor_path)`: Queries live bounding box from Unreal.
  - `snap_to_actor(subject, target, direction, padding)`: Snaps objects to edges (Top, Bottom, North, South, East, West, NW, NE, SW, SE).

- Mesh settings tools:
  - `list_mesh_settings(actor_or_mesh_path, contains="", limit=120)`
  - `validate_mesh_settings(actor_or_mesh_path, setting_names)`
  - `read_mesh_settings(actor_or_mesh_path, setting_names)`
  - `sync_mesh_settings(actor_or_mesh_path, desired_settings)`
  - `set_mesh_settings(actor_or_mesh_path, settings)`

- Codegen/project tools:
  - `generate_ue_class(blueprint_json)`
  - `preview_ue_class(blueprint_json)`
  - `get_project_info()`
  - `list_project_files()`
  - `list_supported_types()`

## Troubleshooting

### Prompt required errors
If not running interactive mode (`-i`) and not using `--test`, provide `--prompt "..."`.

### Cannot connect to Unreal Remote Control
- Verify UE is running
- Verify Remote Control plugins are enabled
- Verify `UE_WS_URL` matches your editor endpoint (default `ws://127.0.0.1:30020`)
- Check firewall/port conflicts

### Two-phase preflight failure
`run_compile_preflight_check()` fails when:
- `Build.bat` path is wrong
- `.uproject` path is wrong
- `Source/<ProjectName>` is missing
- Unreal Editor is still running
- stale Live Coding patch artifacts are present

Fix paths in `unreal_mcp/config/settings.py`, close editor, remove stale patch artifacts, rerun.

### Compile keeps failing with generic output
The pipeline already extracts focused diagnostics and may append Unreal log tail (`Saved/Logs`). Use those lines first, then rerun with a tighter prompt.

### Generated class not visible/spawnable
- Confirm files are written under `Source/<UE_PROJECT_NAME>/`
- Rebuild from IDE/UE if necessary
- Ensure class path format resolves as `/Script/<UE_PROJECT_NAME>.<ClassName>`

### Orchestrate mode behavior to know
- **Intent Analysis**: The orchestrator uses a hybrid of LLM analysis and robust Regex heuristics to classify user prompts (e.g., "Create a file" vs "Place an actor").
- **State Logs**: Real-time `[Intent]` classification is logged to the terminal for debugging.
- If editor is open and `ORCH_ENABLE_LIVE_CODING=true`, it first tries compile-through-live-coding.
- If that fails, it falls back to close editor -> headless compile -> relaunch -> spawn.

## Development Notes

Add new tools by following `docs/ADDING_TOOLS.md`.

Minimal process:
1. Create a new module in `unreal_mcp/tools/`
2. Import `mcp` from `unreal_mcp`
3. Decorate function(s) with `@mcp.tool()`
4. Import that module in `unreal_mcp/tools/__init__.py`
5. Restart server and verify tool registration

## Best Practice: Semantic Blueprints

Instead of providing raw coordinates in your prompts, use **Semantic Blueprints** in `data/blueprints/`. 

**Example Blueprint Style:**
```markdown
# My Tower
1. Spawn floor.
2. Spawn wall. Snap to North edge of floor.
3. Spawn stairs. Snap to Southwest corner of floor.
```

The system will use **RAG** to find these instructions and the **Alignment Tools** to perform precise bounding-box math, completely eliminating AI-math hallucinations.

## RAG-Driven Code Generation (Ground Truth)

The C++ generation pipeline (`--two-phase`) no longer relies on hardcoded rules in the system prompt. It uses a **Dynamic API Rules** system:

1.  **Ground Truth**: All C++ facts (includes, constructors, pointer rules) are stored in `data/ue_api_knowledge.md`.
2.  **Surgical Retrieval**: For every class being generated, the agent queries the vector DB for the specific component rules.
3.  **Unyielding Constraint**: The LLM is strictly forbidden from guessing and MUST obey the retrieved rules.

### Architecture Blueprints

The system also supports **Architecture Blueprints** stored in `data/blueprints/`. These are natural language descriptions of complex structures (like a "tower" or "hut") that the RAG system retrieves to guide the **Live Builder**.

### How to Expand Knowledge:

#### 1. Manual Addition
To teach the agent a new component (e.g., `UNiagaraComponent`), simply add a new header to `data/ue_api_knowledge.md`:
```markdown
## UNiagaraComponent
Include: "NiagaraComponent.h"
Constructor: CreateDefaultSubobject<UNiagaraComponent>(TEXT("Effect"))
Pointer Rules: UNiagaraComponent*
```

#### 2. Automatic Scraping (Experimental)
You can automatically crawl your Unreal Engine source code to generate knowledge blocks:
```bash
# Update UE_CLASSES_DIR in scripts/scrape_ue_api.py first!
python scripts/scrape_ue_api.py
```

#### 3. Update Vector Database
After modifying markdown files in `data/`, always rebuild the index:
```bash
python -m agents.rag_store
```

## Security Notes

- Never commit `.env` with real API keys
- Treat MCP and FastAPI bridge processes as privileged local services
- Do not expose these endpoints publicly without authentication and network controls
- Generated C++ is written to project source directories and can trigger builds; use trusted prompts/sources
