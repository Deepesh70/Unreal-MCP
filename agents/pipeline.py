"""
Final Multi-Phase CI/CD Pipeline.
Self-Correcting, Topologically Sorted, and Engine-Validated.
"""

import json
import re
import sys
import traceback
import asyncio
from stdio_config import configure_windows_stdio_utf8

# Fix encoding for Windows terminals to prevent UnicodeDecodeErrors
configure_windows_stdio_utf8()

from langchain_core.messages import HumanMessage, SystemMessage

# Internal Imports
from agents.prompts import REFINER_SYSTEM, GENERATOR_SYSTEM
from unreal_mcp.codegen.schema import Blueprint
from unreal_mcp.codegen.renderer import render_both
from unreal_mcp.codegen.file_writer import write_class_files
from unreal_mcp.codegen.sorter import resolve_build_order
from unreal_mcp.codegen.compiler import run_headless_compile_check, run_compile_preflight_check
from unreal_mcp.config.settings import MAX_COMPILE_RETRIES
from agents.rag_store import retrieve_api_knowledge


def _extract_json(text: str) -> str:
    """Robustly extracts the outermost JSON object from LLM response."""
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        print(f"  [DEBUG] No JSON found in LLM response: {text[:100]}...")
        return "{}" 
    return text[start:end+1]


async def _get_scene_context() -> str:
    """Query UE scene for current state awareness."""
    try:
        from unreal_mcp.tools.scene_tool import get_scene_state, format_scene_for_prompt
        scene = await get_scene_state()
        return format_scene_for_prompt(scene)
    except Exception:
        return "Scene unknown (Editor connection offline)"


async def refine_prompt(llm, user_prompt: str, scene_context: str) -> str:
    """Phase 1: Convert user intent into a strict technical engineering spec."""
    system = REFINER_SYSTEM.format(scene_context=scene_context)
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=user_prompt),
    ])
    return response.content.strip()

async def generate_architecture_manifest(llm, refined_spec: str) -> dict:
    """Phase 2a: Map dependencies BEFORE writing code."""
    manifest_system = """You are a Lead UE5 Architect. 
    Break the spec into modular C++ classes. 

    CRITICAL RULES:
    1. ONLY generate modules for the explicitly requested classes in the spec. 
    2. DO NOT invent 'Managers', 'Controllers', or auxiliary helper classes. Keep it simple.
    3. If Class A is used by Class B, Class A is a DEPENDENCY.
    4. DO NOT include AActor or other built-in UE classes in the modules list.
    
    OUTPUT ONLY JSON: {"modules": [{"name": "HealthComponent", "dependencies": []}, {"name": "DamageZone", "dependencies": ["HealthComponent"]}]}"""
    
    response = await llm.ainvoke([
        SystemMessage(content=manifest_system),
        HumanMessage(content=f"Manifest for: {refined_spec}")
    ])
    raw = _extract_json(response.content)
    return json.loads(raw)


async def generate_blueprint_json(llm, targeted_prompt: str) -> dict:
    """Phase 3: Generate a specific class JSON payload with context."""
    # Use explicit replacement instead of str.format() because the prompt
    # intentionally contains literal braces like {class_name} for instruction text.
    system = GENERATOR_SYSTEM.replace(
        "{refined_spec}",
        "Focus on generating the requested class only.",
    ).replace(
        "{api_rules}",
        targeted_prompt.get("api_rules", "No specific rules found.")
    )
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=targeted_prompt.get("prompt", str(targeted_prompt))),
    ])
    
    raw = _extract_json(response.content)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [!] Blueprint JSON Parse Error: {e}\nRaw: {raw}")
        raise


