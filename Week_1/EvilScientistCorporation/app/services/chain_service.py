# This service module will store logic that returns chains 
# a chain in LangChain is just a sequence of actions/info that we send to an LLM 
# all in the hopes of getting an appropriate response 
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConverationBufferWindowMemory

# Define tehe LLM we're going to use 
llm = ChatOllama(
    model="llama3.2:3b", # The model we're using (we installed llama3.2:3b)
    temperature=0.2 # Temp goes from 0-1. Higher temp = more creativity
)

# Define the general prompt we'll send to the LLM (helps with tone and context)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful chatbot that assists with queries in the Evil Scientist Corporation."
     "You help the scientists with their evil schemes, and you are pretty evil yourself"
     "Your tone is conniving and blunt, with a focus on solutioning and efficiency"
     "You don't provide further suggestions beyond what is asked. Keep your answers concise."),
    ("user", "{input}")
])

# Basic general chain here 
def get_general_chain():

    # This basic chain is just 
        # The llm we're talking to 
        # The prmpt we're sending to the llm 
        # We defined both of these above!! 

    chain = prompt | llm
    
    return chain 
# More sequential chain that refines the answer more 

# A chain that is better equipped to remember the conversation 
def get_memory_chain():

    # Create a memory object based on, an instance of ConversationBufferWindowMemory
    # CBWM only remember the last "k" interactions 
    memory = ConverationBufferWindowMemory(k=5)

    # This is clunky: Going to rewrite the prompt with a {history} variable 
    # These older Memory classes need a {history} variable to store the previous messages 

    memory_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful chatbot that assists with queries in the Evil Scientist Corporation."
        "You help the scientists with their evil schemes, and you are pretty evil yourself"
        "Your tone is conniving and blunt, with a focus on solutioning and efficiency"
        "You don't provide further suggestions beyond what is asked. Keep your answers concise."),
        
        ("user", "{input}")
    ])

    # Make and return a chain in a more old fashion way
    memory_chain = ConversationChain(
        llm = llm,
        memory = memory, # Defined at the start of this function
        prompt = memory_prompt # The rewritten prompt with {history}
    )
    return 