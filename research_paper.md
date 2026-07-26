# Bridging Natural Language and 3D World Construction: A Zero-Setup MCP Framework for AI-Driven Unreal Engine Scene Authoring

**Authors:** Deepesh Jeevant, et al.  
**Affiliation:** Independent Research  
**Date:** May 2026  

---

## Abstract

We present **Unreal-MCP**, an open-source framework that enables Large Language Models (LLMs) to directly construct, modify, and query three-dimensional scenes inside Unreal Engine 5 through the Model Context Protocol (MCP). Unlike prior approaches that require extensive manual configuration, custom plugins, or domain-specific scripting, our system achieves **zero-setup deployment** — a single `pip install` followed by an IDE configuration entry is sufficient to connect any MCP-compatible AI assistant to a running Unreal Engine editor. We introduce a layered architecture comprising (1) a self-describing MCP tool registry with 17 specialized tools, (2) an intelligent scene query system that filters environment noise and resolves mesh asset names into human-readable summaries, (3) a material mapping subsystem enabling realistic scene appearance through friendly-name lookups, and (4) a multi-link health diagnostic pipeline. We validate the system through a controlled experiment: the procedural construction of a structurally accurate Howrah Bridge replica comprising 850+ individually placed actors with positional accuracy, demonstrating that complex architectural structures can be assembled entirely through AI-tool interaction without human placement. Our framework reduces the barrier to AI-assisted 3D content creation from hours of setup to under two minutes, while maintaining full extensibility for advanced workflows including Python editor scripting, asset import, and multi-model agent orchestration.

**Keywords:** Model Context Protocol, Large Language Models, Unreal Engine, Procedural Generation, 3D Scene Authoring, AI-Assisted Design, Zero-Configuration Systems

---

## 1. Introduction

### 1.1 Motivation

The creation of three-dimensional virtual environments remains one of the most labor-intensive tasks in game development, architectural visualization, and simulation. A level designer constructing a moderately complex scene in Unreal Engine must manually position, rotate, scale, and configure hundreds to thousands of individual actors — a process that can consume days of skilled human effort for a single environment.

Recent advances in Large Language Models (LLMs) have demonstrated remarkable capability in understanding spatial relationships, generating structured data, and reasoning about complex multi-step tasks. However, connecting these language-based reasoning capabilities to the concrete, low-level APIs of professional 3D engines presents significant engineering challenges:

1. **Protocol Mismatch:** LLMs operate on text; game engines operate on binary scene graphs, UFunctions, and property systems.
2. **Setup Burden:** Existing solutions require cloning repositories, installing complex dependency chains, configuring WebSocket URLs, and understanding engine-specific plugin systems.
3. **Information Asymmetry:** When queried about a scene, raw engine APIs return hundreds of cryptic object paths (e.g., `HLOD0_UAID_3497F631D5890DD300_1234567890`) that are meaningless to both humans and AI models.
4. **Tool Blindness:** Connected AI models receive only tool names and parameter signatures — without rich contextual instructions, they resort to creating files on disk or generating scripts rather than using the available tools.

### 1.2 Contributions

This paper makes the following contributions:

- **A zero-setup pip-installable MCP server** with automatic port fallback and stdio transport for IDE auto-launching, reducing deployment from a multi-step process to a single command.
- **A self-describing tool registry** with embedded instructions that prevent AI models from reverting to file-editing behaviors, ensuring tool-only interaction.
- **An intelligent scene query system** (Scene Intelligence Level 2) that automatically classifies actors, filters environment noise (HLOD, LandscapeStreamingProxy, NavigationMesh), resolves mesh asset names, and produces natural-language summaries.
- **A material mapping and application subsystem** supporting 24 friendly-named materials mapped to Unreal Engine Starter Content paths.
- **A multi-link health diagnostic tool** that independently tests MCP connectivity, WebSocket transport, Remote Control API responsiveness, and Python plugin availability.
- **Empirical validation** through the construction of an 850-actor Howrah Bridge replica, demonstrating structural fidelity, positional accuracy, and real-time construction throughput.

