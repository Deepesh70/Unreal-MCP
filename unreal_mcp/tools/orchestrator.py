import json
import os
from typing import List, Optional, Dict, Any
from unreal_mcp import mcp
from unreal_mcp.tools.scene import get_actors_near_actor as _near_actor
from unreal_mcp.utils import format_error
from unreal_mcp.config.settings import CPP_OUTPUT_DIR, PROJECT_API

@mcp.tool()
async def query_local_space(target_actor_id: str, radius: float = 2000.0) -> str:
    """Find all actors within a certain radius of a specific target actor.
    
    This is highly token-efficient. Use this instead of absolute coordinate math
    to find what is physically near an object you previously placed or discovered.
    
    Args:
        target_actor_id: The partial or full name of the center actor (e.g., "BedFrame_01").
        radius: The search radius in Unreal Units (cm). Default is 2000.0 (20 meters).
    """
    return await _near_actor(target_actor_id, radius)

@mcp.tool()
async def search_asset_database(query: str, max_results: int = 15) -> str:
    """Search the ChromaDB vector database for Unreal Engine assets (meshes, materials).
    
    Args:
        query: Semantic description of the asset you want (e.g., "wooden chair", "concrete wall").
        max_results: Number of top results to return.
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        
        # Go up three directories: tools -> unreal_mcp -> Unreal-MCP
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")
        if not os.path.exists(data_dir):
            return "⚠️ Asset database not found. Please run 'python scripts/populate_vectordb.py'."
            
        import logging
        logging.getLogger("chromadb").setLevel(logging.ERROR)
        
        chroma_client = chromadb.PersistentClient(path=data_dir)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        try:
            collection = chroma_client.get_collection(name="unreal_assets", embedding_function=sentence_transformer_ef)
        except ValueError:
            return "⚠️ Asset collection doesn't exist. Please run 'python scripts/populate_vectordb.py'."
            
        results = collection.query(
            query_texts=[query],
            n_results=max_results
        )
        
        if not results['ids'] or not results['ids'][0]:
            return "No assets found."
            
        asset_paths = results['ids'][0]
        context = "AVAILABLE ASSETS:\n"
        metadatas = results.get('metadatas', [[{}]])[0]
        
        for i, p in enumerate(asset_paths):
            m_class = metadatas[i].get("asset_class", "Object") if metadatas and len(metadatas) > i and metadatas[i] else "Object"
            context += f"- {m_class} '{p}'\n"
            
        return context
    except Exception as e:
        return format_error(e, "Asset database search failed.")


@mcp.tool()
def draft_procedural_blueprint(
    intent: str, 
    structure_id: str, 
    requested_loc: Optional[List[float]] = None, 
    asset_path: Optional[str] = None,
    transforms: Optional[List[Dict[str, Any]]] = None,
    parameters: Optional[Dict[str, Any]] = None, 
    parts: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Draft a procedural JSON blueprint perfectly formatted for the Unreal Engine backend.
    Use this to construct valid JSON payloads for 'InstancedSpawn', 'Spawn', or 'Composite' intents.
    
    Args:
        intent: The action intent (e.g., "InstancedSpawn", "Spawn", "BatchSpawn", "GenerateGeometry").
        structure_id: A unique ID for the structure (e.g., "House_01" or "Forest_Bulk").
        requested_loc: A list of 3 floats [X, Y, Z] representing the base spawn location (for Spawn/Composite).
        asset_path: The exact Unreal Engine asset path (e.g., "/Game/..."), required for InstancedSpawn.
        transforms: A list of transform dictionaries (e.g., [{"Loc": [X, Y, Z], "Rot": [P, Y, R], "Scale": [X, Y, Z]}]), required for InstancedSpawn.
        parameters: A dictionary of structural parameters (e.g., {"StructureType": "Building", "Floors": 3}).
        parts: An optional list of dictionaries for composite structures (e.g., [{"Shape": "cube", "Offset": [0,0,0], "Scale": [1,1,1]}]).
        
    Returns:
        A JSON string representing the exact payload required for execute_and_compile.
    """
    payload = {
        "Intent": intent,
        "ID": structure_id
    }
    
    if requested_loc is not None:
        payload["RequestedLoc"] = requested_loc
        
    if asset_path is not None:
        payload["AssetPath"] = asset_path
        
    if transforms is not None:
        payload["Transforms"] = transforms
        
    if parameters is not None:
        payload["Parameters"] = parameters
        
    if parts is not None:
        payload["Parts"] = parts
        
    if intent in ("Spawn", "Composite"):
        payload["EnvironmentCheck"] = {"RequiresScan": True, "Radius": 2000}
        
    return json.dumps(payload, indent=2)


@mcp.tool()
async def execute_and_compile(blueprint_json: str) -> str:
    """
    Execute the drafted JSON blueprint and compile/spawn it in Unreal Engine.
    
    Args:
        blueprint_json: The valid JSON string generated by draft_procedural_blueprint.
    """
    try:
        from agents.processor import process_agent_output
        return await process_agent_output(blueprint_json, CPP_OUTPUT_DIR, PROJECT_API, user_prompt="MCP Autonomous Execution")
    except Exception as e:
        return format_error(e, "Execution failed.")
