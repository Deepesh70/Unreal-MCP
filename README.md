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
# 1. Clone the repository
git clone https://github.com/your-username/Unreal-MCP.git
cd Unreal-MCP

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set up your environment file
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Open `.env` and fill in the keys for the provider you want to use:

```env
GROQ_API_KEY=your_groq_api_key_here
# or
GOOGLE_API_KEY=your_google_api_key_here
# Ollama needs no key — just have Ollama running locally
```

Additional optional variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `UE_WS_URL` | `ws://127.0.0.1:30020` | WebSocket address of Unreal Remote Control |
| `CPP_OUTPUT_DIR` | `./generated` | Where generated `.h`/`.cpp` files are written |
| `PROJECT_API` | _(none)_ | Your project's API export macro (e.g. `MYPROJECT_API`) |
| `UE_PROJECT_MODULE` | _(none)_ | Your Unreal project module name |

---

## Configuration (for C++ codegen only)

If you want the agent to write and compile Unreal C++ code, open `unreal_mcp/config/settings.py` and set your machine-specific paths:

```python
UE_PROJECT_NAME = "Unreal MCP"           # Must match your Source/ folder name
UE_PROJECT_ROOT = r"C:\Users\Deepesh\Desktop\Unreal MCP"         # your project root directory
UE_ENGINE_PATH  = r"D:\Epic\UE_5.5"             # Your Unreal Engine installation directory
UE_EXPORT_MACRO = "UNREALMCP_API"         # This should be the name of your project
```

> **Skip this block entirely if you only want live scene building.** Scene building connects over WebSocket only and needs no paths configured.

---

## Running the Project

### Step 1 — Open Unreal Editor

Launch your project in Unreal Engine. The Remote Control WebSocket starts automatically on `ws://127.0.0.1:30020`.

### Step 2 — Start the MCP Server (separate terminal)

```bash
python server.py
```

You should see the server start on `http://localhost:8000`. **Keep this terminal open.**

### Step 3 — Run the Agent (another terminal)

Pick your **backend** (`groq`, `gemini`, or `ollama`) and a **mode**:

```bash
# Quick connection test — lists actors in your scene (1 API call)
python agent.py groq --test

# Interactive scene building — type commands one by one
python agent.py groq --interactive

# One-shot scene build with a custom prompt
python agent.py groq --prompt "spawn 3 cubes in a row at the origin"

# Builder mode (C++ Procedural Architect) — interactive
python agent.py groq --builder --interactive
# shorthand:
python agent.py groq -b -i

# Builder mode with a one-shot prompt
python agent.py groq --builder --prompt "Create a HealthComponent with a float CurrentHealth property"

# Run a backend module directly (advanced)
python -m agents.groq_agent
python -m agents.gemini_agent --model gemini-2.5-flash
python -m agents.ollama_agent --model qwen2.5:72b
```

---

## Agent CLI Reference

```
python agent.py <backend> [options]
```

### Backends

| Backend | Model | Notes |
|---|---|---|
| `groq` | Llama 3.3 70B | Fast, free tier available. Requires `GROQ_API_KEY` |
| `gemini` | Gemini 2.5 Pro | Requires `GOOGLE_API_KEY` |
| `ollama` | llama3.3:70b (local) | No API key needed. Requires Ollama running locally |

### Modes

| Flag | Description |
|---|---|
| _(default)_ | Standard MCP mode — spawn, list, and scale actors |
| `--builder`, `-b` | C++ Procedural Architect mode |

### Options

| Flag | Description |
|---|---|
| `--test` | Quick test — 1 API call, lists actors currently in scene |
| `--interactive`, `-i` | Chat mode — type commands one by one |
| `--prompt "..."` | Run a single custom prompt and exit |

---

## Quick Reference

| Goal | Command |
|---|---|
| Verify connection to Unreal | `python agent.py groq --test` |
| Interactive scene building | `python agent.py groq --interactive` |
| One-shot scene build | `python agent.py groq --prompt "spawn 5 spheres"` |
| Interactive C++ builder | `python agent.py groq --builder --interactive` |
| One-shot C++ generation | `python agent.py groq --builder --prompt "Create a HealthComponent"` |
| Use Gemini instead | Replace `groq` with `gemini` in any command |
| Use local Ollama | Replace `groq` with `ollama` in any command |

---

## Project Structure

```
Unreal-MCP/
├── agent.py            # CLI launcher — pick backend & mode here
├── server.py           # MCP server entry point (FastMCP / SSE)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── agents/             # LLM backend modules (groq, gemini, ollama)
├── unreal_mcp/         # Core MCP tools & config
│   └── config/         # settings.py — UE paths for C++ codegen
├── generated/          # Output directory for generated .h/.cpp files
├── recipes/            # Pre-built scene / building JSON recipes
├── templates/          # C++ class templates
└── docs/               # Additional documentation
```

---

## Troubleshooting

**`Cannot connect to Unreal Remote Control`**
Make sure Unreal Editor is running and the Remote Control plugins are enabled. The default WebSocket port is `30020`.

**`GROQ_API_KEY` / `GOOGLE_API_KEY` not found**
Ensure you copied `.env.example` to `.env` and filled in the correct key for your chosen backend.

**Build path error / preflight check fails** (C++ builder mode only)
Set the correct paths in `unreal_mcp/config/settings.py`. Close Unreal Editor before running Builder mode with compilation — headless builds require the editor to be shut down.

**`Prompt required` error**
Add `--prompt "..."` or use `--interactive` / `-i` for interactive mode.

**Generated class not showing in editor**
Confirm the `.h` and `.cpp` files were written under `Source/<YourProjectName>/`, then rebuild from Visual Studio or Unreal Editor.