---

## 2. Related Work

### 2.1 Text-to-3D Object Generation

Text-to-3D generation has seen rapid progress through diffusion-based methods. DreamFusion [1] introduced Score Distillation Sampling (SDS) for optimizing Neural Radiance Fields from text prompts using pretrained 2D diffusion models. Magic3D [2] improved upon this with a coarse-to-fine optimization strategy achieving higher-resolution outputs via a DMTet representation. Instant3D [3] further advanced the field with a feed-forward architecture combining sparse-view generation and large reconstruction models. However, all these approaches generate *individual objects* outside any game engine context, requiring manual import and scene integration.

### 2.2 LLM-Driven Scene Layout

More relevant to our work are methods that leverage LLMs for scene-level spatial reasoning. LayoutGPT [4] demonstrated that in-context learning with GPT-3.5/4 can produce 3D bounding box layouts for indoor scenes using CSS-style coordinate templates. SceneFormer [5] treats indoor scene generation as a sequence prediction task using Transformer self-attention to learn implicit object relationships. Holodeck [6] generates fully furnished 3D environments in AI2-THOR by combining GPT-4 with a constraint satisfaction solver.

3D-GPT [7] is particularly related — it uses multiple LLM agents (a task dispatcher, a 3D modeler, and a layout designer) to generate procedural Blender scripts that build 3D scenes. Our system shares the goal of LLM-driven procedural construction but differs in three critical ways: (1) we target a professional game engine (Unreal Engine 5) rather than a modeling tool, (2) we operate *live* within the editor session rather than generating offline scripts, and (3) we use a standardized protocol (MCP) rather than custom API wrappers.

### 2.3 Model Context Protocol (MCP)

The Model Context Protocol, introduced by Anthropic in November 2024 [8], standardizes the interface between AI models and external tools using JSON-RPC 2.0 over stdio or SSE transport. The Python reference SDK [9] and the FastMCP framework [10] significantly reduce the boilerplate required to build MCP servers. Prior MCP implementations have targeted web APIs, databases, file systems, and code editors. To our knowledge, **this is the first MCP server designed for real-time 3D game engine control**.

### 2.4 Existing Unreal Engine MCP Integrations

Several concurrent open-source projects have explored connecting AI assistants to Unreal Engine via MCP. Notable implementations include `chongdashu/unreal-mcp` [11], which uses a custom C++ TCP plugin paired with a Python MCP server, and `flopperam/unreal-engine-mcp` [12], which focuses on Blueprint and scene management. Our system differentiates itself by: (a) requiring **no custom C++ plugin** — relying solely on UE's built-in Remote Control Web Interface, (b) providing intelligent scene querying with noise filtering and mesh name resolution, (c) including a self-describing instruction system that prevents AI tool blindness, and (d) offering a material mapping and application subsystem.

### 2.5 Unreal Engine Remote Control

Unreal Engine's Remote Control API (introduced in UE 4.27) exposes editor subsystems via HTTP and WebSocket endpoints [13]. The API supports UFunction invocation (`/remote/object/call`), property access (`/remote/object/property`), and batch operations. Originally designed for broadcast production workflows (virtual LED sets, multi-camera rigs), we repurpose it as the transport layer for AI-driven scene authoring. The WebSocket transport provided by the `websockets` Python library [14] enables the low-latency, bidirectional communication required for real-time scene manipulation.

---

## 3. System Architecture

### 3.1 Overview

The Unreal-MCP system comprises four layers, each with a single responsibility:

```
┌──────────────────────────────────────────────────────┐
│                   AI Client Layer                     │
│    (VS Code Copilot / Cursor / Claude / Antigravity) │
└───────────────────────┬──────────────────────────────┘
                        │  MCP Protocol (stdio or SSE)
┌───────────────────────▼──────────────────────────────┐
│                   MCP Server Layer                    │
│    FastMCP instance + 17 registered tools             │
│    Self-describing instructions for AI guidance       │
│    Material/Asset/Class mapping subsystem             │
└───────────────────────┬──────────────────────────────┘
                        │  WebSocket (ws://127.0.0.1:30020)
┌───────────────────────▼──────────────────────────────┐
│                 Transport Layer                       │
│    5 transport functions (command, property,           │
│    get_property, console, execute_python)              │
└───────────────────────┬──────────────────────────────┘
                        │  Remote Control API
┌───────────────────────▼──────────────────────────────┐
│               Unreal Engine Editor                    │
│    EditorActorSubsystem, EditorLevelLibrary,          │
│    Python Interpreter, Console System                 │
└──────────────────────────────────────────────────────┘
```

