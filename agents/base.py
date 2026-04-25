"""
Base Agent Runner — shared MCP connection + agent execution logic.

Every backend (Groq, Ollama, Gemini) calls `run_agent()` with its
own LLM instance.  The MCP connection, tool loading, and execution
loop are identical across backends.

Builder mode (-b) bypasses LangChain entirely — calls the LLM directly
with a lean system prompt, then routes JSON output through processor.py.
This keeps token usage under Groq's free-tier 12k TPM limit.
"""

import sys

# Ensure Windows consoles can print emojis without throwing a UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

from agents.processor import process_agent_output, reset_manager_cache
from unreal_mcp.config.settings import CPP_OUTPUT_DIR, PROJECT_API


# ── MCP Server Configuration ─────────────────────────────────────────
MCP_SERVER_CONFIG = {
    "UnrealMCP": {
        "transport": "sse",
        "url": "http://localhost:8000/sse",
    }
}

# ── Default prompts ───────────────────────────────────────────────────
DEFAULT_PROMPT = (
    "Spawn a cube at X:0, Y:0, Z:100 and sphere at X:1000, Y:1000, Z:1000. "
    "Next, use the list_actors tool to find the full path of the cube you just spawned. "
    "Then, use the set_actor_scale tool to scale that exact cube to X:500.0, Y:500.0, Z:500.0 "
    "so it is huge and easy to see. Finally, tell me that it worked."
)

# Minimal test — only 1 tool call, uses very few tokens
TEST_PROMPT = "List all actors currently in the Unreal level."


