"""
Two-Phase Pipeline - The smart agent orchestrator.

Phase 1: Refine user prompt into precise technical spec (~200 tokens)
Phase 2: Generate Blueprint JSON from refined spec (~500 tokens)
Then: Render C++ via templates and write to project

Total: ~700 tokens vs ~18,000 for the old approach.
"""

import json
import re
import sys
import io

# Fix encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from langchain_core.messages import HumanMessage, SystemMessage

from agents.prompts import REFINER_SYSTEM, GENERATOR_SYSTEM, SINGLE_PHASE_SYSTEM
from unreal_mcp.codegen.schema import Blueprint
from unreal_mcp.codegen.renderer import render_both
from unreal_mcp.codegen.file_writer import write_class_files


# ── Scene Query ──────────────────────────────────────────────────────
async def _get_scene_context() -> str:
    """Try to query the UE scene. Returns a compact string."""
    try:
        from unreal_mcp.tools.scene_tool import get_scene_state, format_scene_for_prompt
        scene = await get_scene_state()
        return format_scene_for_prompt(scene)
    except Exception:
        return "Scene unknown (server may not be running)"


# ── Phase 1: Refine ─────────────────────────────────────────────────
async def refine_prompt(llm, user_prompt: str, scene_context: str) -> str:
    """
    Convert a vague user request into a precise technical spec.
    Uses ~200 tokens.
    """
    system = REFINER_SYSTEM.format(scene_context=scene_context)

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user_prompt),
    ])

    return response.content.strip()


# ── Phase 2: Generate Blueprint JSON ────────────────────────────────
async def generate_blueprint_json(llm, refined_spec: str) -> dict:
    """
    Generate a Blueprint JSON from the refined spec.
    Uses ~500 tokens. Output is pure JSON.
    """
    system = GENERATOR_SYSTEM.format(refined_spec=refined_spec)

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content="Generate the Blueprint JSON now."),
    ])

    raw = response.content.strip()

    # Strip markdown code fences if LLM added them
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    return json.loads(raw)


# ── Single-Phase Fallback ────────────────────────────────────────────
async def single_phase_generate(llm, user_prompt: str) -> dict:
    """
    Fallback: single LLM call that directly outputs Blueprint JSON.
    Simpler but less refined.
    """
    response = await llm.ainvoke([
        SystemMessage(content=SINGLE_PHASE_SYSTEM),
        HumanMessage(content=user_prompt),
    ])

    raw = response.content.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    return json.loads(raw)


# ── Full Pipeline ────────────────────────────────────────────────────
async def two_phase_run(llm, user_prompt: str, write_files: bool = True) -> str:
    """
    The complete two-phase pipeline.

    Args:
        llm: LangChain chat model instance
        user_prompt: Raw user input like "build me a hut"
        write_files: If True, write .h/.cpp to UE project

    Returns:
        Summary string with generated code
    """
    print(f"\n{'='*60}")
    print(f"  Two-Phase Pipeline")
    print(f"{'='*60}")

    # Phase 0: Scene awareness
    print("\n[Phase 0] Querying scene...")
    scene_context = await _get_scene_context()
    print(f"  {scene_context.split(chr(10))[0]}")

    # Phase 1: Refine the prompt
    print(f"\n[Phase 1] Refining prompt...")
    print(f"  Input: \"{user_prompt}\"")

    refined = await refine_prompt(llm, user_prompt, scene_context)

    print(f"\n  Refined spec:")
    for line in refined.split("\n"):
        print(f"    {line}")

    # Phase 2: Generate Blueprint JSON
    print(f"\n[Phase 2] Generating Blueprint JSON...")

    blueprint_data = await generate_blueprint_json(llm, refined)

    blueprint = Blueprint(**blueprint_data)
    prefix = "A" if blueprint.parent_class.startswith("A") else "U"
    print(f"  Class: {prefix}{blueprint.class_name}")
    print(f"  Variables: {len(blueprint.variables)}")
    print(f"  Functions: {len(blueprint.functions)}")

    # Phase 3: Render C++ from templates
    print(f"\n[Phase 3] Rendering C++ code...")
    header_code, source_code = render_both(blueprint)
    print(f"  Header: {len(header_code)} bytes")
    print(f"  Source: {len(source_code)} bytes")

    # Phase 4: Write files (optional)
    file_msg = ""
    if write_files:
        try:
            h_path, cpp_path = write_class_files(
                class_name=blueprint.class_name,
                header_code=header_code,
                source_code=source_code,
            )
            file_msg = f"\n  Written: {h_path}\n  Written: {cpp_path}"
            print(f"\n[Phase 4] Files written!")
            print(file_msg)
        except Exception as e:
            file_msg = f"\n  Could not write files: {e}"
            print(f"\n[Phase 4] {file_msg}")

    # Summary output
    print(f"\n{'='*60}")
    print(f"  DONE - {prefix}{blueprint.class_name}")
    print(f"{'='*60}")

    print(f"\n--- {blueprint.class_name}.h ---")
    print(header_code)
    print(f"\n--- {blueprint.class_name}.cpp ---")
    print(source_code)

    return (
        f"Generated {prefix}{blueprint.class_name}\n"
        f"Variables: {len(blueprint.variables)}, "
        f"Functions: {len(blueprint.functions)}\n"
        f"Header: {len(header_code)} bytes, "
        f"Source: {len(source_code)} bytes"
        f"{file_msg}"
    )


# ── Interactive Two-Phase Mode ───────────────────────────────────────
async def interactive_two_phase(llm, model_label: str):
    """Interactive REPL using the two-phase pipeline."""
    print(f"\n{'='*60}")
    print(f"  Two-Phase Generator - {model_label}")
    print(f"  Describe what you want to create in Unreal.")
    print(f"  Type 'quit' to exit.")
    print(f"{'='*60}")
    print(f"\n  Examples:")
    print(f"    > build a small hut with a door")
    print(f"    > create a floating platform with anti-gravity")
    print(f"    > make a rotating spotlight system")
    print(f"    > design a health pickup actor")
    print(f"\n")

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        try:
            result = await two_phase_run(llm, user_input, write_files=False)
            print(f"\n{result}")
        except json.JSONDecodeError as e:
            print(f"\n  LLM did not output valid JSON: {e}")
            print(f"  Try rephrasing your request.")
        except Exception as e:
            print(f"\n  Error: {e}")
        print()