### 3.2 MCP Server Layer

The server is implemented as a Python package (`unreal_mcp`) using the FastMCP library. The central design decision is the **self-describing instruction block** — a text payload embedded in the FastMCP constructor that is transmitted to every connecting AI client:

```python
mcp = FastMCP("UnrealMCP", instructions="""
You are connected to a LIVE Unreal Engine editor via MCP tools.
⚠️ DO NOT create, edit, or modify any files on the user's disk.
You work ENTIRELY through the MCP tools listed below.
🎨 SPAWNABLE SHAPES: cube, sphere, cylinder, cone, plane
🎨 MATERIALS: steel, chrome, gold, brick, wood, concrete...
""")
```

This instruction block solves the **Tool Blindness** problem identified in Section 1.1. Without it, AI models connected from an empty workspace directory would attempt to create Python scripts or modify local files. With it, models consistently use only the provided MCP tools.

### 3.3 Tool Registry

The 17 tools are organized into functional categories:

| Category | Tools | Plugin Required |
|----------|-------|----------------|
| Health | `check_connection` | None |
| Scene Intelligence | `get_scene_state`, `list_actors` | None |
| Spawning | `spawn_actor` | None |
| Modification | `modify_actor`, `destroy_actor`, `set_actor_scale` | None |
| Properties | `set_actor_property`, `get_actor_property` | None |
| Materials | `set_material`, `list_materials` | None |
| Scripting | `execute_python_in_editor` | Python Plugin |
| Discovery | `find_assets`, `import_asset`, `add_starter_content` | Python Plugin |
| Feedback | `capture_viewport` | Python Plugin |
| Console | `run_console_command` | Python Plugin |

A critical design principle is the **graceful degradation** of the tool set. The 10 core tools (Health through Materials) function using only the Remote Control WebSocket API with no additional UE plugins. The 7 advanced tools require the Python Editor Script Plugin, but their absence does not prevent basic operation.

### 3.4 Mapping Subsystem

Three mapping dictionaries translate friendly names to engine-specific paths:

- **Asset Map** (27 entries): `"cube"` → `"/Engine/BasicShapes/Cube.Cube"`, `"chair"` → `"/Game/StarterContent/Props/SM_Chair.SM_Chair"`
- **Class Map** (3 entries): `"pointlight"` → `"/Script/Engine.PointLight"`
- **Material Map** (24 entries): `"steel"` → `"/Game/StarterContent/Materials/M_Metal_Steel.M_Metal_Steel"`

This abstraction layer means the AI never needs to know Unreal Engine's internal path format. It simply says `spawn_actor("chair", 100, 0, 0)` and the mapping resolves the full asset reference.

### 3.5 Scene Intelligence (Level 2)

The `get_scene_state` tool implements a three-stage pipeline:

**Stage 1 — Classification:** Each actor returned by `GetAllLevelActors` is classified by name pattern matching into one of 15 recognized types (StaticMeshActor, PointLight, CineCameraActor, etc.) or marked as environment noise.

**Stage 2 — Noise Filtering:** Actors matching 11 noise prefixes (hlod, landscapestreamingproxy, worlddatastorage, navmeshboundsvolume, etc.) are separated into an `environment` section with aggregate counts, removing them from the primary actor list.

**Stage 3 — Enrichment:** For the first 80 actors, the system queries individual locations via `GetActorLocation` and resolves mesh names for StaticMeshActors by reading the `StaticMesh` property from `StaticMeshComponent0`.

The output is a structured JSON document with a natural-language summary:

