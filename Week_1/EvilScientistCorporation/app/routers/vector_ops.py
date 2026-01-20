from fastapi import APIRouter
from pydantic import BaseModel
from app.services.vectordb_service import ingest_items, search
from typing import Any
from app.services.vectordb_service import ingest_items, search, ingest_text

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




# Another quick model for similarity search request results 


# Endpoint for data ingestion 
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

# Endpoint for raw text ingestion


@router.post("/search-items")
async def items_similarity_search(request: SearchRequest):
    return search(request.query, request.k)
