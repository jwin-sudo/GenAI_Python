from fastapi import APIRouter
from pydantic import BaseModel
from app.services.vectordb_service import ingest_items, search
from typing import Any
from app.services.vectordb_service import ingest_items, search, ingest_text
from app.services.chain_service import get_general_chain

router = APIRouter(
    prefix="/vector-ops",
    tags=["vector-ops"],
)   

# A quick Pydantic model for document ingestion
class IngestItem(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] | None = None 

# Another quick model for ingesting raw text
class IngestTextRequest(BaseModel):
    text: str



class SearchRequest(BaseModel):
    query: str
    k: int = 3

# Importing the basic chainm for use in the LLM-powered endpoints
chain = get_general_chain()

# Another quick model for similarity search request results 


# Endpoint for raw data ingestion 
@router.post("ingest-text")
async def ingest_raw_text(request: IngestTextRequest):
    count = ingest_text(request.text)
    return {"ingested chunks: ": count}

# Endpoint for similarity search 
@router.post("/ingest-items")
async def ingest_json(items: list[IngestItem]):
    
    # Call the service method to ingest items
    count = ingest_items([item.model_dump() for item in items])

    return {"ingested": count}



@router.post("/search-items")
async def items_similarity_search(request: SearchRequest):
    return search(request.query, request.k)

# Endpoint with LLM-powered response that uses the boss_plans collection 
@router.post("/search-plans")
async def search_plans(request: SearchRequest):
    result = search(request.query, request.k, collection="boss_plans")

    # Really quick prompt that tells the LLM the returned results 
    # and asks for it to answer the user based on those results 

    prompt = (
        "Based on the following extracted info from a boss's evil plans,"
        "Answer the user's query to the best of your ability."
        "If there's no relevant information stored, you can say that."
        f"Extracted info: {result}"
        f"USer query: {request.query}"
    )

    # Invoke our general chain from chain_service 
    return chain.invoke({"input": prompt})