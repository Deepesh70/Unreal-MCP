"""
Gemini Agent — Uses Google Gemini API with Gemini 2.5 Pro / Flash models.

Available models (all large-scale):
  • gemini-2.5-pro       — Google's most capable model, massive parameter count
  • gemini-2.5-flash     — Fast & efficient, still very large
  • gemini-2.0-flash     — Previous gen, fast inference

Note: Google does not publish exact parameter counts for Gemini models,
but Gemini 2.5 Pro is estimated to be well above 100B+ parameters.
Gemini 3.0 / 3.1 will be selectable here as soon as Google releases them —
just update the model name.

Prerequisites:
  1. Get a Google API key: https://aistudio.google.com/apikey
  2. Set GOOGLE_API_KEY in your .env file

Usage:
    python -m agents.gemini_agent
    python -m agents.gemini_agent --model gemini-2.5-flash
"""

import asyncio
import argparse
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.base import run_agent

load_dotenv()

# ── Supported models ─────────────────────────────────────────────────
SUPPORTED_MODELS = {
    "gemini-2.5-pro":   "Most capable Gemini model, 100B+ params (estimated)",
    "gemini-2.5-flash": "Fast & efficient Gemini, large-scale",
    "gemini-2.0-flash": "Previous gen, fast inference",
}

DEFAULT_MODEL = "gemini-2.5-pro"


def create_llm(model: str = DEFAULT_MODEL):
    """Create and return the Gemini LLM instance."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment.\n"
            "Get one at https://aistudio.google.com/apikey and add it to your .env file."
        )

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Run Unreal MCP agent with Google Gemini")
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="List all supported models and exit",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    if args.list_models:
        print("🌟 Supported Gemini models:\n")
        for model, desc in SUPPORTED_MODELS.items():
            marker = " ← default" if model == DEFAULT_MODEL else ""
            print(f"  • {model:25s} {desc}{marker}")
        print("\nWhen Gemini 3.0/3.1 releases, just change the model name here!")
        return

    model = args.model
    llm = create_llm(model)
    await run_agent(llm, model_label=f"{model} via Google Gemini")


if __name__ == "__main__":
    asyncio.run(main())
