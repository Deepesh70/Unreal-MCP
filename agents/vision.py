"""
Vision Module — Feature 3: Visual Feedback Loop.

Captures viewport screenshots from Unreal Engine and sends them
to a multimodal LLM (Gemini) for aesthetic critique. The critique
is returned as suggested Modify intents.

Usage:
    from agents.vision import capture_screenshot, critique_scene, auto_refine
"""

import json
import os
import time
import base64

from agents.processor import _discover_city_manager, _handle_unreal_intent


# ── Screenshot Capture ───────────────────────────────────────────────

async def capture_screenshot(filename: str = None) -> str:
    """
    Request a viewport screenshot from Unreal via the CityManager.

    Returns the file path where the screenshot will be saved, or an error string.
    """
    if not filename:
        filename = f"MCP_Screenshot_{int(time.time())}"

    payload = {
        "Intent": "Screenshot",
        "Filename": filename,
    }

    try:
        manager_path = await _discover_city_manager()
        from unreal_mcp.connection import send_ue_ws_command
        json_payload = json.dumps(payload, separators=(",", ":"))

        response = await send_ue_ws_command(
            object_path=manager_path,
            function_name="ProcessBlueprint",
            parameters={"JsonPayload": json_payload},
        )

        receipt_str = response.get("ResponseBody", {}).get("ReturnValue", "")
        if receipt_str:
            receipt = json.loads(receipt_str)
            filepath = receipt.get("FilePath", "")
            print(f"📸 Screenshot requested: {filepath}")
            return filepath

        return "⚠️  No receipt from Screenshot request."
    except Exception as e:
        return f"❌ Screenshot failed: {e}"


# ── Multimodal Critique ──────────────────────────────────────────────

async def critique_scene(image_path: str, original_prompt: str, llm=None) -> str:
    """
    Send a screenshot to a multimodal LLM for aesthetic analysis.

    Args:
        image_path:      Path to the screenshot file.
        original_prompt: The original build request for context.
        llm:             An optional multimodal LLM instance. If None, uses Gemini.

    Returns:
        A string with the critique and suggested modifications.
    """
    if not os.path.exists(image_path):
        return f"⚠️  Screenshot not found at: {image_path}. Screenshot may still be rendering."

    # Read and base64-encode the image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    critique_prompt = f"""You are an expert 3D environment critic. Analyze this screenshot of a procedurally generated scene.

Original build request: "{original_prompt}"

Evaluate the scene on these criteria:
1. **Spatial Layout** — Are buildings properly spaced? Any overlapping or floating?
2. **Style Coherence** — Do the building styles match the requested theme?
3. **Scale & Proportion** — Are buildings realistically sized relative to each other?
4. **Visual Density** — Is the scene too sparse or too crowded?
5. **Missing Elements** — What would improve the scene? (roads, vegetation, lighting)

Then output a JSON array of suggested Modify/Spawn intents to improve the scene.
Output the critique text first, then the JSON array on a separate line starting with ```json
"""

    if llm:
        try:
            from langchain_core.messages import HumanMessage
            message = HumanMessage(
                content=[
                    {"type": "text", "text": critique_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ]
            )
            response = await llm.ainvoke([message])
            return response.content
        except Exception as e:
            return f"⚠️  Multimodal critique failed: {e}\n   Ensure you're using a vision-capable model (Gemini 2.5 Pro)."

    return (
        "⚠️  No multimodal LLM provided. To use visual critique:\n"
        "   python agent.py gemini -b -i\n"
        "   Then type: screenshot\n"
        "   Then type: refine"
    )


# ── Auto-Refine Loop ────────────────────────────────────────────────

async def auto_refine(llm, original_prompt: str, process_fn) -> str:
    """
    Full auto-refinement loop:
    1. Capture a screenshot
    2. Send to multimodal LLM for critique
    3. Parse suggested modifications
    4. Apply them

    Returns a summary of what was changed.
    """
    print("🔄 Auto-refine: Capturing viewport...")
    filepath = await capture_screenshot()

    if filepath.startswith("❌") or filepath.startswith("⚠️"):
        return filepath

    # Wait a moment for the screenshot to be written to disk
    print("⏳ Waiting 2 seconds for screenshot to render...")
    import asyncio
    await asyncio.sleep(2)

    print("🧠 Sending to multimodal LLM for critique...")
    critique = await critique_scene(filepath, original_prompt, llm)
    print(f"\n📝 Critique:\n{critique}\n")

    # Try to extract JSON modifications from the critique
    import re
    json_match = re.search(r'```json\s*(.*?)```', critique, re.DOTALL)
    if json_match:
        try:
            modifications = json.loads(json_match.group(1))
            if isinstance(modifications, list):
                print(f"🔧 Found {len(modifications)} suggested modification(s). Applying...")
                results = []
                for mod in modifications:
                    if isinstance(mod, dict) and "Intent" in mod:
                        result = await process_fn(json.dumps(mod))
                        results.append(result)
                        print(f"   {result}")
                return f"✅ Auto-refine complete: {len(results)} modification(s) applied."
        except json.JSONDecodeError:
            pass

    return "📝 Critique received but no auto-applicable modifications found."
