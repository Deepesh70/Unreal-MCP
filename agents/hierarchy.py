"""
Hierarchical Multi-Agent System — Feature 6: Mayor → Architect → Builder.

Splits massive scene requests into a three-tier agent hierarchy:
  - Mayor:     Zones the city (Residential, Commercial, Industrial, Park)
  - Architect: Designs street layout + building slots per zone
  - Builder:   Generates final BatchSpawn JSON per block

This allows infinite-scale city generation without hitting LLM token limits.

Usage:
    from agents.hierarchy import run_hierarchical
    result = await run_hierarchical(llm, prompt, process_fn)
"""

import json
import math
import re

from langchain_core.messages import HumanMessage, SystemMessage


# ── Agent System Prompts ─────────────────────────────────────────────

MAYOR_SYSTEM_PROMPT = """\
You are the Mayor — a high-level city planner. You divide a build request into ZONES.

Output ONLY a JSON object with this structure:
{
  "ZoningPlan": {
    "CityName": "string",
    "Zones": [
      {
        "Name": "Residential_North",
        "Type": "Residential|Commercial|Industrial|Park|Mixed",
        "Center": [X, Y, 0],
        "Radius": 3000,
        "BuildingCount": 8,
        "StyleHints": ["House_Wood_Small", "House_Brick_Medium"],
        "Description": "A quiet residential area with small houses"
      }
    ]
  }
}

RULES:
1. Space zone centers at least 5000 UU apart
2. Total building count should match the user's intent
3. Each zone should have 4-12 buildings (keeps within token budget)
4. Use varied styles across zones for visual diversity
5. Z=0 is ground level. Keep all centers at Z=0.
6. Output raw JSON only. No markdown, no explanation."""


ARCHITECT_SYSTEM_PROMPT = """\
You are the Architect — you design the layout for ONE zone of a city.

You receive a zone specification and must output a BatchSpawn JSON with the exact
number of buildings requested, placed in a logical urban layout.

RULES:
1. Every building MUST have "EnvironmentCheck":{"RequiresScan":true,"Radius":2000}
2. Every building needs a UNIQUE "ID" (use the prefix provided)
3. Space buildings at least 1500 UU apart
4. Vary building sizes, floors (1-10), and roof types
5. Use the Style hints provided for the zone
6. Include "Connect" intents for roads between key buildings

Output a JSON array with BatchSpawn and Connect intents. Example:
[
  {"Intent":"BatchSpawn","Blueprints":[...]},
  {"Intent":"Connect","ID":"Road_01","Nodes":[[x1,y1,0],[x2,y2,0]],"Width":300}
]

Output raw JSON only. No markdown."""


# ── Estimation ───────────────────────────────────────────────────────

def estimate_scale(prompt: str) -> int:
    """Estimate total building count from the prompt."""
    prompt_lower = prompt.lower()

    # Direct numbers
    match = re.search(
        r'(\d+)\s*(buildings?|houses?|structures?|towers?)',
        prompt_lower
    )
    if match:
        return int(match.group(1))

    # Area keywords
    area_map = {
        'metropolis': 100, 'city': 60, 'downtown': 40,
        'district': 30, 'town': 20, 'neighborhood': 15,
        'village': 10, 'hamlet': 6, 'street': 8,
        'block': 6, 'compound': 5,
    }
    for keyword, count in area_map.items():
        if keyword in prompt_lower:
            return count

    return 8  # Default


def should_use_hierarchy(prompt: str) -> bool:
    """Check if the prompt warrants hierarchical generation."""
    count = estimate_scale(prompt)
    # Use hierarchy for 12+ buildings
    return count >= 12


# ── Main Pipeline ────────────────────────────────────────────────────

