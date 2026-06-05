# =============================================================================
# kernel.py
#
# Questo è il cuore operativo di Blisk-EL42: contiene la funzione principale
# blisk() che orchestra tutte le capacità del sistema:
#
#   1. Validazione dell'input
#   2. Prima risposta del modello (con memoria della conversazione)
#   3. Ricerca web (BEL42-TSS) se il modello lo ritiene necessario
#   4. Seconda risposta del modello (arricchita dai risultati della ricerca)
#   5. Esecuzione di codice (se il modello ha prodotto un blocco exec-code{})
#   6. Restituzione del risultato in formato testo o tensore PyTorch
#
# Flusso principale:
#   input utente → modello → [ricerca web → modello] → [esecuzione codice] → output
# =============================================================================


# --- Import interni al progetto ----------------------------------------------

# Chain LangChain con memoria persistente su database.
# Definita in chatmemory_models.py: unisce modello + prompt + cronologia DB.
from BEL42_Kernel.chatmemory_models import Blisk_EL42_DBMemoryHistory

# Funzioni per generare messaggi d'errore standardizzati:
#   getErrorMsg_ValueError_Empty    → parametro stringa vuoto
#   getErrorMsg_ValueError_NotOption → parametro con valore non ammesso
#   getErrorMsg_NoneValue           → parametro con valore None
from BEL42_TS.syserrors import (
    getErrorMsg_ValueError_Empty,
    getErrorMsg_ValueError_NotOption,
    getErrorMsg_NoneValue
)

# Componenti del motore di ricerca BEL42-TSS (Tool Strong Search):
#   TSS_Searcher   → classe che esegue la ricerca, calcola la similarità
#                    tramite BERT e seleziona i top 5 risultati
#   BEL42_TSSearch → funzione di alto livello che analizza l'output del modello,
#                    decide se serve una ricerca e la esegue
from BEL42_TS.TSearch_Strong import (
    TSS_Searcher,
    BEL42_TSSearch
)

# code_execution: analizza l'output del modello cercando blocchi "exec-code{...}"
# e, se li trova, esegue il codice in un sandbox RestrictedPython
from BEL42_SFS.code_execution import (
    code_execution
)

# get_default_reasoning_effort: legge il livello di ragionamento di default
# da settings.py (attualmente "medium")
from BEL42_UTILS import get_default_reasoning_effort

# Costanti di configurazione lette da settings.py:
#   BLISK_MODE_SEARCH_SUMMARY  → modalità ricerca di default ("summary")
#   BLISK_DEFAULT_CAN_MKF      → se il modello può creare file (False per ora)
#   SUMMARY_MODEL              → nome del modello usato per riassumere i risultati
#   BLISK_DEFAULT_OUTPUT_FORMAT → formato output di default ("text")
#   RESEARCH_ABILITY           → se la ricerca web è abilitata (True)
#   CODE_EXECUTION_ABILITY     → se l'esecuzione di codice è abilitata (True)
from settings import (
    BLISK_MODE_SEARCH_SUMMARY,
    BLISK_DEFAULT_CAN_MKF,
    SUMMARY_MODEL,
    BLISK_DEFAULT_OUTPUT_FORMAT,
    RESEARCH_ABILITY,
    CODE_EXECUTION_ABILITY
)

# tokenize_blisk_output: converte una stringa di testo in un tensore PyTorch
# (vettore numerico) tramite il tokenizer BERT. Serve quando output_format="pt".
from BEL42_UTILS.output_format import tokenize_blisk_output

# torch: libreria per il calcolo con tensori, necessaria per il tipo di ritorno
# della funzione blisk() quando output_format="pt"
import torch


# Leggiamo il livello di ragionamento di default UNA VOLTA a livello di modulo,
# così non viene riletto da settings ad ogni chiamata di blisk()
default_reasoning_effort = get_default_reasoning_effort()


