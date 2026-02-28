"""
Live Builder Pipeline - Builds things in UE via WebSocket in real time.

Phase 1: Refine user prompt into building spec (~200 tokens)
Phase 2: Generate build plan JSON with spawn/scale/rotate steps (~800 tokens)
Phase 3: Execute each step live against Unreal Engine via WebSocket

Result: Objects appear in the UE viewport immediately.
"""

import json
import re
import sys
import io
import asyncio

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from langchain_core.messages import HumanMessage, SystemMessage

from agents.builder_prompts import BUILDER_SYSTEM, BUILDER_REFINER
from unreal_mcp.tools.spawning import spawn_actor_internal
from unreal_mcp.tools.transform import set_actor_scale, set_actor_rotation


async def _get_scene_context() -> str:
    """Query UE scene for context."""
    try:
        from unreal_mcp.tools.scene_tool import get_scene_state, format_scene_for_prompt
        scene = await get_scene_state()
        return format_scene_for_prompt(scene)
    except Exception:
        return "Scene unknown"


async def _refine_build_prompt(llm, user_prompt: str) -> str:
    """Phase 1: Convert vague request into precise build spec."""
    response = await llm.ainvoke([
        SystemMessage(content=BUILDER_REFINER),
        HumanMessage(content=user_prompt),
    ])
    return response.content.strip()


async def _generate_build_plan(llm, refined: str, scene_context: str) -> dict:
    """Phase 2: Generate the build plan JSON."""
    import traceback

    system = BUILDER_SYSTEM.format(scene_context=scene_context)

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=f"Build this:\n{refined}\n\nOutput ONLY valid JSON. Start with {{ end with }}. No other text."),
        ])
    except Exception as e:
        print(f"\n  [ERROR] LLM call failed: {e}")
        traceback.print_exc()
        raise

    raw = response.content
    if not raw:
        raise ValueError("LLM returned empty response")

    raw = raw.strip()
    print(f"\n  [DEBUG] LLM returned {len(raw)} chars:")
    # Show first 300 chars so we can see what's happening
    for line in raw[:300].split("\n"):
        print(f"    | {line}")
    if len(raw) > 300:
        print(f"    | ... ({len(raw) - 300} more chars)")

    # Extract JSON: find first { and last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found. Raw output starts with: {repr(raw[:100])}")

    json_str = raw[start:end + 1]

    # Fix common LLM JSON mistakes
    json_str = re.sub(r',\s*}', '}', json_str)  # trailing comma before }
    json_str = re.sub(r',\s*]', ']', json_str)  # trailing comma before ]

    try:
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError as e:
        print(f"\n  [ERROR] JSON decode failed: {e}")
        print(f"  [ERROR] Extracted JSON ({len(json_str)} chars):")
        for line in json_str[:500].split("\n"):
            print(f"    | {line}")
        traceback.print_exc()
        raise


async def _execute_build_plan(plan: dict) -> str:
    """Phase 3: Execute the build plan against UE via WebSocket."""
    steps = plan.get("steps", [])
    spawned = {}  # label -> actor_path mapping
    success = 0
    errors = 0

    for i, step in enumerate(steps):
        action = step.get("action", "")
        label = step.get("label", f"step_{i}")

        try:
            if action == "spawn":
                shape = step.get("shape", "cube")
                x = step.get("x", 0)
                y = step.get("y", 0)
                z = step.get("z", 0)

                actor_path, _ = await spawn_actor_internal(shape, x, y, z)
                if actor_path:
                    spawned[label] = actor_path
                    
                    # Apply combined scale if provided
                    sx = step.get("sx", 1.0)
                    sy = step.get("sy", 1.0)
                    sz = step.get("sz", 1.0)
                    if sx != 1.0 or sy != 1.0 or sz != 1.0:
                        await set_actor_scale(actor_path, float(sx), float(sy), float(sz))

                print(f"  [{i+1}/{len(steps)}] Spawned {shape} -> {label}")
                success += 1

            elif action == "scale":
                ref = step.get("ref", "")
                actor_path = spawned.get(ref, "")
                if actor_path:
                    sx = step.get("sx", 1)
                    sy = step.get("sy", 1)
                    sz = step.get("sz", 1)
                    await set_actor_scale(actor_path, sx, sy, sz)
                    print(f"  [{i+1}/{len(steps)}] Scaled {ref} -> ({sx}, {sy}, {sz})")
                    success += 1
                else:
                    print(f"  [{i+1}/{len(steps)}] SKIP: no path for '{ref}'")
                    errors += 1

            elif action == "rotate":
                ref = step.get("ref", "")
                actor_path = spawned.get(ref, "")
                if actor_path:
                    pitch = step.get("pitch", 0)
                    yaw = step.get("yaw", 0)
                    roll = step.get("roll", 0)
                    await set_actor_rotation(actor_path, pitch, yaw, roll)
                    print(f"  [{i+1}/{len(steps)}] Rotated {ref}")
                    success += 1
                else:
                    print(f"  [{i+1}/{len(steps)}] SKIP: no path for '{ref}'")
                    errors += 1

            # Small delay so UE can process
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"  [{i+1}/{len(steps)}] ERROR: {e}")
            errors += 1

    return f"Executed {success}/{len(steps)} steps ({errors} errors)"


