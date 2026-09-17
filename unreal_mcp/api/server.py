"""
FastAPI WebSocket Server for Unreal-MCP.
Connects web frontends (e.g. Next.js) to Unreal Engine multi-agent pipelines.
"""

import json
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from unreal_mcp.config.settings import UE_WS_URL

# Attempt import from unreal_mcp.agents, falling back to agents
try:
    from unreal_mcp.agents.groq_agent import create_llm
except ImportError:
    from agents.groq_agent import create_llm

app = FastAPI(title="Unreal-MCP API Server")


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Wait for prompt from client
            data = await websocket.receive_text()

            # Parse JSON payload if applicable
            try:
                payload = json.loads(data)
                if isinstance(payload, dict) and "prompt" in payload:
                    user_prompt = payload.get("prompt")
                    config = payload.get("config", {})
                else:
                    user_prompt = data
                    config = {}
            except json.JSONDecodeError:
                user_prompt = data
                config = {}

            backend = config.get("backend", "groq")
            mode = config.get("mode", "build")

            # 1.5 Pre-flight check: Is Unreal Engine running?
            try:
                async with websockets.connect(UE_WS_URL) as ws:
                    pass  # Connection successful
            except Exception as e:
                error_msg = (
                    f"Unreal Engine connection failed ({str(e)}). "
                    "Please ensure Unreal Engine is running and the Remote Control Web Interface is started."
                )
                await websocket.send_json({"type": "error", "message": error_msg})
                continue

            # 2. Callback to send real-time logs
            async def ws_callback(msg):
                if isinstance(msg, dict):
                    await websocket.send_json(msg)
                else:
                    await websocket.send_json({"type": "status", "message": str(msg).strip()})

            try:
                # Initialize correct LLM based on backend configuration
                if backend == "groq":
                    try:
                        from unreal_mcp.agents.groq_agent import create_llm
                    except ImportError:
                        from agents.groq_agent import create_llm
                elif backend == "ollama":
                    try:
                        from unreal_mcp.agents.ollama_agent import create_llm
                    except ImportError:
                        from agents.ollama_agent import create_llm
                elif backend == "gemini":
                    try:
                        from unreal_mcp.agents.gemini_agent import create_llm
                    except ImportError:
                        from agents.gemini_agent import create_llm
                else:
                    try:
                        from unreal_mcp.agents.groq_agent import create_llm
                    except ImportError:
                        from agents.groq_agent import create_llm

                llm = create_llm()

                # 3. Process the prompt through the selected mode's pipeline
                if mode == "two_phase":
                    try:
                        try:
                            from unreal_mcp.agents.pipeline import two_phase_run
                        except ImportError:
                            from agents.pipeline import two_phase_run
                        await ws_callback("Starting C++ Generator (Two-Phase Pipeline)...")
                        result = await two_phase_run(llm, user_prompt, write_files=True, validate_compile=True)
                    except ImportError:
                        await ws_callback("two_phase pipeline not available. Falling back to classic.")
                        try:
                            from unreal_mcp.agents.base import run_agent
                        except ImportError:
                            from agents.base import run_agent
                        await run_agent(llm, model_label=backend, prompt=user_prompt, interactive=False)
                        result = "Agent execution complete. Check server terminal for details."
                elif mode == "classic":
                    try:
                        from unreal_mcp.agents.base import run_agent
                    except ImportError:
                        from agents.base import run_agent
                    await ws_callback("Starting Classic Agent Tool Caller...")
                    await run_agent(llm, model_label=backend, prompt=user_prompt, interactive=False)
                    result = "Classic Agent execution complete. Check server terminal for details."
                elif mode == "orchestrate":
                    await ws_callback("Orchestrator not natively supported via WS yet. Re-routing to build...")
                    try:
                        try:
                            from unreal_mcp.agents.builder import build_in_ue
                        except ImportError:
                            from agents.builder import build_in_ue
                        result = await build_in_ue(llm, user_prompt, status_callback=ws_callback)
                    except ImportError:
                        try:
                            from unreal_mcp.agents.base import run_agent
                        except ImportError:
                            from agents.base import run_agent
                        await run_agent(llm, model_label=backend, prompt=user_prompt, interactive=False, builder=True)
                        result = "Builder Agent execution complete. Check server terminal for details."
                else:
                    # Default: Live Builder
                    try:
                        try:
                            from unreal_mcp.agents.builder import build_in_ue
                        except ImportError:
                            from agents.builder import build_in_ue
                        result = await build_in_ue(llm, user_prompt, status_callback=ws_callback)
                    except ImportError:
                        try:
                            from unreal_mcp.agents.base import run_agent
                        except ImportError:
                            from agents.base import run_agent
                        await ws_callback("Starting Builder Agent...")
                        await run_agent(llm, model_label=backend, prompt=user_prompt, interactive=False, builder=True)
                        result = "Builder Agent execution complete. Check server terminal for details."

                # 4. Send success back to client
                await websocket.send_json({"type": "success", "message": result})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        print("Client disconnected")