```
"Scene has 164 actors: 27 static meshes (Cube, Sphere), 
 1 directional light, 1 Sky, 128 environment actors 
 (64 Landscape, 64 HLOD)."
```

### 3.6 Transport Layer

All communication with Unreal Engine passes through a single WebSocket connection module providing five transport functions. Each function opens a transient WebSocket connection, sends a JSON payload conforming to UE's Remote Control message format, and parses the response. The message format wraps HTTP semantics inside WebSocket frames:

```json
{
  "MessageName": "http",
  "Parameters": {
    "Url": "/remote/object/call",
    "Verb": "PUT",
    "Body": {
      "objectPath": "/Script/UnrealEd.Default__EditorActorSubsystem",
      "functionName": "GetAllLevelActors"
    }
  }
}
```

---

## 4. Zero-Setup Deployment

### 4.1 Packaging

The system is packaged as a standard Python package via `pyproject.toml` with a console script entry point:

```toml
[project.scripts]
unreal-mcp = "unreal_mcp.cli:main"
```

Installation requires a single command: `pip install .` (local) or `pip install unreal-mcp` (future PyPI). This registers the `unreal-mcp` command globally.

### 4.2 Transport Modes

The CLI supports two transport modes:

- **stdio** (recommended for IDEs): The IDE launches the MCP server as a child process, communicating via stdin/stdout. Zero network configuration needed.
- **SSE** (for manual operation): The server binds to a configurable host:port with automatic fallback — if port 8000 is occupied, it automatically tries 8001, 8002, etc.

### 4.3 IDE Integration

A single JSON configuration block connects any MCP-compatible IDE:

```json
{
  "mcp.servers": {
    "unreal-engine": {
      "command": "unreal-mcp",
      "args": ["--stdio"]
    }
  }
}
```

This achieves the **two-minute setup** target: `pip install .` (60 seconds) + paste config (30 seconds) + restart IDE (30 seconds).

---

## 5. Experiments and Results

### 5.1 Experimental Setup

All experiments were conducted on the following configuration:

| Component | Specification |
|-----------|--------------|
| OS | Windows 10/11 |
| Engine | Unreal Engine 5.6.1 |
| Python | 3.10+ (Anaconda) |
| MCP Library | FastMCP (latest) |
| Transport | WebSocket on port 30020 |
| Test Scene | Default landscape with sky, fog, and lighting |

### 5.2 Experiment 1: Health Check Pipeline Validation

The `check_connection` tool was tested against four configurations:

| Configuration | MCP | WebSocket | Remote Control | Python Plugin | Status |
|--------------|-----|-----------|---------------|---------------|--------|
| Full stack | ✅ | ✅ | ✅ | ✅ | READY |
| No Python plugin | ✅ | ✅ | ✅ | ⚠️ | READY (degraded) |
| UE not running | ✅ | ❌ | ❌ | ❌ | NOT READY |
| Wrong port | ✅ | ❌ | ❌ | ❌ | NOT READY |

The tool correctly identified each failure mode and produced actionable fix instructions specific to the detected problem. Response time was under 2 seconds in all configurations.

### 5.3 Experiment 2: Scene Intelligence Accuracy

The scene query system was tested on a level containing 164 actors (27 user-placed static meshes, 1 directional light, 1 sky system, and 128 environment actors):

| Metric | Raw API | Scene Intelligence L2 |
|--------|---------|----------------------|
| Actors returned | 164 (all) | 36 (user-placed only) |
| Noise filtered | 0 | 128 (64 HLOD + 64 Landscape) |
| Mesh names resolved | 0 | 27/27 (100%) |
| Summary provided | No | Yes (natural language) |
| Response format | Raw paths | Structured JSON with types |

The noise filtering correctly identified all 128 HLOD and LandscapeStreamingProxy actors, while the mesh resolution successfully extracted friendly names ("Cube", "Sphere") for all 27 StaticMeshActors.

### 5.4 Experiment 3: Howrah Bridge Construction

The primary validation experiment involved the procedural construction of a Howrah Bridge — a 705-meter balanced cantilever truss bridge in Kolkata, India — using only the MCP tools.

