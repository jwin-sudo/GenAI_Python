from app.services.chain_service import get_memory_chain, get_session_messages, get_general_chain
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_community.document_loaders import TextLoader, CSVLoader



#Typical Router setup
route = APIRouter(
    prefix="/chatbot",
    tags=["chatbots"]
)

# I'm going to make a model right here - we don't need to import it around
# So I'll skip making a dedicated model.py file
class ChatInputModel(BaseModel):
    input:str

memory_chain = get_memory_chain()
general_chain = get_general_chain()

# A chatbot endpoint that uses memory
@route.post("/chat-with-memory")
async def chat_with_memory(chat:ChatInputModel):
    session_id = "demo_thread"

    result = await memory_chain.ainvoke(
        {"input": chat.input},
        config={"configurable": {"session_id": session_id}},
    )

    # normalize reply text
    if isinstance(result, dict):
        reply = result.get("answer") or result.get("text") or result.get("output") or str(result)
    else:
        reply = getattr(result, "content", None) or getattr(result, "text", None) or str(result)

    # fetch stored history and return it
    message_memory = get_session_messages(session_id)
    return {"reply": reply, "message_memory": message_memory}

@route.get("/trading-philosophy")
async def summarize_warren_buffet_philosophy():

    # Load in .txt file
    loader = TextLoader("app/files_to_load/warren_buffet.txt")
    docs = loader.load() # return a list of langchain Document objects

    # Extract the text from the docs variable
    warren_buffet_text = docs[0].page_content

    return general_chain.invoke(
        {
            "input": f"Concisely summarize the following text from Warren Buffet trading philosophy: "
            f"{warren_buffet_text}"
        }
    )

# ...existing code...
@route.get("/Warren-Buffet-stock-recommendations")
async def get_stock_recommendations():
    # Load in .txt file
    loader = TextLoader("app/files_to_load/warren_buffet.txt")
    docs = loader.load()  # list[Document]

    # If the file is large, consider summarizing before using as context.
    warren_buffet_text = docs[0].page_content

    prompt_text = (
        "Using the Warren Buffett philosophy below, give a concise stock recommendation for a retail investor.\n\n"
        "Context (Warren Buffett philosophy):\n"
        f"{warren_buffet_text}\n\n"
        "Task:\n"
        "- Based only on the philosophy above, recommend one stock (ticker) and explain why briefly (2-3 sentences).\n"
        "- Give one suggested action (Buy / Hold / Avoid) and a short rationale.\n"
        "- Mention one risk to consider and a confidence level (low/medium/high).\n"
        "Keep the answer short and actionable."
    )

    # call the runnable chain (async)
    result = await general_chain.ainvoke({"input": prompt_text})

    # normalize chain result (supports dict or AIMessage-like objects)
    if isinstance(result, dict):
        reply = result.get("answer") or result.get("text") or result.get("output") or str(result)
    else:
        reply = getattr(result, "content", None) or getattr(result, "text", None) or str(result)

    return {"recommendation": reply}

@route.post("/stock-analysis")
async def analyze_stock(chat:ChatInputModel):

    # Load in .csv file
    loader = CSVLoader("app/files_to_load/tech_performance.csv")
    docs = loader.load()

    # Convert the loaded documents into a single CSV string
    magnificent7_data_csv = "\n".join(doc.page_content for doc in docs)

    # Invoke the LLM with another small prompt encouraging data analysis
    return general_chain.invoke(
        {
            "input": f"Answer the following question based on the history performance of the magnificent seven stocks: "
                     f"{chat.input}"
                     f"Here's the stock data: "
                     f"{magnificent7_data_csv}"
        }
    ).content