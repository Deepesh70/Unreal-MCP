# Unreal-MCP

[![Unreal-MCP Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/Deepesh70/Unreal-MCP)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.0%20to%205.8+-black?logo=unrealengine)](https://www.unrealengine.com/)
[![Python](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12%20|%203.13-blue?logo=python)](https://python.org)
[![Protocol](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol%20(MCP)-orange)](https://modelcontextprotocol.io)
[![FastMCP](https://img.shields.io/badge/FastMCP-Supported-orange)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Natural Language to 3D Virtual Worlds in Real-Time.**  
> Unreal-MCP connects Large Language Models (ChatGPT, Gemini, Claude, Llama) directly to **Unreal Engine 5** via Anthropic's **Model Context Protocol (MCP)**. You type what you want to build, and Unreal Engine renders it live in your viewport with zero manual placement.

---

## 🌟 Key Highlights

* 🗣️ **Natural Language Scene Authoring**: Build, modify, query, inspect, and style 3D environments live using natural language.
* ⚡ **C++ Delegator Engine (HISM)**: Features `AProceduralCityManager` inside Unreal Engine using Hierarchical Instanced Static Meshes (HISM) for massive draw-call reduction, auto-nudge obstacle avoidance, and ground height raycasting.
* 🛠️ **32 Specialized MCP Tools**: Complete toolset covering scene querying, actor transformation, in-editor Python scripting, property inspection, material styling, console commands, viewport screenshots, and C++ class codegen.
* 🎮 **Omnichannel Engine Support**:
  * **UE 5.0 – 5.6+**: Works seamlessly via Unreal Engine's built-in Web Remote Control API WebSocket.
  * **UE 5.8+ (Official MCP)**: Fully compatible with Epic Games' newly introduced in-editor `ModelContextProtocol` plugin and `Toolset Registry`.
* 🤖 **Model-Agnostic Agent Pipeline**: Native support for **Groq Cloud** (Llama 3.3 70B), **Google Gemini** (Gemini 2.5 Pro), and **Ollama** (local GPU inference).
* 🧩 **Token-Aware Spatial Orchestration**: Automatically breaks massive city/district prompts into spatial zones (`northern section`, `central area`) with token budgeting to prevent truncation.

---

## 🏗️ Architecture

```
                 ┌──────────────────────────────────────────────┐
                 │     AI Brain (Groq / Gemini / Ollama)        │
                 │   or AI IDE (Cursor / Claude Code / VS Code) │
                 └──────────────────────┬───────────────────────┘
                                        │ (MCP Protocol: SSE / stdio)
                                        ▼
                 ┌──────────────────────────────────────────────┐
                 │        Unreal-MCP Gateway (FastMCP)          │
                 │   • 32 Tools Registry     • Toolset Search   │
                 │   • Schema Validation     • Token Budgeting  │
                 └──────────────┬───────────────────────────────┘
                                │ WebSocket (ws://127.0.0.1:30020)
                                ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           Unreal Engine 5 Editor                            │
 │                                                                             │
 │  ┌─────────────────────────┐               ┌──────────────────────────────┐ │
 │  │ Web Remote Control API  │ ────────────> │   AProceduralCityManager     │ │
 │  │ (Built-in Plugin)       │               │   • HISM Instance Pools      │ │
 │  └─────────────────────────┘               │   • Ground Tracing & Nudge   │ │
 │                                            │   • Swap-and-Pop Ledger      │ │
 │  ┌─────────────────────────┐               └──────────────────────────────┘ │
 │  │ Python Editor Subsystem │                                                │
 │  └─────────────────────────┘                                                │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

The codebase is organized according to production open-source software engineering standards:

```text
Unreal-MCP/
├── unreal_mcp/                 # 📦 Canonical Python Package
│   ├── core/                   # Engine config, logging, and connection protocols
│   ├── server/                 # FastMCP server runtime & transport layer
│   ├── api/                    # FastAPI WebSocket server & IDE bridge
│   ├── agents/                 # Multi-agent generative system (Builder, Vision, RAG)
│   ├── tools/                  # 32+ registered Unreal MCP tools
│   ├── codegen/                # C++ class generator & Jinja2 templates
│   └── cli.py                  # Unified CLI: serve, agent, api, bridge
│
├── docs/                       # 📚 Diátaxis Documentation Hierarchy
│   ├── getting_started/        # Installation, UE plugin setup, IDE configuration
│   ├── architecture/           # System overview, WebSocket bridge, SaaS relay
│   ├── guides/                 # Combat, retargeting, codegen, web UI integration
│   ├── reference/              # Complete tool dictionary and asset schemas
│   ├── research/               # Academic papers & LaTeX sources
│   └── interview/              # Technical masterclass & system design defenses
│
├── examples/                   # 💡 Cookbooks, Demos & Blueprints
│   ├── demos/                  # Standalone runnable scene authoring demos
│   ├── recipes/                # Animation, combat, and building automation recipes
│   └── blueprints/             # Reference architectural blueprint markdown files
│
├── scripts/                    # 🛠️ Automation & Packaging Scripts
│   ├── setup_unreal.py         # In-engine setup helper
│   ├── setup_materials.py      # Starter material library generator
│   └── build_relay.py          # Standalone relay packaging script
│
├── generated/                  # ⚙️ Generated C++ Procedural City engine
├── tests/                      # 🧪 Test Suite (Imports, CLI, Tools, Codegen)
└── pyproject.toml              # 📄 Modern Python build configuration & dependencies
```

> 📖 **Full Documentation**: Explore the indexed guides and technical deep-dives in **[docs/README.md](docs/README.md)**.

---

## 🚀 Full Setup Guide

Follow these step-by-step instructions to run Unreal-MCP on any windows.(heven't tested on any other OS)

### Prerequisites

1. **Unreal Engine 5.0 or later** installed (UE 5.2, 5.3, 5.4, 5.5, or 5.8 preview).
2. **Python 3.10 to 3.13** installed on your system.
3. An active Unreal Engine project (or a fresh Third Person / Blank template).

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Deepesh70/Unreal-MCP.git
cd Unreal-MCP
```

---

### Step 2: Set Up Python Virtual Environment

```bash
# Windows (PowerShell / Command Prompt)
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables (`.env`)

Copy the template file to `.env`:
```bash
cp .env.example .env
```

Open `.env` and add the API key for whichever model provider you prefer:
```ini
# Choose at least ONE of the following:
GROQ_API_KEY=gsk_your_groq_api_key_here
GOOGLE_API_KEY=AIzaSy_your_gemini_key_here

# Or if using local Ollama, no key is needed (ensure Ollama is running):
# OLLAMA_BASE_URL=http://localhost:11434

# WebSocket connection to Unreal Engine (default is localhost)
UE_WS_URL=ws://127.0.0.1:30020
```

---

### Step 4: Configure Unreal Engine Plugins

Open your project in Unreal Editor and enable the required built-in plugins:

1. In Unreal Editor, go to **Edit → Plugins**.
2. Search and **Enable** the following plugins:
   * ✅ **Remote Control API** (`WebRemoteControl`)
   * ✅ **Python Editor Scripting Plugin**
   * ✅ **Geometry Scripting** (optional, recommended for procedural meshes)
   * **RESTART ENGINE AFTER ENABLING THE ABOVE PLUGINS**
3. Go to **Edit → Project Settings**, search for `Remote Control`, and ensure:
   * ✅ **Enable Remote Web Server** is checked (defaults to port `30010` HTTP and `30020` WebSocket).
   * ✅ **Allow Remote Console Execution** is checked (allows Python scripting and console commands).
4. Restart Unreal Editor when prompted.

---

### Step 5: One-Click C++ Integration (Recommended for High Performance)

Unreal-MCP includes an automated integration script that locates your `.uproject`, copies the optimized C++ procedural manager into your project's `Source/` directory, and patches your `Build.cs`:

```bash
python setup_unreal.py
```
*(Or specify your project path directly: `python setup_unreal.py "C:\Path\To\MyProject.uproject"`)*

**What this does automatically:**
* Copies `ProceduralBuildingTypes.h`, `ProceduralCityManager.h`, and `ProceduralCityManager.cpp` into your C++ source folder.
* Deploys `procedural_toolset.py` into `Content/Python/toolset_registry/` for Epic UE 5.8 Toolset Registry discovery.
* Patches your project's `Build.cs` to include `Json`, `JsonUtilities`, and `GeometryScriptingCore`.
* Sets your `PROJECT_API` macro in `.env`.

> 💡 **Don't have a C++ project?** No problem! Unreal-MCP automatically falls back to direct actor spawning via WebSocket even if you use a purely Blueprint project.

---

### Step 6: Initialize Materials (Optional, 1-Click)

With your Unreal Editor open, run:
```bash
python setup_materials.py
```
This automatically sets up 24 material color presets (`wood`, `concrete`, `gold`, `glass`, `cyan`, etc.) in `/Game/Materials/Colors/` for realistic architectural styling.

---

## 🎮 How to Run

### Option A: Quick Verification (No API Keys Needed!)

Test that your Unreal Engine WebSocket connection is functioning without consuming any LLM tokens:

```bash
# Spawns an impressive procedural house with doors, roof, chimney, and lights:
python demo_house.py

# Spawns a spiral tower with spotlights and orbiting spheres:
python demo_complex.py
```
Watch your Unreal Engine viewport — objects will appear instantly!

---

### Option B: Interactive AI Builder Agent

Run the AI Builder pipeline with natural language input:

```bash
# Using Groq Cloud (Llama 3.3 70B — extremely fast):
python agent.py groq -b -i

# Using Google Gemini (Gemini 2.5 Pro):
python agent.py gemini -b -i

# Using Local Ollama:
python agent.py ollama -b -i
```

Once inside the interactive builder prompt, simply type commands:
```text
🏗️ Builder > build a 3-story modern house at the origin with a pointed roof
🏗️ Builder > build a futuristic car with blue body and cyan cabin next to it
🏗️ Builder > build a medieval village with 10 houses and stone pathways
🏗️ Builder > clear everything
```

---

### Option C: Run the Standalone FastMCP Server

If you want to use Unreal-MCP with AI IDEs or other MCP clients:

```bash
# Start the MCP server over SSE (default port 8000, auto-fallback to 8001 if occupied):
python server.py

# Or run in stdio mode (for IDE auto-spawning):
python server.py --stdio
```

---

### Option D: Target Epic Games Official Unreal MCP (UE 5.8+)

If you are using Unreal Engine 5.8+ with Epic's official `ModelContextProtocol` plugin enabled:

1. In Unreal Editor console, start Epic's server:
   ```text
   ModelContextProtocol.StartServer
   ```
2. Launch our agent targeting Epic's official in-editor endpoint:
   ```bash
   python agent.py groq --epic -i
   ```

---

## 🔌 Connecting to AI IDEs (Antigravity ,Cursor, VS Code, Claude Code)

Add Unreal-MCP to your IDE configuration file so your AI assistant can drive Unreal Engine directly.

### Cursor / VS Code (`.mcp.json` or `claude_desktop_config.json`)

#### Method 1: Stdio Mode (Recommended — Auto-Starts with IDE)
```json
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "python",
      "args": ["C:/Users/YourName/Desktop/Unreal-MCP/server.py", "--stdio"],
      "env": {
        "UE_WS_URL": "ws://127.0.0.1:30020"
      }
    }
  }
}
```

#### Method 2: SSE Mode (Connect to Running Server)
```json
{
  "mcpServers": {
    "unreal-mcp": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

---

## 🛠️ MCP Tools Overview (33 Registered Tools)

| Category | Tools | Description |
| :--- | :--- | :--- |
| **Discovery** | `list_toolsets`, `describe_toolset` | Low-token discovery matching Epic's Toolset Search pattern. |
| **Scene Observation** | `get_scene_state`, `get_scene_summary`, `list_actors` | Query level actors with automatic HLOD/noise filtering. |
| **Actor Manipulation** | `spawn_actor`, `spawn_actors_batch`, `modify_actor`, `destroy_actor`, `set_actor_scale`, `set_actor_rotation`, `set_actor_location` | Create individual or batched actors with location, rotation, and scale; translate, rotate, or remove actors live in viewport. |
| **Materials & Appearance** | `set_material`, `list_materials` | Apply friendly material presets (`wood`, `concrete`, `gold`, `glass`, etc.). |
| **Editor Scripting** | `execute_python_in_editor`, `run_console_command` | Execute arbitrary Unreal Python code and console commands live in editor. |
| **Properties & Mesh** | `get_actor_property`, `set_actor_property`, `list_mesh_settings`, `set_mesh_settings`, `sync_mesh_settings` | Inspect and edit low-level reflection and mesh component properties (with automatic `SetLightColor` support for lights). |
| **Assets & Content** | `find_assets`, `import_asset`, `add_starter_content` | Search Content Browser, import FBX/textures, or add Starter Content. |
| **Viewport & Diagnostics** | `capture_viewport`, `check_connection` | Save high-res screenshots for vision models; test multi-link health. |
| **C++ Code Generation** | `generate_ue_class`, `preview_ue_class`, `get_project_info`, `list_project_files`, `list_supported_types` | Generate, preview, and write compile-ready Unreal C++ classes. |

---

## 🔬 Academic Research & Validation

The framework and its procedural delegator architecture are formally documented in our research paper:  
📖 **[Bridging Natural Language and 3D World Construction: A Zero-Setup MCP Framework for AI-Driven Unreal Engine Scene Authoring](docs/research/research_paper.md)**  
*(LaTeX source available in [docs/research/research_paper.tex](docs/research/research_paper.tex))*

Includes an empirical validation study constructing an 850+ actor structurally accurate Howrah Bridge replica completely through AI-tool interaction.

---

## ❓ Troubleshooting & FAQ

<details>
<summary><b>1. "Unreal Engine connection failed (ws://127.0.0.1:30020)"</b></summary>

* Make sure Unreal Engine is open.
* Verify that the **Remote Control API** (`WebRemoteControl`) plugin is enabled (**Edit → Plugins**).
* In **Project Settings → Remote Control**, ensure **Enable Remote Web Server** is checked.
* Test directly in terminal: `python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://127.0.0.1:30020'))"`
</details>

<details>
<summary><b>2. "Port 8000 is in use"</b></summary>

* If Epic's official MCP server (UE 5.8+) or another web server is on port 8000, Unreal-MCP automatically shifts to port **8001**.
* You can also specify any custom port: `python server.py --port 9000` or set `SERVER_PORT=8001` in your `.env`.
</details>

<details>
<summary><b>3. "Remote console execution is disabled in Unreal Engine"</b></summary>

* Go to **Edit → Project Settings → search "Remote Control"**.
* Check **Allow Remote Console Execution**.
</details>

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
