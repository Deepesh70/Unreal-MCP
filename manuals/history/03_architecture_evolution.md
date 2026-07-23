# 🔄 Architecture Evolution — How the Design Changed Over Time

## Era 1: The Puppet Master (Where We Started)

```
User → Terminal CLI → LLM (Groq/Gemini) → Python processor.py → 26 WebSocket calls → Unreal
```

**How it worked:** You ran `python agent.py groq -b -i` in a terminal. The Python agent called the LLM, got JSON, and processor.py translated each building part into an individual `SpawnActorFromObject` WebSocket call.

**Problems:** 
- 26 calls per building, 1300 for a city
- Python did ALL the math
- No scene awareness
- No IDE integration
- Recipe matching bypassed LLM reasoning

---

## Era 2: The C++ Delegator (The Great Refactor)

```
User → Terminal CLI → LLM → Python (thin gateway) → ONE WebSocket call → C++ CityManager → HISM instances
```

**What changed:** Created `ProceduralCityManager.cpp` (1556 lines). Python sends ONE JSON payload. C++ does all spatial math, HISM instancing, ledger tracking, collision detection.

**Capabilities added:**
- HISM batching (1 draw call for 50 walls instead of 50)
- Spatial awareness (ScanArea, auto-nudge)
- Geometry Scripting (boolean modeling — subtract, union, intersect)
- Swap-and-pop safe deletion
- Ground height detection

**Problems remaining:**
- Still terminal-only
- Still no IDE integration
- Still blind (no screenshots)
- Narrow tool surface (only building-related)

---

## Era 3: The MCP Tool Provider (Where We Are Going)

```
User → IDE (Cursor/Copilot/Antigravity) → AI Model (user's choice) → MCP Tools → WebSocket → Unreal
```

**What's changing:**
- MCP server exposes GENERALIZED tools, not building-specific ones
- The AI model lives in the IDE, not in our code
- `execute_python_in_editor` gives infinite capability
- `get_scene_state` gives the AI eyes
- `capture_viewport` gives visual feedback
- Works with ANY Unreal project, ANY machine
- The standalone `agent.py` is being MERGED to use MCP tools internally (backward compatible)

**The key insight:** We don't embed intelligence. We provide HANDS. The intelligence is whatever AI model the user's IDE provides.

---

## Architecture Comparison

| Aspect | Era 1 (Puppet Master) | Era 2 (C++ Delegator) | Era 3 (MCP Provider) |
|--------|----------------------|----------------------|---------------------|
| AI model | Embedded (Groq/Gemini key in .env) | Embedded | User's IDE provides it |
| Interface | Terminal CLI | Terminal CLI | IDE sidebar |
| Scene awareness | None | Ledger + ScanArea (internal only) | `get_scene_state` (full scene query) |
| Visual feedback | None | None | `capture_viewport` screenshots |
| Capabilities | Buildings only | Buildings + Geometry | EVERYTHING (via `execute_python_in_editor`) |
| Calls per building | 26 | 1 | 1 (via C++ manager) or script-based |
| Project dependency | Hardcoded | Hardcoded | Zero — connects to any UE instance |
| Model dependency | Groq/Gemini API keys required | Same | None — user brings their own |
