# Code Generation Flow

## Overview

The structured code generation system lets the LLM generate UE C++ classes
without writing raw C++. The LLM outputs Blueprint JSON payloads and the server
validates, renders, writes, and compile-checks generated code.

## Flow

```
User: "Create a dynamic weather system"
  |
  v
Phase 0: optional compile preflight checks
  - validate Build.bat path, .uproject path, source folder
  - verify Unreal Editor is closed for headless compile
  - detect live coding patch artifacts
  |
  v
Phase 1: refine request with scene context
  |
  v
Phase 2: architecture manifest
  { modules: [{name, dependencies}] }
  |
  v
codegen/sorter.py resolves topological compile order
  |
  v
Phase 3: per-module Blueprint JSON generation (with retry feedback)
  |
  v
codegen/schema.py validates payloads
  (Pydantic: Blueprint, Variable, Function)
  |
  v
codegen/renderer.py renders via Jinja2
  templates/base_actor.h.j2
  templates/base_actor.cpp.j2
  |
  v
codegen/file_writer.py writes to
  Source/ProjectName/ClassName.h
  Source/ProjectName/ClassName.cpp
  |
  v
codegen/compiler.py runs headless compile check
  - on failure: feed compiler errors back into next retry
```

## CLI Modes

```bash
# Default two-phase mode: write + compile validate
python agent.py groq --two-phase

# Dry run: no file writes and no compile checks
python agent.py groq --two-phase --dry-run
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_ue_class` | Render + write .h/.cpp from Blueprint JSON |
| `preview_ue_class` | Render without writing (dry run) |
| `get_project_info` | Show configured project name and path |
| `list_project_files` | List .h/.cpp in project Source/ |
| `list_supported_types` | Show all 40+ friendly type mappings |

Note:
- `generate_ue_class` is a direct JSON->render/write tool.
- The full multi-phase CI/CD loop is implemented in `agents/pipeline.py`.

## Blueprint JSON Format

```json
{
  "class_name": "DynamicWeather",
  "parent_class": "AActor",
  "variables": [
    { "name": "WindSpeed", "type": "float", "default": "10.0f", "category": "Wind" },
    { "name": "Direction", "type": "vector", "category": "Wind" }
  ],
  "functions": [
    { "name": "UpdateWeather", "body": "WindSpeed += DeltaTime;" }
  ],
  "tick_enabled": true,
  "tick_body": "UpdateWeather();",
  "begin_play_body": "// init"
}
```

## Supported Types

| Friendly | UE C++ Type | Needs Include |
|----------|-------------|---------------|
| float | `float` | - |
| int | `int32` | - |
| bool | `bool` | - |
| string | `FString` | - |
| vector | `FVector` | Math/Vector.h |
| rotator | `FRotator` | Math/Rotator.h |
| color | `FLinearColor` | Math/Color.h |
| actor_ref | `AActor*` | GameFramework/Actor.h |
| mesh | `UStaticMeshComponent*` | Components/StaticMeshComponent.h |

(40+ types total - run `list_supported_types` tool for the full list)

## Setup

Update project/build settings in `unreal_mcp/config/settings.py`:
```python
UE_PROJECT_ROOT = r"C:\Projects\YourProject"
UE_PROJECT_NAME = "YourProject"
UE_PROJECT_FILE_PATH = os.path.join(UE_PROJECT_ROOT, f"{UE_PROJECT_NAME}.uproject")
UE_ENGINE_PATH = r"D:\Epic\UE_5.6"
UE_BATCH_FILES_PATH = os.path.join(UE_ENGINE_PATH, r"Engine\Build\BatchFiles\Build.bat")

UE_MODULE_NAME = "YourProject"
UE_EXPORT_MACRO = "YOURPROJECT_API"
UE_ENGINE_VERSION = "5.6"
MAX_COMPILE_RETRIES = 3
```