# ── Main Pipeline ────────────────────────────────────────────────────
async def build_in_ue(llm, user_prompt: str) -> str:
    """
    Full live build pipeline.
    Refine -> Plan -> Execute in UE via WebSocket.
    """
    print(f"\n{'='*60}")
    print(f"  Live Builder")
    print(f"{'='*60}")

    # Phase 0: Scene
    print("\n[Phase 0] Querying scene...")
    scene_context = await _get_scene_context()
    print(f"  {scene_context.split(chr(10))[0]}")

    # Phase 1: Refine
    print(f"\n[Phase 1] Planning build...")
    print(f"  Input: \"{user_prompt}\"")
    refined = await _refine_build_prompt(llm, user_prompt)
    print(f"\n  Plan:")
    for line in refined.split("\n"):
        print(f"    {line}")

    # Phase 2: Generate build plan
    print(f"\n[Phase 2] Generating build steps...")
    
    try:
        plan = await _generate_build_plan(llm, refined, scene_context)
        
        # Robustly handle the plan, even if it's a string, list, or mapping with weird keys
        if isinstance(plan, str):
            try:
                plan = json.loads(plan)
            except json.JSONDecodeError:
                plan = {"steps": []}

        if isinstance(plan, list):
             plan = {"steps": plan}
             
        if not isinstance(plan, dict):
            plan = {"steps": []}
            
        # Clean up keys in case the LLM added newlines to the keys themselves
        clean_plan = {}
        for k, v in plan.items():
            if isinstance(k, str):
               clean_plan[k.strip()] = v
            else:
               clean_plan[k] = v
        plan = clean_plan

        step_count = len(plan.get("steps", []))
        print(f"  Name: {plan.get('name', 'Unknown')}")
        print(f"  Steps: {step_count}")

        # Phase 3: Execute in UE
        print(f"\n[Phase 3] BUILDING IN UNREAL ENGINE...")
        result = await _execute_build_plan(plan)

        print(f"\n{'='*60}")
        print(f"  BUILD COMPLETE!")
        print(f"  {result}")
        print(f"  Look at your Unreal viewport!")
        print(f"{'='*60}")

        return result
    except Exception as e:
        print(f"\n  [ERROR] Build pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        raise


# ── Interactive Builder ──────────────────────────────────────────────
async def interactive_builder(llm, model_label: str):
    """Interactive mode — describe what to build, see it appear in UE."""
    print(f"\n{'='*60}")
    print(f"  Live Builder - {model_label}")
    print(f"  Describe what to build. It appears in UE instantly.")
    print(f"  Type 'quit' to exit.")
    print(f"{'='*60}")
    print(f"\n  Examples:")
    print(f"    > build a small hut with a door")
    print(f"    > create a watchtower")
    print(f"    > make a fence around the area")
    print(f"    > build a bridge")
    print()

    while True:
        try:
            user_input = input("BUILD > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        try:
            await build_in_ue(llm, user_input)
        except json.JSONDecodeError as e:
            print(f"\n  LLM output was not valid JSON: {e}")
            print(f"  Try rephrasing.")
        except Exception as e:
            print(f"\n  Error: {e}")
        print()