# =============================================================================
# Funzione principale
# =============================================================================
def blisk(
            binput: str = "",
            reasoning_effort: str = default_reasoning_effort,
            blisk_mode_search: str = BLISK_MODE_SEARCH_SUMMARY,
            blisk_can_mkf: bool = BLISK_DEFAULT_CAN_MKF,
            summary_modeln: str = SUMMARY_MODEL,
            output_format: str = BLISK_DEFAULT_OUTPUT_FORMAT,
            research_ability: bool = RESEARCH_ABILITY,
            session_id: str = "",
            execution_code_ability: bool = CODE_EXECUTION_ABILITY
        ) -> str | torch.Tensor:
    """
    Funzione principale di Blisk-EL42. Genera una risposta all'input dell'utente.

    Parametri
    ---------
    binput : str
        Il messaggio dell'utente. Non può essere vuoto.

    reasoning_effort : str
        Livello di ragionamento del modello: "low", "medium", o "high".
        Influenza la profondità dell'analisi nel summary della ricerca.
        Default: "medium" (da settings.py).

    blisk_mode_search : str
        Modalità di presentazione dei risultati di ricerca al modello:
          "summary" → il modello di summary riassume i risultati prima
                      di passarli al modello principale
          "direct"  → i risultati grezzi vengono passati direttamente
        Default: "summary".

    blisk_can_mkf : bool
        Se True, il modello può creare file. Attualmente disabilitato
        perché la funzione di creazione file è ancora rudimentale.
        Default: False.

    summary_modeln : str
        Nome del modello usato per il riassunto dei risultati di ricerca.
        Default: valore di SUMMARY_MODEL in settings.py.

    output_format : str
        Formato dell'output restituito:
          "text" → stringa di testo normale
          "pt"   → tensore PyTorch (vettore di embedding BERT)
        Default: "text".

    research_ability : bool
        Se True, il sistema può fare ricerche web tramite BEL42-TSS.
        Default: True.

    session_id : str
        Identificatore univoco della conversazione. Usato per recuperare
        e salvare la cronologia nel database. Non può essere vuoto.
        Deve includere l'identità dell'utente, es. "user_42_conv_001".

    execution_code_ability : bool
        Se True, il sistema può eseguire codice Python in sandbox
        RestrictedPython se il modello produce un blocco exec-code{}.
        Default: True.

    Ritorna
    -------
    str | torch.Tensor
        La risposta del modello come stringa (output_format="text")
        o come tensore PyTorch (output_format="pt").
    """

    # -------------------------------------------------------------------------
    # Blocco 1 — Validazione degli input
    # -------------------------------------------------------------------------

    # binput vuoto: non ha senso invocare il modello senza un messaggio
    if not binput:
        errmsg = getErrorMsg_ValueError_Empty(
            functionName="blisk", parameter="binput", parameterType="string"
        )
        raise ValueError(errmsg)

    # session_id vuoto: senza di esso non possiamo recuperare né salvare
    # la cronologia nel database — la memoria non funzionerebbe
    if not session_id:
        errmsg = getErrorMsg_ValueError_Empty(
            functionName="blisk", parameter="session_id", parameterType="string"
        )
        raise ValueError(errmsg)

    # output_format accetta solo "pt" o "text": qualsiasi altro valore
    # causerebbe un comportamento non definito nel blocco di return finale
    if output_format != "pt" and output_format != "text":
        errmsg = getErrorMsg_ValueError_NotOption(
            "blisk", "output_format", "string",
            ["pt", "text"]
        )
        raise ValueError(errmsg)

    # -------------------------------------------------------------------------
    # Blocco 2 — Prima chiamata al modello
    # -------------------------------------------------------------------------

    # config è il dizionario che LangChain usa per identificare la sessione.
    # RunnableWithMessageHistory legge session_id da config["configurable"]
    # e lo passa a get_session_history() per recuperare la cronologia corretta.
    config = {"configurable": {"session_id": session_id}}

    # Prima invocazione: il modello riceve la cronologia completa + binput
    # e genera la sua prima risposta. Questa risposta può contenere:
    #   - una risposta diretta all'utente, oppure
    #   - un tag di ricerca: [% SEARCH | query %]  (definito in system_prompt.txt)
    # .content estrae solo il testo dalla risposta (scartando metadata, token usage, ecc.)
    response = Blisk_EL42_DBMemoryHistory.invoke(
        input=binput, config=config
    ).content

    # -------------------------------------------------------------------------
    # Blocco 3 — Ricerca web (BEL42-TSS)
    # -------------------------------------------------------------------------
    if research_ability:
        # BEL42_TSSearch analizza la risposta del modello cercando il tag
        # [% SEARCH | query %]. Se lo trova, esegue la ricerca tramite DuckDuckGo,
        # usa BERT per calcolare la similarità semantica tra i risultati e la query,
        # seleziona i top 5 risultati e (in modalità summary) li riassume.
        # Se NON trova il tag, restituisce None → il modello ha risposto direttamente.
        research_result = BEL42_TSSearch(
            modelmsg=response,
            reasoning_effort=reasoning_effort,
            output=blisk_mode_search,
            summary_modeln=summary_modeln
        )

        if research_result is None:
            # Il modello non ha richiesto una ricerca: la risposta è già completa.
            # Restituiamo subito senza una seconda invocazione.
            if output_format == "text":
                return response
            if output_format == "pt":
                return tokenize_blisk_output(response)

        # Il modello ha richiesto una ricerca e abbiamo i risultati.
        # Costruiamo un nuovo messaggio che istruisce il modello a usare
        # i dati della ricerca per formulare la risposta finale all'utente.
        result = f"now answer to the user with this data: {research_result}"

        # Seconda invocazione: il modello riceve i risultati della ricerca
        # e genera la risposta finale, arricchita di informazioni aggiornate.
        # Anche questo messaggio viene salvato nella cronologia del DB.
        final = Blisk_EL42_DBMemoryHistory.invoke(
            input=result, config=config
        ).content

        if output_format == "text":
            return final
        if output_format == "pt":
            return tokenize_blisk_output(final)

    # -------------------------------------------------------------------------
    # Blocco 4 — Creazione di file (non ancora attiva)
    # -------------------------------------------------------------------------
    if blisk_can_mkf:
        # La funzione di creazione file è ancora troppo rudimentale per l'uso
        # in produzione. Il blocco è disabilitato (pass) per sicurezza.
        # Quando verrà riabilitata, il flusso sarà:
        #   analizeModel_OSFS_AndExec(modelmsg=response)  → analizza e crea il file
        #   seconda invocazione → conferma al modello che il file è stato creato
        pass
        #analizeModel_OSFS_AndExec(modelmsg=response)
        #final = Blisk_EL42_DBMemoryHistory.invoke(
            #input="FILE CREATED SUCCESSIFULLY; now continue with the user", config=config
        #).content
        #if output_format == "text":
            #return final
        #if output_format == "pt":
            #return tokenize_blisk_output(final)

    # -------------------------------------------------------------------------
    # Blocco 5 — Esecuzione di codice
    # -------------------------------------------------------------------------
    if execution_code_ability:
        # code_execution cerca nel testo di binput un blocco nella forma:
        #   exec-code{ <codice python> }
        # Se lo trova, esegue il codice nel sandbox RestrictedPython
        # (moduli pericolosi come os, subprocess, ecc. sono bloccati).
        # Se non lo trova, non fa nulla e ritorna senza errori.
        # NOTA: si passa binput (input utente), non response (output modello),
        # perché è l'utente a poter richiedere l'esecuzione di codice.
        code_execution(
            binput=binput
        )

    # -------------------------------------------------------------------------
    # Blocco 6 — Restituzione del risultato
    # -------------------------------------------------------------------------
    # Raggiungiamo questo punto solo se research_ability è False oppure
    # se la ricerca era abilitata ma non è stata eseguita (research_result=None
    # viene gestito prima con un return anticipato).
    # Restituiamo la prima risposta del modello nel formato richiesto.
    if output_format == "text":
        return response

    if output_format == "pt":
        # tokenize_blisk_output converte la stringa in un tensore di embedding
        # BERT: un vettore numerico che rappresenta il significato semantico
        # della risposta. Utile per elaborazioni successive con PyTorch.
        return tokenize_blisk_output(response)
