"""
IDE Bridge — Lets IDE AI models drive Unreal-MCP by injecting JSON intents.

Usage:
    python -m unreal_mcp.api.bridge '{"Intent":"Spawn","ID":"House_01",...}'
    python -m unreal_mcp.api.bridge batch file.json
    python -m unreal_mcp.api.bridge status
    python -m unreal_mcp.api.bridge screenshot
    python -m unreal_mcp.api.bridge refine "prompt"
"""

import sys
import os
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

# Safe console encoding on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from unreal_mcp.agents.processor import process_agent_output, reset_manager_cache
except ImportError:
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
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return await send_intent(content)


async def check_status() -> str:
    """Quick connection check — tries to discover the CityManager."""
    try:
        try:
            from unreal_mcp.agents.processor import _discover_city_manager
        except ImportError:
            from agents.processor import _discover_city_manager
        path = await _discover_city_manager()
        return f"Connected! CityManager at: {path}"
    except Exception as e:
        return f"CityManager not found: {e}\n(Legacy direct-spawn mode will be used)"


async def run_screenshot() -> str:
    """Capture a screenshot from Unreal Engine viewport."""
    try:
        try:
            from unreal_mcp.agents.vision import capture_screenshot
        except ImportError:
            from agents.vision import capture_screenshot
        filepath = await capture_screenshot()
        return filepath
    except Exception as e:
        return f"Screenshot error: {e}"


async def run_refine(prompt: str) -> str:
    """Vision-based scene refinement using Gemini."""
    try:
        try:
            from unreal_mcp.agents.vision import auto_refine
        except ImportError:
            from agents.vision import auto_refine
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.2
        )

        print("Taking screenshot and querying vision model...")
        result = await auto_refine(
            llm,
            prompt,
            lambda raw: process_agent_output(raw, CPP_OUTPUT_DIR, PROJECT_API)
        )
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
