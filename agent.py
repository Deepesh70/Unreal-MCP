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
    --two-phase / -2   C++ class generator (writes .h/.cpp files)
    --test             Quick test (1 API call)
    (default)          Classic tool-calling agent

  Options:
    --interactive / -i  Interactive chat mode
    --prompt "..."      Custom prompt

  Examples:
    python agent.py groq -b -i              # Interactive builder (BEST)
    python agent.py groq -b --prompt "build a hut"
    python agent.py groq -2 -i              # C++ code generator
    python agent.py groq --test             # Quick test

==============================================================
""")


def parse_options():
    test_mode = "--test" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv
    two_phase = "--two-phase" in sys.argv or "-2" in sys.argv
    build_mode = "--build" in sys.argv or "-b" in sys.argv
    prompt = None

    if "--prompt" in sys.argv:
        idx = sys.argv.index("--prompt")
        if idx + 1 < len(sys.argv):
            prompt = sys.argv[idx + 1]

    return test_mode, interactive, two_phase, build_mode, prompt


async def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print_usage()
        sys.exit(1)

    backend = sys.argv[1].lower()
    test_mode, interactive, two_phase, build_mode, custom_prompt = parse_options()

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
        elif custom_prompt:
            await build_in_ue(llm, custom_prompt)
        else:
            await build_in_ue(llm, "build a small hut with walls, a roof, and a door")
        return

    # ── C++ Code Generation Mode ────────────────────────────────
    if two_phase:
        from agents.pipeline import two_phase_run, interactive_two_phase

        if interactive:
            await interactive_two_phase(llm, label)
        elif custom_prompt:
            await two_phase_run(llm, custom_prompt, write_files=False)
        else:
            await two_phase_run(llm, "Create a hut actor", write_files=False)
        return

    # ── Classic Tool-Calling Mode ───────────────────────────────
    from agents.base import run_agent, TEST_PROMPT

    if test_mode:
        prompt = TEST_PROMPT
        interactive = False
    else:
        prompt = custom_prompt

    await run_agent(llm, model_label=label, prompt=prompt, interactive=interactive)


if __name__ == "__main__":
    asyncio.run(main())