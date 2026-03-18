from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import websockets
from agents.builder import build_in_ue
from agents.groq_agent import create_llm # or your preferred LLM
from unreal_mcp.config.settings import UE_WS_URL

app = FastAPI()
llm = create_llm()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Wait for prompt from Next.js
            data = await websocket.receive_text()
            
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
            async def ws_callback(msg: str):
                await websocket.send_json({"type": "status", "message": msg.strip()})
            
            try:
                # 3. Process the prompt through your existing agent pipeline
                result = await build_in_ue(llm, data, status_callback=ws_callback)
                
                # 4. Send success back to Next.js
                await websocket.send_json({"type": "success", "message": result})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        print("Client disconnected")