# ── Builder System Prompt (Delegator Architecture — CSG Spatial Reasoning) ────
BUILDER_SYSTEM_PROMPT = """\
You are an Unreal Engine 3D world builder. You are a spatial reasoning engine that can construct ANY real-world object by decomposing it into primitive shapes (cube, sphere, cylinder, cone).

Output ONLY a single JSON object. No markdown, no explanation, no code fences.

═══════════════════════════════════════════════════════
CRITICAL RULES — EVERY Spawn/BatchSpawn MUST include:
═══════════════════════════════════════════════════════
1. "EnvironmentCheck": {"RequiresScan": true, "Radius": 2000} — MANDATORY on every Spawn object. This prevents buildings from spawning inside each other.
2. Every structure MUST have a UNIQUE "ID" string.
3. Every structure MUST have a UNIQUE "RequestedLoc" — NEVER [0,0,0] for more than one object.
4. Space structures at least 1500 UU apart.

═══════════════════════════════════════════════════════
STRUCTURE TYPES (set in Parameters.StructureType):
═══════════════════════════════════════════════════════

1. "Building" — Multi-floor box with walls and roof:
{"Intent":"Spawn","ID":"Office_01","Style":"Office_Glass","RequestedLoc":[0,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":2000},
"Parameters":{"StructureType":"Building","Floors":5,"FloorHeight":300,"BuildingWidth":1000,"BuildingDepth":1000,"WallThickness":20,"RoofType":"flat"}}
Use for: houses, offices, apartments, skyscrapers — anything with repeating floors.

2. "Solid" — Single primitive shape:
{"Intent":"Spawn","ID":"Crate_01","Style":"Default","RequestedLoc":[500,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":1000},
"Parameters":{"StructureType":"Solid","Shape":"cube","Width":200,"Depth":200,"Height":200}}
Shapes: cube, sphere, cylinder, cone.
Use for: simple objects — crates, balls, pillars, boulders.

3. "Bridge" — Deck on support pillars:
{"Intent":"Spawn","ID":"Bridge_01","Style":"Bridge_Steel","RequestedLoc":[0,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":3000},
"Parameters":{"StructureType":"Bridge","Span":3000,"DeckWidth":500,"DeckThickness":30,"DeckHeight":500,"PillarWidth":150,"NumPillars":4,"Railings":true}}

4. "Composite" — YOUR MOST POWERFUL TOOL. Build ANY complex object from primitives:
{"Intent":"Spawn","ID":"Tower_01","Style":"WatchTower","RequestedLoc":[0,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":2000},
"Parameters":{"StructureType":"Composite","Width":800,"Depth":800},
"Parts":[
  {"Shape":"cylinder","Offset":[0,0,0],"Scale":[3,3,8],"Label":"Tower_Body"},
  {"Shape":"cube","Offset":[0,0,850],"Scale":[5,5,0.3],"Label":"Platform"},
  {"Shape":"cone","Offset":[0,0,900],"Scale":[4,4,3],"Label":"Roof"},
  {"Shape":"cube","Offset":[350,0,400],"Scale":[0.3,0.3,6],"Label":"Ladder"}
]}

═══════════════════════════════════════════════════════
HOW TO BUILD ANY OBJECT (CSG Spatial Reasoning):
═══════════════════════════════════════════════════════
When asked to build something you've never seen, THINK step by step:
1. What is the basic silhouette? (tall cylinder? wide box? dome?)
2. What are the major sub-parts? (body, roof, legs, arms, base, platform)
3. What primitive shape best approximates each part? (cube=box/panel/wall, cylinder=tube/pole/tower, sphere=dome/ball, cone=roof/point/funnel)
4. What is each part's position relative to the base? (Offset [X,Y,Z])
5. What is each part's scale? (Scale [SX,SY,SZ], where 1.0 = 100 UU = 1 meter)

EXAMPLES of spatial decomposition:
• Lamp Post: cylinder body [0.2,0.2,4] + sphere bulb at top [0.5,0.5,0.5]
• Table: cube top [1.5,1,0.1] at Z=80 + 4x cylinder legs [0.1,0.1,0.8] at corners
• Car: cube body [4,2,1] + cube cabin [2,1.8,1] at offset + 4x cylinder wheels [0.4,0.4,0.4]
• Fountain: cylinder base [3,3,0.3] + cylinder mid [1,1,2] + sphere top [1.5,1.5,1]
• Helicopter: cube body [3,1.5,1.5] + cylinder tail [0.3,0.3,3] + cube rotor [5,0.1,0.1] + cube tail rotor [0.1,1,0.1]
• Tree: cylinder trunk [0.5,0.5,4] + sphere canopy [3,3,3] at Z=400
• Chair: cube seat [0.5,0.5,0.05] + cube back [0.5,0.05,0.5] + 4x cylinder legs [0.05,0.05,0.5]

═══════════════════════════════════════════════════════
INTENTS:
═══════════════════════════════════════════════════════
- Spawn: create one structure
- BatchSpawn: {"Intent":"BatchSpawn","Blueprints":[...]} — array of Spawn-like objects. Each blueprint MUST have its own EnvironmentCheck.
- ClearAll: {"Intent":"ClearAll"}
- Destroy: {"Intent":"Destroy","TargetID":"<id>"}
- CreateClass: {"Action":"CreateClass","ClassName":"<AMyActor>","Files":[...]}
- GenerateGeometry: Runtime dynamic mesh with boolean cuts (see below)

═══════════════════════════════════════════════════════
GENERATE GEOMETRY (Dynamic Mesh + Boolean Operations):
═══════════════════════════════════════════════════════
Use this when you need TRUE geometry modeling — walls with cut-out windows, doors with arches, panels with holes, sculpted shapes. This creates REAL mesh geometry at runtime, not just scaled cubes.

{"Intent":"GenerateGeometry","ID":"SciFi_Wall_01","RequestedLoc":[0,0,0],"Color":"steel",
"BaseShape":{"Type":"Box","Dimensions":[1000,20,500]},
"Operations":[
  {"Action":"BooleanSubtract","ToolShape":"Cylinder","Radius":150,"Height":50,"RelativeLoc":[0,0,250]},
  {"Action":"BooleanSubtract","ToolShape":"Box","Dimensions":[200,50,300],"RelativeLoc":[-300,0,150]}
]}

BaseShape Types: Box (Dimensions: [W,D,H]), Cylinder (Dimensions: [Radius,Radius,Height]), Sphere (Dimensions: [Radius,Radius,Radius])
Operation Actions: BooleanSubtract (cut hole), BooleanUnion (merge shapes), BooleanIntersect (keep overlap)
ToolShape Types: Box, Cylinder, Sphere
Color options: red, blue, green, yellow, orange, purple, cyan, white, black, gray, steel, gold, concrete, wood

EXAMPLES:
• Wall with circular window: BaseShape Box [1000,20,500] + BooleanSubtract Cylinder R:120 at [0,0,300]
• Wall with door: BaseShape Box [1000,20,500] + BooleanSubtract Box [200,50,400] at [0,0,200]
• Wall with 3 windows: BaseShape Box [1200,20,500] + 3x BooleanSubtract Cylinder at different X offsets
• Dome with hole: BaseShape Sphere [300,300,300] + BooleanSubtract Cylinder R:100 at top

═══════════════════════════════════════════════════════
MANDATORY RULES (NEVER VIOLATE):
═══════════════════════════════════════════════════════
1. ANY building with floors/stories/levels MUST use StructureType "Building" — NEVER Composite.
2. A "hut" is a 1-floor Building with RoofType "pointed". A "house" is a Building. A "cabin" is a Building.
3. Composite is ONLY for non-building objects: vehicles, furniture, statues, trees, robots, machines.
4. Scale 1.0 = 100 UU = 1 meter. A 3-story house is about 9 meters tall (Floors:3, FloorHeight:300).

═══════════════════════════════════════════════════════
DECISION GUIDE:
═══════════════════════════════════════════════════════
- house/hut/cabin/cottage/shack/bungalow → "Building" (Floors:1, RoofType:"pointed")
- office/apartment/skyscraper/tower block → "Building" (Floors:N, RoofType:"flat")
- any building with N stories/floors → "Building" (Floors:N)
- single cube/sphere/cylinder/ball/rock/crate → "Solid"
- bridge/overpass → "Bridge"
- wall with window/door/hole/cutout/arch → GenerateGeometry
- sculpted/carved/modeled geometry → GenerateGeometry
- vehicle/furniture/statue/tree/robot/machine → "Composite"
- mixed scene → BatchSpawn with varied StructureTypes

═══════════════════════════════════════════════════════
BUILDING EXAMPLES:
═══════════════════════════════════════════════════════
• 3-story house with pointed roof:
  {"Intent":"Spawn","ID":"House_01","Style":"Residential","RequestedLoc":[0,0,0],
   "EnvironmentCheck":{"RequiresScan":true,"Radius":2000},
   "Parameters":{"StructureType":"Building","Floors":3,"FloorHeight":300,"BuildingWidth":800,"BuildingDepth":800,"WallThickness":20,"RoofType":"pointed"}}

• Hut:
  {"Intent":"Spawn","ID":"Hut_01","Style":"Wooden","RequestedLoc":[0,0,0],
   "EnvironmentCheck":{"RequiresScan":true,"Radius":1000},
   "Parameters":{"StructureType":"Building","Floors":1,"FloorHeight":250,"BuildingWidth":400,"BuildingDepth":400,"WallThickness":15,"RoofType":"pointed"}}

• Skyscraper:
  {"Intent":"Spawn","ID":"Tower_01","Style":"Office_Glass","RequestedLoc":[0,0,0],
   "EnvironmentCheck":{"RequiresScan":true,"Radius":3000},
   "Parameters":{"StructureType":"Building","Floors":20,"FloorHeight":300,"BuildingWidth":1200,"BuildingDepth":1200,"WallThickness":30,"RoofType":"flat"}}

POSITIONING:
- 1000 UU = 10 meters. Z=0 is ground. Positive Z = up.
- For BatchSpawn: calculate positions so structures form the requested layout (row, circle, grid, etc.)

SCALE REFERENCE (Scale 1.0 = 100 UU ≈ 1 meter):
- Person height: Z=1.8 | Door: [1,0.1,2] | Table: [1.5,1,0.8]
- Wall segment: [10,0.2,3] | Pillar: [0.5,0.5,5]
- Small house: Building with Width=800,Depth=800,Floors=2 | Hut: Width=400,Depth=400,Floors=1
- Skyscraper: Width=1200,Depth=1200,Floors=20

Output raw JSON only."""

