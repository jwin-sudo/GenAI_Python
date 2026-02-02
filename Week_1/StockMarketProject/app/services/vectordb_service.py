from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

import uuid
import json

PERSIST_DIRECTORY = "app/chroma_store" # Where the DB will be stored on disk
COLLECTION = "macro_reports" # What kind of data we're storing (like the tables in SQL)
EMBEDDING = OllamaEmbeddings(model="nomic-embed-text") # The embedding model to use 

# The actual chroma vector store itself  is a dict that holds Chroma instances
# This allows us to manage multiple collections at once
vector_store: dict[str, Chroma] = {}

def get_vector_store(collection: str = COLLECTION) -> Chroma:
    # Get (or create) the vector store instsance
    # If creating, define the collection name, persist directory, and embedding function
    if collection not in vector_store:
        vector_store[collection] = Chroma(
            collection_name=collection,
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=EMBEDDING
        )  
    
    return vector_store[collection]

# --- New: ingest and search helpers for per-year macro reports ---

def _collection_for_year(year: int) -> str:
    return f"macro_report_{year}"

def ingest_text_for_year(year: int, text: str, id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Ingest a single text document into the collection for the given year.
    Returns the document id used.
    """
    collection = _collection_for_year(year)
    db = get_vector_store(collection)
    doc_id = id or str(uuid.uuid4())
    doc = Document(page_content=text, metadata=metadata or {})
    # add_documents expects an iterable of Document and optional ids
    db.add_documents([doc], ids=[doc_id])
    # persist if supported by the Chroma wrapper
    if hasattr(db, "persist"):
        try:
            db.persist()
        except Exception:
            pass
    return doc_id

def ingest_items_for_year(year: int, items: List[Dict[str, Any]]) -> List[str]:
    """
    Ingest multiple items into the year collection.
    Each item is a dict with keys: 'id' (optional), 'text' (required), 'metadata' (optional).
    Returns list of document ids ingested.

    This implementation is defensive:
    - Accepts either the langchain Document / add_documents API or the add_texts API.
    - Logs and raises a clear error when the underlying vector store call fails.
    """
    collection = _collection_for_year(year)
    db = get_vector_store(collection)

    if not isinstance(items, list):
        raise ValueError("items must be a list of dicts")

    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    def _sanitize_value(v: Any) -> Any:
        # allowed primitives for Chroma: str, int, float, bool, None
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        # lists/tuples of primitives -> join to comma string
        if isinstance(v, (list, tuple)):
            try:
                return ", ".join(str(x) for x in v)
            except Exception:
                return json.dumps(v, ensure_ascii=False)
        # dict or other complex type -> json string
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)

    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not text:
            continue
        doc_id = item.get("id") or str(uuid.uuid4())
        raw_meta = item.get("metadata") or {}
        # sanitize metadata values
        safe_meta: Dict[str, Any] = {}
        if isinstance(raw_meta, dict):
            for k, v in raw_meta.items():
                safe_meta[k] = _sanitize_value(v)
        else:
            # non-dict metadata -> store as a string
            safe_meta = {"metadata": _sanitize_value(raw_meta)}

        texts.append(text)
        metadatas.append(safe_meta)
        ids.append(doc_id)

    if not texts:
        return []

    try:
        # Prefer add_documents with langchain Document if available
        used_method = None
        try:
            # attempt to import canonical Document class
            from langchain.schema import Document as LC_Document  # type: ignore
            docs = [LC_Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
            if hasattr(db, "add_documents"):
                db.add_documents(docs, ids=ids)
                used_method = "add_documents(LC Document)"
        except Exception:
            # fallback to add_texts if available (many vectorstore wrappers support this)
            if hasattr(db, "add_texts"):
                db.add_texts(texts, metadatas=metadatas, ids=ids)
                used_method = "add_texts"
            else:
                # last resort: try add_documents with whatever Document class was previously used
                if hasattr(db, "add_documents"):
                    db.add_documents(docs, ids=ids)  # may raise
                    used_method = "add_documents(fallback)"
                else:
                    raise RuntimeError("Vector store does not support add_documents or add_texts")
    except Exception as e:
        import traceback; traceback.print_exc()
        # Raise a clear, actionable error so the router can return 500 with details
        raise RuntimeError(f"Failed to ingest items into collection '{collection}': {e}") from e

    # persist if supported
    try:
        if hasattr(db, "persist"):
            db.persist()
    except Exception:
        # ignore persistence errors but keep the ingestion result
        pass

    # debug print which method was used (optional)
    print(f"[VECTORDB] ingested {len(ids)} docs into '{collection}' via {used_method or 'unknown'}")

    return ids

def search_year(year: int, query: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the year's collection for the query and return top-k results as dicts:
    [{'id': ..., 'text': ..., 'metadata': {...}}, ...]
    """
    collection = _collection_for_year(year)
    db = get_vector_store(collection)

    # try high-level similarity_search if available
    results = []
    if hasattr(db, "similarity_search"):
        docs = db.similarity_search(query, k=k)
    elif hasattr(db, "similarity_search_by_vector"):
        vec = EMBEDDING.embed_query(query)
        docs = db.similarity_search_by_vector(vec, k=k)
    else:
        # fallback: return empty
        docs = []

    for d in docs:
        # d may be a Document or a mapping depending on adapter
        if isinstance(d, Document):
            results.append({"id": getattr(d, "id", None), "text": d.page_content, "metadata": d.metadata})
        elif isinstance(d, dict):
            results.append({"id": d.get("id"), "text": d.get("page_content") or d.get("text"), "metadata": d.get("metadata")})
        else:
            # best-effort convert
            try:
                text = getattr(d, "page_content", None) or getattr(d, "text", None) or str(d)
                metadata = getattr(d, "metadata", None) or {}
            except Exception:
                text = str(d)
                metadata = {}
            results.append({"id": None, "text": text, "metadata": metadata})

    return results