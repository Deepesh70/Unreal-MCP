import os
import glob
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# ── RAG Store Data Paths ──────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLUEPRINTS_DIRS = [
    os.path.join(PROJECT_ROOT, "examples", "blueprints"),
    os.path.join(PROJECT_ROOT, "data", "blueprints"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "blueprints"),
]
CHROMA_DB_DIR = os.path.join(PROJECT_ROOT, "data", "chroma_db")

# ── Local Embeddings ─────────────────────────────────────────────────
# Using a fast, free local CPU embedding model (MiniLM)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

_vectorstore = None

def get_vectorstore():
    """Builds or loads the Chroma database on demand."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    # We ensure the chroma db directory exists
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    # Load all markdown blueprints from disk
    docs = []
    seen_files = set()
    for bp_dir in BLUEPRINTS_DIRS:
        if os.path.isdir(bp_dir):
            for filepath in glob.glob(os.path.join(bp_dir, "*.md")):
                filename = os.path.basename(filepath)
                if filename in seen_files:
                    continue
                seen_files.add(filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    docs.append(Document(page_content=content, metadata={"source": filename}))

    if not docs:
        print(" [RAG] No blueprints found in data/blueprints. Vector DB will be empty.")
        _vectorstore = Chroma(
            collection_name="blueprints",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        return _vectorstore

    # If Chroma DB already exists on disk and is populated, we could just load it,
    # but for this scale (a few files), we can just re-init it to ensure it's fresh.
    print(f" [RAG] Reloading {len(docs)} blueprints into Chroma vector database...")
    _vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
        collection_name="blueprints"
    )
    return _vectorstore


def retrieve_blueprint(user_query: str) -> str:
    """Uses Vector Math to find the single most semantically relevant blueprint."""
    store = get_vectorstore()
    
    # K=1 because we just want the absolute best matching blueprint (if any)
    results = store.similarity_search_with_relevance_scores(user_query, k=1)
    
    if not results:
        return ""
        
    doc, score = results[0]
    
    # We only inject if it's actually somewhat relevant (score > 0.0 means it's mathematically similar at all)
    # Cosine distance scores vary wildly, but generally anything highly negative is irrelevant
    if score > 0.1:
        print(f" [RAG] Found highly relevant blueprint: {doc.metadata.get('source')} (Score: {score:.2f})")
        return doc.page_content
    else:
        print(f" [RAG] No highly relevant blueprint found (Best score: {score:.2f} for {doc.metadata.get('source')})")
        return ""