BUILDER_DEFAULT_PROMPT = "Build a 3-story house at the origin with a pointed roof."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_agent(llm, model_label: str, prompt: str = None,
                    interactive: bool = False, builder: bool = False):
    """
    Connect to the MCP server, load tools, create a LangChain agent,
    and execute the given prompt.

    Args:
        llm:          An initialized LangChain chat model (any provider).
        model_label:  Human-readable name for logging.
        prompt:       The instruction to send. Falls back to DEFAULT_PROMPT.
        interactive:  If True, enter a loop where the user types commands.
        builder:      If True, use Builder mode (bypasses LangChain, calls LLM directly).
    """
    mode_label = "Builder 🏗️" if builder else "Standard"
    print(f"🤖 Booting up {model_label} [{mode_label}] and connecting to Unreal Engine...")

    if builder:
        # ── Builder mode: LLM direct call, no LangChain agent ────
        print(f"🏗️  Builder mode — LLM will output strict JSON (no ReAct overhead).")
        if interactive:
            await _interactive_builder_loop(llm, model_label)
        else:
            prompt = prompt or BUILDER_DEFAULT_PROMPT
            await _run_builder(llm, prompt)
    else:
        # ── Standard mode: LangChain tool-calling agent ──────────
        client = MultiServerMCPClient(MCP_SERVER_CONFIG)
        tools = await client.get_tools()
        print(f"🛠️  Loaded {len(tools)} tools from FastMCP.")
        agent = create_agent(llm, tools)

        if interactive:
            await _interactive_loop(agent, model_label)
        else:
            prompt = prompt or DEFAULT_PROMPT
            await _run_single(agent, prompt)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Builder Mode — Direct LLM Call (no LangChain overhead)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import json as _json
