Some thing needed to be here so that we are easily able to use this inside our pc easily

python populate_vectordb.py         to update the vector database


Run python setup_unreal.py to copy the new ProceduralBaseActor.h/.cpp files to your Unreal Engine Source/ directory


Autonomous MCP Orchestration
The Unreal-MCP project has been updated to act as a fully autonomous MCP server. You can now connect directly to it using any orchestrator (e.g., Claude Desktop, Cursor) without needing intermediate scripts.

Key Components
New Module: unreal_mcp/tools/orchestrator.py provides the following high-level tools:
query_local_space: Query actors in the vicinity of a target actor.
search_asset_database: Search the ChromaDB vector store for assets.
draft_procedural_blueprint: Generate validated JSON payloads for procedural generation.
execute_and_compile: Execute the procedural generation request in Unreal Engine.
Getting Started
Ensure you have run the setup script to copy the C++ files to your Unreal Engine project.

Run the server: python -m unreal_mcp.server
Connect your MCP client and use the tools listed above to orchestrate your Unreal Engine environment.