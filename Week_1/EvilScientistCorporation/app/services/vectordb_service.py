# This service will help us initailize and interact with our vector database.
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from typing import Any


PERSIST_DIRECTORY = "app/chroma_store" # Where the DB will be stored on disk
COLLECTION = "evil_items" # What kind of data we're storing (like the tables in SQL)
EMBEDDING = OllamaEmbeddings(model="nomic-embed-text") # The embedding model to use 


# The actual chroma vector store itself  is a dict that holds Chroma instances
# This allows us to manage multiple collections at once 
vector_store: dict[str, Chroma] = {}



# Get an instance of the Chroma vector store (lets us interact with the DB instance)
# Takes in a collection to use, or defaults to COLLECTION ("evil_items")
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

# Ingest documents into the vector store (this is where the embeddings happen)
def ingest_items(items: list[dict[str, Any]], collection:str=COLLECTION) -> int:
    # Get an instance of the vector store 
    db_instance = get_vector_store(collection)

    # Turn the input into a list of documents to get inserted 
    docs = [
        Document(page_content=item["text"], metadata=item.get("metadata", {}))
        for item in items
                 
    ]
    # Also, append IDs to the documents (also found in the sample data)
    ids = [item["id"] for item in items]


    # Add the documents, return the length of the ingested items 
    db_instance.add_documents(docs, ids=ids)
    return len(items)

# Search the vector store for similar or relevant documents
def search(query: str, k: int = 3, collection:str = COLLECTION) -> list[dict[str, Any]]:
    # Get an instance of the vector store 
    db_instance = get_vector_store(collection)

    # Save the results of the similarity search
    results = db_instance.similarity_search_with_score(query, k=k)

    # Return the  results as a list of dicts with the expected fields 
    return [
        {
            "text": result[0].page_content,
            "metadata": result[0].metadata,
            "score": result[1]
        }
        for result in results
    ]


