# =============================================================================
# BEL42_Database.py
#
# Questo file gestisce tutta la logica di accesso al database per la
# cronologia delle chat. È composto da tre classi:
#
#   _ChatMessageRecord  → descrive la struttura della tabella nel database
#   BEL42_SQLChatHistory → legge e scrive messaggi per una singola sessione
#   BEL42_Database       → gestisce la connessione e fornisce l'accesso
#
# L'isolamento tra utenti si basa sul session_id: ogni utente deve usare
# un session_id che includa la propria identità, es. "user_42_conv_001".
# Il database non conosce il concetto di "utente" — conosce solo session_id.
# =============================================================================

import os    # per os.getenv() — legge DATABASE_URL dal file .env
import json  # per json.dumps() e json.loads() — serializza i messaggi LangChain

# --- Import da SQLAlchemy ----------------------------------------------------
# SQLAlchemy è l'ORM (Object-Relational Mapper) che usiamo per interagire
# col database scrivendo Python invece di SQL puro.

# create_engine   : crea il pool di connessioni al database partendo dalla
#                   connection string (es. "sqlite:///chat_memory.db")
# Column          : rappresenta una colonna nella definizione di una tabella
# String          : tipo colonna → VARCHAR(n)  — testo a lunghezza limitata
# Text            : tipo colonna → TEXT        — testo a lunghezza illimitata
# Integer         : tipo colonna → INTEGER     — numero intero
# DateTime        : tipo colonna → DATETIME    — data e ora
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime

# declarative_base : crea la classe Base da cui ereditano tutte le tabelle.
#                    Base tiene un registro interno di tutte le sue sottoclassi:
#                    Base.metadata.create_all() usa questo registro per creare
#                    le tabelle nel database.
# sessionmaker     : crea una "fabbrica" di sessioni. Una sessione è un'unità
#                    di lavoro: raggruppa operazioni e le invia al DB con commit().
from sqlalchemy.orm import declarative_base, sessionmaker

# func : funzioni SQL speciali. Qui usiamo func.now() per far sì che il DB
#        inserisca automaticamente il timestamp corrente in created_at.
from sqlalchemy.sql import func

# --- Import da LangChain -----------------------------------------------------

# BaseChatMessageHistory : interfaccia astratta di LangChain per la memoria.
#                          Definisce i metodi che ogni sistema di memoria deve avere.
#                          La nostra classe BEL42_SQLChatHistory la implementa.
from langchain_core.chat_history import BaseChatMessageHistory

# BaseMessage       : classe base di tutti i tipi di messaggio LangChain
#                     (HumanMessage, AIMessage, SystemMessage, ecc.)
# messages_to_dict  : converte List[BaseMessage] → List[dict]
#                     necessario per salvare i messaggi come JSON nel DB
# messages_from_dict: converte List[dict] → List[BaseMessage]
#                     necessario per ricostruire i messaggi letti dal DB
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict


# =============================================================================
# ORM Base
# =============================================================================
# declarative_base() crea la classe Base: il "registro" centrale di SQLAlchemy.
# Ogni classe che eredita da Base viene automaticamente registrata come tabella.
# Senza questo, Base.metadata.create_all() non saprebbe quali tabelle creare.
Base = declarative_base()


# =============================================================================
# Definizione della tabella
# =============================================================================
class _ChatMessageRecord(Base):
    """
    Rappresenta la tabella 'chat_messages' nel database.
    Il prefisso _ indica che questa classe è privata: usata solo in questo file.

    Ogni istanza di questa classe corrisponde a UNA RIGA della tabella,
    cioè a UN singolo messaggio (umano o AI) di una conversazione.

    Un'intera conversazione è l'insieme di tutte le righe con lo stesso session_id,
    ordinate per id crescente (= ordine cronologico).

    Struttura della tabella
    -----------------------
    | id | session_id          | message              | created_at          |
    |----|---------------------|----------------------|---------------------|
    |  1 | user_42_conv_001    | {"type":"human",...} | 2026-05-30 10:00:00 |
    |  2 | user_42_conv_001    | {"type":"ai",...}    | 2026-05-30 10:00:01 |
    |  3 | user_99_conv_001    | {"type":"human",...} | 2026-05-30 11:00:00 |
    """

    # __tablename__ è un attributo speciale riconosciuto da SQLAlchemy:
    # specifica il nome fisico della tabella nel database.
    __tablename__ = "chat_messages"

    # Chiave primaria: identificatore unico di ogni riga.
    # autoincrement=True → il DB assegna il valore automaticamente (1, 2, 3, …).
    # Serve anche per mantenere l'ordine cronologico dei messaggi.
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identifica la conversazione a cui appartiene questo messaggio.
    # nullable=False → campo obbligatorio, il DB rifiuta inserimenti senza di esso.
    # index=True → crea un indice su questa colonna, rendendo molto più veloci
    #              le query "WHERE session_id = ..." (che eseguiamo ad ogni lettura).
    # String(255) → lunghezza massima 255 caratteri, sufficiente per qualsiasi ID.
    session_id = Column(String(255), nullable=False, index=True)

    # Il messaggio LangChain serializzato in formato JSON.
    # Usiamo Text (lunghezza illimitata) perché i messaggi possono essere molto lunghi.
    # Esempio di valore: '{"type": "human", "data": {"content": "Ciao!", ...}}'
    message = Column(Text, nullable=False)

    # Timestamp di inserimento gestito direttamente dal database.
    # server_default=func.now() → il DB inserisce il timestamp corrente
    # automaticamente, senza che Python debba passarlo esplicitamente.
    created_at = Column(DateTime, server_default=func.now())