**Construction Parameters:**

| Parameter | Value |
|-----------|-------|
| Bridge span | 150m (15,000 UU) |
| Tower height | 45m (4,500 UU) |
| Road width | 20m (2,000 UU) |
| Deck elevation | 8m (800 UU) |

**Structural Breakdown:**

| Component | Actor Count | Description |
|-----------|-------------|-------------|
| River surface | 1 | Scaled plane (300×80 UU) |
| Main deck | 1 | Scaled cube (150×20×0.5) |
| Under-deck girders | 20 | Transverse support beams |
| Tower pylons | 4 towers × (4 legs + 15×3 braces) | Lattice structure per pylon |
| Top chord segments | ~40 | Parabolic upper beam |
| Vertical struts | ~82 | Variable height (parabolic profile) |
| Diagonal bracing | ~48 | Cross-bracing on both sides |
| Railing bars | ~300 | Individual bars on both deck edges |
| Approach ramps | 2 | Road extensions |
| Point lights | 24 | Deck (gold), tower (cyan), peak (magenta) |
| **Total** | **~850** | |

**Construction Performance:**

| Metric | Value |
|--------|-------|
| Total actors spawned | 850+ |
| Total modify_actor calls | 800+ (for scaling) |
| Total execution time | ~4 minutes |
| Throughput | ~3.5 actors/second |
| Failures | 0 spawn failures |
| Post-construction scene query | Correctly reports all new actors |

**Key Observations:**

1. **Parabolic Profile Fidelity:** The vertical strut heights followed the formula `h = 500 + TOWER_HEIGHT × (d/d_max)²`, producing the characteristic Howrah Bridge silhouette where struts are tallest at the towers and shortest at the center span.

2. **Batch Scalability:** The 850-actor construction completed without WebSocket timeouts, demonstrating that the transient-connection-per-call model (rather than a persistent connection) provides reliable throughput for large-scale operations.

3. **RGB Lighting System:** Three distinct light colors (gold for deck illumination, cyan for tower highlighting, magenta for peak markers) were applied using the `set_actor_property` tool to set `LightColor` and `Intensity` properties, demonstrating the property system's versatility.

### 5.5 Experiment 4: Self-Describing Server Validation

To test the **Tool Blindness** fix, the MCP server was connected from an empty workspace directory (not the Unreal-MCP source directory). Without the `instructions` field, the AI model attempted to create local files (e.g., `bridge_builder.py`, `modify.js`). With the instructions field enabled, the model exclusively used MCP tools across 20 consecutive interaction turns, with zero file-creation attempts.

---

## 6. Discussion

### 6.1 Limitations

**Deletion Reliability.** The `destroy_actor` tool currently uses `K2_DestroyActor`, which is the runtime destruction method on AActor. While this works for dynamically spawned actors, it may not persist across editor save/load cycles for actors with static mobility. A more robust approach would use the EditorActorSubsystem's `DestroyActors` batch method, pending Remote Control API support for actor reference parameters.

**Material Availability.** The 24-material mapping depends on Starter Content being present in the user's project. Projects created without Starter Content will receive clear error messages, but the fallback of creating dynamic material instances at runtime is not yet implemented.

**Python Plugin Dependency.** Seven of seventeen tools require the Python Editor Script Plugin and Remote Console Execution to be enabled. These are advanced features and the system degrades gracefully, but the most powerful capabilities (viewport capture, asset import, arbitrary scripting) are gated behind this requirement.

**Throughput Ceiling.** At ~3.5 actors/second, constructing very large scenes (10,000+ actors) would take approximately 45 minutes. Batch spawning APIs and persistent WebSocket connections could improve this by an estimated 5-10×.

### 6.2 Design Decisions

**Transient vs. Persistent WebSocket Connections.** We chose transient connections (open-send-receive-close per call) over persistent connections. While this sacrifices throughput, it provides two critical advantages: (a) no connection state management or reconnection logic, and (b) natural serialization of commands, preventing race conditions in the editor's transaction system.

