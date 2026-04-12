# 🚀 Unreal Editor Model Context Protocol (MCP) Agent

Welcome to the **Unreal MCP Agent**! This repository provides an essential bridge between Large Language Models (LLMs) and **Unreal Engine 5**. By integrating the Model Context Protocol (MCP) with Unreal Engine's Remote Control API, this powerful tool allows AI agents to dynamically build scenes, automate workflows, and write C++ code inside your Unreal project using natural language prompts.

Whether you're looking for a virtual assistant to automatically populate environments or automate complex C++ entity generation, the Unreal MCP Agent orchestrates it all.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Pros and Cons](#-pros-and-cons)
- [Tech Stack & Tools](#-tech-stack--tools)
- [Core Workflows](#-core-workflows)
- [Architecture & Tools](#-architecture--tools)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Troubleshooting](#-troubleshooting)
- [Security](#-security)

---

## 🌟 Overview

The Unreal MCP Agent empowers you to command your Unreal Engine environment directly through LLM reasoning. At its core, the system runs an MCP server that exposes tools to interact with Unreal Engine. You can interact with it via an agent CLI, a classic tool-calling mode, or through the **UnrealUI** web application.

### Who is this for?
- **Technical Artists & Level Designers** who want to rapid-prototype scenes.
- **Gameplay Programmers** seeking to automate boilerplate C++ generation.
- **AI Tooling Enthusiasts** wanting to integrate LLM logic into existing game engines.

---

## ⚖️ Pros and Cons

### **Pros**
✅ **Accelerated Prototyping:** Build scenes and generate foundational C++ classes rapidly simply by describing what you want.
✅ **Seamless Integration:** Uses standard Unreal Engine APIs (Remote Control Plugin) without needing custom engine forks or heavy plugins.
✅ **Extensible AI Pipelines:** Easily pluggable LangChain agents support various backends: Groq, Gemini, or even a local Ollama model for offline privacy.
✅ **Live Web Interface:** Comes with `UnrealUI`, a chat-based frontend that streams real-time execution data natively.
✅ **Advanced Orchestration:** Features sophisticated safety guardrails like multi-phase code generation, dry-runs, and token budget management based on scene scale. 

### **Cons**
❌ **Experimental/Fragile Workflows:** Heavily relies on the LLM's reliability. Complex prompts might result in incorrect scaling or hallucinated Unreal properties.
❌ **Live Coding Quirks:** The two-stage C++ generation sometimes requires the Unreal Editor to be closed to ensure clean headless compiles, interrupting the creative flow briefly.
❌ **Performance Overhead:** Depending on the LLM backend (e.g., local Ollama), generation latency can take a few moments for complex logic. 
❌ **Network/Socket Dependencies:** Prone to connectivity limits if the Remote Control WebSocket behaves unexpectedly or ports conflict.

---

## 🛠️ Tech Stack & Tools

This system leverages cutting-edge open-source tools:

- **Language:** Python 3.10+
- **Agent Orchestration:** `langchain` suite (Core, adapters, Chroma for Vector DB).
- **Supported LLMs:** 
  - `langchain_groq` (Fast Llama 3 models in the cloud).
  - `langchain_google_genai` (Google Gemini 2.5 Pro / Flash).
  - `langchain_ollama` (Local execution for LLMs).
- **Communication Protocols:** 
  - `fastmcp` (Model Context Protocol for robust tool definitions).
  - `websockets` & `httpx` (Integration with Unreal Engine Remote Control WebSocket).
- **Web Bridge:** `FastAPI` + `Uvicorn` for serving the connection between the Agent and the external UnrealUI Next.js frontend.
- **Code Generation:** `Pydantic` for schema validation and `Jinja2` for generating clean `.h` and `.cpp` Unreal C++ classes. 

---

## 🔄 Core Workflows

This system provides three distinct production pipelines to automate your engine tasks:

### 1. 🏗️ Live Builder (`--build`)
Directly edits an open Unreal Editor scene. The LLM queries the scene context, generates an action plan (spawn, scale, rotate, update mesh settings), and sanitizes operations to place assets beautifully within your map.

### 2. 💻 Two-Phase C++ Pipeline (`--two-phase`)
An offline workflow. It refines your prompt to create functional Unreal C++ architectures. It:
1. Preflights compile checks.
2. Validates JSON schemas and topological dependency order.
3. Renders `.h`/`.cpp` using Jinja templates.
4. Auto-compiles the project headless and uses compiler feedback on failure.

### 3. 🤖 Orchestrator Pipeline (`--orchestrate`)
The holy grail. If your request involves generating *new code* and *placing* it in the scene:
1. Safely triggers a Live Coding compile if the editor is open (or closes it if needed).
2. Generates and compiles C++.
3. Relaunches Unreal Editor.
4. Automatically Spawns the newly compiled classes directly into your scene. 

---

## 🧬 Architecture & Tools 

At runtime, the MCP server exposes precise **Tools** the LLMs utilize to see and alter the engine state:
- **Scene Exploration:** `list_actors()`, `get_scene_summary()`
- **Transformations:** `spawn_actor()`, `set_actor_scale()`, `set_actor_location()`, `set_actor_rotation()`
- **Mesh Manipulation:** `list_mesh_settings()`, `sync_mesh_settings()`, `validate_mesh_settings()`
- **Code Assistance:** `get_project_info()`, `list_project_files()`, `generate_ue_class()`

**Transport** utilizes the existing `/remote/object/describe` and related HTTP endpoints natively provided by Unreal. 

---

## 📋 Prerequisites

Before setting up, ensure you have the following ready:

1. **Python 3.10+**
2. **Unreal Engine 5** project running on your machine.
3. **Plugins enabled in Unreal** (Edit > Plugins):
   - **Remote Control API**
   - **Remote Control Web Interface**
   *(Note: Ensure the websocket defaults to `ws://127.0.0.1:30020`)*
4. API keys from **Groq**, **Google (Gemini)**, or an active **Ollama** server.

---

## 💾 Installation

Clone this repository and run:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your essential details:

```ini
# --- CORE AI PROVIDERS ---
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_gemini_key_here
OLLAMA_BASE_URL=http://localhost:11434 # Optional

# --- BUILDER SETTINGS ---
BUILD_TOKEN_MODE=balanced
BUILD_ENABLE_PLAN_REVIEW=true

# --- ORCHESTRATOR SETTINGS ---
ORCH_ENABLE_LIVE_CODING=true
ORCH_EDITOR_CLOSE_TIMEOUT_SEC=45
```

Inside `unreal_mcp/config/settings.py`, you can also configure your specific Unreal **Project paths**, **Engine versions**, and **Remote Control addresses**.

---

## 🎮 Usage Guide

### 1. Launching the MCP Server
To just run the backend tool server:
```bash
python server.py
```

### 2. Using the Agent CLI
Interact directly with the agent through Python using various backends (`groq`, `ollama`, `gemini`).

Syntax:
```bash
python agent.py <backend> [mode] [options]
```

**Examples:**
- **Spawn basic shapes natively:**
  `python agent.py groq --build --prompt "spawn 3 cubes at origin"`
- **Create and Compile a C++ Actor:**
  `python agent.py groq --two-phase --prompt "Create a WeatherController actor"`
- **The full Orchestration Flow:**
  `python agent.py groq --orchestrate --prompt "Create a C++ LaserTrap and place 3 of them in my scene"`
- **Testing connectivity:**
  `python agent.py gemini --test`

*(Options like `--dry-run` and `--interactive (-i)` are also supported).*

### 3. Launching UnrealUI (Web Interface)
UnrealUI offers a sleek chat experience outside the terminal.

1. **Start the FastAPI Bridge**
```bash
uvicorn api_server:app --port 8080
```
2. **Start the Frontend**
Open a new terminal navigate to your web app folder (e.g. your Next.js directory), and hit:
```bash
npm run dev
```
The FastAPI bridge server automatically tests Unreal Engine connectivity prior to resolving standard commands.

---

## 🚨 Troubleshooting

- **"Prompt missing error" in CLI:** If you execute the agent without `-i`, you must supply a prompt via `--prompt`. 
- **Two-phase preflight fails:** Ensure your paths in `unreal_mcp/config/settings.py` (like `UE_PROJECT_ROOT`, `UE_BATCH_FILES_PATH`) accurately point to your disk locations. Also, verify that Unreal Editor is fully closed.
- **Classes are generated but not seen in UE Content Browser:** Rebuild your C++ project via your IDE or Unreal Editor's Compile button, and confirm files are truly in `Source/<UE_PROJECT_NAME>/`.
- **Live builder fails to connect:** Ensure you checked the box to enable remote web servers in your Unreal Engine project settings and that no firewall is blocking `30020` or `30010`.

---

## 🔒 Security 

- **Do not commit API tokens!** (`.env` is safely within `.gitignore`).
- This server interacts directly with your filesystem to write C++ code and automate batch processes. Do not expose your local fastapi interface (`0.0.0.0`) publicly over the internet without proper authentication middleware.

---
*Happy Building! 🎮✨*
