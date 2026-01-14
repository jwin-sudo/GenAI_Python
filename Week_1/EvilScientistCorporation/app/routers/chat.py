from typing import List

from fastapi import APIRouter
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from app.models.item_model import ItemModel
from app.services.chain_service import get_general_chain, get_memory_chain

#Typical Router setup
router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

# I'm going to make a model right here - we don't need to import it around
# So I'll skip making a dedicated model.py file
class ChatInputModel(BaseModel):
    input:str

# Here's another short model that will help us format responses into Pydantic Lists
class ItemListModel(BaseModel):
    items:list[ItemModel] # A list of our ItemModel from models/item_model.py

# Import the chain-creation functions from the chain service here
general_chain = get_general_chain()
memory_chain = get_memory_chain()

# Generic chatbot-esque endpoint
@router.post("/")
async def general_chat(chat:ChatInputModel):
    return general_chain.invoke(input={"input":chat.input})

# DOCUMENT LOADING EXAMPLE: Endpoint that summarizes a .txt file
@router.get("/plan-summary")
async def summarize_plans():

    # Load in .txt file
    loader = TextLoader("app/files_to_load/boss_plans.txt")
    docs = loader.load() # return a list of langchain Document objects

    # Extract the text from the docs variable
    evil_plans_text = docs[0].page_content

    # Invoke the LLM and give it another small prompt to summarize the boss's plans
    return general_chain.invoke(
        {
            "input": f"Concisely summarize the following text from my boss: "
            f"{evil_plans_text}"
        }
    )

# DOCUMENT LOADING EXAMPLE: Endpoint that lets user ask questions about a .csv file
@router.post("/data-analysis")
async def analyze_data(chat:ChatInputModel):

    # Load in .csv file
    loader = CSVLoader("app/files_to_load/sales_data.csv")
    docs = loader.load()

    # Convert the loaded documents into a single CSV string
    sales_data_csv = "\n".join(doc.page_content for doc in docs)

    # Invoke the LLM with another small prompt encouraging data analysis
    return general_chain.invoke(
        {
            "input": f"Answer the following question based on the provided sales data: "
                     f"{chat.input}"
                     f"Here's the sales data: "
                     f"{sales_data_csv}"
        }
    ).content


# OUTPUT PARSER EXAMPLE: An endpoint that sends item recs based on our Pydantic ItemModel
# We're going to parse the LLM's output into a Pydantic model
@router.get("/recommendations")
async def get_item_recommendations(amount: int = 3):

    # I'm going the prompt here, instead of in the invocation
    # I prefer to do it this way if the prompt is long
    rec_prompt = f"""
    You are an evil sales assistant at the Evil Scientist Corporation. 
    Share {amount} of the most popular evil items on the market right now. 
    
    Format the response as a single JSON object with the following structure:
    {{
        "items": [
            {{
                "id": int (greater than 0),
                "name": str (3-50 characters),
                "description": str (10-100 characters),
                "inventory": int (0-100),
                "price": float (greater than 0 with no commas in the numbers)
            }},
            ...
        ]
    }}
    
    Return ONLY the JSON, no extra text.
    """

    # Pydantic has its own output parser in LangChain
    parser = PydanticOutputParser(pydantic_object=ItemListModel)

    # This time, we'll actually save the response
    response = general_chain.invoke({"input": rec_prompt})

    # Finally, parse the response into our Pydantic Model and return it!
    parsed_output = parser.parse(response.content)
    return parsed_output.items

# MEMORY EXAMPLE - This endpoint uses our memory chain for better conversational memory 
@router.post("/memory-chat")

async def chat_with_memory(chat:ChatInputModel):
    # That's it! The chain will remember the last "k" interactions automatically
    # Note we use "run" instead of invoke 
    return memory_chain.run(input=chat.input)

# You can ignore this - I stole it from Shane for week 4 cuz I liked it
# @tool
# def fetch_from_map_wrapper(*args, **kwargs):
#     """
#     takes in a list of items to search through as the first argument,
#     then the key word arguments for the attributes of the object you want to find.
#     """
#     fetch_from_map(*args, **kwargs)
#
# tools = [fetch_from_map_wrapper]
# llm_with_tools = llm.bind_tools(tools)


#
# def fetch_from_map(my_list: list, func=None, **kwargs) -> list:
#     if not isinstance(my_list, list):
#         # print("not a list")
#         return []
#
#     if func is None:
#         # print("new function")
#         def func(k, v, x):
#             # print(f"{k}: {v} -> {x.dict()}")
#             return x.dict().get(k) == v
#
#     reduced = list(my_list)
#     # print(reduced)
#     for k, v in kwargs.items():
#         reduced = filter(partial(func, k, v), reduced)
#         # print(list(reduced))
#
#     return list(reduced)