**Friendly Name Abstraction.** Rather than exposing raw Unreal Engine paths to AI models, we maintain mapping dictionaries. This design allows the AI to operate at a semantic level ("spawn a steel chair") while the mapping layer handles engine-specific path resolution. The abstraction is one-directional by design — the AI never needs to learn UE's path format.

---

## 7. Future Work

### 7.1 Near-Term Extensions

- **Dynamic Material Creation:** Generate colored materials at runtime using `ConstructObject` and property setters, removing the Starter Content dependency.
- **Asset Import Pipeline:** Enable importing FBX/OBJ/PNG files from disk into the UE Content Browser via `AssetToolsHelpers`.
- **Viewport Capture Integration:** Establish a visual feedback loop where the AI captures screenshots, analyzes them via vision models, and iteratively refines the scene.

### 7.2 Medium-Term Research Directions

- **Hierarchical Scene Decomposition:** For scenes exceeding LLM context windows, implement an orchestrator that breaks complex requests into spatial sub-tasks, each handled independently.
- **Persistent Memory:** Maintain a spatial index of constructed elements across sessions, enabling long-running world-building projects that span multiple conversations.
- **Multi-Agent Collaboration:** Deploy specialized agents (architect, lighting designer, landscape artist) that collaborate through shared scene state.

### 7.3 Long-Term Vision

- **Real-Time Collaborative Editing:** Multiple AI agents and human designers working simultaneously in the same Unreal Engine session, with conflict resolution and intent negotiation.
- **Learned Construction Heuristics:** Fine-tuning construction strategies based on user feedback, developing models that learn architectural style preferences from past interactions.
- **Cross-Engine Portability:** Extending the MCP tool interface to Unity, Godot, and Blender, enabling a single AI assistant to operate across multiple 3D authoring platforms.

---

## 8. Conclusion

We have presented Unreal-MCP, a zero-setup framework that bridges Large Language Models and Unreal Engine 5 through the Model Context Protocol. Our system demonstrates that complex 3D scenes — including an 850-actor structural bridge with parabolic truss geometry, multi-color lighting, and approach infrastructure — can be constructed entirely through natural language interaction with an AI agent, without any manual actor placement.

The key technical contributions — self-describing tool registries, intelligent scene noise filtering, friendly-name material mapping, and multi-link health diagnostics — address fundamental usability barriers that have previously limited AI-assisted 3D content creation to expert users with deep engine knowledge.

By reducing setup time from hours to under two minutes and ensuring the AI operates exclusively through structured tool calls rather than ad-hoc scripting, we establish a practical foundation for AI-driven 3D world construction that is accessible to researchers, developers, and creative professionals alike.

---

## References

