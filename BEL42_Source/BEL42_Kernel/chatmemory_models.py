# =============================================================================
# chatmemory_models.py
#
# Questo file ha due responsabilità:
#   1. Definire come recuperare la cronologia di una sessione dal database
#   2. Costruire la chain LangChain che unisce modello + prompt + memoria
#
# La chain finale (Blisk_EL42_DBMemoryHistory) è quella che viene importata
# e usata da kernel.py per generare le risposte.
# =============================================================================


# --- Import da LangChain -----------------------------------------------------

# BaseChatMessageHistory: interfaccia astratta che ogni sistema di memoria
# deve implementare (la nostra implementazione concreta è in BEL42_Database.py)
from langchain_core.chat_history import BaseChatMessageHistory

# RunnableWithMessageHistory: wrapper che aggiunge la gestione della memoria
# a qualsiasi chain LangChain. Si occupa automaticamente di:
#   - leggere la cronologia prima di ogni invocazione
#   - salvare la nuova coppia domanda/risposta dopo ogni invocazione
from langchain_core.runnables.history import RunnableWithMessageHistory

# ChatPromptTemplate: costruisce il prompt strutturato che il modello riceverà.
# MessagesPlaceholder: segnaposto nel prompt dove verrà inserita la cronologia.
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ChatOpenAI: il wrapper LangChain per i modelli OpenAI (es. gpt-4o).
from langchain_openai import ChatOpenAI

# load_dotenv: legge il file .env e carica le variabili nell'ambiente del processo,
# rendendo disponibili MODEL, DATABASE_URL, OPENAI_API_KEY, ecc.
from dotenv import load_dotenv

# os: libreria standard per leggere variabili d'ambiente con os.getenv()
import os

# --- Import interni al progetto -----------------------------------------------

# Funzione di utilità per generare messaggi d'errore standardizzati
# quando un parametro stringa è vuoto
from BEL42_TS import getErrorMsg_ValueError_Empty

# BEL42_Database: la nostra classe che gestisce la connessione al database
# e restituisce la cronologia per ogni sessione (definita in BEL42_UTILS/BEL42_Database.py)
from BEL42_UTILS.BEL42_Database import BEL42_Database

# Funzione che legge il system prompt da Docs/system_prompt.txt
from BEL42_UTILS.setutils import get_system_prompt


# Carica le variabili dal file .env (deve essere chiamato prima di os.getenv)
load_dotenv()


# =============================================================================
# Connessione al database
# =============================================================================
# Creiamo UNA SOLA istanza di BEL42_Database per tutto il modulo.
# BEL42_Database legge DATABASE_URL dal .env e apre la connessione.
# Crearla a livello di modulo (fuori dalle funzioni) significa che la
# connessione viene aperta una volta sola all'avvio, non ad ogni chiamata.
# Il prefisso _ indica che è una variabile "privata" di questo modulo.
_db = BEL42_Database()


# =============================================================================
# Funzione richiesta da RunnableWithMessageHistory
# =============================================================================
def get_session_history(session_id: str = "") -> BaseChatMessageHistory:
    """
    Restituisce la cronologia della chat per la sessione indicata.

    Viene chiamata automaticamente da RunnableWithMessageHistory ad ogni
    invocazione della chain: prima di generare la risposta (per leggere
    la storia) e dopo (per salvare i nuovi messaggi).

    Il session_id dovrebbe includere l'identità dell'utente per garantire
    l'isolamento tra utenti diversi, ad esempio: "user_42_conv_001".

    Parametri
    ---------
    session_id : str
        Identificatore univoco della conversazione. Non può essere vuoto.

    Ritorna
    -------
    BaseChatMessageHistory
        Un oggetto BEL42_SQLChatHistory collegato alla sessione richiesta.
    """
    # Validazione: session_id vuoto causerebbe una query senza filtro,
    # restituendo messaggi di sessioni sbagliate o errori SQL
    if not session_id:
        errmsg = getErrorMsg_ValueError_Empty("get_session_history", "session_id", "string")
        raise ValueError(errmsg)

    # Delega al database la creazione dell'oggetto cronologia.
    # Non apre una nuova connessione: usa il pool già gestito da _db.engine.
    return _db.get_history(session_id)


# =============================================================================
# Modello
# =============================================================================
# Istanzia il modello OpenAI specificato in MODEL nel .env.
# Se MODEL non è definito nel .env, usa "gpt-4o" come valore di default.
# Il modello viene creato una volta sola a livello di modulo.
model = ChatOpenAI(model=os.getenv("MODEL", "gpt-4o"))


# =============================================================================
# Prompt
# =============================================================================
# Il prompt è la struttura del messaggio che viene inviata al modello ad ogni
# chiamata. È composto da tre parti nell'ordine:
#
#   1. ("system", ...) → istruzioni fisse per il comportamento del modello,
#                         lette da Docs/system_prompt.txt
#
#   2. MessagesPlaceholder("history") → qui LangChain inserisce automaticamente
#                                        tutta la cronologia della conversazione
#                                        (coppie domanda/risposta precedenti)
#
#   3. ("human", "{input}") → il messaggio attuale dell'utente.
#                              {input} è un segnaposto sostituito al momento
#                              dell'invocazione con il testo reale.
prompt = ChatPromptTemplate.from_messages([
    ("system", get_system_prompt()),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])


# =============================================================================
# Chain base (senza memoria)
# =============================================================================
# L'operatore | è il "pipe" di LangChain: collega prompt e model in sequenza.
# prompt | model significa: "passa l'output del prompt come input al modello".
# Questa chain da sola non ha memoria: ad ogni chiamata riceve solo il prompt
# dell'invocazione corrente, senza storico.
chain = prompt | model


# =============================================================================
# Chain finale con memoria persistente
# =============================================================================
# RunnableWithMessageHistory avvolge la chain base aggiungendo la gestione
# automatica della cronologia. Parametri:
#
#   chain               → la chain da avvolgere
#   get_session_history → funzione che restituisce la cronologia dato un session_id
#   input_messages_key  → nome della chiave che contiene il messaggio dell'utente
#                         nell'input passato a .invoke() — deve corrispondere
#                         al segnaposto {input} nel prompt
#   history_messages_key → nome della variabile nel prompt in cui inserire
#                          la cronologia — deve corrispondere a
#                          MessagesPlaceholder(variable_name="history")
#
# ATTENZIONE: history_messages_key usa "messages" al PLURALE.
# Il nome "history_message_key" (singolare) è sbagliato: LangChain lo ignora
# silenziosamente e il modello non riceve nessuna cronologia.
Blisk_EL42_DBMemoryHistory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
