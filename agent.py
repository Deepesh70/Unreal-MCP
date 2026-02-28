"""
Unreal MCP Agent — Multi-Model CLI Launcher.

Run with one of three LLM backends:

    python agent.py groq                    ← Full demo prompt
    python agent.py gemini --test           ← Quick test (1 API call only)
    python agent.py groq --interactive      ← Chat mode (type commands)

Or run a backend directly:

    python -m agents.groq_agent
    python -m agents.ollama_agent --model qwen2.5:72b
    python -m agents.gemini_agent --model gemini-2.5-flash
"""

import asyncio
import sys


def print_usage():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              🎮  Unreal MCP Agent Launcher  🎮              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Usage:  python agent.py <backend> [options]                 ║
║                                                              ║
║  Backends:                                                   ║
║    groq     Groq Cloud  — Llama 3.3 70B (fast, free tier)    ║
║    ollama   Local       — 70B+ models on your GPU            ║
║    gemini   Google      — Gemini 2.5 Pro (100B+ estimated)   ║
║                                                              ║
║  Options:                                                    ║
║    --test          Quick test (1 API call, lists actors)      ║
║    --interactive   Chat mode (type commands one by one)       ║
║    --prompt "..."  Custom prompt                              ║
║                                                              ║
║  Examples:                                                   ║
║    python agent.py groq                                      ║
║    python agent.py gemini --test                              ║
║    python agent.py groq --interactive                         ║
║    python agent.py groq --prompt "spawn a cube at 0 0 200"   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def parse_options():
    """Parse --test, --interactive, and --prompt flags."""
    test_mode = "--test" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv
    prompt = None

    if "--prompt" in sys.argv:
        idx = sys.argv.index("--prompt")
        if idx + 1 < len(sys.argv):
            prompt = sys.argv[idx + 1]

    return test_mode, interactive, prompt


async def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print_usage()
        sys.exit(1)

    backend = sys.argv[1].lower()
    test_mode, interactive, custom_prompt = parse_options()

    # Determine prompt
    from agents.base import run_agent, TEST_PROMPT
    if test_mode:
        prompt = TEST_PROMPT
        interactive = False
    else:
        prompt = custom_prompt  # None = use DEFAULT_PROMPT

    if backend == "groq":
        from agents.groq_agent import create_llm
        llm = create_llm()
        label = "Llama 3.1 8B via Groq (free tier)"

    elif backend == "ollama":
        from agents.ollama_agent import create_llm
        llm = create_llm()
        label = "llama3.3:70b via Ollama (local)"

    elif backend == "gemini":
        from agents.gemini_agent import create_llm
        llm = create_llm()
        label = "gemini-2.5-pro via Google Gemini"

    else:
        print(f"❌ Unknown backend: '{backend}'")
        print_usage()
        sys.exit(1)

    await run_agent(llm, model_label=label, prompt=prompt, interactive=interactive)


if __name__ == "__main__":
    asyncio.run(main())