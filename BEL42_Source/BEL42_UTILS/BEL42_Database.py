#appunto per me: devo finire di ricontrollare il codice
import os
import json #usata per convertire i messaggi LangChain in stringhe di testo per il database

# Importazioni da SQLAlchemy: (commento creato da Claude, quindi da ricontrollare)
# - create_engine   : Crea la connessione al database (legge la connection string)
# - Column          : Rappresenta una colonna nella tabella
# - String, Text,
#   Integer,
#   DateTime        : I tipi di dato delle colonne
# - declarative_base: Crea la classe base da cui ereditano le nostre tabelle
# - sessionmaker    : Crea una "fabbrica" di sessioni per fare query
# - func            : Funzioni SQL speciali, qui usata per func.now() (timestamp automatico)
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

# Importazioni da LangChain: (commento creato da Claude, quindi da ricontrollare)
# - BaseChatMessageHistory : Interfaccia astratta che ogni sistema di memoria deve implementare
# - BaseMessage            : Classe base di tutti i messaggi LangChain (HumanMessage, AIMessage, ecc.)
# - messages_to_dict       : Converte una lista di messaggi LangChain → lista di dizionari Python
# - messages_from_dict     : Fa il contrario: dizionari Python → messaggi LangChain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict


# ---------------------------------------------------------------------------
# ORM Base – tutte le classi-tabella ereditano da qui
# ---------------------------------------------------------------------------
Base = declarative_base()


class _ChatMessageRecord(Base):
    """
    Tabella 'chat_messages' nel database.

    Colonne
    -------
    id          : chiave primaria autoincrementante (intero)
    session_id  : identifica la sessione/conversazione (stringa, indicizzata)
    message     : il messaggio serializzato in JSON (testo)
    created_at  : timestamp automatico di inserimento
    """
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    message    = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Implementazione di BaseChatMessageHistory per il database
# ---------------------------------------------------------------------------
class BEL42_SQLChatHistory(BaseChatMessageHistory):
    """
    Implementazione personalizzata di BaseChatMessageHistory.

    LangChain richiede che qualunque history-provider abbia:
      • messages  → proprietà che restituisce List[BaseMessage]
      • add_message(msg) → aggiunge un messaggio al DB
      • clear()          → cancella tutta la storia della sessione

    I messaggi vengono serializzati in JSON prima di essere salvati
    (messages_to_dict) e deserializzati in lettura (messages_from_dict).
    """

    def __init__(self, session_id: str, engine):
        self.session_id = session_id
        self.engine     = engine
        self._Session   = sessionmaker(engine)   # SQLAlchemy 2.0: niente 'bind='

    # ------------------------------------------------------------------
    # Lettura: recupera tutti i messaggi della sessione, in ordine
    # ------------------------------------------------------------------
    @property
    def messages(self) -> list[BaseMessage]:
        with self._Session() as session:
            records = (
                session.query(_ChatMessageRecord)
                .filter_by(session_id=self.session_id)
                .order_by(_ChatMessageRecord.id)   # ordine cronologico
                .all()
            )
            # ogni record.message è una stringa JSON → convertiamo in dict
            dicts = [json.loads(r.message) for r in records]
            # poi da dict → oggetti BaseMessage (HumanMessage, AIMessage, …)
            return messages_from_dict(dicts)

    # ------------------------------------------------------------------
    # Scrittura: aggiunge un singolo messaggio al DB
    # ------------------------------------------------------------------
    def add_message(self, message: BaseMessage) -> None:
        # messages_to_dict([msg]) → lista con un dict → prendiamo [0]
        serialized = json.dumps(messages_to_dict([message])[0])
        with self._Session() as session:
            record = _ChatMessageRecord(
                session_id=self.session_id,
                message=serialized
            )
            session.add(record)
            session.commit()

    # ------------------------------------------------------------------
    # Reset: cancella tutti i messaggi di questa sessione
    # ------------------------------------------------------------------
    def clear(self) -> None:
        with self._Session() as session:
            (
                session.query(_ChatMessageRecord)
                .filter_by(session_id=self.session_id)
                .delete()
            )
            session.commit()


# ---------------------------------------------------------------------------
# Classe principale: gestisce la connessione e crea le tabelle
# ---------------------------------------------------------------------------
class BEL42_Database:
    """
    Punto di accesso unico al database.

    Legge DATABASE_URL dal file .env tramite python-dotenv.
    Se la variabile non è definita, usa SQLite locale come fallback sicuro.

    Esempi di DATABASE_URL nel file .env
    -------------------------------------
    # SQLite locale (zero configurazione, perfetto per sviluppo)
    DATABASE_URL=sqlite:///chat_memory.db

    # Supabase – piano Free: 500 MB PostgreSQL
    # → https://supabase.com  (Settings > Database > Connection string > URI)
    DATABASE_URL=postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres

    # Neon – piano Free: 0.5 GB PostgreSQL serverless
    # → https://neon.tech  (Dashboard > Connection string)
    DATABASE_URL=postgresql://<USER>:<PASSWORD>@<ENDPOINT>.neon.tech/neondb?sslmode=require

    Nota: per PostgreSQL installa il driver:
        pip install psycopg2-binary
    """

    def __init__(self, db_url: str = ""):
        if not db_url:
            db_url = os.getenv("DATABASE_URL", "sqlite:///chat_memory.db")

        # SQLite richiede check_same_thread=False per ambienti multi-thread
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

        self.engine = create_engine(db_url, connect_args=connect_args)

        # Crea la tabella 'chat_messages' se non esiste già
        # (operazione idempotente: sicura da chiamare ogni volta)
        Base.metadata.create_all(self.engine)

    def get_history(self, session_id: str) -> BEL42_SQLChatHistory:
        """
        Restituisce un'istanza di BEL42_SQLChatHistory per la sessione data.
        Equivale al vecchio  store[session_id] = InMemoryChatMessageHistory()
        ma legge/scrive sul database invece che in RAM.
        """
        return BEL42_SQLChatHistory(session_id=session_id, engine=self.engine)
