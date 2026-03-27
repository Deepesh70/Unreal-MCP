"""
Live Builder Pipeline - Builds things in UE via WebSocket in real time.

Phase 1: Refine user prompt into building spec (~200 tokens)
Phase 2: Generate build plan JSON with spawn/scale/rotate/mesh steps (~800 tokens)
Phase 3: Execute each step live against Unreal Engine via WebSocket

Result: Objects appear in the UE viewport immediately.
"""

import json
import re
import sys
import asyncio
import os
from typing import Any, Dict, List, Tuple
from stdio_config import configure_windows_stdio_utf8

configure_windows_stdio_utf8()

from langchain_core.messages import HumanMessage, SystemMessage

from agents.builder_prompts import BUILDER_SYSTEM, BUILDER_REFINER, BUILDER_PLAN_REVIEWER
from unreal_mcp.tools.spawning import spawn_actor_internal
from unreal_mcp.tools.transform import set_actor_scale, set_actor_rotation
from unreal_mcp.tools.mesh_settings import set_mesh_settings, sync_mesh_settings


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with common truthy values."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable with safe fallback."""
    try:
        value = os.getenv(name)
        return int(value) if value is not None else default
    except Exception:
        return default


def _load_token_policy() -> Dict[str, Any]:
    """
    Load token optimization policy from environment.

    BUILD_TOKEN_MODE values:
      - low: aggressive token saving
      - balanced: default
      - high: quality-first (more tokens)
    """
    mode = os.getenv("BUILD_TOKEN_MODE", "balanced").strip().lower()
    if mode not in {"low", "balanced", "high"}:
        mode = "balanced"

    if mode == "low":
        defaults = {
            "max_scene_context_chars": 900,
            "max_blueprint_context_chars": 700,
            "enable_plan_review": False,
            "enable_json_repair": True,
        }
    elif mode == "high":
        defaults = {
            "max_scene_context_chars": 5000,
            "max_blueprint_context_chars": 5000,
            "enable_plan_review": True,
            "enable_json_repair": True,
        }
    else:
        defaults = {
            "max_scene_context_chars": 2500,
            "max_blueprint_context_chars": 2200,
            "enable_plan_review": True,
            "enable_json_repair": True,
        }

    return {
        "mode": mode,
        "max_scene_context_chars": _env_int("BUILD_MAX_SCENE_CONTEXT_CHARS", defaults["max_scene_context_chars"]),
        "max_blueprint_context_chars": _env_int("BUILD_MAX_BLUEPRINT_CONTEXT_CHARS", defaults["max_blueprint_context_chars"]),
        "enable_plan_review": _env_bool("BUILD_ENABLE_PLAN_REVIEW", defaults["enable_plan_review"]),
        "enable_json_repair": _env_bool("BUILD_ENABLE_JSON_REPAIR", defaults["enable_json_repair"]),
    }