async def two_phase_run(
    llm,
    user_prompt: str,
    write_files: bool = True,
    validate_compile: bool = True,
) -> str:
    """The Complete Self-Healing CI/CD Pipeline."""
    print(f"\n{'='*60}\n  STARTING CI/CD PIPELINE\n{'='*60}")

    if write_files and validate_compile:
        ok, preflight_msg = run_compile_preflight_check()
        if not ok:
            print("\n[PRECHECK] Environment not ready for headless compile.")
            print(preflight_msg)
            return f"PRECHECK FAILED:\n{preflight_msg}"
        print("[PRECHECK] Environment ready.")

    # Phase 0 & 1: Context and Refinement
    scene_context = await _get_scene_context()
    refined = await refine_prompt(llm, user_prompt, scene_context)
    print(f"\n[PHASE 1] Refined Specification:\n{refined}")

    # Phase 2: Architecture Manifest & Topological Sort
    try:
        manifest_data = await generate_architecture_manifest(llm, refined)
        compile_order = resolve_build_order(manifest_data)
        print(f"\n[PHASE 2] Verified Build Order: {compile_order}")
    except Exception as e:
        return f"CRITICAL FAILURE during Dependency Mapping: {e}"

    # Phase 3 & 4: Iterative Generation + Compiler Feedback Loop
    code_context = "" 
    
    for class_name in compile_order:
        print(f"\n--- Building Module: [ {class_name} ] ---")
        success_this_class = False
        current_error_log = ""
        last_error = ""

        for attempt in range(MAX_COMPILE_RETRIES):
            print(f"  Attempt {attempt + 1}/{MAX_COMPILE_RETRIES}...")
            
            # Step 3: Intercept Loop & Query Ground Truth
            api_rules = retrieve_api_knowledge(class_name)
            
            prompt_data = {
                "prompt": (
                    f"Project Objective: {refined}\n\n"
                    f"Previously Written Headers (Use for #includes):\n{code_context}\n\n"
                    f"TASK: Generate the C++ Blueprint JSON for the class: {class_name}"
                ),
                "api_rules": api_rules
            }
            
            if current_error_log:
                prompt_data["prompt"] += f"\n\nCRITICAL: The previous attempt failed. Fix these errors:\n{current_error_log}"

            try:
                # 1. Generate JSON
                data = await generate_blueprint_json(llm, prompt_data)
                
                # --- BRUTAL DIAGNOSTIC: See what the LLM is actually doing ---
                if not isinstance(data, dict):
                    raise ValueError(f"LLM output must be a JSON object, got: {type(data).__name__}")

                print(f"  [DEBUG] Keys received from LLM: {list(data.keys())}")
                
                # If the LLM used 'className' instead of 'class_name', fix it manually
                if 'className' in data:
                    data['class_name'] = data.pop('className')
                if 'name' in data and 'class_name' not in data:
                    data['class_name'] = data.pop('name')
                if 'ClassName' in data and 'class_name' not in data:
                    data['class_name'] = data.pop('ClassName')
                
                # Force the class_name if it's still missing
                if 'class_name' not in data or not data['class_name']:
                    print(f"  [FIX] Forcing class_name to: {class_name}")
                    data['class_name'] = class_name
                else:
                    # Keep module boundaries strict: one loop iteration == one target class.
                    if str(data['class_name']) != class_name:
                        print(f"  [FIX] Rewriting class_name '{data['class_name']}' -> '{class_name}'")
                    data['class_name'] = class_name

                # Ensure parent class exists for schema validation.
                if 'parent_class' not in data or not data.get('parent_class'):
                    data['parent_class'] = 'AActor'

                # Normalize common include mistakes that break UHT/compile.
                includes = data.get('extra_includes', [])
                if isinstance(includes, list):
                    fixed_includes = []
                    for inc in includes:
                        inc_text = str(inc).strip()
                        if inc_text == 'GameFramework/ActorComponent.h':
                            inc_text = 'Components/ActorComponent.h'
                        if inc_text and inc_text not in fixed_includes:
                            fixed_includes.append(inc_text)
                    data['extra_includes'] = fixed_includes

                # Normalize common pointer mistakes in templated actor arrays.
                for var in data.get('variables', []) if isinstance(data.get('variables', []), list) else []:
                    if isinstance(var, dict) and isinstance(var.get('type'), str):
                        var['type'] = var['type'].replace('TArray<AActor>', 'TArray<AActor*>')
                for fn in data.get('functions', []) if isinstance(data.get('functions', []), list) else []:
                    if isinstance(fn, dict) and isinstance(fn.get('return_type'), str):
                        fn['return_type'] = fn['return_type'].replace('TArray<AActor>', 'TArray<AActor*>')
                    params = fn.get('params', []) if isinstance(fn, dict) else []
                    if isinstance(params, list):
                        for p in params:
                            if isinstance(p, dict) and isinstance(p.get('type'), str):
                                p['type'] = p['type'].replace('TArray<AActor>', 'TArray<AActor*>')
                
                # 2. Validate schema + render C++
                blueprint = Blueprint(**data)
                header_code, source_code = render_both(blueprint)

                # 3. Persist files (optional)
                if write_files:
                    h_path, cpp_path = write_class_files(
                        class_name=blueprint.class_name,
                        header_code=header_code,
                        source_code=source_code,
                    )
                    print(f"  [WRITE] {h_path}")
                    print(f"  [WRITE] {cpp_path}")
                
                # --- NEW: NO-COMPILE BYPASS ---
                if not validate_compile:
                    print(f" [SUCCESS] Module {class_name} written to disk.")
                    print(" -> SKIP: Headless compiler bypassed. Alt-Tab to Unreal and press Ctrl+Alt+F11 to Live Code.")
                    # Pass header context forward so multi-class generation remains coherent.
                    code_context += f"\n// {blueprint.class_name}.h\n{header_code[:4000]}\n"
                    success_this_class = True
                    break # Exit the retry loop for this class immediately

                # 4. Compile validation (optional, headless mode)
                if write_files and validate_compile:
                    ok, compile_log = run_headless_compile_check()
                    if not ok:
                        current_error_log = compile_log or "Unknown compile error"
                        last_error = current_error_log
                        print("  [CI/CD] Compile failed. Retrying with compiler feedback...")
                        continue

                # When compile validation is disabled (live coding path), still
                # pass header context forward so multi-class generation remains coherent.
                if write_files and (not validate_compile):
                    code_context += f"\n// {blueprint.class_name}.h\n{header_code[:4000]}\n"
                elif write_files and validate_compile:
                    # Add successful module header to future class context only after validation passes.
                    code_context += f"\n// {blueprint.class_name}.h\n{header_code[:4000]}\n"

                success_this_class = True
                print(f"  [OK] Module {class_name} built successfully.")
                break

            except Exception as e:
                print(f"\n  [!] FATAL VALIDATION ERROR on {class_name}")
                print(f"  [!] Error Type: {type(e).__name__}")
                print(f"  [!] Error Message: {str(e)}")
                last_error = str(e)
                current_error_log = str(e)
                if 'data' in locals():
                    print(f"  [!] RAW DATA RECEIVED FROM LLM:\n{json.dumps(data, indent=2)}")
                # Retry with explicit validation failure feedback.
                continue

        if not success_this_class:
            fail_reason = last_error or "unknown error"
            return (
                f"ABORTED: Module {class_name} failed to compile after {MAX_COMPILE_RETRIES} attempts. "
                f"Last error: {fail_reason}"
            )

    print(f"\n{'='*60}\n  CI/CD PIPELINE COMPLETE: {len(compile_order)} modules written.\n{'='*60}")
    if write_files and not validate_compile:
        return f"Build Generated (compile deferred): {compile_order}"
    return f"Build Successful: {compile_order}"


async def interactive_two_phase(llm, model_label: str, write_files: bool = False):
    """Interactive loop for two-phase C++ generation mode."""
    print("\n" + "=" * 62)
    print(f"  Two-Phase C++ Generator (Model: {model_label})")
    print("=" * 62)
    print("Type a request and press Enter.")
    print("Commands: 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("\nPrompt> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting two-phase mode.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Exiting two-phase mode.")
            break

        result = await two_phase_run(llm, user_input, write_files=write_files, validate_compile=write_files)
        print(f"\n[RESULT] {result}")
