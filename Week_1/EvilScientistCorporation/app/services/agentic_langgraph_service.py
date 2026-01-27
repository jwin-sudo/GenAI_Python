

'''This Service accomplishes the same thing as langgraph service 
BUT we'll use an AGENT in the routing node insteand of keyword matching
The vectorDB retrieval nodes become tools
The chat nodes pretty much stay the same
'''


"""
This Service accomplishes the same thing as langgraph_service
BUT we'll use an AGENT in the routing node instead of keyword matching
The vectorDB retrieval nodes become tools
The chat nodes pretty much stay the same
"""
from typing import TypedDict, Any, Annotated

from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langgraph.graph import add_messages
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from app.services.vectordb_service import search

llm = ChatOllama(
    model="llama3.2:3b", # The model we're using (we installed llama3.2:3b)
    temperature=0.2 # Temp goes from 0-1. Higher temp = more creativity
)

# Same state as the old service
class GraphState(TypedDict, total=False): #total=False makes all fields optional
    query: str
    route: str
    docs: list[dict[str, Any]]
    answer: str
    # with add_messages reducer 
    message_memory: Annotated[list[BaseMessage], add_messages]

# TOOLS --------------------------------
# The agentic route node will use one or none of these based on the User's query 
# Remember, tools are just python functions that an agent CAN execute at run time
# IMPORTANT: Each tool needs '''docstrings''' to describe what they do for the agent 

@tool(name_or_callable="extract_items_tool")
def extract_items_tool(query: str) -> list[dict[str, Any]]:
    """
    Based on the user's input, the "query" arg, do a semantic search.
    Retrieve relevant docs on the boss's plans/schemes based on the boss_plans vectorDB collection.
    """
    return search(query, k=5, collection="evil_items")

@tool(name_or_callable="extract_plans_tool")
def extract_plans_tool(query: str) -> list[dict[str, Any]]:
    """
    Based on the user's input, the "query" arg, do a semantic search.
    Retrieve relevant docs on the boss's plans/schemes based on the boss_plans vectorDB collection.
    """

    return search(query, k=5, collection="boss_plans")

# Some variables that will help us make the agent aware of the tools 

# List of the available tools
TOOLS = [extract_items_tool, extract_plans_tool]

# Map tool names to their functions in a scalable way 
# We need this to call tools by their name in the agentic router node 
# (See us defining and assigning names in the agentic router node)
TOOL_MAP = {tool.name: tool for tool in TOOLS}

# Get a version of the LLM that is aware of its toolbox 
llm_with_tools = llm.bind_tools(TOOLS)

# NODES (including our agentic router)-----------------------------

# Here's the AGENT part - this routing node uses agentic AI to determine what tool to call, if any 
def agentic_router_node(state: GraphState) -> GraphState:
    
    # Get the user's query from State 
    query = state.get("query", "")

    # Using this different chat prompting style just cuz it looks cool 
    # Feel free to use the typical prompt string like we've been doing 

    messages = [
        SystemMessage(concent=(
            """
            You are an internal agent that decides whether VectorDB retrieval is needed
            If the User is asking about product, items, recs, prices, etc., use the "extract_items" tool
            If the User is asking about their boss's evil plans or schemes, use the "extract_plans" tool  
            If neither applies, it's a general chat. DO NOT call a tool.
            If you call a tool, call EXACTLY ONE tool.
            """
        )),
        HumanMessage(content=query)
    ]

    #First LLM call to decide which tool to use 
    agentic_response = llm_with_tools.invoke(messages)

    # If there was no tool call, route to general chat
    if not agentic_response.tool_calls:
        return {"route": "chat"}
    
    # if a tool WAS called, invoked it and store results and the appropriate route in State 
    tool_call = agentic_response.tool_calls[0] # We only expect one tool call 
    tool_name = tool_call["tool_name"] # Extract the name of the tool that was called 

    # Finally, here's us actually invoking the tool by name 
    results = TOOL_MAP[tool_name].invoke({"query": query})

    # Automatically set the route to the answer_with_context node 
    return {
        "route": "answer_with_context",
        "docs": results
    }