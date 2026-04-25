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


# ── Builder System Prompt (Trimmed for token efficiency) ────
BUILDER_SYSTEM_PROMPT = """\
You are an Unreal Engine 3D builder. Output ONLY a single JSON object. No markdown, no explanation.

RULES:
1. Every Spawn MUST have "EnvironmentCheck":{"RequiresScan":true,"Radius":2000}
2. Every structure needs a UNIQUE "ID" and UNIQUE "RequestedLoc" (space 1500+ UU apart)
3. Scale 1.0 = 100 UU = 1 meter. Z=0 is ground, +Z is up.

STRUCTURE TYPES:

"Composite" — Build ANY object from primitive parts:
{"Intent":"Spawn","ID":"Car_01","RequestedLoc":[0,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":2000},
"Parameters":{"StructureType":"Composite","Width":400,"Depth":200},
"Parts":[
  {"Shape":"cube","Offset":[0,0,50],"Scale":[4,2,1],"Label":"Body","material":"blue"},
  {"Shape":"cube","Offset":[0,0,130],"Scale":[2,1.8,1],"Label":"Cabin","material":"cyan"},
  {"Shape":"cylinder","Offset":[-120,100,20],"Scale":[0.4,0.4,0.2],"Label":"Wheel_FL","material":"black"}
]}
Shapes: cube, sphere, cylinder, cone
Materials: red, blue, green, yellow, orange, purple, cyan, white, black, gray, steel, gold, concrete, wood, stone

"Building" — Multi-floor box:
{"Intent":"Spawn","ID":"House_01","RequestedLoc":[0,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":2000},
"Parameters":{"StructureType":"Building","Floors":3,"FloorHeight":300,"BuildingWidth":800,"BuildingDepth":800,"WallThickness":20,"RoofType":"pointed"}}

"Solid" — Single shape:
{"Intent":"Spawn","ID":"Rock_01","RequestedLoc":[500,0,0],
"EnvironmentCheck":{"RequiresScan":true,"Radius":1000},
"Parameters":{"StructureType":"Solid","Shape":"sphere","Width":200,"Depth":200,"Height":200}}

OTHER: ClearAll: {"Intent":"ClearAll"} | Destroy: {"Intent":"Destroy","TargetID":"<id>"} | BatchSpawn: {"Intent":"BatchSpawn","Blueprints":[...]}

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
        
        # Force ALL recipes through LEGACY path (individual actors per part)
        # C++ HISM has issues: wrong floor counts, no per-part colors, single-block visual
        data = _json.loads(raw)
        from agents.processor import _handle_spawn_fallback
        struct_type = data.get("Parameters", {}).get("StructureType", "Composite")
        floors = data.get("Parameters", {}).get("Floors", "?")
        print(f"🔧 Direct-spawn: {struct_type} | Floors: {floors}")
        result = await _handle_spawn_fallback(data)
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
