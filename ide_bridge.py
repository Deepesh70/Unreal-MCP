"""
IDE Bridge — Lets the IDE's AI model (Antigravity/Gemini Code Assist)
drive Unreal-MCP directly by injecting JSON intents.

Usage:
    python ide_bridge.py '{"Intent":"Spawn","ID":"House_01",...}'
    python ide_bridge.py batch file.json        # Read JSON from file
    python ide_bridge.py status                 # Check connection
    python ide_bridge.py screenshot             # Take a screenshot
    python ide_bridge.py refine "prompt"        # Vision-based refinement

The IDE agent generates the correct JSON (it knows the schema),
then runs this script to push it straight to Unreal Engine.
No separate LLM call needed — the IDE IS the brain.
"""

import sys
import os

# Fix Windows console encoding for emoji output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import json

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from agents.processor import process_agent_output, reset_manager_cache
from unreal_mcp.config.settings import CPP_OUTPUT_DIR, PROJECT_API


async def send_intent(json_str: str) -> str:
    """Send a JSON intent string through the processor pipeline."""
    result = await process_agent_output(
        raw_content=json_str,
        output_dir=CPP_OUTPUT_DIR,
        project_api=PROJECT_API,
        user_prompt="(IDE Bridge)"
    )
    return result


async def send_intents_from_file(filepath: str) -> str:
    """Read JSON from a file and send it."""
    with open(filepath, "r") as f:
        content = f.read()
    return await send_intent(content)


async def check_status() -> str:
    """Quick connection check — tries to discover the CityManager."""
    try:
        from agents.processor import _discover_city_manager
        path = await _discover_city_manager()
        return f"Connected! CityManager at: {path}"
    except Exception as e:
        return f"CityManager not found: {e}\n(Legacy direct-spawn mode will be used)"


async def run_screenshot() -> str:
    try:
        from agents.vision import capture_screenshot
        filepath = await capture_screenshot()
        return filepath
    except Exception as e:
        return f"Screenshot error: {e}"


async def run_refine(prompt: str) -> str:
    try:
        from agents.vision import auto_refine
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Instantiate a multimodal LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.2
        )
        
        print("Taking screenshot and querying vision model...")
        result = await auto_refine(llm, prompt, 
            lambda raw: process_agent_output(raw, CPP_OUTPUT_DIR, PROJECT_API))
        return result
    except Exception as e:
        return f"Refine error: {e}"


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].strip()

    if cmd == "status":
        print(await check_status())
        return

    if cmd == "reset":
        reset_manager_cache()
        print("Cache cleared.")
        return

    if cmd == "screenshot":
        print(await run_screenshot())
        return

    if cmd == "refine" and len(sys.argv) >= 3:
        prompt = " ".join(sys.argv[2:])
        print(await run_refine(prompt))
        return

    if cmd == "batch" and len(sys.argv) >= 3:
        result = await send_intents_from_file(sys.argv[2])
        print(result)
        return

    # Treat argument as raw JSON
    json_input = " ".join(sys.argv[1:])
    result = await send_intent(json_input)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
