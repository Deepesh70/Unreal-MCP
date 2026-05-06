# Full Project Overview: Unreal-MCP Procedural City Builder

> An exhaustive, highly detailed technical compilation of the Unreal-MCP architecture, systems, internal mechanisms, code-level algorithms, and execution roadmap. Designed as the ultimate foundational document for academic and technical research.

---

## Table of Contents
1. [Abstract & Introduction](#1-abstract--introduction)
2. [Project Evolution: From Blueprint to City Builder](#2-project-evolution-from-blueprint-to-city-builder)
3. [Architecture: The Three-Body System](#3-architecture-the-three-body-system)
4. [The JSON Contract & Schema Details](#4-the-json-contract--schema-details)
5. [The Python Gateway: Validation, Repair, & Transport](#5-the-python-gateway-validation-repair--transport)
6. [The C++ Engine: AProceduralCityManager](#6-the-c-engine-aproceduralcitymanager)
7. [HISM Deep Dive: The Swap-and-Pop Algorithm](#7-hism-deep-dive-the-swap-and-pop-algorithm)
8. [Spatial Awareness: Dual-Check & Auto-Nudge](#8-spatial-awareness-dual-check--auto-nudge)
9. [Token-Aware Complexity Routing (The Orchestrator)](#9-token-aware-complexity-routing-the-orchestrator)
10. [Web UI Integration & WebSocket API](#10-web-ui-integration--websocket-api)
11. [Execution Roadmap & Risk Assessment](#11-execution-roadmap--risk-assessment)

---

## 1. Abstract & Introduction

The **Unreal-MCP Procedural City Builder** is a cutting-edge automated 3D environment generator that bridges the creative semantic intelligence of Large Language Models (LLMs) with the high-performance rendering capabilities of Unreal Engine 5. It translates natural language descriptions (e.g., "Build a medieval village with wooden houses on the left and stone towers on the right") into fully constructed, physical, collision-aware 3D worlds in real-time, operating with zero manual asset placement.

### The Core Problem
Level design in Unreal Engine is a highly manual, labor-intensive process requiring the meticulous positioning, scaling, and rotating of thousands of individual static meshes. Traditional procedural generators rely on hard-coded algorithms (e.g., Perlin noise or rigid grid structures) which completely lack semantic understanding and contextual intent.

### The Innovation
By leveraging the **Model Context Protocol (MCP)** and robust WebSockets, this system uses an LLM (such as Llama 3.3 70B via Groq, Gemini 2.5 Pro, or Ollama) as its semantic "Brain". The AI:
- Understands complex, relative layout requests.
- Maintains a memory of generated structures, allowing for targeted iterations (e.g., "Change the wooden house to a skyscraper").
- Relies on the C++ engine to handle exact geometric constraints and physical obstacles through autonomous feedback loops.

---

## 2. Project Evolution: From Blueprint to City Builder

The project underwent a fundamental paradigm shift referred to as **"The Great Refactor"**.

### The Puppet Master (Legacy Architecture)
Initially, Python acted as the "Puppet Master". Python calculated all spatial math (floor slabs, wall coordinates, roof placements) and sent individual WebSocket commands to Unreal Engine for every single piece of a building. 
- **The Process:** To build a 5-story house, Python calculated 26 individual transforms and executed 26 distinct WebSocket RPC calls, spawning 26 independent `StaticMeshActors`.
- **The Bottleneck:** Generating a city block of 1,000 buildings required 26,000 RPC calls over the network. Unreal Engine, tasked with rendering 26,000 independent actors, suffered catastrophic draw call bottlenecks, dropping frame rates to unplayable levels.

### The Delegator (Modern Architecture)
The architecture shifted to delegate computational heavy lifting to Unreal C++. Python was minimized to a "Thin Gateway" responsible only for extracting and validating JSON. Unreal C++ became a "Smart Builder", receiving a single JSON payload per building, computing the geometry locally, and instantiating components using **Hierarchical Instanced Static Meshes (HISM)**.
- **The Result:** 26 RPC calls per building were reduced to 1 RPC call per building. Most importantly, draw calls were reduced from ~26,000 to ~3 (one for all walls, one for all floors, one for all roofs), easily maintaining 60 FPS under massive generation loads.

---

## 3. Architecture: The Three-Body System

The modern architecture strictly enforces a separation of concerns across three distinct layers to prevent cascading failures.

### I. The Dreamer (LLM)
- **Role:** Creative intent, style decisions, and relative layout planning.
- **Boundaries:** The LLM never knows exact Unreal asset paths (e.g., `/Game/Meshes/Wall`). It never manages engine memory indices, and it does not blindly retry blocked coordinates. It outputs standardized JSON blueprints.

### II. The Gateway (Python API)
- **Role:** Strip markdown fences, dynamically repair truncated JSON caused by LLM token limits, validate schema parameters, and act as the transport layer via WebSocket and MCP.
- **Boundaries:** Never calculates spatial math. Never spawns actors. Never tracks world state.

### III. The Builder (Unreal C++)
- **Role:** Deserializes JSON, performs spatial math, handles HISM instantiation, physical collision detection, auto-nudging, and ledger state management. It is the sole authority on geometric precision.
- **Boundaries:** Never talks directly to the LLM. Never validates JSON schema. Never writes local files.

### Detailed Data Flow
```text
1. [User Prompt] -> "Build a street with houses and an office"
2. [LLM Brain] -> Processes intent and generates structured JSON Blueprint.
3. [Python Gateway] -> Strips markdown -> Repairs JSON -> Validates Schema -> Discovers CityManager.
4. [WebSocket Transport] -> Invokes ProcessBlueprint() via Unreal Remote Control API.
5. [Unreal C++] -> Checks Collision (Dual-Check) -> Computes Math Loop -> Spawns HISM Instances -> Updates Ledger.
6. [Unreal C++] -> Serializes Receipt -> Returns success/fail state back to Python.
7. [Python Gateway] -> Displays receipt/result to the User.
```

### Deployment Modes
Because the transport layer uses the standard Remote Control API WebSocket, the architecture natively supports two deployment topologies:
1. **Local Mode:** Python and Unreal run on the same machine over `ws://127.0.0.1:30020`.
2. **Cloud Mode:** Python runs on a remote cloud server routing through ngrok/localtunnel (`ws://ngrok-url:30020`) to a local Unreal Engine client, requiring zero code changes.

---

## 4. The JSON Contract & Schema Details

Communication uses a highly structured JSON contract. There is one primary `Intent` per payload (except for arrays within `BatchSpawn`).

### The 6 Core Intents

1. **`Spawn`**: Creates a single building at `RequestedLoc`.
2. **`BatchSpawn`**: Processes an array of `Blueprints`. Handled sequentially in C++ to ensure intra-batch spatial awareness (Building 2 knows about Building 1 and avoids overlapping it).
3. **`Modify`**: Targets an existing `TargetID`, destroys it using the Swap-and-Pop algorithm, and rebuilds it at the identical original location with new parameters.
4. **`Destroy`**: Target removal of a building and all its associated HISM components.
5. **`ClearAll`**: Empties the `HISMPool` and clears the Ledger memory entirely.
6. **`ScanArea`**: Read-only query returning `GroundZ`, `ExternalCollisions`, and `InternalCollisions` within a requested radius.

### Detailed Schema Structure (`Spawn` Example)
```json
{
  "Intent": "Spawn",
  "ID": "ProcBldg_01",
  "Style": "House_Wood_Small",
  "EnvironmentCheck": {
    "RequiresScan": true,
    "Radius": 500
  },
  "RequestedLoc": [0, 0, 0],
  "Parameters": {
    "Floors": 3,
    "FloorHeight": 300,
    "BuildingWidth": 1000,
    "BuildingDepth": 1000,
    "WallThickness": 20,
    "RoofType": "flat"
  }
}
```

### Parameter Defaults & Fallbacks
If the LLM omits optional parameters, C++ utilizes sensible defaults:
- `Floors`: 3 (A typical house)
- `FloorHeight`: 300 UU (3 meters)
- `BuildingWidth` / `Depth`: 1000 UU (10 meters)
- `WallThickness`: 20 UU (20 centimeters)
- `RoofType`: `"flat"`
- `Style`: `"Default"`

### Semantic Tagging (`AssetDictionary`)
The LLM specifies a semantic `Style` (e.g., `"Cyberpunk_Neon"`, `"Industrial_Steel"`). Unreal C++ queries a user-defined `UDataTable` (`FAssetDictionaryRow`) to map this string to actual `TSoftObjectPtr<UStaticMesh>` and `TSoftObjectPtr<UMaterialInterface>`. If missing, C++ safely falls back to Engine basic shapes (`/Engine/BasicShapes/Cube` and `Cone`) avoiding any critical crash scenarios.

### Legacy Auto-Migration
The Python gateway includes a fail-safe that catches old JSON structures (`{"Action": "SpawnActor"}`) generated by cached sessions or older prompts, automatically translating them into the new Intent-based syntax, ensuring uninterrupted legacy compatibility.

---

## 5. The Python Gateway: Validation, Repair, & Transport

Because LLMs are inherently probabilistic, their structured output is prone to structural errors—especially when hitting hard token limits. The Python layer serves as an impenetrable firewall.

### 1. Dynamic JSON Repair (`_repair_truncated_json`)
When a massive generation exceeds the LLM's context limit (e.g., stopping abruptly at 4096 tokens), the JSON is truncated. Python employs a sophisticated algorithm:
- It tracks string literals. If the output ends mid-string, it appends a closing `"`.
- It maintains a stack of open braces `{` and brackets `[`.
- It iterates the stack in reverse order and appends the missing closing characters (e.g., `]}`).
*Result:* Malformed outputs are salvaged dynamically, preserving the vast majority of the generated data instead of failing completely.

### 2. Strict Schema Validation (`_validate_intent_schema`)
Before any WebSocket transmission, Python explicitly verifies:
- Intents are valid strings.
- Required fields are present (e.g., `Spawn` mandates `ID` and `RequestedLoc`).
- Type limits are respected (e.g., `Parameters.Floors` must be an integer; `RequestedLoc` an array of exactly 3 floats).
If validation fails, the command is blocked and the error is fed back to the LLM for correction.

### 3. CityManager Pre-Flight Discovery
Python executes an asynchronous pre-flight query to Unreal's `EditorActorSubsystem` via `GetAllLevelActors`. It iterates the returned actors, identifies the path containing `"ProceduralCityManager"`, caches the object path, and guarantees that RPC calls are strictly targeted to the actively instanced manager.

---

## 6. The C++ Engine: AProceduralCityManager

The engine-side brain is the `AProceduralCityManager`, a standard `AActor` placed in the persistent level.

### Core Memory Structures (`ProceduralBuildingTypes.h`)
1. **`FHISMInstanceRef`**: Tracks the exact memory array location of a generated geometric piece.
   ```cpp
   USTRUCT() struct FHISMInstanceRef {
       UPROPERTY() UHierarchicalInstancedStaticMeshComponent* Component;
       UPROPERTY() int32 InstanceIndex;
   };
   ```
2. **`FProceduralBuilding`**: The core "Ledger" tracking object. Holds `BuildingID`, `OriginalJson`, actual `Location`, and a `TArray<FHISMInstanceRef> Instances`.
3. **`FAssetDictionaryRow`**: The structure for the `UDataTable` linking `StyleKey` to the respective Mesh and Material pointers.

### The Geometric Math Loop
To convert a JSON blueprint into physical 3D geometry, C++ calculates relative scale factors against Unreal's standard 100x100x100 UU (Unreal Unit) base cube:
```text
Floor slab scale:
  SX = BuildingWidth / 100.0f
  SY = BuildingDepth / 100.0f
  SZ = 0.2f  (thin slab)

Front/Back wall scale:
  SX = BuildingWidth / 100.0f
  SY = WallThickness / 100.0f
  SZ = FloorHeight / 100.0f
```
The logic iterates sequentially:
```cpp
for (int floor = 0; floor < NumFloors; ++floor) {
    float floor_z = base_z + (floor * FloorHeight);
    float wall_z = floor_z + (FloorHeight / 2.0f);
    
    // Floor Slab
    HISM->AddInstance(FTransform(Rot, FVector(base_x, base_y, floor_z), FVector(slab_sx, slab_sy, 0.2f)), true);
    // Walls (Front, Back, Left, Right calculated similarly and pushed)
}
// Roof logic (flat slab or pointed cone)
```
> **Critical Factor:** All `AddInstance` calls utilize `bWorldSpace = true`. Standard HISM defaults to component-local space; bypassing this flag would incorrectly anchor all city geometry to the origin of the CityManager actor.

### The Lazy HISMPool Instantiation
HISM components are dynamically created via the `GetOrCreateHISM(UStaticMesh* Mesh, UMaterialInterface* Material)` function.
- Components are stored in `TMap<FHISMPoolKey, UHierarchicalInstancedStaticMeshComponent*>`.
- `FHISMPoolKey` is a composite of `{Mesh, Material}` ensuring distinct components per visual pair.
- Components are lazily spawned, attached via `SetupAttachment(GetRootComponent())`, and finalized with `RegisterComponent()`.

---

## 7. HISM Deep Dive: The Swap-and-Pop Algorithm

The most mathematically complex problem in procedural generation using HISM is **safe deletion**.

### The Core Problem: Draw Calls vs Array Deletions
Standard `StaticMeshActors` cause CPU bottlenecks with 1 draw call per actor. `UHierarchicalInstancedStaticMeshComponent` solves this, maintaining instances in a highly optimized internal array.
However, when `RemoveInstance(Index)` is called, Unreal Engine does *not* shift subsequent indices down (an O(n) operation). Instead, it optimizes removal using **Swap-and-Pop** (O(1)):
1. Takes the absolute *last* instance in the memory array.
2. Swaps it directly into the index slot of the deleted instance.
3. Pops (truncates) the last slot.

If Building A and Building B are generated, and Building A is destroyed, Building B's instances (which resided at the end of the array) are abruptly swapped into Building A's old memory slots. Building B's internal `Ledger` is now completely desynchronized, leading to guaranteed engine crashes or memory corruption upon future deletions.

### The Resolution Algorithm (`DestroyBuilding`)
The C++ Engine resolves this through a meticulous descent tracking algorithm:
```text
function DestroyBuilding(BuildingID):
    Building = Ledger[BuildingID]
    Group instances by HISM component.
    
    for each (Component, InstanceRefs):
        // CRITICAL: Sort indices DESCENDING (remove highest first)
        Sort(InstanceRefs by InstanceIndex, Descending)
        
        for each Ref in InstanceRefs:
            Index = Ref.InstanceIndex
            LastIdx = Component->GetInstanceCount() - 1
            
            if Index == LastIdx:
                Component->RemoveInstance(Index) // Just Pop
            else:
                // Swap-and-Pop imminent: LastIdx will shift to Index.
                OwnerBuilding = FindBuildingOwningIndex(Component, LastIdx)
                
                if OwnerBuilding AND OwnerBuilding != Building:
                    OwnerBuilding.UpdateInstanceIndex(Component, LastIdx, Index)
                    
                Component->RemoveInstance(Index)
    
    Ledger.Remove(BuildingID)
```
**Performance Impact:** A 5-floor building uses 26 instances, approximately 1.5 KB of memory. Searching the ledger takes O(k × n). For a metropolis of 10,000 buildings, memory is roughly 15 MB, well within trivial operational bounds.

---

## 8. Spatial Awareness: Dual-Check & Auto-Nudge

Procedural generation is inherently blind, often spawning clipping or floating geometry. The system implements a **Dual-Check ScanArea** to provide the engine with simulated "eyes".

### Check 1: External Detection (Physics Trace)
Detects standard static geometry (landscapes, BSP brushes, manually placed assets).
- **Ground Z-Trace:** A `LineTraceSingleByChannel` fired downwards captures `Hit.ImpactPoint.Z`, redefining the building's absolute foundation height.
- **Bounding Box Check:** `BoxOverlapActors` searches for foreign collisions overlapping the target area.

### Check 2: Internal Detection (Memory Trace)
HISM instances are effectively invisible to standard discrete physics traces. To avoid self-clipping with other procedural structures:
- **Ledger Distance Check:** The system loops through the `Ledger` utilizing an `FVector::Dist` calculation against known procedural building centers and predefined safety clearances.

### The Spiral Search Auto-Nudge Algorithm
If `RequiresScan: true` is enabled and an obstacle is detected, C++ executes an autonomous spiral search rather than rejecting the command.
```cpp
// Pseudocode for FindClearLocation
float StepSize = 100.0f; 
int32 PointsPerRing = 8;

for (float Dist = StepSize; Dist <= MaxRadius; Dist += StepSize) {
    for (int32 i = 0; i < PointsPerRing; ++i) {
        float Angle = (2.0f * PI * i) / PointsPerRing;
        FVector Candidate = Requested + FVector(Cos(Angle)*Dist, Sin(Angle)*Dist, 0);
        
        if (IsExternallyClear(Candidate) && IsInternallyClear(Candidate)) {
            return Candidate; // Valid location found
        }
    }
}
```
If a clear spot is verified, the geometry is built, and a JSON receipt containing `"Status": "Success_Nudged"` and the `"ActualLoc"` is dispatched back to the LLM for continued contextual awareness.

### BatchSpawn Intra-Batch Check
Because `BatchSpawn` arrays are processed sequentially in C++, Building 1 is immediately registered in the Ledger prior to computing Building 2. Building 2 therefore mathematically recognizes Building 1 during its Dual-Check sequence, completely eliminating intra-batch collisions.

---

## 9. Token-Aware Complexity Routing (The Orchestrator)

Generating massive city blocks effortlessly surpasses Maximum LLM Output Token Limits:
- Groq (Llama 3.3 70B): ~4,096 tokens.
- Gemini 2.5 Pro: ~8,192 tokens.
A 40-building prompt requires roughly 8,000 tokens (40 * 200 tokens/building). Traditional LLM requests would fatally truncate this. 

### The Orchestrator Logic
`agents/orchestrator.py` dynamically routes complex tasks:
1. **Estimation:** It parses the prompt using RegEx and keyword heuristics (`village`=15, `district`=40, `metropolis`=200).
2. **Evaluation:** `estimated_tokens = (count * 200) + 150`. If this value exceeds 70% of the active model's budget (`max_output_tokens * 0.7`), the Orchestrator flags the prompt for splitting.
3. **Spatial Partitioning:** The scene is divided into logical zones ("northern section", "central area").
4. **Coordinate Offsets:** To enforce macro-level structural separation, explicit coordinate offsets are injected into the sub-prompts (e.g., Chunk 1: Y +3000 UU, Chunk 2: Y 0, Chunk 3: Y -3000 UU).
5. **Sequential Aggregation:** It fires independent LLM queries, validates them sequentially, streams the batches into Unreal Engine, and aggregates the final counts.

---

## 10. Web UI Integration & WebSocket API

While backend development uses the CLI `agent.py`, production integrations utilize a full Graphical Interface layer driven by `api_server.py`.

### Architecture
Built entirely on **FastAPI**, it exposes a WebSocket endpoint at `/ws/chat`. A frontend application (such as a Next.js React Dashboard) interfaces via standard JSON payloads.

### Communication Payload
The client transmits execution constraints alongside the natural language prompt:
```json
{
  "prompt": "Build a massive 20-building industrial zone.",
  "config": {
    "backend": "groq",
    "mode": "orchestrate"
  }
}
```

### Pipeline Execution Modes
The WebSocket server dynamically routes logic based on the `mode` parameter:
- **`build`:** Direct, single-pass generation instantly ported to Unreal.
- **`two_phase`:** Triggers code-generation paths, validates compilation, then executes.
- **`classic`:** Utilizes standard iterative MCP Tool Caller loops.
- **`orchestrate`:** Manually enforces the multi-chunk Token Orchestrator system.

The FastAPI wrapper intercepts deep internal prints and yields real-time execution logs back to the UI as JSON `{"type": "status", "message": "..."}`. Error catches (such as Unreal Engine connection drops) instantly broadcast `{"type": "error", "message": "..."}`, providing a resilient, highly responsive dashboard ecosystem.

---

## 11. Execution Roadmap & Risk Assessment

The realization of the "Delegator" architecture was meticulously executed across three verifiable phases to prevent cascading integration failures.

### Phase 1: Core Foundation
- **Goal:** Establish base C++ logic, structural headers, and the HISM pool.
- **Features:** Implementation of `ProceduralBuildingTypes.h`, the C++ math loop, Ledger, and basic blind `Spawn` and `ClearAll` intents. Deprecation of legacy Python math logic.

### Phase 2: Eyes & Nudge (Spatial Awareness)
- **Goal:** Provide physical reality constraints to the procedural algorithm.
- **Features:** Implementation of the Dual-Check ScanArea query, Ground-Z downward traces, and the Spiral Search Auto-Nudge radial function.

### Phase 3: The Masterpiece (Scale & Safety)
- **Goal:** Enable massive, memory-safe city generation dynamically.
- **Features:** The Swap-and-Pop descending deletion algorithm for `Destroy` and `Modify`, intra-batch awareness for `BatchSpawn`, the Token Orchestrator deployment, and the `AssetDictionary` semantic-to-mesh DataTable lookup system.

### Risk Assessment matrix
| Risk | Severity | Mitigation Strategy |
|------|----------|---------------------|
| HISM Deletion Memory Corruption | **CRITICAL** | Implementation of Descending-Order Swap-and-Pop re-indexing logic. |
| Macro-level Overlaps (Multi-chunk) | Medium | Handled via Coordinate Offset partitioning in Orchestrator prompts. |
| Malformed JSON Schema Outputs | Low | Fallback to Stack-based dynamic JSON string repair within Gateway. |

---
*Comprehensive technical documentation synthesized and generated by Antigravity AI for Unreal-MCP.*
