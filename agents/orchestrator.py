"""
Orchestrator — Token-aware complexity routing for massive scenes.

When a user requests a complex scene ("build a medieval village with 40 buildings"),
the Orchestrator estimates the required output tokens and decides whether to split
the request into multiple LLM calls to stay within the model's token limit.

Each chunk targets a spatial "zone" (northern section, central area, etc.)
and maximizes detail within the available token budget.

Usage:
    from agents.orchestrator import should_orchestrate, run_orchestrated

    if should_orchestrate(prompt, max_tokens=4096):
        result = await run_orchestrated(llm, prompt, max_tokens=4096, ...)
"""

import math
import re

from langchain_core.messages import HumanMessage, SystemMessage


# ── Token Budget Constants ───────────────────────────────────────────
TOKENS_PER_BUILDING = 200      # Average tokens for one building spec
OVERHEAD_TOKENS = 150           # JSON structure overhead (Intent, EnvironmentCheck, etc.)
SAFETY_MARGIN = 0.70            # Use only 70% of max to avoid truncation

# Model-specific output token limits
MODEL_TOKEN_BUDGETS = {
    "groq": 4096,
    "gemini": 8192,
    "ollama": 4096,       # Conservative default for local models
}


# ── Zone definitions for spatial partitioning ────────────────────────
# Each zone gets a coordinate offset to prevent overlap between chunks.
_ZONE_DEFS = [
    ("northern section",    0,     3000),
    ("eastern section",     3000,  0),
    ("southern section",    0,    -3000),
    ("western section",    -3000,  0),
    ("central area",        0,     0),
    ("northeastern corner", 3000,  3000),
    ("southeastern corner", 3000, -3000),
    ("southwestern corner",-3000, -3000),
    ("northwestern corner",-3000,  3000),
    ("outer ring",          5000,  0),
]


def estimate_building_count(prompt: str) -> int:
    """
    Estimate how many buildings the user wants from their natural language prompt.

    Uses regex to find explicit counts, then falls back to area keyword heuristics.
    """
    prompt_lower = prompt.lower()

    # Direct numbers: "40 buildings", "50 houses", "20 structures"
    match = re.search(
        r'(\d+)\s*(buildings?|houses?|structures?|towers?|offices?|shops?|homes?)',
        prompt_lower
    )
    if match:
        return int(match.group(1))

    # Range expressions: "10-15 houses"
    match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)\s*(buildings?|houses?|structures?)', prompt_lower)
    if match:
        return (int(match.group(1)) + int(match.group(2))) // 2

    # Area descriptors (keyword → estimated building count)
    area_keywords = {
        'metropolis': 200, 'city': 100, 'downtown': 60,
        'district': 40,    'town': 30,  'neighborhood': 20,
        'village': 15,     'hamlet': 8,  'street': 10,
        'block': 8,        'row': 5,     'compound': 6,
    }
    for keyword, count in area_keywords.items():
        if keyword in prompt_lower:
            return count

    # Detail multipliers
    detail_count = sum(1 for word in ('detailed', 'complex', 'varied', 'unique', 'diverse')
                       if word in prompt_lower)
    if detail_count > 0:
        return max(8, 5 + detail_count * 3)

    return 5  # Default: assume a small scene


def should_orchestrate(prompt: str, max_tokens: int) -> bool:
    """Check if the prompt likely needs more output tokens than the model can produce."""
    count = estimate_building_count(prompt)
    estimated = (count * TOKENS_PER_BUILDING) + OVERHEAD_TOKENS
    budget = max_tokens * SAFETY_MARGIN
    return estimated > budget


def calculate_chunks(prompt: str, max_tokens: int) -> int:
    """Calculate how many LLM calls are needed to cover the scene."""
    count = estimate_building_count(prompt)
    estimated = (count * TOKENS_PER_BUILDING) + OVERHEAD_TOKENS
    budget = max_tokens * SAFETY_MARGIN
    return max(1, math.ceil(estimated / budget))


def generate_zone_prompts(original_prompt: str, num_chunks: int,
                           system_prompt: str) -> list:
    """
    Split a scene prompt into zone-specific sub-prompts.

    Each sub-prompt targets a spatial zone with a coordinate offset
    and a proportional share of the total building count.
    """
    total_count = estimate_building_count(original_prompt)
    per_chunk = math.ceil(total_count / num_chunks)

    prompts = []
    for i in range(num_chunks):
        zone_name, offset_x, offset_y = _ZONE_DEFS[i % len(_ZONE_DEFS)]
        start_idx = i * per_chunk
        end_idx = min((i + 1) * per_chunk, total_count)
        actual_count = end_idx - start_idx

        if actual_count <= 0:
            break

        sub_prompt = (
            f"You are generating part {i + 1} of {num_chunks} of a larger scene.\n"
            f"Original request: \"{original_prompt}\"\n\n"
            f"Your task: Generate the {zone_name} with exactly {actual_count} buildings.\n"
            f"Use IDs starting from 'Bldg_{start_idx + 1:03d}' to 'Bldg_{end_idx:03d}'.\n"
            f"Base coordinates: offset all X positions by {offset_x} and Y positions by {offset_y}.\n"
            f"Vary building styles, sizes, and roof types for visual diversity.\n"
            f"Space buildings at least 1500 UU apart.\n"
            f"EnvironmentCheck.RequiresScan should be true for auto-nudge.\n\n"
            f"Output a single BatchSpawn JSON with exactly {actual_count} blueprints."
        )
        prompts.append(sub_prompt)

    return prompts


async def run_orchestrated(llm, prompt: str, max_tokens: int,
                           system_prompt: str, process_fn, model_label: str = ""):
    """
    Run a complex scene generation across multiple LLM calls.

    Args:
        llm:            The LangChain chat model instance.
        prompt:         The user's original prompt.
        max_tokens:     The model's max output token limit.
        system_prompt:  The builder system prompt string.
        process_fn:     Async function to process LLM output (process_agent_output).
        model_label:    Human-readable model name for logging.

    Returns:
        A summary string of all chunks processed.
    """
    num_chunks = calculate_chunks(prompt, max_tokens)
    zone_prompts = generate_zone_prompts(prompt, num_chunks, system_prompt)

    est_count = estimate_building_count(prompt)
    print(f"\n🧠 Complex scene detected — ~{est_count} buildings estimated.")
    print(f"   Splitting into {num_chunks} generation pass(es) to stay within token budget.")
    print(f"   Model budget: {max_tokens} tokens × {SAFETY_MARGIN:.0%} safety = "
          f"{int(max_tokens * SAFETY_MARGIN)} usable tokens.\n")

    all_results = []
    total_success = 0
    total_failed = 0

    for i, sub_prompt in enumerate(zone_prompts):
        zone_name = _ZONE_DEFS[i % len(_ZONE_DEFS)][0]
        print(f"📦 Pass {i + 1}/{num_chunks} — Generating {zone_name}...")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=sub_prompt),
        ]

        try:
            response = await llm.ainvoke(messages)
            raw = response.content
            result = await process_fn(raw)
            all_results.append(result)
            print(f"   {result}\n")

            # Count successes/failures from the result string
            total_success += result.count("✅")
            total_failed += result.count("❌")

        except Exception as e:
            error_msg = f"   ❌ Pass {i + 1} failed: {e}"
            all_results.append(error_msg)
            print(error_msg + "\n")

    # Summary
    summary = (
        f"\n🏙️ Scene generation complete!\n"
        f"   {num_chunks} passes processed\n"
        f"   {total_success} building(s) placed successfully\n"
    )
    if total_failed > 0:
        summary += f"   {total_failed} building(s) failed\n"

    return summary