import os as _os

# ── Recipe Store — Pre-defined building templates ────────────────────
_RECIPE_DB = None

def _load_recipes():
    """Load the building recipe database from recipes/buildings.json."""
    global _RECIPE_DB
    if _RECIPE_DB is not None:
        return _RECIPE_DB
    recipe_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "recipes", "buildings.json")
    if _os.path.exists(recipe_path):
        with open(recipe_path, "r", encoding="utf-8") as f:
            _RECIPE_DB = _json.load(f).get("recipes", [])
        print(f"📚 Loaded {len(_RECIPE_DB)} building recipes")
    else:
        _RECIPE_DB = []
    return _RECIPE_DB


def _find_recipe(user_prompt: str):
    """Search recipes for a match based on name or aliases."""
    recipes = _load_recipes()
    prompt_lower = user_prompt.lower()
    
    best_match = None
    for recipe in recipes:
        # Check exact name match
        if recipe["name"] in prompt_lower:
            best_match = recipe
            break
        # Check aliases
        for alias in recipe.get("aliases", []):
            if alias.replace("_", " ") in prompt_lower:
                best_match = recipe
                break
        if best_match:
            break
    
    return best_match


def _enrich_prompt_with_recipe(user_prompt: str) -> str:
    """If a recipe matches, inject it into the prompt so the LLM uses exact parts."""
    recipe = _find_recipe(user_prompt)
    if not recipe:
        return user_prompt
    
    print(f"📐 Recipe matched: '{recipe['name']}' ({len(recipe.get('parts', recipe.get('decorations', [])))} parts)")
def _recipe_to_json(recipe: dict, user_prompt: str) -> str:
    """Convert a recipe directly to Spawn JSON — no LLM needed."""
    import re
    import time
    
    # Try to extract location from user prompt like "at 500 0 0"
    loc = [0, 0, 0]
    loc_match = re.search(r'at\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)', user_prompt)
    if loc_match:
        loc = [int(loc_match.group(1)), int(loc_match.group(2)), int(loc_match.group(3))]
    
    # Try to extract floor count like "3-story" or "5 floor"
    floors = recipe.get("defaultFloors", 1)
    floor_match = re.search(r'(\d+)\s*(?:stor|floor|level)', user_prompt.lower())
    if floor_match:
        floors = int(floor_match.group(1))
    
    structure_type = recipe.get("structureType", "Composite")
    name = recipe["name"]
    # Unique ID with timestamp so you can build multiple of the same type
    uid = int(time.time() * 1000) % 100000
    
    if structure_type == "Building":
        result = {
            "Intent": "Spawn",
            "ID": f"{name.title()}_{uid}",
            "Style": recipe.get("aliases", [name])[0] if recipe.get("aliases") else name,
            "RequestedLoc": loc,
            "EnvironmentCheck": {"RequiresScan": True, "Radius": 2000},
            "Parameters": {
                "StructureType": "Building",
                "Floors": floors,
                "FloorHeight": recipe.get("floorHeight", 300),
                "BuildingWidth": recipe.get("width", 800),
                "BuildingDepth": recipe.get("depth", 800),
                "WallThickness": recipe.get("wallThickness", 20),
                "RoofType": recipe.get("roofType", "flat"),
            }
        }
        # Add decorations as Parts if the recipe has them
        if recipe.get("decorations"):
            result["Parts"] = recipe["decorations"]
    else:
        # Composite — use parts directly
        result = {
            "Intent": "Spawn",
            "ID": f"{name.title()}_{uid}",
            "Style": name.title(),
            "RequestedLoc": loc,
            "EnvironmentCheck": {"RequiresScan": True, "Radius": 2000},
            "Parameters": {
                "StructureType": "Composite",
                "Width": recipe.get("width", 400),
                "Depth": recipe.get("depth", 400),
            },
            "Parts": [
                {
                    "Shape": p["shape"],
                    "Offset": p["offset"],
                    "Scale": p["scale"],
                    "Label": p["name"],
                    "material": p.get("material", ""),
                }
                for p in recipe.get("parts", [])
            ]
        }
    
    return _json.dumps(result)


