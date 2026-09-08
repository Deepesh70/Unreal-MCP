# 📜 Origins — How This Project Started

## The Original Idea

The project started as a **7-level game plan** to create an automated pipeline that turns text descriptions into fully constructed 3D environments in Unreal Engine. The concept: you type "build a medieval village" and it appears in the Unreal viewport.

## The 7 Levels (Original Plan)

| Level | Name | Goal |
|-------|------|------|
| 1 | The Architect's Blueprint | Design a JSON schema for buildings |
| 2 | The Draftsman's Chamber | Prompt-engineer the LLM to output valid JSON |
| 3 | The Builder's Awakening | C++ class in Unreal to parse and build from JSON |
| 4 | The Masonry Phase | Spawning loops for floors, walls, roofs |
| 5 | The Polish Protocol | Materials, textures, collision |
| 6 | The Automation Bridge | Connect LLM output to Unreal without copy-paste |
| 7 | The Masterpiece | Scale to entire city blocks |

## What Actually Happened

- **Level 1:** Bypassed C++ structs entirely. Used Python dictionaries instead. Fast prototyping, but no type safety.
- **Level 2:** Mastered. Built multi-model support (Groq, Gemini, Ollama). Created battle-tested JSON repair for truncated LLM output.
- **Level 3:** Plot twist — Python became the builder, not C++. All spatial math lives in `processor.py`, not Unreal.
- **Level 4:** Achieved, but remotely. Each wall/floor is a separate WebSocket call. 26 calls per building.
- **Level 5:** Never started. All geometry is untextured gray cubes.
- **Level 6:** Fully conquered and built FIRST. The MCP server, WebSocket bridge, and tool registration system were the foundation.
- **Level 7:** Critical bottleneck. 26 actors per building × 50 buildings = 1,300 draw calls. Engine dies.

## The Technology Stack

- **Python**: FastMCP server, LLM integration (Groq/Gemini/Ollama), JSON processing
- **WebSocket**: Bidirectional bridge between Python and Unreal Engine
- **Unreal Engine 5.x**: Remote Control Web Interface plugin for receiving commands
- **C++ (generated)**: `ProceduralCityManager` with HISM, Ledger, Geometry Scripting (1556 lines)

## Key Files From the Beginning

| File | Purpose | Status |
|------|---------|--------|
| `server.py` | MCP server entry point | ✅ Still in use |
| `agent.py` | Standalone CLI agent launcher | ⚠️ Being merged into MCP tools |
| `agents/base.py` | LLM routing + recipe matching | ⚠️ Has the "bridge paralysis" bug |
| `agents/processor.py` | JSON → WebSocket spawn calls | ⚠️ 800 lines of legacy code |
| `recipes/buildings.json` | Pre-built structure definitions | ✅ Data file, kept as reference |
| `generated/ProceduralCityManager.cpp` | C++ geometry engine | ✅ Advanced, 3 phases implemented |
