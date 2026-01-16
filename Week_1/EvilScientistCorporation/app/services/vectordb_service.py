# This service will help us initailize and interact with our vector database.
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings

PERSIST_DIRECTORY = "app/chroma_store" # Where the DB will be stored on disk
COLLECTION = "evil_items" # What kind of data we're storing (like the tables in SQL)

# The actual chroma vector store itself 
vector_store: Chroma | None = None 

# Initialize the ChromaDB vector store 
def init_vector_store():
    # Use the global instance defined above to accomplish Singleton behavior
    global vector_store
    if vector_store is None:
        vector_store = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            collection_name=COLLECTION
            embedding_function=OllamaEmbeddings(model="nomic-embed-text")
        )
        

# Get an instance of the Chroma vector store

# Ingest documents into the vector store (this is where the embeddings happen)

# Search the vector store for similar or relevant documents
