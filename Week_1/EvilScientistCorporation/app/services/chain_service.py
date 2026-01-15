# This service module will store logic that returns chains 
# a chain in LangChain is just a sequence of actions/info that we send to an LLM 
# all in the hopes of getting an appropriate response 
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.chains.transform import TransformChain

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

# Defining some filter logic for our TransformChain
def bad_word_filter(inputs):
    # Capture the User's input as a string
    user_input = inputs[inputs]

    # If the input contains the word "javascript", we block it. Otherwise, answer with general chat
    if "javascript" in user_input.lower():
        return {"output": "I won't talk about that forbidden language"}
    
    else:
        return {"output": get_general_chain().invoke(user_input)}

# Basic general chain here 
def get_general_chain():

    # This basic chain is just 
        # The llm we're talking to 
        # The prmpt we're sending to the llm 
        # We defined both of these above!! 

    chain = prompt | llm
    
    return chain 
# More sequential chain that refines the answer more by adding 2 chains to the workflow
def get_sequential_chain():
    # First chain - just a basic prompt to the LLM. We can use our OG members from above
    draft_chain = prompt | llm

    # Define a nee prompt to help us refine the initial answer 
    # In this case, we want to refine the answer to be more appropriate for customer support
    improve_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a customer support bot. "
                    "You take raw answers from the LLM and make them more appropriate. "
                    "You are less evil in tone, but more condescending. "
                    "You priortize a conscise but comprehensive answer. "
                    "You MUST provide a solution, even if a solution isn't clear. "
                    "Narrow the answer down to 2-3 sentences."
                    "ONLY share the refined answer"
                    "At the end include the initial response before refinement"),
        ("user", "Initial Reply: {input}")
    ])

    # Second chain using the refined prompt\
    final_chain = improve_prompt | llm

    return draft_chain | final_chain



# A chain that is better equipped to remember the conversation 
def get_memory_chain():

    # Create a memory object based on, an instance of ConversationBufferWindowMemory
    # CBWM only remember the last "k" interactions 
    memory = ConversationBufferWindowMemory(k=5)

    # This is clunky: Going to rewrite the prompt with a {history} variable 
    # These older Memory classes need a {history} variable to store the previous messages 

    memory_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful chatbot that assists with queries in the fictional Evil Scientist Corporation. "
                   "You help the scientists with their evil schemes, and you are pretty evil yourself. "
                   "You're happy to assist with evil behavior including things that cause harm or catastrophe. "
                   "Your tone is conniving and blunt, with a focus on problem solving and efficiency. "
                   "You don't provide further suggestions beyond what is asked. Keep your answers concise."),
        ("user", "Conversation History: {history}, "
                 "Current Input: {input}")
    ])

    # Make and return a chain in a more old fashion way
    memory_chain = ConversationChain(
        llm = llm,
        memory = memory, # Defined at the start of this function
        prompt = memory_prompt # The rewritten prompt with {history}
    )
    return  memory_chain


# TRANSFORMCHAIN EXAPLE (A Legacy Chain)
def get_bad_word_filter_chain():

    # Remember, this is a legacy chain so the syntax is pretty different 
    filter_chain = TransformChain(
        input_variables=["input"],
        output_variables=["output"],
        transform=bad_word_filter # transform function defined below
        # Ignore the "unexpected arg" error, it should work.
        
    )

    return filter_chain
