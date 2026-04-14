# Unreal-MCP

![Unreal-MCP](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13+-blue)
![FastMCP](https://img.shields.io/badge/FastMCP-Supported-orange)

Unreal-MCP is a powerful backend architecture that seamlessly integrates Large Language Models (LLMs) with Unreal Engine via the Model Context Protocol (MCP). Built on FastMCP and LangChain, it enables LLMs to observe and manipulate the Unreal Engine environment by executing commands such as querying actors, transforming coordinates, and spawning entities dynamically.

## 🎯 Purpose and Vision
The goal of Unreal-MCP is to act as a bridge between high-level autonomous agents and low-level game engine APIs. By exposing Unreal Engine's functionality locally as a standard FastMCP server, AI agents can intuitively interact with the game world, effectively making the engine "scriptable" directly through natural language. 

The project natively supports a multimodal array of LLM providers to ensure flexibility. Whether you want to leverage top-tier proprietary models or run purely on local hardware, Unreal-MCP is designed to be model-agnostic.

## 🏗 Architecture & Codebase Structure
The project follows a decoupled client-server architecture:

- **Server (`server.py`)**: Runs the `FastMCP` protocol over Server-Sent Events (SSE). It exposes various Unreal Engine functions as standard MCP tools.
- **Client Agents (`agent.py`)**: A multi-model CLI launcher acting as the MCP client. It connects an LLM of choice to the FastMCP server, parses natural language, and determines which MCP tool to trigger. 
- **Tools package (`unreal_mcp/tools/`)**:
  - `actors.py` - For listing and inspecting actors in the level.
  - `spawning.py` - For dynamically spawning new actors.
  - `transform.py` - For manipulating transforming coordinates (location, rotation, scale) of actors.
- **Agent Handlers (`agents/`)**: Contains provider-specific LangChain implementations (`groq_agent.py`, `ollama_agent.py`, `gemini_agent.py`).

## 🛠 Features & Supported Backends
The system uses LangChain adapters to interact dynamically with the MCP server. The currently supported backends are:
- **Groq Cloud** (`langchain_groq`): Llama 3.3 70B (Fast, remote execution).
- **Google Gemini** (`langchain_google_genai`): Gemini 2.5 Pro (Powerful, multimodal context).
- **Ollama** (`langchain_ollama`): Runs models locally 70B+ (Private, GPU-dependent).

*Note: Environment variables for each backend (e.g., `GROQ_API_KEY`, `GEMINI_API_KEY`) need to be provided in the `.env` file since different model APIs are fundamentally needed.*

## 🚀 Quick Start / Usage

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Make sure you provide identical `.env` mappings per the `.env.example`.*

2. **Start the FastMCP Server**:
   Before agents can interact with Unreal Engine, run the server process:
   ```bash
   python server.py
   ```

3. **Launch the Agent**:
   Run the CLI launcher targeting your backend of choice in a separate terminal:
   ```bash
   # Quick Test
   python agent.py gemini --test
   
   # Chat/Interactive Mode
   python agent.py groq --interactive
   
   # Single Custom Prompt Shell 
   python agent.py groq --prompt "spawn a cube at 0 0 200"
   ```

## ⚖️ Pros and Cons (Honest Assessment)

**Pros**:
- **Agnostic & Future-Proof**: Designed with LangChain and fastmcp, meaning it will easily support future models as long as they can consume MCP tools.
- **Highly Modular**: Adding new tools (e.g. materials, lighting control) is as simple as adding Python modules under `unreal_mcp/tools/` and decorating them.
- **Fast Development Cycle**: Decoupling the Unreal Engine client architecture into a local SSE server makes it easier to test agent reasoning pipelines independently.

**Cons**:
- **Dependency Footprint**: Currently pins `httpx` and requires the `legacy-cgi` package for Python 3.13+ compatibility because of upstream `httpcore` conflicts.
- **Complexity Overhead**: Requires running a separate Node/Python bridging server layer constantly while Unreal is open.
- **Context Limits**: Heavily populated UE scenes returned by `actors.py` could potentially blow out the LLM's context window. Care must be taken to implement pagination or filtered search.
