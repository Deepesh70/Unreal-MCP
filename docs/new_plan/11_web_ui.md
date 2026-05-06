# 🌐 The Web UI Connection

> How the Next.js frontend connects to the Unreal MCP via FastAPI WebSockets.

---

## 1. Overview

While the Command Line Interface (CLI) via `agent.py` is great for debugging and quick tests, the system also supports a full **Web UI integration**. This allows a Next.js (or any frontend) application to stream commands to the backend, monitor real-time logs, and receive structural updates visually.

The connection is handled by a new component: **`api_server.py`**.

---

## 2. The Architecture

```
┌─────────────────┐       WebSocket        ┌──────────────────┐
│   Next.js UI    │  ◄──────────────────►  │  api_server.py   │ (FastAPI)
│ (Client Web App)│  (JSON & Text Msgs)    │  Port: 8000      │
└─────────────────┘                        └────────┬─────────┘
                                                    │
                                           ┌────────▼─────────┐
                                           │   Agent Logic    │ (groq/gemini/ollama)
                                           └────────┬─────────┘
                                                    │
                                           ┌────────▼─────────┐
                                           │  Unreal Engine   │ (C++ Builder)
                                           │ Remote Control   │
                                           └──────────────────┘
```

The `api_server.py` acts as a proxy between the frontend client and the AI/Unreal backend.

---

## 3. Communication Protocol

The Web UI communicates with FastAPI over a WebSocket connection at the endpoint `/ws/chat`.

### Client -> Server (Request)
The Next.js client sends a JSON payload containing the prompt and configuration:

```json
{
  "prompt": "Build a 3-story wooden house at the origin",
  "config": {
    "backend": "groq",
    "mode": "build"
  }
}
```

- **`backend`**: The LLM provider (`groq`, `gemini`, `ollama`).
- **`mode`**: The execution pipeline (`build` [default], `two_phase`, `classic`, `orchestrate`).

### Server -> Client (Real-time Logs)
As the agent runs, the server streams live status updates back to the UI:

```json
{
  "type": "status",
  "message": "Starting Builder Agent..."
}
```

### Server -> Client (Completion/Error)
Once the task finishes (or fails), the server sends a final payload:

```json
{
  "type": "success",
  "message": "Builder Agent execution complete. Check server terminal for details."
}
```
Or in case of failure:
```json
{
  "type": "error",
  "message": "Unreal Engine connection failed. Please ensure Unreal Engine is running..."
}
```

---

## 4. Pipeline Execution Modes

The WebSocket server supports routing the request through different agent pipelines:

| Mode | What It Does |
|------|-------------|
| **`build` (Default)** | Routes to the live `build_in_ue()` function. Fast, one-shot procedural generation. |
| **`two_phase`** | Uses the two-phase pipeline (generate C++ files, validate compilation, then execute). |
| **`classic`** | Uses the standard MCP tool caller loop. |
| **`orchestrate`** | Future support for complex token routing and multi-agent coordination. |

---

## 5. Running the Web API

To start the Web UI API server, run the following command instead of the standard CLI agent:

```bash
uvicorn api_server:app --port 8000
```

*Note: Make sure Unreal Engine is running with the Remote Control API plugin active before sending requests from the frontend, as `api_server.py` performs a pre-flight check to verify the engine connection.*
