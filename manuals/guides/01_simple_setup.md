# 🎮 Unreal MCP — Simple Setup Guide

**What is this?** A tool that lets AI assistants (like Antigravity, Copilot, Claude, Cursor) 
control your Unreal Engine editor. You talk in plain English, the AI builds things in Unreal for you.

---

## ⚡ Setup in 2 Minutes

### Step 1: Install (one time only)

Open a terminal (Command Prompt or PowerShell) and run:

```
cd d:\Desktop\Unreal-MCP
pip install .
```

That's it. You now have the `unreal-mcp` command available.

### Step 2: Open Unreal Engine

1. Open your Unreal Engine project
2. Make sure these plugins are ON:
   - **Remote Control Web Interface** (should already be enabled)
   - **Python Editor Script Plugin** (optional, for advanced features)
3. (Optional but recommended) Go to **Edit → Project Settings** → search `Remote Control` → turn ON **"Allow Remote Console Execution"**

### Step 3: Connect your AI tool

Pick the tool you use and follow the instructions below.

---

## 🔗 How to Connect — Pick Your Tool

### VS Code (GitHub Copilot)

1. Open VS Code
2. Press `Ctrl+Shift+P` → type `settings json` → click **"Preferences: Open User Settings (JSON)"**
3. Add this inside the `{ }`:

```json
"mcp.servers": {
    "unreal-engine": {
        "command": "unreal-mcp",
        "args": ["--stdio"]
    }
}
```

4. Save the file and restart VS Code
5. Open Copilot Chat and type: **"Check my connection to Unreal"**

> **What happens:** VS Code automatically starts the MCP server for you. No terminal needed.

---

### Cursor

1. In your project folder, create a file: `.cursor/mcp.json`
2. Put this inside:

```json
{
    "mcpServers": {
        "unreal-engine": {
            "command": "unreal-mcp",
            "args": ["--stdio"]
        }
    }
}
```

3. Restart Cursor
4. In the AI chat, type: **"What's in my scene?"**

---

### Antigravity

**Option A — Automatic (recommended if supported):**

Set the MCP server command to `unreal-mcp` with args `["--stdio"]`.

**Option B — Manual:**

1. Open a terminal and run: `unreal-mcp`
2. You should see:
   ```
   🚀 Unreal MCP Server starting on http://localhost:8000
      SSE endpoint: http://localhost:8000/sse
   ```
3. In Antigravity, connect to: `http://localhost:8000/sse`

---

### Claude Desktop

1. Find the file `claude_desktop_config.json` 
   - On Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Add this:

```json
{
    "mcpServers": {
        "unreal-engine": {
            "command": "unreal-mcp",
            "args": ["--stdio"]
        }
    }
}
```

3. Restart Claude Desktop

---

### Any Other MCP Tool

If your tool supports MCP, you can connect two ways:

**Way 1 — stdio (tool auto-starts the server):**
- Command: `unreal-mcp`
- Args: `["--stdio"]`

**Way 2 — SSE (you start the server yourself):**
1. Run `unreal-mcp` in a terminal
2. Connect to: `http://localhost:8000/sse`

---

## ✅ Test Your Connection

After connecting, say this to your AI:

> "Check my connection to Unreal"

You should see something like:

```
✅ MCP Server     → Running
✅ UE WebSocket   → Connected
✅ Remote Control → Responding (X actors in level)
✅ Python Plugin  → Available

🟢 Status: READY
```

If something shows ❌, follow the fix instruction shown.

---

## 🗣️ What Can You Say?

Here are real examples you can type in your AI chat:

### See what's in your scene
- *"What's in my scene?"*
- *"List all the lights"*
- *"Show me actors near position 0, 0, 0"*

### Build things
- *"Spawn a cube at 0, 0, 200"*
- *"Create a ring of 8 spheres"*
- *"Build a small house using cubes"*
- *"Place a point light above the scene"*

### Move and change things
- *"Move the cube to 500, 0, 100"*
- *"Make the sphere 3 times bigger"*
- *"Rotate the camera 90 degrees"*
- *"Delete the cone"*

### Change properties
- *"Set the light intensity to 10000"*
- *"Change the light color to warm orange"*
- *"Hide the floor plane"*

### Advanced (needs Python plugin enabled)
- *"Take a screenshot"*
- *"Find all static meshes in my project"*
- *"Create a cinematic camera with 35mm focal length"*
- *"Apply a red material to all cubes"*

---

## ❓ Common Problems & Fixes

### "Connection refused" or "UE WebSocket" shows ❌

**Meaning:** Unreal Engine is not reachable.

**Fix:**
1. Is Unreal Engine open? Open it.
2. Is the **Remote Control Web Interface** plugin enabled?
   - Go to **Edit → Plugins** → search "Remote Control" → make sure it's checked ✅
3. Restart Unreal Engine after enabling the plugin.

---

### "unreal-mcp" command not found

**Meaning:** The package isn't installed.

**Fix:**
```
cd d:\Desktop\Unreal-MCP
pip install .
```

---

### "Port 8000 already in use"

**Meaning:** Something else is using port 8000.

**Fix:** The server will automatically try the next port (8001, 8002, etc.) 
You can also pick a port manually:
```
unreal-mcp --port 9000
```

---

### Python Plugin shows ⚠️

**Meaning:** Some advanced features (screenshots, asset search, custom scripts) won't work.

**Fix:**
1. **Edit → Plugins** → search "Python" → enable **Python Editor Script Plugin**
2. **Edit → Project Settings** → search "Remote Control" → enable **"Allow Remote Console Execution"**
3. Restart Unreal Engine

---

### "No tools found" in my IDE

**Fix:** Restart your IDE after adding the MCP config.

---

### Things spawn but I can't see them

**Fix:** The objects might be far from your camera. Try:
- *"What's in my scene?"* — check the locations
- *"Move the cube to 0, 0, 0"* — bring it to origin
- Press `F` in Unreal Editor with the object selected to focus on it

---

## 🔧 For Advanced Users

### Unreal Engine on a different machine

Set the `UE_WS_URL` environment variable:

```json
"mcp.servers": {
    "unreal-engine": {
        "command": "unreal-mcp",
        "args": ["--stdio"],
        "env": {
            "UE_WS_URL": "ws://192.168.1.50:30020"
        }
    }
}
```

### Running the server on a different port

```
unreal-mcp --port 9000
```

### Using a specific host (for network access)

```
unreal-mcp --host 0.0.0.0 --port 8000
```

---

## 📋 Quick Reference

| Command | What it does |
|---------|-------------|
| `unreal-mcp` | Start the server (SSE mode, port 8000) |
| `unreal-mcp --stdio` | Start in stdio mode (for IDE auto-launch) |
| `unreal-mcp --port 9000` | Start on a custom port |
| `unreal-mcp --help` | Show all options |
| `pip install .` | Install/update the package |

| AI Prompt | What happens |
|-----------|-------------|
| "Check my connection" | Tests MCP → UE pipeline, shows ✅/❌ |
| "What's in my scene?" | Shows summary with actor types and mesh names |
| "Spawn a cube at 0,0,100" | Creates a cube in the level |
| "Delete all spheres" | Removes all sphere actors |
| "Take a screenshot" | Captures the viewport |
