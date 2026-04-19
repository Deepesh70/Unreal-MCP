# 🏙️ Unreal-MCP Procedural City Builder — Overview

> **One sentence:** You type "build a city with wooden houses on the left and glass skyscrapers on the right," and Unreal Engine builds it — automatically, in real-time, with zero manual placement.

---

## What Is This Project?

This project is an **automated 3D environment generator**. It connects the creative intelligence of Large Language Models (LLMs like ChatGPT, Gemini, or Llama) to the rendering power of Unreal Engine 5 — so that natural language descriptions are translated into fully constructed 3D worlds.

### The Problem It Solves

Building 3D environments in Unreal Engine is painfully manual. A level designer has to:
1. Open the editor
2. Drag a wall mesh from the content browser
3. Position it precisely at X: 500, Y: 0, Z: 150
4. Rotate it 90 degrees
5. Scale it to fit
6. Repeat this hundreds or thousands of times

**This project automates the entire process.** Instead of dragging meshes by hand, you describe what you want in plain English, and an AI generates the exact coordinates, dimensions, and styles — then the engine builds it instantly.

---

## How Does It Work? (The 30-Second Version)

```
You: "Build a 5-story office building at the park entrance"
         │
         ▼
   ┌─────────────┐
   │  LLM Brain  │  ← Groq / Gemini / Ollama
   │  (The AI)   │     Understands your intent
   └──────┬──────┘     Generates structured JSON
          │
          ▼
   ┌─────────────┐
   │   Python     │  ← The MCP Server
   │  Gateway     │     Validates the JSON
   └──────┬──────┘     Sends ONE command
          │
          ▼
   ┌─────────────┐
   │  Unreal C++ │  ← The Builder
   │  Engine     │     Does the math
   └──────┬──────┘     Spawns HISM instances
          │
          ▼
   🏢 A 5-story office appears in your 3D world
```

---

## Who Is This For?

- **Game Developers** who want to rapidly prototype environments
- **Architects** exploring spatial layouts via natural language
- **AI Researchers** building bridges between language models and 3D engines
- **Hobbyists** who just think it's cool to say "build a castle" and watch it happen

---

## What Makes This Different From Other Procedural Generators?

Most procedural generators use hard-coded algorithms (e.g., "randomly place buildings in a grid"). This project uses **LLM intelligence** — meaning:

1. **It understands context:** "Wooden houses on the left, glass offices on the right" produces semantically different structures on each side.
2. **It remembers what it built:** You can say "change the wooden house to a skyscraper" and it modifies just that building.
3. **It avoids obstacles:** If there's a mountain at the target location, the engine automatically moves the building to clear ground nearby.
4. **It's model-agnostic:** Swap between Groq (cloud), Gemini (Google), or Ollama (local) with a single CLI flag. Users can plug in their own API keys to use frontier models.

---

## The Technology Stack

| Component | Technology | Role |
|-----------|-----------|------|
| AI Brain | Groq / Gemini / Ollama LLMs | Understands natural language, generates structured building blueprints |
| Communication | Model Context Protocol (MCP) | Standardized protocol for AI-to-tool communication |
| API Gateway | Python + FastMCP + WebSocket | Validates AI output, routes commands to Unreal |
| 3D Engine | Unreal Engine 5.6.1 (C++) | Renders buildings using HISM for maximum performance |
| Transport | WebSocket (Remote Control API) | Real-time bidirectional communication between Python and Unreal |

---

## Key Terminology

| Term | What It Means |
|------|--------------|
| **MCP** | Model Context Protocol — a standard for connecting AI models to external tools |
| **HISM** | Hierarchical Instanced Static Mesh — Unreal's way of rendering thousands of identical objects with a single draw call |
| **Ledger** | The C++ `TMap` that tracks every building by its ID, storing which HISM instances belong to it |
| **Intent** | The action type in the JSON payload (Spawn, BatchSpawn, Modify, Destroy, ClearAll, ScanArea) |
| **Style** | A semantic tag like `"House_Wood_Small"` that the LLM uses to describe a building type. Unreal resolves this to actual meshes/materials via a DataTable |
| **Auto-Nudge** | When a building can't be placed at the requested location (obstacle), C++ automatically moves it to the nearest clear spot |
| **Swap-and-Pop** | Unreal's memory optimization: when deleting an HISM instance, the last instance is moved into the vacated slot instead of shifting all elements |

---

## Project Status

The project is currently in **The Great Refactor** — transitioning from a prototype architecture (Python does all the work) to a production architecture (C++ does the heavy lifting). See [01_the_journey.md](./01_the_journey.md) for the full story.

---

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd Unreal-MCP

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Copy .env.example to .env and add your API keys
cp .env.example .env

# 4. Start the MCP server
python server.py

# 5. In another terminal, run the builder agent
python agent.py groq -b -i

# 6. Type your building commands!
🏗️ Builder > Build a 3-story house at the origin
```

> **Prerequisites:** Unreal Engine must be running with the **Remote Control API** plugin enabled, and the `AProceduralCityManager` actor must be placed in your level.
