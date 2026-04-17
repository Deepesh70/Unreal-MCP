"""
Orchestrator Pipeline - bridges C++ generation and in-editor placement.

Goal:
- Handle mixed requests like "Create a C++ LaserTrap and place 3 in scene"
  without manual editor restart steps.
"""

from __future__ import annotations

import ast
import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.builder import build_in_ue
from agents.pipeline import two_phase_run
from unreal_mcp.codegen.compiler import (
    is_unreal_editor_running,
    start_unreal_editor,
    stop_unreal_editor,
)
from unreal_mcp.config.settings import (
    ORCH_EDITOR_BOOT_TIMEOUT_SEC,
    ORCH_ENABLE_LIVE_CODING,
    ORCH_FORCE_EDITOR_CLOSE,
    UE_PROJECT_NAME,
)
from unreal_mcp.connection import is_ue_ws_reachable, send_ue_ws_command, send_ue_ws_http_request
from unreal_mcp.tools.spawning import spawn_actor_internal


_ANALYZER_SYSTEM = """You classify Unreal requests for orchestration.
Return ONLY valid JSON:
{
  "requires_cpp_generation": boolean,
  "requires_scene_placement": boolean,
  "placement_count": integer,
  "primary_class_name": string,
  "codegen_prompt": string,
  "placement_prompt": string
}

Rules:
- requires_cpp_generation=true when the prompt asks for a new C++ class, actor, component, or gameplay system.
- requires_scene_placement=true when the prompt asks to place/spawn/add objects in the scene.
- placement_count is the count to place/spawn (default 1).
- primary_class_name is PascalCase class name if present (for example LaserTrap).
- codegen_prompt should keep only C++ implementation intent.
- placement_prompt should keep only scene placement intent.
Do not include markdown or explanations."""


_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


@dataclass
class OrchestrationIntent:
    requires_cpp_generation: bool
    requires_scene_placement: bool
    placement_count: int
    primary_class_name: str
    codegen_prompt: str
    placement_prompt: str


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return "{}"
    return text[start : end + 1]


def _to_int(value: Any, default: int = 1) -> int:
    try:
        if isinstance(value, bool):
            return default
        n = int(value)
        return n if n > 0 else default
    except Exception:
        return default


def _extract_word_number(prompt: str) -> int | None:
    low = prompt.lower()
    for word, number in _WORD_NUMBERS.items():
        if re.search(rf"\b{word}\b", low):
            return number
    return None


def _heuristic_intent(prompt: str) -> OrchestrationIntent:
    low = prompt.lower()

    # Improved C++ markers using regex for flexibility
    cpp_patterns = [
        r"\bc\+\+\b",
        r"\bcpp\b",
        r"\bnew\s+class\b",
        r"\bcreate\s+class\b",
        r"\bcreate\s+a\s+class\b",
        r"\bcreate\s+(?:a|an)?\s*(?:new)?\s*actor\b",
        r"\bgenerate\s+(?:some|the)?\s*code\b",
        r"\bimplement\b",
        r"\bheader\b",
        r"\bsource\b",
        r"\b\.h\b",
        r"\b\.cpp\b",
    ]
    
    requires_cpp = any(re.search(pat, low) for pat in cpp_patterns) or bool(
        re.search(r"\bclass\s+[A-Z][A-Za-z0-9_]*\b", prompt)
    )

    place_markers = ("place", "spawn", "add in scene", "add to scene", "put in scene", "drop in scene")
    requires_place = any(marker in low for marker in place_markers)

    number_match = re.search(r"\b(\d+)\b", prompt)
    placement_count = _to_int(number_match.group(1), 1) if number_match else (_extract_word_number(prompt) or 1)

    class_name = ""
    class_patterns = [
        r"\bclass\s+([A-Z][A-Za-z0-9_]*)\b",
        r"\bactor\s+([A-Z][A-Za-z0-9_]*)\b",
        r"\bcreate\s+(?:a|an)?\s*(?:c\+\+|cpp)?\s*([A-Z][A-Za-z0-9_]*)\b",
    ]
    for pattern in class_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            class_name = match.group(1)
            break

    return OrchestrationIntent(
        requires_cpp_generation=requires_cpp,
        requires_scene_placement=requires_place,
        placement_count=placement_count if requires_place else 0,
        primary_class_name=class_name,
        codegen_prompt=prompt,
        placement_prompt=prompt,
    )


