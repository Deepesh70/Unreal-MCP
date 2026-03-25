"""
Base Agent Runner — shared MCP connection + agent execution logic.

Every backend (Groq, Ollama, Gemini) calls `run_agent()` with its
own LLM instance.  The MCP connection, tool loading, and execution
loop are identical across backends.

Builder mode (-b) bypasses LangChain entirely — calls the LLM directly
with a lean system prompt, then routes JSON output through processor.py.
This keeps token usage under Groq's free-tier 12k TPM limit.
"""

import sys

# Ensure Windows consoles can print emojis without throwing a UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

from agents.processor import process_agent_output
from unreal_mcp.config.settings import CPP_OUTPUT_DIR, PROJECT_API


# ── MCP Server Configuration ─────────────────────────────────────────
MCP_SERVER_CONFIG = {
    "UnrealMCP": {
        "transport": "sse",
        "url": "http://localhost:8000/sse",
    }
}

# ── Default prompts ───────────────────────────────────────────────────
DEFAULT_PROMPT = (
    "Spawn a cube at X:0, Y:0, Z:100 and sphere at X:1000, Y:1000, Z:1000. "
    "Next, use the list_actors tool to find the full path of the cube you just spawned. "
    "Then, use the set_actor_scale tool to scale that exact cube to X:500.0, Y:500.0, Z:500.0 "
    "so it is huge and easy to see. Finally, tell me that it worked."
)

# Minimal test — only 1 tool call, uses very few tokens
TEST_PROMPT = "List all actors currently in the Unreal level."


# ── Builder System Prompt (lean — ~500 tokens) ───────────────────────
BUILDER_SYSTEM_PROMPT = """\
You are an Unreal Engine Procedural Builder. Output ONLY a single JSON object, no markdown, no explanation.

Pick ONE action per response:

ACTION 1 — SpawnActor (build structures from basic shapes):
{"Action":"SpawnActor","ClassToSpawn":"<DescriptiveName>","Parameters":{"NumberOfFloors":<int>,"X":0,"Y":0,"Z":0}}
The system auto-generates per floor: 1 floor slab + 4 walls + 1 roof on top.
Optional overrides: "FloorHeight":300, "BuildingWidth":1000, "BuildingDepth":1000.
Estimate floors from height requests (1 floor ≈ 3m). A "25 height" skyscraper ≈ 8 floors.

ACTION 2 — CreateClass (generate C++ files):
{"Action":"CreateClass","ClassName":"<AMyActor>","Files":[{"FileName":"MyActor.h","Content":"#pragma once\\n..."},{"FileName":"MyActor.cpp","Content":"#include \\"MyActor.h\\"\\n..."}]}
Use {{PROJECT_API}} as the export macro. Include UCLASS(Blueprintable, Placeable).

Rules:
- For buildings/structures → SpawnActor.
- For new gameplay classes/components → CreateClass.
- Output raw JSON only. No code fences, no prose."""

BUILDER_DEFAULT_PROMPT = (
    "Build a simple house structure: "
    "Use scaled cubes for walls and a floor, and a scaled cube angled as a roof. "
    "Place the structure at X:0, Y:0, Z:0. "
    "List all actors when done to confirm."
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_agent(llm, model_label: str, prompt: str = None,
                    interactive: bool = False, builder: bool = False):
    """
    Connect to the MCP server, load tools, create a LangChain agent,
    and execute the given prompt.

    Args:
        llm:          An initialized LangChain chat model (any provider).
        model_label:  Human-readable name for logging.
        prompt:       The instruction to send. Falls back to DEFAULT_PROMPT.
        interactive:  If True, enter a loop where the user types commands.
        builder:      If True, use Builder mode (bypasses LangChain, calls LLM directly).
    """
    mode_label = "Builder 🏗️" if builder else "Standard"
    print(f"🤖 Booting up {model_label} [{mode_label}] and connecting to Unreal Engine...")

    if builder:
        # ── Builder mode: LLM direct call, no LangChain agent ────
        print(f"🏗️  Builder mode — LLM will output strict JSON (no ReAct overhead).")
        if interactive:
            await _interactive_builder_loop(llm, model_label)
        else:
            prompt = prompt or BUILDER_DEFAULT_PROMPT
            await _run_builder(llm, prompt)
    else:
        # ── Standard mode: LangChain tool-calling agent ──────────
        client = MultiServerMCPClient(MCP_SERVER_CONFIG)
        tools = await client.get_tools()
        print(f"🛠️  Loaded {len(tools)} tools from FastMCP.")
        agent = create_agent(llm, tools)

        if interactive:
            await _interactive_loop(agent, model_label)
        else:
            prompt = prompt or DEFAULT_PROMPT
            await _run_single(agent, prompt)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Builder Mode — Direct LLM Call (no LangChain overhead)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_builder(llm, prompt: str):
    """Call the LLM directly with the builder system prompt, then route JSON to processor."""
    print(f"\n🗣️ Prompt: {prompt}\n")

    messages = [
        SystemMessage(content=BUILDER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content

    print(f"📦 Raw LLM output:\n{raw}\n")

    result = await process_agent_output(raw, CPP_OUTPUT_DIR, PROJECT_API)
    print(f"\n{result}")


async def _interactive_builder_loop(llm, model_label: str):
    """Interactive REPL for builder mode — each command is a fresh LLM call."""
    print(f"\n{'='*60}")
    print(f"  🏗️  Builder Mode — {model_label}")
    print(f"  Type a command and press Enter.")
    print(f"  Type 'quit' or 'exit' to stop.")
    print(f"{'='*60}")
    print(f"\n  Quick commands to try:")
    print(f"    • create a 5 floor skyscraper")
    print(f"    • build a house at 0 0 0")
    print(f"    • create a freeze trap C++ class")
    print(f"\n")

    while True:
        try:
            user_input = input("🏗️ Builder > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break

        try:
            await _run_builder(llm, user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}")
        print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Standard Mode — LangChain Tool-Calling Agent
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _run_single(agent, prompt: str):
    """Execute a single prompt through the LangChain agent and print the result."""
    print(f"\n🗣️ Prompt: {prompt}\n")

    response = await agent.ainvoke({
        "messages": [HumanMessage(content=prompt)]
    })

    print("\n✅ Final Response:")
    print(response["messages"][-1].content)


async def _interactive_loop(agent, model_label: str):
    """Interactive REPL — type commands one at a time to save API quota."""
    print(f"\n{'='*60}")
    print(f"  🎮 Interactive Mode — {model_label}")
    print(f"  Type a command and press Enter.")
    print(f"  Type 'quit' or 'exit' to stop.")
    print(f"{'='*60}")
    print(f"\n  Quick commands to try:")
    print(f"    • list all actors")
    print(f"    • spawn a cube at 0 0 200")
    print(f"    • spawn a sphere at 500 500 500")
    print(f"\n")

    while True:
        try:
            user_input = input("🎮 You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break

        try:
            await _run_single(agent, user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}")
        print()
