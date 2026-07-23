# 🏛️ The Three-Body System — Architecture

> Three separate systems, each with a strict responsibility boundary, working in concert to turn text into 3D worlds.

---

## The Philosophy

The most common mistake in AI-to-engine pipelines is making one component do everything. When the LLM generates coordinates AND the Python script validates AND spawns AND tracks state — every bug cascades through the entire system.

Our architecture enforces **strict separation of concerns:**

| Layer | Codename | Responsibility | What It NEVER Does |
|-------|----------|---------------|--------------------|
| LLM | **The Dreamer** | Creative intent, style decisions, relative layout | Never knows Unreal asset paths. Never manages HISM indices. Never retries blocked coordinates. |
| Python | **The Gateway** | JSON validation, repair, transport | Never runs spatial math. Never spawns actors. Never tracks world state. |
| C++ (Unreal) | **The Builder** | HISM spawning, spatial math, collision, state management | Never talks to the LLM. Never validates JSON schema. Never writes files to disk. |

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER PROMPT                                │
│         "Build a street with houses and an office"                │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                     🤖 LLM (THE DREAMER)                         │
│                                                                    │
│  Input:  Natural language prompt + system instructions             │
│  Output: Strict JSON with Intent, IDs, Styles, Coordinates        │
│                                                                    │
│  Example output:                                                   │
│  {                                                                 │
│    "Intent": "BatchSpawn",                                         │
│    "Blueprints": [                                                 │
│      {"ID": "House_01", "Style": "House_Wood_Small", ...},         │
│      {"ID": "Office_01", "Style": "Office_Concrete_Large", ...}    │
│    ]                                                               │
│  }                                                                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                  🐍 PYTHON (THE GATEWAY)                          │
│                                                                    │
│  Step 1: Strip markdown code fences if present                     │
│  Step 2: Repair truncated JSON (unclosed brackets/strings)         │
│  Step 3: Parse JSON and validate schema                            │
│  Step 4: Check required fields (ID, Intent, etc.)                  │
│  Step 5: Type-check values (Floors=int, Location=float array)      │
│  Step 6: Discover AProceduralCityManager in the level              │
│  Step 7: Send ONE WebSocket call to ProcessBlueprint()             │
│  Step 8: Receive JSON receipt from C++                             │
│  Step 9: Display result to user                                    │
│                                                                    │
│  Files: processor.py, base.py, websocket.py                        │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                     Single WebSocket Call
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│              🏗️ UNREAL C++ (THE BUILDER)                          │
│                                                                    │
│  Step 1: Deserialize JSON via FJsonSerializer                      │
│  Step 2: Route by Intent (Spawn/Batch/Modify/Destroy/Scan/Clear)   │
│  Step 3: For Spawn:                                                │
│     a. Check EnvironmentCheck → Dual-Check scan                    │
│     b. Auto-nudge if blocked (within radius)                       │
│     c. Resolve Style → DataTable → actual meshes                   │
│     d. Run math loop: floor slabs + walls + roof                   │
│     e. AddInstance() to HISM components                             │
│     f. Register in Ledger TMap with building ID                    │
│  Step 4: Serialize receipt JSON                                    │
│  Step 5: Return receipt string via Remote Control API              │
│                                                                    │
│  Files: ProceduralCityManager.h/.cpp, ProceduralBuildingTypes.h    │
└──────────────────────────────────────────────────────────────────┘
```

---

## The Chain of Command

A critical architectural decision: **who resolves spatial conflicts?**

### The Scenario
The LLM says "Build a house at X:100." There's a massive rock at X:100.

### The Decision: C++ Holds Spatial Authority

```
❌ WRONG: C++ rejects → Python relays → LLM guesses new coords → repeat
   Problem: Each retry costs ~500 tokens + 2 seconds of API latency
   
✅ RIGHT: C++ auto-nudges within declared radius → reports actual coords
   Benefit: Zero token waste, instant placement, one round trip
```

### How Auto-Nudge Works

1. The LLM declares `"EnvironmentCheck": {"RequiresScan": true, "Radius": 500}`
2. C++ scans the requested location
3. If blocked: spiral outward in increments, checking each candidate point
4. If a clear spot is found within the 500-unit radius: build there
5. If the entire radius is blocked: return `"Status": "Failed"`
6. The receipt tells Python exactly where the building was placed

This keeps the LLM focused on **semantic creativity** while C++ handles **geometric precision**.

---

## The Communication Protocol

All communication between Python and Unreal uses the **Remote Control API** over WebSocket.

### Python → Unreal (Command)
```json
{
  "MessageName": "http",
  "Parameters": {
    "Url": "/remote/object/call",
    "Verb": "PUT",
    "Body": {
      "objectPath": "/Game/Maps/MyMap.MyMap:PersistentLevel.ProceduralCityManager_0",
      "functionName": "ProcessBlueprint",
      "parameters": {
        "JsonPayload": "{\"Intent\":\"Spawn\",\"ID\":\"House_01\",...}"
      }
    }
  }
}
```

### Unreal → Python (Receipt)
```json
{
  "ResponseBody": {
    "ReturnValue": "{\"Action\":\"BuildResult\",\"Status\":\"Success\",\"ID\":\"House_01\",\"ActualLoc\":[100,0,150]}"
  }
}
```

Python reads the `ReturnValue` string, parses it as JSON, and displays the result.

---

## Why Three Bodies Instead of Two?

**Why not just LLM → Unreal directly?**

Because LLMs hallucinate. They forget closing brackets. They put strings where numbers should be. They generate 8,000-token payloads that get truncated at 4,096. Python's `_repair_truncated_json()` function catches all of this before it reaches the C++ deserializer, which would crash on malformed input.

**Why not just Python → Unreal (no LLM)?**

Because then you're just writing a manual scripting tool. The LLM is what makes the system understand "build a cozy neighborhood" versus "build a brutalist industrial district." It translates human intent into machine coordinates.

---

## Deployment Modes

The architecture supports two deployment modes without code changes:

### Local Mode (Default)
```
Python ←── ws://127.0.0.1:30020 ──→ Unreal Engine
         (same machine)
```

### Cloud Mode (Remote)
```
Python (Cloud Server) ←── ws://your-ngrok-url:30020 ──→ Unreal Engine (Local PC)
                          (via ngrok / localtunnel / port forwarding)
```

The only change: set `UE_WS_URL` in `.env` to the public address. The C++ side doesn't care — it just listens on its port.
