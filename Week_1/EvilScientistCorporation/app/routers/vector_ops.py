from fastapi import APIRouter
from pydantic import BaseModel
from app.services.vectordb_service import ingest_items, search
from typing import Any

router = APIRouter(
    prefix="/vector-ops",
    tags=["vector-ops"],
)   

# A quick Pydantic model for document ingestion
class IngestItem(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] | None = None 

class SearchRequest(BaseModel):
    query: str
    k: int = 3




# Another quick model for similarity search request results 


# Endpoint for data ingestion 

# Endpoint for similarity search 
@router.post("/ingest")
async def ingest(items: list[IngestItem]):
    
    # Call the service method to ingest items
    count = ingest_items([item.model_dump() for item in items])

    return {"ingested": count}

@router.post("/search")
async def similarity_search(request: SearchRequest):
    return search(request.query, request.k)
