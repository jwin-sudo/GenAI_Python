from langchain_classic.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from typing import Dict, List, Any
import asyncio

# simple in-memory session store for message history
_sessions_store: Dict[str, List[Any]] = {}

# Adapter: RunnableWithMessageHistory expects a "message history" object
# that implements both sync and async accessors (get_messages / aget_messages)
class SimpleMessageHistory:
    def __init__(self, session_id: str, store: Dict[str, List[Any]]):
        self._session_id = session_id
        self._store = store

    def get_messages(self) -> List[str]:
        # return stored messages as a list of readable strings
        return list(self._store.get(self._session_id, []))

    async def aget_messages(self) -> List[str]:
        return self.get_messages()

    def set_messages(self, messages: List[Any]) -> None:
        # accept either list[str] or list[message-objects]
        normalized: List[str] = []
        for m in messages:
            if isinstance(m, str):
                normalized.append(m)
            else:
                content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)
                role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
                if content is None:
                    normalized.append(str(m))
                else:
                    normalized.append(f"{role + ': ' if role else ''}{content}")
        self._store[self._session_id] = normalized

    async def aset_messages(self, messages: List[Any]) -> None:
        self.set_messages(messages)

    # Append multiple messages (sync)
    def add_messages(self, messages: List[Any]) -> None:
        current = self._store.get(self._session_id, [])
        # normalize incoming message objects to strings
        for m in messages:
            if isinstance(m, str):
                current.append(m)
            else:
                content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)
                role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
                if content is None:
                    current.append(str(m))
                else:
                    current.append(f"{role + ': ' if role else ''}{content}")
        self._store[self._session_id] = list(current)

    async def aadd_messages(self, messages: List[Any]) -> None:
        self.add_messages(messages)

    def add_message(self, message: Any) -> None:
        self.add_messages([message])

    async def aadd_message(self, message: Any) -> None:
        self.add_message(message)

def _get_session_history(session_id: str) -> SimpleMessageHistory:
    # return a history adapter object (not a raw list)
    return SimpleMessageHistory(session_id, _sessions_store)

def _save_session_history(session_id: str, history_obj: Any) -> None:
    # history_obj may be a SimpleMessageHistory or similar object;
    # prefer sync get_messages to avoid creating event loop issues.
    if hasattr(history_obj, "get_messages"):
        msgs = history_obj.get_messages()
    elif hasattr(history_obj, "aget_messages"):
        # fallback: try to run the async accessor if sync one doesn't exist
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # running inside async loop - create task to retrieve messages (shouldn't generally happen)
            msgs = loop.run_until_complete(history_obj.aget_messages())
        else:
            msgs = loop.run_until_complete(history_obj.aget_messages())
    else:
        # last resort: treat as plain iterable
        msgs = list(history_obj)

    _sessions_store[session_id] = list(msgs)

def get_session_messages(session_id: str) -> List[str]:
    """
    Return the normalized messages for a session as stored by our SimpleMessageHistory.
    """
    hist = _get_session_history(session_id)
    if hasattr(hist, "get_messages"):
        return hist.get_messages()
    # fallback
    return list(_sessions_store.get(session_id, []))

llm = ChatOllama(
    model="llama3.2:3b", # The model we're using (we installed llama3.2:3b)
    temperature=0.2 # Temp goes from 0-1. Higher temp = more creativity
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert in the US stock market. "
                   "You help investor making wise decision. You are quite profitable yourself. "
                   "You like to encourage others to start investing to gain financial freedom. "
                   "Your tone is straight forward and blunt. You want people to succeed. "
                   "You only provide useful, short, and concise answers"),
    ("user", "{input}")
])

def get_general_chain():
    chain = prompt | llm 
    return chain 

# A chain that is better equipped to remember the conversation (memory)
def get_memory_chain():
    # Create a memory object, an instance of ConversationBufferWindowMemory
    memory = ConversationBufferWindowMemory(k=20)

    # maybe a summary memory is better? I don't like losing older interactions
    # It SUMMARIZES the chat history instead of dropping older interactions entirely
    #memory = ConversationSummaryMemory(llm=llm)

    # This is clunky: Going to rewrite the prompt with a {history} variable
    # These older Memory classes need a {history} variable to store the previous messages
    memory_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert in the US stock market. "
                   "You help investor making wise decision. You are quite profitable yourself. "
                   "You like to encourage others to start investing to gain financial freedom. "
                   "Your tone is straight forward and blunt. You want people to succeed. "
                   "You only provide useful, short, and concise answers"),
        ("user", "Conversation History: {history}, "
                 "Current Input: {input}")
    ])

    # Build a runnable pipeline
    # RunnableWithMessageHistory will format the prompt (using `prompt=memory_prompt`)
    # so the core runnable should be the LLM (not prompt|llm). If you pass prompt|llm
    # the prompt will receive a raw list (history) and raise the mapping/type error.
    core_runnable = llm

    # pass the required get/save session-history callables
    memory_chain = RunnableWithMessageHistory(
        runnable = core_runnable,
        get_session_history = _get_session_history,
        save_session_history = _save_session_history,
        prompt=memory_prompt,
    )

    return memory_chain