from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from BEL42_TS import getErrorMsg_ValueError_Empty
from BEL42_UTILS import BEL42_Json
from BEL42_UTILS.setutils import get_system_prompt


load_dotenv()

jf = BEL42_Json(
    _MainJsonValue={}, _JsonFileName="store.memory.json",
    _gitignore_presence=False, add_mjv_given=True
)

store = jf.get_data()


def get_session_history(session_id: str = "") -> BaseChatMessageHistory:
    if not session_id:
        errmsg = getErrorMsg_ValueError_Empty("get_session_history", "session_id", "string")
        raise ValueError(errmsg)
    
    if session_id not in store:
        jf.set_value(session_id, InMemoryChatMessageHistory())

    return jf.get_value(session_id)


model = ChatOpenAI("gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", get_system_prompt()),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])


chain = prompt | model 

Blisk_EL42_JsonMemoryHistory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_message_key="history"
)
