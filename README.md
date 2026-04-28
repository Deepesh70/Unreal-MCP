# Unreal MCP Agent

Connect LLM agents to Unreal Engine through the Model Context Protocol. Give natural-language commands to spawn actors, build scenes, and generate Unreal C++ classes automatically.

---

## Prerequisites

- Python 3.10+
- Unreal Engine 5.x project with **C++ source** enabled
- In Unreal Editor → Plugins, enable:
  - **Remote Control API**
  - **Remote Control Web Interface**
- At least one LLM provider key: Groq, Google Gemini, or a local Ollama install

---

## Installation

```bash
# 1. Clone / switch to the branch you want
git checkout ue-docs-intgr   # for C++ codegen features
# or
git checkout main             # for live scene building only

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set up your environment file
copy .env.example .env
```

Open `.env` and fill in the keys for the provider you want to use:

```env
GROQ_API_KEY=your_groq_api_key_here
# or
GOOGLE_API_KEY=your_google_api_key_here
# Ollama needs no key — just have Ollama running locally
```

---

## Configuration (for C++ codegen only)

If you want the agent to write and compile Unreal C++ code, open `unreal_mcp/config/settings.py` and set your machine-specific paths:

```python
UE_PROJECT_NAME = "YourProjectName"           # Must match your Source/ folder name
UE_PROJECT_ROOT = r"C:\Path\To\YourProject"
UE_ENGINE_PATH  = r"D:\Epic\UE_5.5"
UE_EXPORT_MACRO = "YOURPROJECT_API"           # From your project's Build.cs
```

> **Skip this block entirely if you only want live scene building** (`--build` mode). It connects over WebSocket only and needs no paths configured.

---

## Running the Project

### Step 1 — Open Unreal Editor
Launch your project in Unreal Engine. The Remote Control WebSocket starts automatically on `ws://127.0.0.1:30020`.

### Step 2 — Start the MCP Server (separate terminal)

```bash
python server.py
```

You should see the server start on `http://localhost:8000`. Keep this terminal open.

### Step 3 — Run the Agent (another terminal)

Pick your backend (`groq`, `gemini`, or `ollama`) and a mode:

```bash
# Quickest test — lists actors in your scene
python agent.py groq --test

# Interactive scene building (type commands one by one)
python agent.py groq --build -i

# One-shot scene build
python agent.py groq --build --prompt "spawn 3 cubes in a row at the origin"

# Generate a C++ class (dry run — no files written, no compile)
python agent.py groq --two-phase --dry-run --prompt "Create a HealthComponent with a float CurrentHealth property"

# Generate a C++ class, write files, and compile
python agent.py groq --two-phase --prompt "Create a HealthComponent with a float CurrentHealth property"

# Full pipeline: generate code + compile + place in scene
python agent.py groq --orchestrate --prompt "Create a C++ LaserTrap actor and place 2 in the scene"
```

---

## Quick Reference

| Goal | Command |
|---|---|
| Verify connection to Unreal | `python agent.py groq --test` |
| Interactive scene building | `python agent.py groq --build -i` |
| One-shot prompt | `python agent.py groq --build --prompt "..."` |
| Preview C++ generation | `python agent.py groq --two-phase --dry-run --prompt "..."` |
| Generate + compile C++ | `python agent.py groq --two-phase --prompt "..."` |
| Generate + compile + spawn | `python agent.py groq --orchestrate --prompt "..."` |
| Use Gemini instead | Replace `groq` with `gemini` in any command |
| Use local Ollama | Replace `groq` with `ollama` in any command |

---

## Troubleshooting

**`Cannot connect to Unreal Remote Control`**
Make sure Unreal Editor is running and the Remote Control plugins are enabled. The default port is `30020`.

**`Build.bat path error` / preflight check fails** (C++ mode only)
Set the correct paths in `unreal_mcp/config/settings.py`. Close Unreal Editor before running `--two-phase` or `--orchestrate` — headless compilation requires the editor to be shut down.

**`Prompt required` error**
Add `--prompt "..."` or use `-i` for interactive mode.

**Generated class not showing in editor**
Confirm the `.h` and `.cpp` files were written under `Source/<YourProjectName>/`, then rebuild from Visual Studio or Unreal Editor.
