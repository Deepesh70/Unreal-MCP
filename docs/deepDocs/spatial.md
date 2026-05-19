Scaling Spatial Context Rendering
The Unreal-MCP project has been successfully updated to support high-performance spatial awareness and scalable procedural scene generation. By removing token-heavy global queries and migrating bulk rendering to a permanent C++ base class, the system is now capable of bypassing LLM context constraints and maintaining low draw calls for massive environments.

Spatial Queries (Context Preservation)
The legacy, token-intensive list_actors tool has been fully retired and replaced with Relative Spatial Queries. This prevents the LLM from hallucinating coordinates when working within large worlds.

[NEW] get_actors_near_actor: Retrieves all actors within a specified radius (e.g., 2000 units) relative to a specific target actor. Automatically filters out environment noise like HLODs and streaming proxies.
[NEW] get_actors_with_tag: Retrieves all actors marked with a specific Gameplay Tag, bypassing the need to enumerate the entire level.
[DELETED] list_actors: Completely removed to enforce the use of localized spatial context gathering.
HISM Base Class Architecture (Performance Scaling)
The framework now separates ephemeral LLM code generation from core instancing performance loops.

[NEW] AProceduralBaseActor: A manually coded, persistent C++ base class (ProceduralBaseActor.h/.cpp) that manages the HISM component pool.
Template Inheritance: The Jinja2 templates (ActorHeader.h.j2 and ActorSource.cpp.j2) have been updated so that all newly LLM-generated procedural classes automatically inherit from AProceduralBaseActor rather than AActor.
Refactoring CityManager: The AProceduralCityManager was updated to inherit from AProceduralBaseActor to prevent logic duplication. HISMPool and GetOrCreateHISM were successfully relocated.
Backend Intent Routing
The Python to Unreal Engine bridge has been extended to support the new instancing logic seamlessly.

InstancedSpawn Intent: agents/processor.py was updated to recognize and validate the InstancedSpawn intent, allowing the LLM to output massive arrays of transforms to the C++ Delegator.
WebSocket Handlers: The C++ ProcessBlueprint function now natively catches InstancedSpawn and feeds the JSON transform array into HandleInstancedSpawnIntent(), converting JSON arrays directly into highly-performant HISM instances.