# =============================================================================
# Implementazione della memoria per una singola sessione
# =============================================================================
class BEL42_SQLChatHistory(BaseChatMessageHistory):
    """
    Implementa l'interfaccia BaseChatMessageHistory di LangChain usando il database.

    LangChain chiama automaticamente questi metodi durante ogni invocazione:
      - .messages     → prima di generare la risposta, per leggere la cronologia
      - .add_message() → dopo aver generato la risposta, per salvare i messaggi
      - .clear()       → quando si vuole cancellare la storia di una sessione

    Non viene mai istanziata direttamente dall'utente: è BEL42_Database
    a crearla tramite il metodo get_history().
    """

    def __init__(self, session_id: str, engine):
        # session_id: identifica la conversazione di cui questa istanza gestisce la storia
        self.session_id = session_id

        # engine: la connessione al database, condivisa tra tutte le istanze.
        # Passarla come parametro (invece di ricrearla ogni volta) è più efficiente.
        self.engine = engine

        # sessionmaker(engine) crea la "fabbrica" di sessioni per questo engine.
        # NOTA: in SQLAlchemy 2.0 il parametro si passa direttamente senza bind=.
        # Usare sessionmaker(bind=engine) causerebbe un TypeError in SQLAlchemy 2.0.
        # Ogni chiamata a self._Session() apre una nuova sessione indipendente:
        # questo è il pattern corretto in ambienti multi-thread.
        self._Session = sessionmaker(engine)

    # -------------------------------------------------------------------------
    # LETTURA — proprietà messages
    # -------------------------------------------------------------------------
    @property
    def messages(self) -> list[BaseMessage]:
        """
        Restituisce tutti i messaggi della sessione in ordine cronologico.

        @property trasforma questo metodo in un attributo: LangChain accede
        a .messages senza parentesi. Senza @property il codice non funzionerebbe
        perché LangChain si aspetta un attributo, non un metodo da chiamare.

        Equivale a: SELECT * FROM chat_messages
                    WHERE session_id = '...'
                    ORDER BY id ASC;
        """
        # "with self._Session() as session:" apre la sessione e la chiude
        # automaticamente alla fine del blocco, anche in caso di eccezione.
        # È equivalente a try/finally con session.close() nel finally.
        with self._Session() as session:
            records = (
                session.query(_ChatMessageRecord)
                # WHERE session_id = self.session_id
                .filter_by(session_id=self.session_id)
                # ORDER BY id ASC — garantisce l'ordine cronologico
                .order_by(_ChatMessageRecord.id)
                # esegue la query e restituisce una lista di oggetti _ChatMessageRecord
                .all()
            )

            # Ogni record.message è una stringa JSON (es. '{"type":"human",...}').
            # json.loads() la converte in un dizionario Python.
            # Questa è una list comprehension: equivale a un ciclo for che costruisce
            # una lista. Risultato: lista di dizionari Python.
            dicts = [json.loads(r.message) for r in records]

            # messages_from_dict converte la lista di dizionari in oggetti LangChain
            # (HumanMessage, AIMessage, ecc.) che il modello sa interpretare.
            return messages_from_dict(dicts)

    # -------------------------------------------------------------------------
    # SCRITTURA — aggiunge un messaggio
    # -------------------------------------------------------------------------
    def add_message(self, message: BaseMessage) -> None:
        """
        Salva un singolo messaggio nel database.

        Chiamato automaticamente da LangChain due volte dopo ogni risposta:
          1. con il messaggio dell'utente (HumanMessage)
          2. con la risposta del modello (AIMessage)

        Equivale a: INSERT INTO chat_messages (session_id, message)
                    VALUES ('...', '{"type":"human",...}');
        """
        # I messaggi LangChain non possono essere salvati direttamente nel DB.
        # messages_to_dict([message]) → lista con un solo dizionario Python.
        # Prendiamo [0] perché passiamo sempre un solo messaggio alla volta.
        # json.dumps() converte il dizionario in una stringa JSON salvabile nel DB.
        serialized = json.dumps(messages_to_dict([message])[0])

        with self._Session() as session:
            # Crea un nuovo oggetto-riga con i valori da inserire.
            # created_at non serve: il DB lo inserisce automaticamente (server_default).
            record = _ChatMessageRecord(
                session_id=self.session_id,
                message=serialized
            )

            # session.add() prepara l'INSERT in memoria (non lo esegue ancora).
            session.add(record)

            # session.commit() invia effettivamente l'operazione al database.
            # Senza commit, le modifiche verrebbero annullate alla chiusura
            # della sessione (fine del blocco with).
            session.commit()

    # -------------------------------------------------------------------------
    # RESET — cancella tutti i messaggi della sessione
    # -------------------------------------------------------------------------
    def clear(self) -> None:
        """
        Cancella tutta la cronologia della sessione corrente.

        Utile per "resettare" una conversazione senza eliminare l'intera sessione.
        Non cancella sessioni di altri utenti: il filtro WHERE session_id = '...'
        garantisce che si tocchino solo le righe di questa sessione.

        Equivale a: DELETE FROM chat_messages WHERE session_id = '...';
        """
        with self._Session() as session:
            (
                session.query(_ChatMessageRecord)
                # WHERE session_id = self.session_id — tocca SOLO questa sessione
                .filter_by(session_id=self.session_id)
                # delete() genera ed esegue il DELETE SQL
                .delete()
            )
            # Come in add_message, il commit è necessario per rendere
            # permanente la cancellazione.
            session.commit()


