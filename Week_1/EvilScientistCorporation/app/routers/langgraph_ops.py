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
    # We're going to add a config object to configure the "thread ID" for our memory
    # NOTE: I'm just hardcoding this, realistically you'd pull a User ID, Session ID, etc. 
    #result = langgraph.invoke({chat.input})
    result = langgraph.invoke(
        {"query": chat.input},
        config={
            "configurable": {"thread_id":"demo_thread"}
        }
    )
    
    return {
        "route": result.get("route"),
        "answer": result.get("answer"),
        "sources": result.get("docs"),
        "message_memory": result.get("message_memory")
    }


# Endpoint that invokes the graph in the langgraph service 
@router.post("/agent-chat")
def agent_chat(chat: ChatInputModel):
    # We're going to add a config object to configure the "thread ID" for our memory
    # NOTE: I'm just hardcoding this, realistically you'd pull a User ID, Session ID, etc. 
    #result = langgraph.invoke({chat.input})
    result = langgraph.invoke(
        {"query": chat.input},
        config={
            "configurable": {"thread_id":"demo_thread"}
        }
    )
    
    return {
        "route": result.get("route"),
        "answer": result.get("answer"),
        "sources": result.get("docs"),
        "message_memory": result.get("message_memory")
    }
    

