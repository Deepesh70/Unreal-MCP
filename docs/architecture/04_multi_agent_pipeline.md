# 🤖 Agent Backends — Model Comparison

> Three LLM backends, all using 30B+ parameter models.

---

## Quick Start

```bash
# 1. Start the MCP server
python server.py

# 2. Run an agent (pick one)
python agent.py groq       # Cloud — fastest
python agent.py ollama     # Local — private, needs GPU
python agent.py gemini     # Google — most capable
```

---

## Backend Comparison

| Backend | Model | Params | Speed | Cost | Privacy |
|---------|-------|--------|-------|------|---------|
| **Groq** | Llama 3.3 70B | 70B | ⚡⚡⚡ Fastest | Free tier | Cloud |
| **Ollama** | llama3.3:70b | 70B | ⚡ Depends on GPU | Free | 🔒 Fully local |
| **Gemini** | gemini-2.5-pro | 100B+ (est.) | ⚡⚡ Fast | Subscription | Cloud |

---

## Groq (Cloud)

- **Model**: `llama-3.3-70b-versatile` (70B params)
- **API Key**: `GROQ_API_KEY` in `.env`
- **Get key**: https://console.groq.com
- **Best for**: Fast iteration, free prototyping

```bash
python agent.py groq
# or directly:
python -m agents.groq_agent
```

---

## Ollama (Local)

- **Default model**: `llama3.3:70b` (70B params)
- **No API key needed** — runs on your machine
- **Requires**: Ollama installed + model pulled + strong GPU (24GB+ VRAM for 70B)

```bash
# Setup
# 1. Install Ollama: https://ollama.com
# 2. Pull a model:
ollama pull llama3.3:70b

# Run
python agent.py ollama
# or with a different model:
python -m agents.ollama_agent --model qwen2.5:72b
# list all recommended models:
python -m agents.ollama_agent --list-models
```

### Recommended Models

| Model | Params | Notes |
|-------|--------|-------|
| `llama3.3:70b` | 70B | Best balance (default) |
| `qwen2.5:72b` | 72B | Strong tool-calling |
| `deepseek-r1:70b` | 70B | Reasoning focused |
| `command-r-plus:104b` | 104B | Very large, needs 48GB+ VRAM |
| `llama3.1:70b` | 70B | Stable & proven |

---

## Gemini (Google Cloud)

- **Default model**: `gemini-2.5-pro` (100B+ estimated)
- **API Key**: `GOOGLE_API_KEY` in `.env`
- **Get key**: https://aistudio.google.com/apikey
- **Best for**: Most capable reasoning, native tool-calling

```bash
python agent.py gemini
# or with a specific model:
python -m agents.gemini_agent --model gemini-2.5-flash
# list all models:
python -m agents.gemini_agent --list-models
```

> **Note on Gemini 3/3.1**: When Google releases Gemini 3.0 or 3.1,
> just update the model name in `agents/gemini_agent.py` — the code
> is already set up to handle any model string.

---

## Architecture

```
agent.py                  ← CLI launcher (picks backend)
agents/
├── __init__.py
├── base.py               ← Shared: MCP connection + agent loop
├── groq_agent.py         ← Groq: create_llm() → ChatGroq
├── ollama_agent.py       ← Ollama: create_llm() → ChatOllama
└── gemini_agent.py       ← Gemini: create_llm() → ChatGoogleGenerativeAI
```

All three backends share `base.py` — the MCP connection, tool loading,
and agent execution are identical. Only the LLM instance differs.
