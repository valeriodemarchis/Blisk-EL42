from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from BEL42_TS import getErrorMsg_ValueError_Empty
#from BEL42_UTILS.BEL42_Json import BEL42_Json #valutare se eliminarlo
from BEL42_UTILS.setutils import get_system_prompt
from BEL42_UTILS.BEL42_Database import BEL42_Database #importa il nuovo file per il database

load_dotenv()

#jf = BEL42_Json( #funzione precedente per recuperare dati dai file json
#    _MainJsonValue={}, _JsonFileName="store.memory.json",
#    _gitignore_presence=False, _add_mjv_given=False
#)
#store = jf.get_data()
_db = BEL42_Database() #comando per recuperare dati dal database

def get_session_history(session_id: str = "") -> BaseChatMessageHistory:
    if not session_id:
        errmsg = getErrorMsg_ValueError_Empty("get_session_history", "session_id", "string")
        raise ValueError(errmsg)
    
#    if session_id not in store:# controlla se c'è una chat (non più necessario, perché get_history già lo fa)
#        store[session_id] = InMemoryChatMessageHistory()
#    return store[session_id] #restituisce la chat
    return _db.get_history(session_id) #restituisce la chat


model = ChatOpenAI(model=os.getenv("MODEL", "gpt-4o"))

prompt = ChatPromptTemplate.from_messages([
    ("system", get_system_prompt()),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])


chain = prompt | model 

Blisk_EL42_JsonMemoryHistory = RunnableWithMessageHistory( #valutare se rinominarlo, dato che facendolo dovrei anche cambiarlo in tutte le altre parti in cui compare, in ogni caso ora usiamo un database, non file json
    chain,
    get_session_history,
    input_messages_key="input",
    history_message_key="history"
)