# =============================================================================
# Punto di accesso principale al database
# =============================================================================
class BEL42_Database:
    """
    Gestisce la connessione al database e fornisce l'accesso alla cronologia.

    È l'unica classe che chatmemory_models.py deve conoscere:
    tutto il resto (tabelle, sessioni SQLAlchemy, serializzazione) è incapsulato
    qui dentro e in BEL42_SQLChatHistory.

    Legge DATABASE_URL dal file .env. Se non è definita, usa SQLite locale.

    Esempi di DATABASE_URL nel file .env
    -------------------------------------
    # SQLite locale (zero configurazione, perfetto per sviluppo)
    DATABASE_URL=sqlite:///chat_memory.db

    # Supabase - piano Free: 500 MB PostgreSQL
    # -> https://supabase.com  (Settings > Database > Connection string > URI)
    DATABASE_URL=postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres

    # Neon - piano Free: 0.5 GB PostgreSQL serverless
    # -> https://neon.tech  (Dashboard > Connection string)
    DATABASE_URL=postgresql://<USER>:<PASSWORD>@<ENDPOINT>.neon.tech/neondb?sslmode=require

    Nota: per PostgreSQL installa il driver aggiuntivo con:
        pip install psycopg2-binary
    """

    def __init__(self, db_url: str = ""):
        # Se db_url non è passato esplicitamente, lo leggiamo dal .env.
        # Il secondo argomento di os.getenv è il valore di default: se DATABASE_URL
        # non esiste nel .env, usiamo SQLite locale invece di crashare.
        if not db_url:
            db_url = os.getenv("DATABASE_URL", "sqlite:///chat_memory.db")

        # SQLite ha una limitazione: di default permette l'accesso solo dal thread
        # che ha creato la connessione. LangChain può operare su thread diversi,
        # quindi disabilitiamo questo controllo con check_same_thread=False.
        # Per PostgreSQL (Supabase, Neon) questa limitazione non esiste,
        # quindi connect_args rimane un dizionario vuoto {}.
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

        # create_engine crea il pool di connessioni. Non apre una connessione
        # immediatamente: lo fa solo quando serve (lazy connection).
        self.engine = create_engine(db_url, connect_args=connect_args)

        # Crea la tabella 'chat_messages' nel database SE NON ESISTE GIÀ.
        # Questa operazione è idempotente: eseguirla più volte non causa problemi
        # e non cancella dati esistenti. Usa il registro di Base per sapere
        # quali tabelle creare (nel nostro caso, solo _ChatMessageRecord).
        Base.metadata.create_all(self.engine)

    def get_history(self, session_id: str) -> BEL42_SQLChatHistory:
        """
        Restituisce l'oggetto cronologia per la sessione indicata.

        Non legge nulla dal DB in questo momento: crea solo l'oggetto
        BEL42_SQLChatHistory che sa come leggere e scrivere per quella sessione.
        La lettura effettiva avviene solo quando LangChain accede a .messages.

        Parametri
        ---------
        session_id : str
            Identificatore della sessione, es. "user_42_conv_001".
            Deve includere l'identità dell'utente per garantire l'isolamento.
        """
        return BEL42_SQLChatHistory(session_id=session_id, engine=self.engine)
