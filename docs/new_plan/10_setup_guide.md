# 📦 Setup Guide — Getting Started From Scratch

> Step-by-step instructions for setting up the entire Unreal-MCP Procedural City Builder, from a fresh repository clone to your first generated building.

---

## Prerequisites

### Software Required

| Software | Version | Purpose |
|----------|---------|---------|
| Unreal Engine | 5.4+ (tested on 5.6.1) | The 3D rendering engine |
| Python | 3.10+ | The MCP server and LLM agent |
| Git | Any | Version control |
| A code editor | VS Code, Rider, etc. | Editing Python and C++ |

### Unreal Engine Plugins Required

The following plugins must be enabled in your Unreal project:

1. **Remote Control API** — Allows external programs to talk to the editor via WebSocket
   - Enable in: Edit → Plugins → Search "Remote Control"
   - Enable both "Remote Control API" and "Web Remote Control"

2. **Editor Scripting Utilities** — Provides the `EditorLevelLibrary` used for spawning
   - Usually enabled by default in C++ projects

### API Keys (Choose One or More)

| Provider | Where to Get | Free Tier? |
|----------|-------------|-----------|
| Groq | [console.groq.com](https://console.groq.com) | ✅ Yes (limited TPM) |
| Google Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | ✅ Yes |
| Ollama | [ollama.ai](https://ollama.ai) | ✅ Yes (runs locally) |

---

## Step 1: Clone and Install

```bash
# Clone the repository
git clone <repo-url>
cd Unreal-MCP

# Install Python dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your API keys and Unreal project settings:

```bash
# ── Required: At least one LLM provider ──────────────────────
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here

# ── Required: Your Unreal project's API macro ────────────────
# Find this in your project's Build.cs or generated header
# Example: If your project is "MyCityProject", set:
PROJECT_API=MYCITYPROJECT_API

# ── Optional: WebSocket URL ──────────────────────────────────
# Default: ws://127.0.0.1:30020 (local Unreal)
# For remote: UE_WS_URL=ws://your-ngrok-url:30020
```

---

## Step 3: Set Up the Unreal Project

### 3a. Generate the C++ Files

The C++ files for the `AProceduralCityManager` are generated into the `generated/` folder. After Phase 1 is built, they will appear as:

```
generated/
├── ProceduralBuildingTypes.h
├── ProceduralCityManager.h
└── ProceduralCityManager.cpp
```

### 3b. Copy C++ Files to Your Unreal Project

Copy these files to your Unreal project's Source directory:

```
YourProject/
└── Source/
    └── YourProject/
        ├── ProceduralBuildingTypes.h    ← Copy here
        ├── ProceduralCityManager.h      ← Copy here
        └── ProceduralCityManager.cpp    ← Copy here
```

### 3c. Compile

1. Open your Unreal project in the editor
2. If Live Coding is enabled: press `Ctrl+Alt+F11` to hot-reload
3. Otherwise: close the editor, build from your IDE (Visual Studio / Rider), then reopen

### 3d. Place the City Manager in Your Level

1. In the Content Browser, search for `ProceduralCityManager`
2. Drag it into your level viewport
3. Place it anywhere — its position doesn't matter (buildings are spawned at absolute coordinates)
4. Save your level

> **Important:** There should be exactly ONE `AProceduralCityManager` in your level. Python discovers it automatically by searching the actor list.

---

## Step 4: Verify the WebSocket Connection

1. Open your Unreal project
2. Ensure Remote Control is running:
   - Window → Remote Control
   - Verify the WebSocket port (default: 30020)
   - The port in your `.env` (`UE_WS_URL`) must match

---

## Step 5: Start the MCP Server

Open a terminal:

```bash
cd Unreal-MCP
python server.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://localhost:8000
```

---

## Step 6: Run the Builder Agent

Open a **second** terminal:

```bash
# Quick test — lists actors to verify connection
python agent.py groq --test

# Builder mode — one-shot
python agent.py groq -b --prompt "Build a 3-story house at the origin"

# Builder mode — interactive REPL
python agent.py groq -b -i
```

### Interactive Mode Commands

```
🏗️ Builder > Build a 5-story office at 0 0 0
🏗️ Builder > Build a house with a pointed roof at 2000 0 0
🏗️ Builder > Clear everything
🏗️ Builder > quit
```

---

## Step 7: Verify It Worked

After running a build command:

1. Switch to the Unreal Editor
2. Look at the viewport — you should see cube-based geometry forming a building
3. Check the Outliner — you should see only your `ProceduralCityManager` actor (no individual StaticMeshActors)
4. In the Python terminal: you should see a JSON receipt with `"Status": "Success"`

---

## Troubleshooting

### "Unreal Engine API is offline"

```
❌ Unreal Engine API is offline. Please start Unreal Engine 
   and ensure the Remote Control Web Interface plugin is enabled.
```

**Fix:**
1. Open your Unreal project
2. Enable the Remote Control plugin (Edit → Plugins)
3. Check the WebSocket port matches your `.env` setting
4. Restart the Unreal Editor after enabling the plugin

### "No AProceduralCityManager found in the level"

```
❌ No AProceduralCityManager found in the level.
   Please place one in your map (drag from Content Browser).
```

**Fix:**
1. Compile the C++ files first (Step 3c)
2. Drag `AProceduralCityManager` from Content Browser into your level
3. Save the level

### "YOURPROJECT_API" in compiled code

If you see compilation errors about `YOURPROJECT_API`:

**Fix:** Set `PROJECT_API` in your `.env` file to your actual project's API macro:
```bash
PROJECT_API=MYCITYPROJECT_API
```
Then regenerate the C++ files.

### JSON Parse Errors

```
❌ JSON Parse Error: ...
```

**Fix:** This usually means the LLM produced invalid output. Try:
1. Use a larger model: `python agent.py gemini -b -i`
2. Simplify your prompt
3. Check if `_repair_truncated_json` caught a truncation (look for the ⚠️ warning)

---

## Optional: Set Up the Asset Dictionary

The `AssetDictionary` is a DataTable that maps Style tags to actual meshes. Without it, all buildings use gray basic shapes (which is fine for prototyping).

To add custom visuals:

1. In Unreal Editor: Content Browser → Right Click → Miscellaneous → Data Table
2. Select `FAssetDictionaryRow` as the row struct
3. Add rows with Style keys like `"House_Wood_Small"`:
   - `WallMesh` → select your wooden wall mesh
   - `FloorMesh` → select your wooden floor mesh
   - `RoofMesh` → select your roof mesh
   - Set materials similarly
4. Select the `ProceduralCityManager` in your level
5. In the Details panel: set `AssetDictionary` → your new DataTable
6. Save

See [docs/ASSET_DICTIONARY.md](../ASSET_DICTIONARY.md) for detailed instructions.

---

## Optional: Cloud Deployment

To run the Python MCP server in the cloud while Unreal runs locally:

### On Your Local Machine (Unreal)

1. Install [ngrok](https://ngrok.com/) or similar tunnel
2. Run: `ngrok tcp 30020`
3. Note the public URL (e.g., `tcp://0.tcp.ngrok.io:12345`)

### On the Cloud Server (Python)

1. Clone the repo and install dependencies
2. Set `.env`:
   ```bash
   UE_WS_URL=ws://0.tcp.ngrok.io:12345
   ```
3. Run: `python server.py` and `python agent.py gemini -b -i`

The cloud server sends WebSocket commands to your local Unreal Editor through the tunnel.

---

## Project Structure (Post-Refactor)

```
Unreal-MCP/
├── server.py                  ← MCP server entry point
├── agent.py                   ← CLI launcher
├── .env                       ← API keys + project config
├── requirements.txt
│
├── agents/                    ← LLM agent logic
│   ├── base.py               ← Agent runner + system prompts
│   ├── processor.py           ← JSON repair + validation + routing
│   ├── orchestrator.py        ← Token-aware complexity routing (Phase 3)
│   ├── groq_agent.py          ← Groq backend
│   ├── gemini_agent.py        ← Gemini backend
│   └── ollama_agent.py        ← Ollama backend
│
├── unreal_mcp/                ← MCP server package
│   ├── config/settings.py     ← All configurable values
│   ├── connection/websocket.py ← WebSocket transport
│   ├── tools/                 ← MCP tool registrations
│   ├── mappings/              ← Asset/class lookups
│   └── utils/                 ← Response helpers
│
├── generated/                 ← Generated C++ files (copy to UE project)
│   ├── ProceduralBuildingTypes.h
│   ├── ProceduralCityManager.h
│   └── ProceduralCityManager.cpp
│
└── docs/
    ├── new_plan/              ← This documentation suite
    │   ├── 00_overview.md
    │   ├── 01_the_journey.md
    │   ├── ...
    │   └── 10_setup_guide.md
    └── ARCHITECTURE.md        ← Original architecture docs
```
