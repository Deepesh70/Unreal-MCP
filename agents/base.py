"""
Base Agent Runner — shared MCP connection + agent execution logic.

Every backend (Groq, Ollama, Gemini) calls `run_agent()` with its
own LLM instance.  The MCP connection, tool loading, and execution
loop are identical across backends.
"""

import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage


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


async def run_agent(llm, model_label: str, prompt: str = None, interactive: bool = False):
    """
    Connect to the MCP server, load tools, create a LangChain agent,
    and execute the given prompt.

    Args:
        llm:          An initialized LangChain chat model (any provider).
        model_label:  Human-readable name for logging.
        prompt:       The instruction to send. Falls back to DEFAULT_PROMPT.
        interactive:  If True, enter a loop where the user types commands.
    """
    print(f"🤖 Booting up {model_label} and connecting to Unreal Engine...")

    client = MultiServerMCPClient(MCP_SERVER_CONFIG)
    tools = await client.get_tools()
    print(f"🛠️  Loaded {len(tools)} tools from FastMCP.")

    agent = create_agent(llm, tools)

    if interactive:
        await _interactive_loop(agent, model_label)
    else:
        prompt = prompt or DEFAULT_PROMPT
        await _run_single(agent, prompt)


async def _run_single(agent, prompt: str):
    """Execute a single prompt and print the result."""
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
