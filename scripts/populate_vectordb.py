import sys
import os
import json
import asyncio
import re

# Ensure Windows consoles can print emojis without throwing a UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure unreal_mcp is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unreal_mcp.connection.websocket import execute_python

import chromadb
from chromadb.utils import embedding_functions

# The UE python script
UE_SCRIPT = """
import unreal
import json

def get_assets():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    
    ar_filter = unreal.ARFilter(
        package_paths=["/Game/"],
        class_names=["StaticMesh", "MaterialInstanceConstant"],
        recursive_paths=True
    )
    
    assets = ar.get_assets(ar_filter)
    
    results = []
    for asset in assets:
        results.append({
            "asset_name": str(asset.asset_name),
            "asset_class": str(asset.asset_class_path.asset_name),
            "object_path": f"{asset.package_name}.{asset.asset_name}"
        })
        
    return results

print(json.dumps(get_assets()))
"""

def generate_semantic_string(asset):
    # e.g., StaticMesh'/Game/Environment/Furniture/Bedroom/SM_WoodItem_04.SM_WoodItem_04'
    # Wait, the object_path comes as a plain string, e.g. /Game/Environment/Furniture/Bedroom/SM_WoodItem_04.SM_WoodItem_04
    object_path = asset["object_path"]
    asset_class = asset["asset_class"]
    
    # Strip the .Name part
    package_path = object_path.split('.')[0]
    
    # Split folders
    parts = package_path.split('/')
    
    # Remove empty strings and 'Game'
    parts = [p for p in parts if p and p != 'Game']
    
    if not parts:
        return asset_class
        
    # Clean the last part (filename) by removing SM_, MI_, etc.
    last_part = parts[-1]
    # Remove prefix like SM_, MI_, M_, BP_
    last_part = re.sub(r'^(SM|MI|M|BP)_', '', last_part, flags=re.IGNORECASE)
    # Split camel case and underscores
    last_part_words = re.sub(r'([a-z])([A-Z])', r'\1 \2', last_part).replace('_', ' ')
    
    parts[-1] = last_part_words
    
    # Combine
    semantic_string = f"{asset_class} " + " ".join(parts)
    return semantic_string

async def main():
    print("🔌 Connecting to Unreal Engine to query Asset Registry...")
    result = await execute_python(UE_SCRIPT, timeout=30.0)
    
    if result.startswith("ERROR"):
        print(f"❌ Failed to get assets from Unreal:\\n{result}")
        return
        
    # The output from execute_python starts with "SUCCESS\\n" followed by stdout
    lines = result.split('\n', 1)
    if len(lines) > 1 and lines[0].strip() == "SUCCESS":
        try:
            # Find the line that looks like a JSON array
            json_str = None
            for line in lines[1].split('\n'):
                if line.startswith('['):
                    json_str = line
                    break
            
            if not json_str:
                raise ValueError("Could not find JSON array in output.")
                
            assets = json.loads(json_str)
            print(f"✅ Retrieved {len(assets)} assets from Unreal Engine.")
        except Exception as e:
            print(f"❌ Failed to parse JSON from Unreal: {e}\nRaw output:\n{result}")
            return
    else:
        print(f"❌ Unexpected output from Unreal:\n{result}")
        return

    print("📚 Initializing ChromaDB and sentence-transformers...")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        chroma_client = chromadb.PersistentClient(path=data_dir)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = chroma_client.get_or_create_collection(
            name="unreal_assets", 
            embedding_function=sentence_transformer_ef
        )
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB: {e}")
        return
        
    ids = []
    documents = []
    metadatas = []
    
    for asset in assets:
        # Avoid empty IDs
        if not asset["object_path"]:
            continue
            
        ids.append(asset["object_path"])
        documents.append(generate_semantic_string(asset))
        metadatas.append({
            "asset_name": asset["asset_name"],
            "asset_class": asset["asset_class"]
        })
        
    if not ids:
        print("⚠️ No assets found to insert.")
        return
        
    print(f"🧠 Upserting {len(ids)} assets into ChromaDB...")
    
    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        print(f"   Upserted batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
        
    print("✅ Vector database population complete!")

if __name__ == "__main__":
    asyncio.run(main())