1. B. Poole, A. Jain, J. T. Barron, and B. Mildenhall, "DreamFusion: Text-to-3D using 2D Diffusion," in *Proc. ICLR*, Kigali, Rwanda, 2023. https://arxiv.org/abs/2209.14988
2. C.-H. Lin, J. Gao, L. Tang, T. Takikawa, X. Zeng, X. Huang, K. Kreis, S. Fidler, M.-Y. Liu, and T.-Y. Lin, "Magic3D: High-Resolution Text-to-3D Content Creation," in *Proc. IEEE/CVF CVPR*, Vancouver, Canada, 2023, pp. 300–309.
3. J. Li, H. Tan, K. Zhang, Z. Xu, F. Luan, Y. Xu, Y. Hong, K. Sunkavalli, G. Shakhnarovich, and S. Bi, "Instant3D: Fast Text-to-3D with Sparse-View Generation and Large Reconstruction Model," in *Proc. ICLR*, Vienna, Austria, 2024. https://openreview.net/forum?id=2lDQLiH1W4
4. W. Feng, W. Zhu, T.-J. Fu, V. Jampani, A. Akula, X. He, S. Basu, X. E. Wang, and W. Y. Wang, "LayoutGPT: Compositional Visual Planning and Generation with Large Language Models," in *Proc. NeurIPS*, vol. 36, New Orleans, USA, 2024. https://arxiv.org/abs/2305.15393
5. X. Wang, Y. Yeshwanth, and M. Nießner, "SceneFormer: Indoor Scene Generation with Transformers," in *Proc. Int. Conf. 3D Vision (3DV)*, London, UK, 2021, pp. 106–115. doi: 10.1109/3DV53792.2021.00021
6. Y. Yang, Z. Yang, L. Fan, and Y. Zhu, "Holodeck: Language Guided Generation of 3D Embodied AI Environments," in *Proc. IEEE/CVF CVPR*, Seattle, USA, 2024, pp. 16227–16237.
7. C. Sun, S. Han, W. Deng, Z. Zhao, C. Qin, and L. Zhang, "3D-GPT: Procedural 3D Modeling with Large Language Models," in *Proc. AAAI*, vol. 38, no. 5, 2024, pp. 4922–4930. https://arxiv.org/abs/2310.12945
8. Anthropic, "Model Context Protocol Specification, v1.0," Nov. 2024. https://modelcontextprotocol.io/specification
9. Model Context Protocol Contributors, "MCP Python SDK," GitHub, 2024. https://github.com/modelcontextprotocol/python-sdk
10. J. Lowin and PrefectHQ, "FastMCP: The Fast, Pythonic Way to Build MCP Servers and Clients," GitHub, 2025. https://github.com/jlowin/fastmcp
11. D. Chu, "unreal-mcp: Model Context Protocol Server for Unreal Engine," GitHub, 2024. https://github.com/chongdashu/unreal-mcp
12. Flopperam, "unreal-engine-mcp: MCP Server for Unreal Engine Blueprint and Scene Management," GitHub, 2025. https://github.com/flopperam/unreal-engine-mcp
13. Epic Games, "Remote Control API," Unreal Engine Documentation, 2024. https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-for-unreal-engine
14. A. Augustin, "websockets: A Library for Building WebSocket Servers and Clients in Python," GitHub, 2024. https://github.com/python-websockets/websockets

---

## Appendix A: Complete Tool Reference

| # | Tool | Parameters | Returns |
|---|------|-----------|---------|
| 1 | `check_connection` | — | Status board (✅/❌) |
| 2 | `get_scene_state` | filter_type, detail, near_x/y/z, radius | JSON summary |
| 3 | `list_actors` | — | Raw actor list |
| 4 | `spawn_actor` | actor_class_or_asset, x, y, z, rotation | Actor path |
| 5 | `modify_actor` | actor_path, location, rotation, scale | Confirmation |
| 6 | `destroy_actor` | actor_path | Confirmation |
| 7 | `set_actor_scale` | actor_path, scale_x/y/z | Confirmation |
| 8 | `set_actor_property` | actor_path, property_name, property_value | Confirmation |
| 9 | `get_actor_property` | actor_path, property_name | Property value |
| 10 | `set_material` | actor_path, material, slot_index | Confirmation |
| 11 | `list_materials` | — | Categorized material list |
| 12 | `execute_python_in_editor` | script, timeout | Script output |
| 13 | `find_assets` | search_path, asset_type, name_filter | Asset list |
| 14 | `import_asset` | file_path, destination | Content path |
| 15 | `add_starter_content` | — | Status message |
| 16 | `capture_viewport` | filename, resolution_x/y | File path |
| 17 | `run_console_command` | command | Confirmation |

## Appendix B: Required Unreal Engine Plugins

| Plugin Name (exact) | Where to Enable | Required For |
|---------------------|-----------------|-------------|
| Remote Control API | Edit → Plugins → "Remote Control API" | All tools (core) |
| Remote Control Web Interface | Edit → Plugins → "Web Remote Control" | All tools (core) |
| Editor Scripting Utilities | Edit → Plugins → "Editor Scripting Utilities" | Spawn/Modify tools |
| Python Editor Script Plugin | Edit → Plugins → "Python Editor Script Plugin" | Advanced tools (7-17) |

**Project Setting (for advanced tools):**
Edit → Project Settings → Plugins → Remote Control → ☑ Allow Remote Console Execution