async def _analyze_intent(llm, user_prompt: str, status_callback=None) -> OrchestrationIntent:
    async def log(msg: str):
        if status_callback:
            await status_callback(msg)

    fallback = _heuristic_intent(user_prompt)
    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=_ANALYZER_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
        raw = _extract_json(response.content or "")
        data = json.loads(raw)
        await log(f"[Intent] LLM classified: cpp={data.get('requires_cpp_generation')} placement={data.get('requires_scene_placement')}")
    except Exception as e:
        await log(f"[Intent] LLM analysis failed ({str(e)}). Falling back to heuristics...")
        return fallback

    requires_cpp = bool(data.get("requires_cpp_generation", fallback.requires_cpp_generation))
    requires_place = bool(data.get("requires_scene_placement", fallback.requires_scene_placement))
    placement_count = _to_int(data.get("placement_count", fallback.placement_count), 1)
    class_name = str(data.get("primary_class_name", fallback.primary_class_name) or "").strip()
    codegen_prompt = str(data.get("codegen_prompt", user_prompt) or user_prompt).strip()
    placement_prompt = str(data.get("placement_prompt", user_prompt) or user_prompt).strip()

    return OrchestrationIntent(
        requires_cpp_generation=requires_cpp,
        requires_scene_placement=requires_place,
        placement_count=placement_count if requires_place else 0,
        primary_class_name=class_name,
        codegen_prompt=codegen_prompt,
        placement_prompt=placement_prompt,
    )


def _parse_built_modules(result_text: str) -> list[str]:
    match = re.search(r"Build (?:Successful|Generated \(compile deferred\)):\s*(\[[^\]]*\])", result_text)
    if not match:
        return []
    try:
        parsed = ast.literal_eval(match.group(1))
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
    except Exception:
        pass
    return []


def _pick_class_name(preferred: str, generated_modules: list[str]) -> str:
    if not generated_modules:
        return preferred

    actor_candidates = [m for m in generated_modules if m.lower().endswith("actor")]

    if preferred:
        pref = preferred.lower()
        for module in generated_modules:
            if module.lower() == pref:
                return module

        # Flexible match: "CubeTower" should resolve to "CubeTowerActor".
        for module in generated_modules:
            m = module.lower()
            if m.startswith(pref) or pref.startswith(m) or pref in m or m in pref:
                return module

        # Try common Actor naming variant.
        for candidate in (f"{preferred}Actor", f"A{preferred}"):
            cand = candidate.lower()
            for module in generated_modules:
                if module.lower() == cand:
                    return module

    if actor_candidates:
        return actor_candidates[0]
    return generated_modules[0]


async def _get_level_actor_paths() -> set[str]:
    """Read all actor object paths from the current editor level."""
    response = await send_ue_ws_command(
        object_path="/Script/UnrealEd.Default__EditorActorSubsystem",
        function_name="GetAllLevelActors",
    )
    body = response.get("ResponseBody", {}) if isinstance(response, dict) else {}
    actors = body.get("ReturnValue", [])
    if not isinstance(actors, list):
        return set()

    out: set[str] = set()
    for actor in actors:
        if isinstance(actor, str) and actor.strip():
            out.add(actor.strip())
    return out


async def _wait_for_editor_ws(timeout_seconds: int) -> bool:
    loops = max(1, timeout_seconds)
    for _ in range(loops):
        if await is_ue_ws_reachable(timeout_seconds=1.5):
            return True
        await asyncio.sleep(1)
    return False


def _extract_response_body(payload: Any) -> Any:
    if isinstance(payload, dict):
        return payload.get("ResponseBody", payload)
    return payload


def _extract_http_routes(remote_info_payload: Any) -> list[dict[str, Any]]:
    body = _extract_response_body(remote_info_payload)
    if not isinstance(body, dict):
        return []
    routes = body.get("HttpRoutes") or body.get("httpRoutes") or body.get("Routes") or []
    if not isinstance(routes, list):
        return []
    normalized: list[dict[str, Any]] = []
    for route in routes:
        if isinstance(route, dict):
            normalized.append(route)
    return normalized