def _truncate_text(text: str, max_chars: int) -> str:
    """Trim long prompt context text to reduce token usage."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated for token budget]"


async def _get_scene_context() -> str:
    """Query UE scene for context."""
    try:
        from unreal_mcp.tools.scene_tool import get_scene_state, format_scene_for_prompt
        scene = await get_scene_state()
        return format_scene_for_prompt(scene)
    except Exception:
        return "Scene unknown"


def _extract_token_usage(ai_message) -> dict:
    """
    Extract token usage from LangChain AIMessage across provider formats.

    Returns a dict with: input_tokens, output_tokens, total_tokens.
    Missing values default to 0.
    """
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    usage_meta = getattr(ai_message, "usage_metadata", None)
    if isinstance(usage_meta, dict):
        usage["input_tokens"] = int(usage_meta.get("input_tokens", usage["input_tokens"]))
        usage["output_tokens"] = int(usage_meta.get("output_tokens", usage["output_tokens"]))
        usage["total_tokens"] = int(usage_meta.get("total_tokens", usage["total_tokens"]))

    resp_meta = getattr(ai_message, "response_metadata", None)
    if isinstance(resp_meta, dict):
        token_usage = resp_meta.get("token_usage", {})
        if isinstance(token_usage, dict):
            if not usage["input_tokens"]:
                usage["input_tokens"] = int(token_usage.get("prompt_tokens", 0) or 0)
            if not usage["output_tokens"]:
                usage["output_tokens"] = int(token_usage.get("completion_tokens", 0) or 0)
            if not usage["total_tokens"]:
                usage["total_tokens"] = int(token_usage.get("total_tokens", 0) or 0)

    if not usage["total_tokens"]:
        usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]

    return usage


def _accumulate_usage(tracker: dict, phase: str, usage: dict) -> None:
    """Accumulate token usage into phase buckets and overall totals."""
    if phase not in tracker:
        tracker[phase] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    tracker[phase]["input_tokens"] += usage.get("input_tokens", 0)
    tracker[phase]["output_tokens"] += usage.get("output_tokens", 0)
    tracker[phase]["total_tokens"] += usage.get("total_tokens", 0)

    tracker["overall"]["input_tokens"] += usage.get("input_tokens", 0)
    tracker["overall"]["output_tokens"] += usage.get("output_tokens", 0)
    tracker["overall"]["total_tokens"] += usage.get("total_tokens", 0)


def _coerce_number(value: Any, default: float = 0.0) -> float:
    """Best-effort numeric coercion for LLM-generated fields."""
    try:
        if isinstance(value, bool):
            return default
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def _extract_json_object(raw_text: str) -> str:
    """Extract the outermost JSON object from model output text."""
    raw = (raw_text or "").strip().replace("\ufeff", "")
    raw = raw.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found. Raw output starts with: {repr(raw[:100])}")

    json_str = raw[start:end + 1]
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    return json_str


def _sanitize_build_plan(plan: dict) -> Tuple[dict, int]:
    """
    Normalize and validate build-plan steps so executor gets stable input.

    Returns:
        (sanitized_plan, dropped_step_count)
    """
    if not isinstance(plan, dict):
        return {"name": "Unknown", "description": "", "steps": []}, 0

    actions_allowed = {"spawn", "scale", "rotate", "mesh_settings", "sync_mesh_settings"}
    source_steps = plan.get("steps", [])
    if not isinstance(source_steps, list):
        source_steps = []

    sanitized_steps: List[Dict[str, Any]] = []
    dropped = 0

    for idx, step in enumerate(source_steps):
        if not isinstance(step, dict):
            dropped += 1
            continue

        action = str(step.get("action", "")).strip().lower()
        if action not in actions_allowed:
            dropped += 1
            continue

        label = str(step.get("label", f"step_{idx}")).strip() or f"step_{idx}"
        out: Dict[str, Any] = {"action": action, "label": label}

        if action == "spawn":
            shape = str(step.get("shape", "cube")).strip().lower() or "cube"
            out["shape"] = shape
            out["x"] = _coerce_number(step.get("x", 0), 0.0)
            out["y"] = _coerce_number(step.get("y", 0), 0.0)
            out["z"] = _coerce_number(step.get("z", 0), 0.0)
            out["sx"] = _coerce_number(step.get("sx", 1.0), 1.0)
            out["sy"] = _coerce_number(step.get("sy", 1.0), 1.0)
            out["sz"] = _coerce_number(step.get("sz", 1.0), 1.0)

        elif action == "scale":
            out["ref"] = str(step.get("ref", "")).strip()
            out["sx"] = _coerce_number(step.get("sx", 1.0), 1.0)
            out["sy"] = _coerce_number(step.get("sy", 1.0), 1.0)
            out["sz"] = _coerce_number(step.get("sz", 1.0), 1.0)
            if not out["ref"]:
                dropped += 1
                continue

        elif action == "rotate":
            out["ref"] = str(step.get("ref", "")).strip()
            out["pitch"] = _coerce_number(step.get("pitch", 0.0), 0.0)
            out["yaw"] = _coerce_number(step.get("yaw", 0.0), 0.0)
            out["roll"] = _coerce_number(step.get("roll", 0.0), 0.0)
            if not out["ref"]:
                dropped += 1
                continue

        else:
            out["ref"] = str(step.get("ref", "")).strip()
            settings = step.get("settings", {})
            out["settings"] = settings if isinstance(settings, dict) else {}
            if not out["ref"] or not out["settings"]:
                dropped += 1
                continue

        sanitized_steps.append(out)

    sanitized = {
        "name": str(plan.get("name", "Generated Build")).strip() or "Generated Build",
        "description": str(plan.get("description", "")).strip(),
        "steps": sanitized_steps,
    }
    return sanitized, dropped


async def _refine_build_prompt(llm, user_prompt: str, blueprint_context: str = "", token_tracker: dict = None) -> str:
    """Phase 1: Convert vague request into precise build spec."""

    system = BUILDER_REFINER.format(blueprint_context=blueprint_context)
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user_prompt),
    ])

    usage = _extract_token_usage(response)
    print(
        "  [TOKENS][Phase 1 Refine] "
        f"input={usage['input_tokens']} output={usage['output_tokens']} total={usage['total_tokens']}"
    )
    if token_tracker is not None:
        _accumulate_usage(token_tracker, "phase_1_refine", usage)

    return response.content.strip()


async def _repair_json_with_llm(llm, broken_json: str, error_message: str, token_tracker: dict = None) -> dict:
    """
    Ask the LLM to repair malformed JSON and return a parsed dict.

    This is a fallback path when the initial build-plan JSON parsing fails.
    """
    repair_system = (
        "You are a strict JSON repair engine. "
        "Fix malformed JSON and return ONLY valid JSON. "
        "Do not add explanations, markdown, or code fences."
    )

    repair_prompt = (
        "The following JSON is malformed. Repair it without changing the intent.\n\n"
        f"Parse error: {error_message}\n\n"
        "MALFORMED JSON START\n"
        f"{broken_json}\n"
        "MALFORMED JSON END"
    )

    response = await llm.ainvoke([
        SystemMessage(content=repair_system),
        HumanMessage(content=repair_prompt),
    ])

    usage = _extract_token_usage(response)
    print(
        "  [TOKENS][Phase 2 Repair] "
        f"input={usage['input_tokens']} output={usage['output_tokens']} total={usage['total_tokens']}"
    )
    if token_tracker is not None:
        _accumulate_usage(token_tracker, "phase_2_repair", usage)

    repaired_json = _extract_json_object(response.content or "")
    return json.loads(repaired_json)


async def _review_build_plan_with_llm(
    llm,
    plan: dict,
    refined_spec: str,
    scene_context: str,
    token_tracker: dict = None,
) -> dict:
    """
    Run a second-pass geometry QA/refinement over the generated plan.

    This significantly improves roof/wall/door alignment in complex builds.
    """
    review_system = BUILDER_PLAN_REVIEWER.format(scene_context=scene_context)
    review_prompt = (
        "Refine the candidate build plan for geometric correctness.\n\n"
        "Refined specification:\n"
        f"{refined_spec}\n\n"
        "Candidate JSON plan:\n"
        f"{json.dumps(plan, ensure_ascii=False)}\n\n"
        "Return corrected JSON only."
    )

    response = await llm.ainvoke([
        SystemMessage(content=review_system),
        HumanMessage(content=review_prompt),
    ])

    usage = _extract_token_usage(response)
    print(
        "  [TOKENS][Phase 2 Review] "
        f"input={usage['input_tokens']} output={usage['output_tokens']} total={usage['total_tokens']}"
    )
    if token_tracker is not None:
        _accumulate_usage(token_tracker, "phase_2_review", usage)

    json_str = _extract_json_object(response.content or "")
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"  [WARN] Plan review JSON parse failed: {e}. Attempting repair...")
        return await _repair_json_with_llm(llm, json_str, str(e), token_tracker=token_tracker)


async def _generate_build_plan(
    llm,
    refined: str,
    scene_context: str,
    token_tracker: dict = None,
    enable_json_repair: bool = True,
) -> dict:
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

    usage = _extract_token_usage(response)
    print(
        "  [TOKENS][Phase 2 Plan] "
        f"input={usage['input_tokens']} output={usage['output_tokens']} total={usage['total_tokens']}"
    )
    if token_tracker is not None:
        _accumulate_usage(token_tracker, "phase_2_plan", usage)

    raw = response.content
    if not raw:
        raise ValueError("LLM returned empty response")

    raw = (raw or "").strip().replace("\ufeff", "")
    raw = raw.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    print(f"\n  [DEBUG] LLM returned {len(raw)} chars:")
    for line in raw[:300].split("\n"):
        print(f"    | {line}")
    if len(raw) > 300:
        print(f"    | ... ({len(raw) - 300} more chars)")

    json_str = _extract_json_object(raw)

    try:
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError as e:
        print(f"\n  [ERROR] JSON decode failed: {e}")
        print(f"  [ERROR] Extracted JSON ({len(json_str)} chars):")
        for line in json_str[:500].split("\n"):
            print(f"    | {line}")
        traceback.print_exc()

        if not enable_json_repair:
            raise

        try:
            print("  [INFO] Attempting automatic JSON repair...")
            repaired = await _repair_json_with_llm(llm, json_str, str(e), token_tracker=token_tracker)
            print("  [INFO] JSON repair succeeded.")
            return repaired
        except Exception as repair_error:
            print(f"  [ERROR] JSON repair failed: {repair_error}")
            raise


async def _execute_build_plan(plan: dict, status_callback=None) -> str:
    """Phase 3: Execute the build plan against UE via WebSocket."""
    async def log(msg: str):
        print("  " + msg)
        if status_callback:
            await status_callback(msg)

    steps = plan.get("steps", [])
    spawned = {}
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

                    sx = step.get("sx", 1.0)
                    sy = step.get("sy", 1.0)
                    sz = step.get("sz", 1.0)
                    if sx != 1.0 or sy != 1.0 or sz != 1.0:
                        await set_actor_scale(actor_path, float(sx), float(sy), float(sz))

                await log(f"[{i+1}/{len(steps)}] Spawned {shape} -> {label}")
                success += 1

            elif action == "scale":
                ref = step.get("ref", "")
                actor_path = spawned.get(ref, "")
                if actor_path:
                    sx = step.get("sx", 1)
                    sy = step.get("sy", 1)
                    sz = step.get("sz", 1)
                    await set_actor_scale(actor_path, sx, sy, sz)
                    await log(f"[{i+1}/{len(steps)}] Scaled {ref} -> ({sx}, {sy}, {sz})")
                    success += 1
                else:
                    await log(f"[{i+1}/{len(steps)}] SKIP: no path for '{ref}'")
                    errors += 1

            elif action == "rotate":
                ref = step.get("ref", "")
                actor_path = spawned.get(ref, "")
                if actor_path:
                    pitch = step.get("pitch", 0)
                    yaw = step.get("yaw", 0)
                    roll = step.get("roll", 0)
                    await set_actor_rotation(actor_path, pitch, yaw, roll)
                    await log(f"[{i+1}/{len(steps)}] Rotated {ref}")
                    success += 1
                else:
                    await log(f"[{i+1}/{len(steps)}] SKIP: no path for '{ref}'")
                    errors += 1

            elif action == "mesh_settings":
                ref = step.get("ref", "")
                actor_path = spawned.get(ref, "")
                settings = step.get("settings", {})
                if actor_path:
                    await set_mesh_settings(actor_path, settings)
                    await log(f"[{i+1}/{len(steps)}] Updated mesh settings for {ref}")
                    success += 1
                else:
                    await log(f"[{i+1}/{len(steps)}] SKIP: no path for '{ref}'")
                    errors += 1

            elif action == "sync_mesh_settings":
                ref = step.get("ref", "")
                actor_path = spawned.get(ref, "")
                desired_settings = step.get("settings", {})
                if actor_path:
                    await sync_mesh_settings(actor_path, desired_settings)
                    await log(f"[{i+1}/{len(steps)}] Synced mesh settings for {ref}")
                    success += 1
                else:
                    await log(f"[{i+1}/{len(steps)}] SKIP: no path for '{ref}'")
                    errors += 1

            await asyncio.sleep(0.1)

        except Exception as e:
            await log(f"[{i+1}/{len(steps)}] ERROR: {e}")
            errors += 1

    return f"Executed {success}/{len(steps)} steps ({errors} errors)"


async def build_in_ue(llm, user_prompt: str, status_callback=None) -> str:
    """
    Full live build pipeline.
    Refine -> Plan -> Execute in UE via WebSocket.
    """
    async def log(msg: str):
        print(msg)
        if status_callback:
            await status_callback(msg)

    print(f"\n{'='*60}")
    print("  Live Builder")
    print(f"{'='*60}")

    token_policy = _load_token_policy()
    print(
        "  Token mode: "
        f"{token_policy['mode']} "
        f"(review={'on' if token_policy['enable_plan_review'] else 'off'}, "
        f"repair={'on' if token_policy['enable_json_repair'] else 'off'})"
    )

    token_tracker = {
        "overall": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    }

    print("\n[Phase 0] Querying scene...")
    scene_context = await _get_scene_context()
    scene_context = _truncate_text(scene_context, token_policy["max_scene_context_chars"])
    print(f"  {scene_context.split(chr(10))[0]}")

    from .rag_store import retrieve_blueprint
    blueprint_context = ""
    try:
        blueprint_text = retrieve_blueprint(user_prompt)
        if blueprint_text:
            print(" [+] Found RAG Blueprint match! Injecting into context.")
            blueprint_text = _truncate_text(blueprint_text, token_policy["max_blueprint_context_chars"])
            blueprint_context = f"\n\n === ARCHITECTURE BLUEPRINT ===\n{blueprint_text}"
            scene_context += blueprint_context
        else:
            print(" [-] No RAG Blueprint found for this request.")
    except Exception as e:
        print(f" [!] RAG retrieval failed (is chromadb installed?): {e}")

    await log("\n[Phase 1] Planning build...")
    print(f"  Input: \"{user_prompt}\"")
    refined = await _refine_build_prompt(llm, user_prompt, blueprint_context, token_tracker=token_tracker)
    print("\n  Plan:")
    for line in refined.split("\n"):
        print(f"    {line}")

    await log("\n[Phase 2] Generate Build Steps...")

    try:
        plan = await _generate_build_plan(
            llm,
            refined,
            scene_context,
            token_tracker=token_tracker,
            enable_json_repair=token_policy["enable_json_repair"],
        )

        if token_policy["enable_plan_review"]:
            await log("\n[Phase 2b] Refine Geometry & Alignment...")
            try:
                reviewed_plan = await _review_build_plan_with_llm(
                    llm,
                    plan,
                    refined_spec=refined,
                    scene_context=scene_context,
                    token_tracker=token_tracker,
                )
                if isinstance(reviewed_plan, dict):
                    plan = reviewed_plan
                    print("  [INFO] Plan review succeeded.")
            except Exception as review_error:
                print(f"  [WARN] Plan review skipped due to error: {review_error}")
        else:
            print("  [INFO] Plan review disabled by token policy.")

        if isinstance(plan, str):
            try:
                plan = json.loads(plan)
            except json.JSONDecodeError:
                plan = {"steps": []}

        if isinstance(plan, list):
            plan = {"steps": plan}

        if not isinstance(plan, dict):
            plan = {"steps": []}

        clean_plan = {}
        for k, v in plan.items():
            if isinstance(k, str):
                clean_plan[k.strip()] = v
            else:
                clean_plan[k] = v
        plan = clean_plan

        plan, dropped_steps = _sanitize_build_plan(plan)
        if dropped_steps > 0:
            print(f"  [WARN] Dropped {dropped_steps} invalid step(s) during sanitization.")

        step_count = len(plan.get("steps", []))
        print(f"  Name: {plan.get('name', 'Unknown')}")
        print(f"  Steps: {step_count}")

        await log("\n[Phase 3] BUILDING IN UNREAL ENGINE...")
        result = await _execute_build_plan(plan, status_callback=status_callback)

        print(f"\n{'='*60}")
        print("  BUILD COMPLETE!")
        print(f"  {result}")
        print(
            "  TOKEN USAGE (overall): "
            f"input={token_tracker['overall']['input_tokens']} "
            f"output={token_tracker['overall']['output_tokens']} "
            f"total={token_tracker['overall']['total_tokens']}"
        )
        if token_tracker.get("phase_2_repair", {}).get("total_tokens", 0) > 0:
            print(
                "  TOKEN USAGE (repair): "
                f"input={token_tracker['phase_2_repair']['input_tokens']} "
                f"output={token_tracker['phase_2_repair']['output_tokens']} "
                f"total={token_tracker['phase_2_repair']['total_tokens']}"
            )
        if token_tracker.get("phase_2_review", {}).get("total_tokens", 0) > 0:
            print(
                "  TOKEN USAGE (review): "
                f"input={token_tracker['phase_2_review']['input_tokens']} "
                f"output={token_tracker['phase_2_review']['output_tokens']} "
                f"total={token_tracker['phase_2_review']['total_tokens']}"
            )
        print("  Look at your Unreal viewport!")
        print(f"{'='*60}")

        return result
    except Exception as e:
        await log(f"\n  [ERROR] Build pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def interactive_builder(llm, model_label: str):
    """Interactive mode — describe what to build, see it appear in UE."""
    print(f"\n{'='*60}")
    print(f"  Live Builder - {model_label}")
    print("  Describe what to build. It appears in UE instantly.")
    print("  Type 'quit' to exit.")
    print(f"{'='*60}")
    print("\n  Examples:")
    print("    > build a small hut with a door")
    print("    > create a watchtower")
    print("    > make a fence around the area")
    print("    > build a bridge")
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
            print("  Try rephrasing.")
        except Exception as e:
            print(f"\n  Error: {e}")
        print()