async def _run_builder(llm, prompt: str):
    """Call the LLM directly with the builder system prompt, then route JSON to processor."""
    print(f"\n🗣️ Prompt: {prompt}\n")

    # Check if we have a recipe — if so, bypass the LLM entirely
    recipe = _find_recipe(prompt)
    if recipe:
        parts_count = len(recipe.get('parts', recipe.get('decorations', [])))
        print(f"📐 Recipe matched: '{recipe['name']}' ({parts_count} parts) — bypassing LLM")
        raw = _recipe_to_json(recipe, prompt)
        print(f"📦 Recipe JSON:\n{raw}\n")
        
        # Force recipe composites through LEGACY path (individual actors)
        # C++ HISM merges all same-mesh instances into one visual entity = ugly single block
        data = _json.loads(raw)
        if data.get("Parameters", {}).get("StructureType") == "Composite":
            from agents.processor import _handle_spawn_fallback
            print("🔧 Using direct-spawn mode for recipe (individual actors per part)")
            result = await _handle_spawn_fallback(data)
            print(f"\n{result}")
            return
        
        result = await process_agent_output(raw, CPP_OUTPUT_DIR, PROJECT_API, user_prompt=prompt)
        print(f"\n{result}")
        return

    # No recipe — use LLM
    messages = [
        SystemMessage(content=BUILDER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content

    print(f"📦 Raw LLM output:\n{raw}\n")

    result = await process_agent_output(raw, CPP_OUTPUT_DIR, PROJECT_API, user_prompt=prompt)
    print(f"\n{result}")


async def _interactive_builder_loop(llm, model_label: str):
    """Interactive REPL for builder mode — each command is a fresh LLM call."""
    print(f"\n{'='*60}")
    print(f"  🏗️  Builder Mode — {model_label}")
    print(f"  Type a command and press Enter.")
    print(f"  Type 'quit' or 'exit' to stop.")
    print(f"{'='*60}")
    print(f"\n  Quick commands to try:")
    print(f"    • build a 5 floor skyscraper at 0 0 0")
    print(f"    • build a street with houses on both sides")
    print(f"    • clear everything")
    print(f"    • create a freeze trap C++ class")
    print(f"  Utility commands:")
    print(f"    • refresh  — re-discover the CityManager actor")
    print(f"\n")

    while True:
        try:
            user_input = input("🏗️ Builder > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break
        if user_input.lower() == "refresh":
            reset_manager_cache()
            print("🔄 CityManager cache cleared. Will re-discover on next command.")
            continue

        try:
            await _run_builder(llm, user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}")
        print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Standard Mode — LangChain Tool-Calling Agent
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_single(agent, prompt: str):
    """Execute a single prompt through the LangChain agent and print the result."""
    print(f"\n🗣️ Prompt: {prompt}\n")

    response = await agent.ainvoke({
        "messages": [HumanMessage(content=prompt)]
    })

    print("\n✅ Final Response:")
    print(response["messages"][-1].content)


async def _interactive_loop(agent, model_label: str):
    """Interactive REPL — type commands one at a time to save API quota."""
    print(f"\n{'='*60}")
    print(f"  🎮 Interactive Mode — {model_label}")
    print(f"  Type a command and press Enter.")
    print(f"  Type 'quit' or 'exit' to stop.")
    print(f"{'='*60}")
    print(f"\n  Quick commands to try:")
    print(f"    • list all actors")
    print(f"    • spawn a cube at 0 0 200")
    print(f"    • spawn a sphere at 500 500 500")
    print(f"\n")

    while True:
        try:
            user_input = input("🎮 You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break

        try:
            await _run_single(agent, user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}")
        print()
