from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import websockets
from agents.builder import build_in_ue
from agents.groq_agent import create_llm # or your preferred LLM
from unreal_mcp.config.settings import UE_WS_URL

import json

app = FastAPI()
# We remove the global llm initialization to allow dynamic backend selection per-request

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Wait for prompt from Next.js
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
                    pass # Connection successful
            except Exception as e:
                error_msg = f"Unreal Engine connection failed ({str(e)}). Please ensure Unreal Engine is running and the Remote Control Web Interface is started."
                await websocket.send_json({"type": "error", "message": error_msg})
                # We skip building and wait for the next prompt
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
                    from agents.groq_agent import create_llm
                elif backend == "ollama":
                    from agents.ollama_agent import create_llm
                elif backend == "gemini":
                    from agents.gemini_agent import create_llm
                else:
                    from agents.groq_agent import create_llm
                llm = create_llm()

                # 3. Process the prompt through the selected mode's pipeline
                if mode == "two_phase":
                    from agents.pipeline import two_phase_run
                    await ws_callback("Starting C++ Generator (Two-Phase Pipeline)...")
                    result = await two_phase_run(llm, user_prompt, write_files=True, validate_compile=True)
                elif mode == "classic":
                    from agents.base import run_agent
                    await ws_callback("Starting Classic Agent Tool Caller...")
                    await run_agent(llm, model_label=backend, prompt=user_prompt, interactive=False)
                    result = "Classic Agent execution complete. Check server terminal for details."
                elif mode == "orchestrate":
                    from agents.orchestrator import orchestrate_in_ue
                    await ws_callback("Starting Orchestrator (Hybrid Pipeline)...")
                    result = await orchestrate_in_ue(llm, user_prompt, status_callback=ws_callback)
                else:
                    # Default: Live Builder
                    from agents.builder import build_in_ue
                    result = await build_in_ue(llm, user_prompt, status_callback=ws_callback)
                
                # 4. Send success back to Next.js
                await websocket.send_json({"type": "success", "message": result})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        print("Client disconnected")
