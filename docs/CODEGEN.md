# Code Generation Flow

## Overview

The structured code generation system lets the LLM generate UE C++ classes
without writing raw C++. The LLM outputs a JSON Blueprint, and the server
renders it through Jinja2 templates into proper .h/.cpp files.

## Flow

```
User: "Create a dynamic weather system"
  |
  v
LLM outputs structured JSON:        <-- ~80% fewer tokens
  { class_name, variables, functions }
  |
  v
codegen/schema.py validates it       <-- Zero hallucinations
  (Pydantic: Blueprint, Variable, Function)
  |
  v
codegen/type_mapper.py resolves types
  float -> float, vector -> FVector
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
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_ue_class` | Render + write .h/.cpp from Blueprint JSON |
| `preview_ue_class` | Render without writing (dry run) |
| `get_project_info` | Show configured project name and path |
| `list_project_files` | List .h/.cpp in project Source/ |
| `list_supported_types` | Show all 40+ friendly type mappings |

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

Update your project path in `unreal_mcp/config/settings.py`:
```python
UE_PROJECT_PATH = "C:/Users/You/Documents/Unreal Projects/YourProject"
UE_PROJECT_NAME = "YourProject"
```
