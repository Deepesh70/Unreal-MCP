# ❌ Mistakes & Lessons — What Went Wrong and What We Learned

## Mistake 1: The "Bridge Paralysis" Bug

**What happened:** In `agents/base.py`, the `_find_recipe` function uses greedy substring matching:
```python
if recipe["name"] in prompt_lower:
    # Bypass LLM entirely and just spawn the recipe!
```

If you say "build a house next to the bridge," it matches "bridge" first and spawns a Brooklyn Bridge instead of understanding context.

**Why it happened:** Quick shortcut during prototyping. It was easier to match keywords than to let the LLM reason.

**Lesson learned:** Never bypass the LLM's reasoning. The LLM should ALWAYS process the prompt and decide what to do. Greedy matching creates false positives that destroy the user experience.

**Fix:** Semantic routing — inject a compact recipe catalog into the LLM's system prompt and let the LLM choose. Python handles the heavy data (part arrays, coordinates) AFTER the LLM makes the semantic choice.

---

## Mistake 2: Python as the Builder (The Puppet Master Problem)

**What happened:** All spatial math (floor slabs, wall coordinates, roof placement) was written in Python (`processor.py`). Every wall, every floor slab is a separate WebSocket call to Unreal.

**Impact:** Building a 5-floor house sends 26 individual WebSocket calls. Building a 50-building city would send 1,300 calls. Unreal creates 1,300 individual `StaticMeshActors`, each with its own draw call. The engine freezes.

**Lesson learned:** Python should be a thin gateway, not the brain AND the hands. Heavy computation (geometry loops, HISM instancing) belongs in C++ on the engine side.

**Fix:** The `ProceduralCityManager.cpp` was created to move all spatial math to C++. Python sends ONE JSON payload, C++ builds the entire building with HISM instances.

---

## Mistake 3: Identical Recipes (No Variation)

**What happened:** Recipe `hut` in `buildings.json` is a frozen JSON blob. Every hut looks exactly the same — same dimensions, same roof height, same chimney position.

**Why it's a problem:** Real-world scenes need variety. A village with 20 identical huts looks fake.

**Lesson learned:** Recipes should be templates with ranges, not fixed values. Instead of `"scale": [3.0, 3.0, 2.8]`, use `"scale_range": [[2.5, 3.5], [2.5, 3.5], [2.0, 3.5]]`. Python randomizes within the range each time.

**Fix (planned):** Add jitter ranges to recipe schema. Python picks random values within bounds before sending to Unreal.

---

## Mistake 4: The AI Is Blind (No Scene Awareness)

**What happened:** When the AI generates a spawn command, it has zero idea what's already in the Unreal level. It doesn't know if there's already a house at the target location. It doesn't know about manually placed objects, terrain, or things from a previous session.

**Impact:** If the user says "change the house to a bungalow," the AI might wipe everything, or spawn a second building on top of the existing one, because it simply doesn't know the house exists.

**Lesson learned:** The AI must ALWAYS query the scene state before acting. Every action should start with "what exists right now?" This is how the Unity MCP does it — screenshot feedback + scene queries.

**Fix:** `get_scene_state` tool — queries all actors, their types, locations, and properties. The AI calls this before every action.

---

## Mistake 5: Building 28 Narrow Tools Instead of 10 General Ones

**What happened (in planning):** The first implementation plan proposed 28 domain-specific tools: `trigger_destruction`, `set_camera_lens`, `add_niagara_track_to_sequence`, etc.

**Why it's wrong:** 
- Each narrow tool requires maintenance
- You can't anticipate every use case
- When UE updates, you have to update 28 tools
- A smart AI model can write the Python script itself if given `execute_python_in_editor`

**Lesson learned:** Build GENERAL PRIMITIVES, not specific features. The Unity MCP doesn't have 50 tools — it has `execute_csharp_code` and the AI writes whatever is needed.

**Fix:** 10 generalized tools. The key tool is `execute_python_in_editor` — the AI writes and runs arbitrary Unreal Python scripts. Infinite flexibility, zero maintenance.

---

## Mistake 6: Hardcoding Project Paths

**What happened:** Early designs assumed a fixed project path like `E:\Epic Games\game folder\...`. 

**Why it's wrong:** The MCP server should work with ANY Unreal project on ANY machine. Other people will use this too.

**Lesson learned:** Zero hardcoded paths. The WebSocket connects to `localhost:30020` — whatever Unreal instance is running, that's what we talk to.

---

## Mistake 7: Embedding AI Logic in the MCP Server

**What happened (in planning):** Early plans had the MCP server running its own LLM (Groq/Gemini) to process prompts and route them.

**Why it's wrong:** The MCP server should be a TOOL PROVIDER, not an AI agent. The intelligence lives in the user's IDE (Cursor, Copilot, Antigravity). The user brings their own model.

**Lesson learned:** Separation of concerns. MCP server = hands. IDE AI model = brain. They don't mix.