def _live_coding_candidate_routes(routes: list[dict[str, Any]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for route in routes:
        path = str(route.get("Path") or route.get("path") or "").strip()
        if not path.startswith("/remote/"):
            continue
        low = path.lower()
        if not any(token in low for token in ("console", "command", "exec")):
            continue

        verb = str(route.get("Verb") or route.get("verb") or "PUT").upper()
        key = f"{verb}:{path}"
        if key in seen:
            continue
        seen.add(key)
        out.append((verb, path))

    # Hard fallback candidates for common RC endpoint names.
    fallbacks = [
        ("PUT", "/remote/console/command"),
        ("PUT", "/remote/console"),
        ("PUT", "/remote/execute"),
        ("PUT", "/remote/command"),
    ]
    for verb, path in fallbacks:
        key = f"{verb}:{path}"
        if key not in seen:
            out.append((verb, path))
    return out


async def _trigger_live_coding_compile() -> tuple[bool, str]:
    """
    Attempt to trigger Live Coding compile in an already-open Unreal Editor session.

    Uses Remote Control route discovery + common fallback endpoints.
    """
    if not await is_ue_ws_reachable(timeout_seconds=2.0):
        return False, "Remote Control websocket is not reachable."

    routes: list[dict[str, Any]] = []
    try:
        info_payload = await send_ue_ws_http_request(url="/remote/info", verb="GET", body={})
        routes = _extract_http_routes(info_payload)
    except Exception:
        routes = []

    candidates = _live_coding_candidate_routes(routes)
    command_payload_variants = [
        {"Command": "LiveCoding.Compile"},
        {"command": "LiveCoding.Compile"},
        {"ExecCommand": "LiveCoding.Compile"},
        {"ConsoleCommand": "LiveCoding.Compile"},
        {"CommandString": "LiveCoding.Compile"},
    ]

    attempts = 0
    for verb, path in candidates:
        for body in command_payload_variants:
            attempts += 1
            try:
                await send_ue_ws_http_request(url=path, verb=verb, body=body)
                return True, f"Triggered Live Coding compile via {verb} {path}."
            except Exception:
                continue

    return False, (
        "Could not find a working Remote Control endpoint for Live Coding compile "
        f"(attempted {attempts} combinations)."
    )


async def _request_editor_quit_remote() -> tuple[bool, str]:
    """
    Ask Unreal Editor to quit via Remote Control console command.

    This is a graceful pre-step before process termination fallback.
    """
    if not await is_ue_ws_reachable(timeout_seconds=2.0):
        return False, "Remote Control websocket is not reachable for graceful quit."

    routes: list[dict[str, Any]] = []
    try:
        info_payload = await send_ue_ws_http_request(url="/remote/info", verb="GET", body={})
        routes = _extract_http_routes(info_payload)
    except Exception:
        routes = []

    candidates = _live_coding_candidate_routes(routes)
    quit_payload_variants = [
        {"Command": "QUIT_EDITOR"},
        {"command": "QUIT_EDITOR"},
        {"ExecCommand": "QUIT_EDITOR"},
        {"ConsoleCommand": "QUIT_EDITOR"},
        {"CommandString": "QUIT_EDITOR"},
    ]

    attempts = 0
    for verb, path in candidates:
        for body in quit_payload_variants:
            attempts += 1
            try:
                await send_ue_ws_http_request(url=path, verb=verb, body=body)
                await asyncio.sleep(2)
                if not is_unreal_editor_running():
                    return True, f"Editor quit triggered via {verb} {path}."
            except Exception:
                continue

    if not is_unreal_editor_running():
        return True, "Editor appears closed after remote quit attempts."
    return False, f"Remote quit command failed (attempted {attempts} combinations)."


async def _spawn_generated_class_instances(class_name: str, count: int) -> str:
    class_path = f"/Script/{UE_PROJECT_NAME}.{class_name}"
    success = 0
    errors = 0
    spawned_paths: list[str] = []

    spacing = 300
    for i in range(max(1, count)):
        x = i * spacing
        y = 0
        z = 100
        try:
            before = await _get_level_actor_paths()
            actor_path, _ = await spawn_actor_internal(class_path, x=x, y=y, z=z)
            after = await _get_level_actor_paths()

            created = list(after - before)
            chosen_path = ""
            if created:
                chosen_path = created[0]
            elif actor_path and actor_path not in before:
                chosen_path = actor_path

            if not chosen_path:
                errors += 1
                continue

            success += 1
            spawned_paths.append(chosen_path)
        except Exception:
            errors += 1

    if success == 0:
        return f"Failed to spawn class {class_name} ({class_path})."

    details = "\n".join(f"  - {p}" for p in spawned_paths[:10])
    return (
        f"Spawned {success}/{max(1, count)} instances of {class_name}.\n"
        f"Class path: {class_path}\n"
        f"{'Errors: ' + str(errors) if errors else 'Errors: 0'}\n"
        f"Spawned actor paths:\n{details}"
    )


async def orchestrate_in_ue(
    llm,
    user_prompt: str,
    level: str | None = None,
    status_callback=None,
) -> str:
    async def log(message: str) -> None:
        print(message)
        if status_callback:
            await status_callback(message)

    await log("\n============================================================")
    await log("  Orchestrator Mode")
    await log("============================================================")

    intent = await _analyze_intent(llm, user_prompt, status_callback=status_callback)
    await log(
        "[Intent] "
        f"cpp={intent.requires_cpp_generation} "
        f"placement={intent.requires_scene_placement} "
        f"count={intent.placement_count or 0} "
        f"class='{intent.primary_class_name or '-'}'"
    )

    if not intent.requires_cpp_generation:
        await log("[Path] No C++ generation needed. Routing to live builder.")
        return await build_in_ue(llm, intent.placement_prompt or user_prompt, status_callback=status_callback)

    # 1. Check State: Before generating code, ping the WebSocket/Process to see if the Editor is alive.
    editor_was_running = is_unreal_editor_running()
    compile_ok = False
    generated_modules: list[str] = []

    if editor_was_running:
        # PATH A: Editor Open -> Live Coding Flow
        await log("[State] Unreal Editor is running. Using Path A (Live Coding Hot-Reload).")
        
        # Generate the files, but DO NOT run the headless compile (Build.bat).
        code_result = await two_phase_run(
            llm,
            intent.codegen_prompt or user_prompt,
            write_files=True,
            validate_compile=False, # SKIP Build.bat to avoid file locking
        )
        
        if code_result.startswith("ABORTED:") or code_result.startswith("CRITICAL FAILURE"):
            return code_result

        generated_modules = _parse_built_modules(code_result)
        
        # Trigger a Live Coding Recompile via the Unreal Remote Control API
        lc_ok, lc_message = await _trigger_live_coding_compile()
        await log(f"[LiveCoding] {lc_message}")
        
        if lc_ok:
            compile_ok = True
            await asyncio.sleep(3) # Wait for patch to apply
        else:
            await log("[Error] Live Coding trigger failed. You may need to compile manually in the Editor.")
            return f"C++ Files Generated but Live Coding failed: {lc_message}"
    else:
        # PATH B: Editor Closed -> Headless Build + Boot
        await log("[State] Unreal Editor is closed. Using Path B (Headless Build + Cold Boot).")
        
        # Run the headless compile as normal
        code_result = await two_phase_run(
            llm,
            intent.codegen_prompt or user_prompt,
            write_files=True,
            validate_compile=True, # FULL HEADLESS COMPILE
        )
        
        compile_ok = code_result.startswith("Build Successful:")
        if compile_ok:
            generated_modules = _parse_built_modules(code_result)
            
            # Boot the Unreal Editor back up before attempting to spawn
            await log("[Lifecycle] Launching Unreal Editor...")
            started, start_message = start_unreal_editor(startup_map=level)
            await log(f"[Lifecycle] {start_message}")
            if not started:
                return f"{code_result}\n\nWARNING: Could not launch Unreal Editor: {start_message}"
            
            # Wait for Remote Control to be ready
            await log("[Lifecycle] Waiting for Unreal Remote Control websocket...")
            ready = await _wait_for_editor_ws(ORCH_EDITOR_BOOT_TIMEOUT_SEC)
            if not ready:
                return (
                    f"{code_result}\n\nPlacement skipped: Unreal websocket did not become reachable "
                    f"within {ORCH_EDITOR_BOOT_TIMEOUT_SEC}s."
                )

    if not compile_ok:
        return code_result

    # Final Step: Scene Placement if requested
    if not intent.requires_scene_placement:
        return code_result

    class_name = _pick_class_name(intent.primary_class_name, generated_modules)
    if not class_name:
        return (
            f"{code_result}\n\nPlacement skipped: could not identify generated class to spawn. "
            f"Generated modules: {generated_modules}"
        )

    await log(f"[Phase] Spawning generated class '{class_name}' x{max(1, intent.placement_count)}...")
    spawn_result = await _spawn_generated_class_instances(class_name, max(1, intent.placement_count))
    
    return f"{code_result}\n\n{spawn_result}"


async def interactive_orchestrator(llm, model_label: str, level: str | None = None) -> None:
    """Interactive loop for orchestrator mode."""
    print("\n" + "=" * 62)
    print(f"  Orchestrator Mode (Model: {model_label})")
    print("=" * 62)
    print("Type a request and press Enter.")
    print("Commands: 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("\nOrchestrate> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting orchestrator mode.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Exiting orchestrator mode.")
            break

        result = await orchestrate_in_ue(llm, user_input, level=level)
        print(f"\n[RESULT] {result}")
