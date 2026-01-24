from fastapi import APIRouter 
from pydantic import BaseModel
from app.services.langgraph_service import langgraph

router = APIRouter(
    prefix="/langgraph",
    tags=["langgraph"],
)

class ChatInputModel(BaseModel):
    input:str

# Endpoint that invokes the graph in the langgraph service 
@router.post("/chat")
def chat(chat: ChatInputModel):
    #result = langgraph.invoke({chat.input})
    result = langgraph.invoke({"query": chat.input})
    
    return {
        "route": result.get("route"),
        "answer": result.get("answer"),
        "sources": result.get("docs")
    }
    

