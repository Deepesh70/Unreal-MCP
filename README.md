# Unreal MCP Agent

**Unreal Engine + Large Language Models (LLMs) + RAG**

This project connects Unreal Engine to LLMs (Groq, Ollama, Gemini) to enable:
- 🏗️ **Live Building**: Generate and spawn actors in real-time
- 🧠 **RAG**: Retrieve architectural blueprints from a vector database
- 💬 **Chat**: Interactive conversation with the engine
- 💻 **Code Gen**: Generate C++ classes for new actors

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
python server.py
```

Press `Enter` to accept the default port (8000).

### 2. Start the Agent

**Option A: Interactive Builder (Recommended)**
```bash
python agent.py groq --build -i
```

**Option B: Quick Test**
```bash
python agent.py groq --test
```

**Option C: C++ Code Generator**
```bash
python agent.py groq --two-phase
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Unreal Engine 5.1+
- Unreal MCP Plugin (installed in your project)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install ChromaDB (for RAG)

```bash
pip install chromadb
```

## 📂 Project Structure

```
unreal-mcp/
├── server.py              # MCP Server
├── agent.py               # Main agent launcher
├── agents/
│   ├── base.py            # Classic tool-calling agent
│   ├── builder.py         # Live builder (Phase 1-3)
│   ├── builder_prompts.py # Prompt templates
│   ├── pipeline.py        # Two-phase C++ generator
│   ├── groq_agent.py      # Groq LLM integration
│   ├── ollama_agent.py    # Ollama LLM integration
│   ├── gemini_agent.py    # Gemini LLM integration
│   └── rag/               # RAG components
│       ├── store.py       # Vector database operations
│       └── prompts.py     # RAG prompts
├── blueprints/            # Architectural blueprints
├── data/                  # Generated data
└── docs/                  # Documentation
```

## 🏗️ Live Builder Workflow

```
User Prompt → [Phase 1: Refine] → [Phase 0.5: RAG] → [Phase 2: Plan] → [Phase 3: Build]
```

### Phase 0.5: RAG Retrieval

1. User asks for a specific building type (e.g., "Victorian house")
2. RAG system searches `blueprints/` for similar documents
3. Relevant blueprints are injected into the LLM context
4. LLM uses blueprints to generate accurate, detailed plans

### Phase 1: Refine Prompt

- Converts vague requests into precise specifications
- Extracts key details: shape, size, position, rotation
- Resolves ambiguities

### Phase 2: Generate Build Plan

- Creates JSON with `steps` array
- Each step has: `action`, `label`, `params`
- Supports `spawn`, `scale`, `rotate` actions

### Phase 3: Execute in UE

- Connects to Unreal Engine via WebSocket
- Spawns actors using `spawn_actor_internal`
- Applies transformations
- Provides real-time feedback

## 💬 Interactive Mode

```bash
python agent.py groq --build -i
```

### Conversation Flow

```
User: Build a small hut

[Phase 1] Planning build...
  Input: "Build a small hut"
  [+] Found RAG Blueprint match! Injecting into context.
  Name: Hut
  Steps: 4

[Phase 3] BUILDING IN UNREAL ENGINE...
  [1/4] Spawned cube -> step_0
  [2/4] Spawned cube -> step_1
  [3/4] Spawned cube -> step_2
  [4/4] Spawned cube -> step_3

============================================================
  BUILD COMPLETE!
  Executed 4/4 steps (0 errors)
  Look at your Unreal viewport!
============================================================

User: Make it bigger

[Phase 1] Planning build...
  Input: "Make it bigger"
  [+] Found RAG Blueprint match! Injecting into context.
  Name: Hut
  Steps: 1

[Phase 3] BUILDING IN UNREAL ENGINE...
  [1/1] Scaled step_0 -> (2.0, 2.0, 2.0)

============================================================
  BUILD COMPLETE!
  Executed 1/1 steps (0 errors)
  Look at your Unreal viewport!
============================================================
```

## 💻 C++ Code Generation

```bash
python agent.py groq --two-phase
```

### Workflow

1. **Refine**: User prompt → detailed spec
2. **Generate**: LLM creates C++ header + source files
3. **Output**: Files saved to `data/generated/`

### Example Output

```cpp
// data/generated/MyActor.h
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MyActor.generated.h"

UCLASS()
class PROJECT_API AMyActor : public AActor
{
    GENERATED_BODY()

public:
    AMyActor();

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;
};

// data/generated/MyActor.cpp
#include "MyActor.h"

AMyActor::AMyActor()
{
    PrimaryActorTick.bCanEverTick = true;
}

void AMyActor::BeginPlay()
{
    Super::BeginPlay();
}

void AMyActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}
```

## ⚙️ Configuration

### Environment Variables

```bash
export GROQ_API_KEY="your-groq-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Model Selection

```bash
# Groq (default)
python agent.py groq ...

# Ollama
python agent.py ollama ...

# Gemini
python agent.py gemini ...
```

## 📂 Blueprint Management

### Add Blueprints

1. Create Markdown files in `blueprints/`:

```markdown
# blueprints/victorian_house.md

## Architecture: Victorian House

**Style**: Victorian
**Rooms**: 4 bedrooms, 2 bathrooms, kitchen, living room
**Materials**: Brick exterior, wood floors, plaster walls
**Key Features**:
- Turret on the west side
- Wrap-around porch
- Decorative trim
- Steeply pitched roof

## Dimensions

- **Footprint**: 15m x 20m
- **Height**: 3 stories
- **Ceiling height**: 3m

## Room Layout

**Ground Floor**:
- Foyer (3m x 4m)
- Living room (5m x 6m)
- Dining room (4m x 5m)
- Kitchen (4m x 5m)
- Stairs (2m x 3m)

**Second Floor**:
- Master bedroom (5m x 6m)
- Bedroom 2 (4m x 5m)
- Bedroom 3 (4m x 5m)
- Bathroom 1 (3m x 4m)
- Hallway (2m x 6m)

**Third Floor**:
- Bedroom 4 (5m x 6m)
- Bathroom 2 (3m x 4m)
-
