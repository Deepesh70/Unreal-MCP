# 🗺️ The Journey — From Blueprint to City Builder

> This document tells the story of how the project evolved, where it deviated from the original plan, and why those deviations were sometimes brilliant and sometimes problematic.

---

## The Original 7-Level Plan

The project was conceived as a game with 7 levels, each building on the last. The idea was simple: create an automated pipeline that turns text descriptions into fully constructed 3D environments in Unreal Engine.

---

## Level 1: The Architect's Blueprint (Data Structuring)

**Original Plan:** Design a rigid JSON schema and create C++ `UStructs` in Unreal to catch this data.

**What Actually Happened:** ⚡ **Bypassed.** We never created C++ structs. Instead, the JSON schema was defined entirely in the Python system prompt (`BUILDER_SYSTEM_PROMPT` in `base.py`), and parsed using Python's standard `json.loads()` into plain dictionaries.

**Why This Was Smart (At The Time):** It let us prototype extremely fast. No compilation cycles, no Unreal restarts. Change the schema? Edit a Python string and re-run.

**Why It Must Change Now:** Python dictionaries have no type safety. A malformed LLM response that puts a string where a float should be won't crash until it hits the math loop — deep inside `processor.py` where debugging is painful.

---

## Level 2: The Draftsman's Chamber (LLM Prompt Engineering)

**Original Plan:** Craft system prompts that force the LLM to output perfectly formatted JSON.

**What Actually Happened:** ✅ **Mastered.** We built a sophisticated multi-model system:
- Groq (Llama 3.3 70B) — fast cloud inference
- Gemini 2.5 Pro — high-quality reasoning
- Ollama — fully local, privacy-first

The `BUILDER_SYSTEM_PROMPT` in `base.py` enforces strict JSON output with no markdown, no prose. The `_repair_truncated_json()` function in `processor.py` dynamically salvages broken JSON when the LLM hits its token limit mid-output — tracking open brackets, unclosed strings, and appending the missing closers.

**What Made This Special:** The JSON repair mechanism is battle-tested infrastructure that most projects don't have. It means even cheap, fast models with small context windows can contribute useful output.

---

## Level 3: The Builder's Awakening (Core C++ Logic)

**Original Plan:** Build an `AProceduralHouseBuilder` class in Unreal C++ to ingest and parse the JSON string.

**What Actually Happened:** 🔄 **Deviated — The Plot Twist.** Python became the builder. The spatial math loop that calculates floor slabs, wall coordinates, and roof placement lives in `processor.py::_handle_spawn_actor()` — a 160-line Python function. Unreal Engine never parses any JSON; it just receives individual "place this cube here" commands.

**Why This Became The Bottleneck:** Building a 5-floor house sends ~26 individual WebSocket RPC calls. Building a 50-building city would send ~1,300 calls. Building a city block at scale is physically impossible at this rate.

---

## Level 4: The Masonry Phase (Spawning & Transforms)

**Original Plan:** Write loops that spawn and transform modular pieces.

**What Actually Happened:** ✅ **Achieved (Remotely).** The math is correct. Floor slabs are flat cubes at the base of each story. Walls are thin cubes on the perimeter. Scale factors are properly calculated:
- `slab_sx = BuildingWidth / 100.0` (Unreal default cube = 100 UU)
- `wall_z = floor_z + FloorHeight / 2.0` (centered vertically)

But it's all done in Python, calling `_spawn_and_scale()` → `send_ue_ws_command()` for each individual piece.

---

## Level 5: The Polish Protocol (Visuals & Physics)

**Original Plan:** Apply dynamic materials, map asset IDs to textures, establish collision.

**What Actually Happened:** ❌ **Not Started.** All spawned geometry is raw, untextured Unreal Engine basic shapes — gray cubes and cones. No material assignment, no collision configuration, no visual polish.

**The Fix (Planned):** A `UDataTable` called `AssetDictionary` will map semantic style tags (e.g., `"House_Wood_Small"`) to actual meshes and materials. The LLM never needs to know Unreal file paths — it just describes the visual intent.

---

## Level 6: The Automation Bridge (The MCP Connection)

**Original Plan:** Connect the LLM output directly to Unreal without manual copy-pasting.

**What Actually Happened:** ✅ **Fully Conquered — And Built First!** This is the project's superpower. The entire MCP server, WebSocket bridge, agent REPL, and tool registration system were built before anything else. The pipeline is:

```
LLM → Python (FastMCP) → WebSocket → Unreal Remote Control API → Editor
```

This was built first because it's the hardest infrastructure to get right. Everything else is "just" logic that runs on top of this bridge.

---

## Level 7: The Masterpiece (Scaling the Generation)

**Original Plan:** Scale to city blocks using HISM for performance.

**What Actually Happened:** ❌ **Critical Bottleneck.** The current architecture cannot scale. Each building piece is an individual `StaticMeshActor` — meaning each wall is its own draw call. A city of 1,000 buildings would create 26,000+ actors and draw calls, bringing the engine to its knees.

**The Fix (The Great Refactor):** Replace individual actors with `UHierarchicalInstancedStaticMeshComponent` (HISM). Instead of spawning 50 wall actors, HISM tells the GPU: "Here is one wall mesh. Draw it 50 times at these transforms." Single draw call. 60 FPS maintained.

---

## Level 8: The Intelligence Layer (Not In The Original Plan)

**What Emerged:** During the refactoring discussion, we discovered that basic procedural generation isn't enough. The system needs:

1. **Spatial Awareness** — Know what's already in the world before building
2. **Memory** — Remember what was built and where
3. **Mutation** — Change existing structures without rebuilding everything

This became the "Dual-Check ScanArea" system (physics traces for external obstacles, Ledger iteration for internal ones) and the "Swap-and-Pop" safe deletion algorithm.

---

## The Architecture Shift

```
BEFORE (Puppet Master):          AFTER (Delegator):
Python = Brain + Hands + Eyes    Python = Thin Gateway
Unreal = Dumb Canvas             Unreal = Smart Builder
26 calls per building            1 call per building
26,000 calls per city            1,000 calls per city (BatchSpawn: 1 call)
```

---

## What Happens Next

The project is now executing **The Great Refactor** in three phases:

| Phase | Codename | What It Achieves |
|-------|----------|-----------------|
| 1 | Core Foundation | C++ math loop + HISM + Ledger + single WebSocket call |
| 2 | Eyes & Nudge | Spatial awareness + auto-nudge around obstacles |
| 3 | The Masterpiece | Modify/Destroy lifecycle + BatchSpawn arrays + AssetDictionary + token-aware complexity routing |

See [08_phases.md](./08_phases.md) for the detailed execution plan.
