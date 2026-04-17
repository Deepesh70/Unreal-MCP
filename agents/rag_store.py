import os
import glob
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# ── RAG Store Data Paths ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUEPRINTS_DIR = os.path.join(BASE_DIR, "data", "blueprints")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

# ── Local Embeddings ─────────────────────────────────────────────────
# Using a fast, free local CPU embedding model (MiniLM)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

_vectorstore = None

def get_vectorstore():
    """Builds or loads the Chroma database on demand."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    # We ensure the blueprints directory exists
    os.makedirs(BLUEPRINTS_DIR, exist_ok=True)
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    # Load all markdown knowledge files from disk
    docs = []
    # We look in both blueprints and the new api_knowledge file
    knowledge_files = glob.glob(os.path.join(BLUEPRINTS_DIR, "*.md"))
    api_knowledge_path = os.path.join(BASE_DIR, "data", "ue_api_knowledge.md")
    if os.path.exists(api_knowledge_path):
        knowledge_files.append(api_knowledge_path)

    for filepath in knowledge_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            filename = os.path.basename(filepath)
            
            # CHUNKING STRATEGY: Split by H2 headers (## ) to keep components isolated
            chunks = content.split("\n## ")
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Re-add the header prefix if it's not the first (pre-header) chunk
                processed_chunk = chunk if i == 0 and not content.startswith("## ") else "## " + chunk
                
                # Extract the title for metadata if possible
                title = processed_chunk.split("\n")[0].replace("#", "").strip()
                
                docs.append(Document(
                    page_content=processed_chunk, 
                    metadata={"source": filename, "chunk_title": title}
                ))

    if not docs:
        print(" [RAG] No knowledge found in data/. Vector DB will be empty.")
        _vectorstore = Chroma(
            collection_name="unreal_knowledge",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        return _vectorstore

    print(f" [RAG] Reloading {len(docs)} knowledge chunks into Chroma vector database...")
    _vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
        collection_name="unreal_knowledge"
    )
    return _vectorstore


def retrieve_api_knowledge(query: str, k: int = 2) -> str:
    """Uses Vector Math to find the most relevant API rules or blueprints."""
    store = get_vectorstore()
    
    results = store.similarity_search_with_relevance_scores(query, k=k)
    
    if not results:
        return ""
        
    chunks = []
    for doc, score in results:
        if score > 0.5:
            print(f" [RAG] Retrieved relevant chunk: {doc.metadata.get('chunk_title')} from {doc.metadata.get('source')} (Score: {score:.2f})")
            chunks.append(doc.page_content)
    
    return "\n\n---\n\n".join(chunks)


def retrieve_blueprint(query: str, k: int = 1) -> str:
    """Alias for retrieve_api_knowledge, typically used for geometry blueprints."""
    return retrieve_api_knowledge(query, k=k)


if __name__ == "__main__":
    print(" [RAG] Manually triggering Vector Database build/reload...")
    get_vectorstore()
    print(" [RAG] Build complete. Knowledge is now indexed in data/chroma_db/")
