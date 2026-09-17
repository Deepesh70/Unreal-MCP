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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


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
║  Modes:                                                      ║
║    (default)       Standard — MCP tools (spawn, list, scale) ║
║    --builder, -b   Builder  — C++ Procedural Architect mode  ║
║                                                              ║
║  MCP Targets:                                                ║
║    --target native (default) Standalone FastMCP (UE 5.0-5.6) ║
║    --target epic / --epic    Epic Official MCP (UE 5.8+)     ║
║    --url <url>               Custom MCP endpoint URL         ║
║                                                              ║
║  Options:                                                    ║
║    --test          Quick test (1 API call, lists actors)      ║
║    --interactive   Chat mode (type commands one by one)       ║
║    --prompt "..."  Custom prompt                              ║
║                                                              ║
║  Examples:                                                   ║
║    python agent.py groq                                      ║
║    python agent.py groq --epic      ← Target Epic UE 5.8 MCP ║
║    python agent.py groq -b -i       ← Builder + Interactive  ║
║    python agent.py gemini --test                             ║
║    python agent.py groq --prompt "spawn a cube at 0 0 200"   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def parse_options():
    """Parse CLI options including MCP targets."""
    test_mode = "--test" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv
    builder = "--builder" in sys.argv or "-b" in sys.argv
    epic_target = "--epic" in sys.argv

    target = "epic" if epic_target else "native"
    if "--target" in sys.argv:
        idx = sys.argv.index("--target")
        if idx + 1 < len(sys.argv):
            val = sys.argv[idx + 1].lower()
            if val in ("epic", "official"):
                target = "epic"
            elif val in ("native", "fastmcp"):
                target = "native"

    mcp_url = None
    if "--url" in sys.argv:
        idx = sys.argv.index("--url")
        if idx + 1 < len(sys.argv):
            mcp_url = sys.argv[idx + 1]

    prompt = None
    if "--prompt" in sys.argv:
        idx = sys.argv.index("--prompt")
        if idx + 1 < len(sys.argv):
            prompt = sys.argv[idx + 1]

    return test_mode, interactive, builder, prompt, target, mcp_url


async def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print_usage()
        sys.exit(1)

    backend = sys.argv[1].lower()
    test_mode, interactive, builder, custom_prompt, target_mcp, mcp_url = parse_options()

    try:
        from unreal_mcp.agents.base import run_agent, TEST_PROMPT
    except ImportError:
        from agents.base import run_agent, TEST_PROMPT

    prompt = TEST_PROMPT if test_mode else custom_prompt

    # ── Create LLM ──────────────────────────────────────────────
    if backend == "groq":
        try:
            from unreal_mcp.agents.groq_agent import create_llm
        except ImportError:
            from agents.groq_agent import create_llm
        llm = create_llm()
        label = "Llama 3.3 70B via Groq"

    elif backend == "ollama":
        try:
            from unreal_mcp.agents.ollama_agent import create_llm
        except ImportError:
            from agents.ollama_agent import create_llm
        llm = create_llm()
        label = "Ollama (local)"

    elif backend == "gemini":
        try:
            from unreal_mcp.agents.gemini_agent import create_llm
        except ImportError:
            from agents.gemini_agent import create_llm
        llm = create_llm()
        label = "Gemini 2.5 Pro"

    else:
        print(f"Unknown backend: '{backend}'")
        print_usage()
        sys.exit(1)

    await run_agent(
        llm,
        model_label=label,
        prompt=prompt,
        interactive=interactive,
        builder=builder,
        target_mcp=target_mcp,
        mcp_url=mcp_url,
    )



if __name__ == "__main__":
    asyncio.run(main())