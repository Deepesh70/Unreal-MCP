"""
Unreal MCP Agent - Multi-Model CLI Launcher.

Modes:
    python agent.py groq --build              # LIVE builder (spawns in UE!)
    python agent.py groq --build -i           # Interactive builder
    python agent.py groq --two-phase          # C++ code generator
    python agent.py groq --test               # Quick test (1 API call)

Backends:
    groq     Groq Cloud (Llama 3.1 8B free tier)
    ollama   Local Ollama models
    gemini   Google Gemini
"""

import asyncio
import sys
import io
import os

# Suppress TensorFlow and oneDNN C++ warnings during HuggingFace embeddings load
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_usage():
    print("""
==============================================================
           Unreal MCP Agent Launcher
==============================================================

  Usage:  python agent.py <backend> [mode] [options]

  Backends:
    groq      Groq Cloud (fast, free tier)
    ollama    Local models via Ollama
    gemini    Google Gemini API

  Modes:
    --build / -b       LIVE BUILDER: spawns objects in UE via WebSocket!
        --two-phase / -2   C++ class generator (writes + compile checks)
    --test             Quick test (1 API call)
    (default)          Classic tool-calling agent

  Options:
    --interactive / -i  Interactive chat mode
    --prompt "..."      Custom prompt
        --dry-run           Two-phase preview only (no file writes, no compile)
        --level "..."       Target level hint for --build mode prompts

  Examples:
    python agent.py groq -b -i              # Interactive builder (BEST)
    python agent.py groq -b --prompt "build a hut"
        python agent.py groq -b --level "/Game/Maps/TestMap" --prompt "spawn 3 cubes"
        python agent.py groq -2 -i              # C++ generator with compile checks
        python agent.py groq -2 --dry-run --prompt "Create WeatherController actor"
    python agent.py groq --test             # Quick test

==============================================================
""")


def parse_options():
    test_mode = "--test" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv
    two_phase = "--two-phase" in sys.argv or "-2" in sys.argv
    build_mode = "--build" in sys.argv or "-b" in sys.argv
    dry_run = "--dry-run" in sys.argv
    level = None
    prompt = None

    if "--prompt" in sys.argv:
        idx = sys.argv.index("--prompt")
        if idx + 1 < len(sys.argv):
            prompt = sys.argv[idx + 1]

    if "--level" in sys.argv:
        idx = sys.argv.index("--level")
        if idx + 1 < len(sys.argv):
            level = sys.argv[idx + 1]

    return test_mode, interactive, two_phase, build_mode, dry_run, level, prompt


def _require_prompt(mode_name: str, prompt: str | None) -> bool:
    """Return False and show guidance when prompt is required but missing."""
    if prompt:
        return True
    print(f"Please provide a prompt for {mode_name} mode using --prompt \"...\".")
    return False


async def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print_usage()
        sys.exit(1)

    backend = sys.argv[1].lower()
    test_mode, interactive, two_phase, build_mode, dry_run, level, custom_prompt = parse_options()

    # ── Create LLM ──────────────────────────────────────────────
    if backend == "groq":
        from agents.groq_agent import create_llm
        llm = create_llm()
        label = "Llama 3.1 8B via Groq"

    elif backend == "ollama":
        from agents.ollama_agent import create_llm
        llm = create_llm()
        label = "Ollama (local)"

    elif backend == "gemini":
        from agents.gemini_agent import create_llm
        llm = create_llm()
        label = "Gemini 2.5 Pro"

    else:
        print(f"Unknown backend: '{backend}'")
        print_usage()
        sys.exit(1)

    # ── LIVE BUILD MODE (spawns in UE!) ─────────────────────────
    if build_mode:
        from agents.builder import build_in_ue, interactive_builder

        if interactive:
            await interactive_builder(llm, label)
        else:
            if not _require_prompt("build", custom_prompt):
                print_usage()
                sys.exit(1)

            prompt_for_build = custom_prompt
            if level:
                prompt_for_build = (
                    f"Target Unreal level: {level}. If this level is not currently open, ask to open it first.\n"
                    f"Task: {custom_prompt}"
                )

            await build_in_ue(llm, prompt_for_build)
        return

    # ── C++ Code Generation Mode ────────────────────────────────
    if two_phase:
        from agents.pipeline import two_phase_run, interactive_two_phase
        write_files = not dry_run

        if level:
            print("Note: --level is ignored in --two-phase mode (C++ class generation is not level-specific).")

        if interactive:
            await interactive_two_phase(llm, label, write_files=write_files)
        else:
            if not _require_prompt("two-phase", custom_prompt):
                print_usage()
                sys.exit(1)

            result = await two_phase_run(llm, custom_prompt, write_files=write_files)
            print(f"\n[RESULT] {result}")
        return

    # ── Classic Tool-Calling Mode ───────────────────────────────
    from agents.base import run_agent, TEST_PROMPT

    if test_mode:
        prompt = TEST_PROMPT
        interactive = False
    else:
        prompt = custom_prompt

    if not interactive and not test_mode and not _require_prompt("classic", prompt):
        print_usage()
        sys.exit(1)

    await run_agent(llm, model_label=label, prompt=prompt, interactive=interactive)


if __name__ == "__main__":
    asyncio.run(main())