async def run_hierarchical(llm, prompt: str, process_fn, model_label: str = "") -> str:
    """
    Execute the full Mayor → Architect → Builder pipeline.

    Args:
        llm:          The LangChain chat model instance.
        prompt:       The user's original prompt.
        process_fn:   Async function to process LLM output (process_agent_output).
        model_label:  Human-readable model name for logging.

    Returns:
        A summary string of all buildings placed.
    """
    est_count = estimate_scale(prompt)
    print(f"\n🏛️  Hierarchical Mode — ~{est_count} buildings estimated")
    print(f"   Phase 1: Mayor zoning the city...")

    # ── Phase 1: Mayor ───────────────────────────────────────────
    mayor_messages = [
        SystemMessage(content=MAYOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Plan a city for this request: \"{prompt}\"\n"
                             f"Target approximately {est_count} buildings total."),
    ]

    try:
        mayor_response = await llm.ainvoke(mayor_messages)
        mayor_raw = mayor_response.content.strip()

        # Clean markdown if present
        if mayor_raw.startswith("```"):
            mayor_raw = re.sub(r'^```(?:json)?\s*\n?', '', mayor_raw)
            mayor_raw = re.sub(r'\n?```\s*$', '', mayor_raw)

        zoning_plan = json.loads(mayor_raw)
    except json.JSONDecodeError:
        print("   ⚠️  Mayor output wasn't valid JSON. Falling back to single-zone.")
        zoning_plan = {
            "ZoningPlan": {
                "CityName": "FallbackCity",
                "Zones": [{
                    "Name": "Main",
                    "Type": "Mixed",
                    "Center": [0, 0, 0],
                    "Radius": 5000,
                    "BuildingCount": est_count,
                    "StyleHints": ["House_Wood_Small", "Office_Concrete_Large"],
                    "Description": prompt,
                }]
            }
        }
    except Exception as e:
        return f"❌ Mayor phase failed: {e}"

    zones = zoning_plan.get("ZoningPlan", {}).get("Zones", [])
    city_name = zoning_plan.get("ZoningPlan", {}).get("CityName", "City")

    print(f"   ✅ Mayor zoned '{city_name}' into {len(zones)} zone(s):")
    for z in zones:
        print(f"      • {z.get('Name', '?')} ({z.get('Type', '?')}) — "
              f"{z.get('BuildingCount', '?')} buildings")

    # ── Phase 2: Architect (per zone) ────────────────────────────
    all_results = []
    total_success = 0
    total_failed = 0

    for i, zone in enumerate(zones):
        zone_name = zone.get("Name", f"Zone_{i}")
        zone_count = zone.get("BuildingCount", 5)
        zone_center = zone.get("Center", [0, 0, 0])
        zone_styles = zone.get("StyleHints", ["Default"])
        zone_desc = zone.get("Description", "")

        print(f"\n🏗️  Phase 2: Architect designing {zone_name} ({zone_count} buildings)...")

        architect_prompt = (
            f"Design the '{zone_name}' zone of '{city_name}'.\n"
            f"Zone type: {zone.get('Type', 'Mixed')}\n"
            f"Description: {zone_desc}\n"
            f"Center coordinates: {zone_center}\n"
            f"Build exactly {zone_count} buildings.\n"
            f"Use ID prefix: '{zone_name}_Bldg_'\n"
            f"Preferred styles: {', '.join(zone_styles)}\n"
            f"Use StructureType 'Building' or 'Composite' based on style.\n"
            f"Also create 1-2 roads connecting key buildings."
        )

        architect_messages = [
            SystemMessage(content=ARCHITECT_SYSTEM_PROMPT),
            HumanMessage(content=architect_prompt),
        ]

        try:
            arch_response = await llm.ainvoke(architect_messages)
            arch_raw = arch_response.content.strip()

            # Clean markdown
            if arch_raw.startswith("```"):
                arch_raw = re.sub(r'^```(?:json)?\s*\n?', '', arch_raw)
                arch_raw = re.sub(r'\n?```\s*$', '', arch_raw)

            # Parse — could be a single object or an array
            arch_data = json.loads(arch_raw)

            # Process each intent
            if isinstance(arch_data, list):
                for intent_obj in arch_data:
                    result = await process_fn(json.dumps(intent_obj))
                    all_results.append(result)
                    print(f"   {result}")
                    total_success += result.count("✅")
                    total_failed += result.count("❌")
            elif isinstance(arch_data, dict):
                result = await process_fn(json.dumps(arch_data))
                all_results.append(result)
                print(f"   {result}")
                total_success += result.count("✅")
                total_failed += result.count("❌")

        except Exception as e:
            error_msg = f"   ❌ Architect failed for {zone_name}: {e}"
            all_results.append(error_msg)
            print(error_msg)
            total_failed += 1

    # ── Summary ──────────────────────────────────────────────────
    summary = (
        f"\n🏙️  Hierarchical generation complete!\n"
        f"   City: {city_name}\n"
        f"   {len(zones)} zone(s) processed\n"
        f"   {total_success} element(s) placed successfully\n"
    )
    if total_failed > 0:
        summary += f"   {total_failed} element(s) failed\n"

    return summary
