"""
Groq Agent — Uses Groq Cloud API.

Models available:
  • llama-3.3-70b-versatile  — 70B params (needs Groq Dev Tier for tool-calling)
  • llama-3.1-8b-instant     — 8B params, works on Free Tier (higher TPM limits)

Usage:
    python -m agents.groq_agent
    python -m agents.groq_agent --model llama-3.1-8b-instant
"""

import asyncio
import argparse
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from agents.base import run_agent

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def create_llm(model: str = DEFAULT_MODEL):
    """Create and return the Groq LLM instance."""
    return ChatGroq(
        model=model,
        temperature=0,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Run Unreal MCP agent with Groq")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--interactive", "-i", action="store_true")
    return parser.parse_args()


async def main():
    args = parse_args()
    llm = create_llm(args.model)

    from agents.base import TEST_PROMPT
    prompt = TEST_PROMPT if args.test else None

    await run_agent(
        llm,
        model_label=f"{args.model} via Groq",
        prompt=prompt,
        interactive=args.interactive,
    )


if __name__ == "__main__":
    asyncio.run(main())
