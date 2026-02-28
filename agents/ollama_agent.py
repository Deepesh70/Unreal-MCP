"""
Ollama Agent — Uses a locally running Ollama server with large models.

Recommended models (all 30B+ parameters):
  • llama3.3:70b        — Meta Llama 3.3, 70B params (best balance)
  • qwen2.5:72b         — Alibaba Qwen 2.5, 72B params (strong tool-calling)
  • deepseek-r1:70b     — DeepSeek R1, 70B params (reasoning focused)
  • command-r-plus:104b — Cohere Command R+, 104B params (large & capable)
  • llama3.1:70b        — Meta Llama 3.1, 70B params (stable & proven)

Prerequisites:
  1. Install Ollama: https://ollama.com
  2. Pull a model: ollama pull llama3.3:70b
  3. Ollama runs automatically at http://localhost:11434

Usage:
    python -m agents.ollama_agent
    python -m agents.ollama_agent --model qwen2.5:72b
"""

import asyncio
import argparse
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from agents.base import run_agent

load_dotenv()

# ── Supported models (all 30B+ parameters) ───────────────────────────
SUPPORTED_MODELS = {
    "llama3.3:70b":        "Meta Llama 3.3 — 70B params, best overall",
    "qwen2.5:72b":         "Alibaba Qwen 2.5 — 72B params, strong tool-calling",
    "deepseek-r1:70b":     "DeepSeek R1 — 70B params, reasoning focused",
    "command-r-plus:104b": "Cohere Command R+ — 104B params, very large",
    "llama3.1:70b":        "Meta Llama 3.1 — 70B params, stable & proven",
}

DEFAULT_MODEL = "llama3.3:70b"


def create_llm(model: str = DEFAULT_MODEL):
    """Create and return the Ollama LLM instance."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Run Unreal MCP agent with local Ollama models")
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Ollama model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="List all recommended models and exit",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    if args.list_models:
        print("📦 Recommended Ollama models (all 30B+ params):\n")
        for model, desc in SUPPORTED_MODELS.items():
            marker = " ← default" if model == DEFAULT_MODEL else ""
            print(f"  • {model:25s} {desc}{marker}")
        print(f"\nPull a model:  ollama pull {DEFAULT_MODEL}")
        return

    model = args.model
    llm = create_llm(model)
    await run_agent(llm, model_label=f"{model} via Ollama (local)")


if __name__ == "__main__":
    asyncio.run(main())
