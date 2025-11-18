import logging
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)

# Dizionario in-memory per memorizzare le istanze di ConversationBufferMemory per sessione.
# Chiave: session_id (str)
# Valore: ConversationBufferMemory
_session_memories = {}

def get_session_memory(session_id: str) -> ConversationBufferMemory:
    """
    Recupera o crea un'istanza di ConversationBufferMemory per un dato session_id.
    """
    if session_id not in _session_memories:
        logger.info(f"Creazione nuova memoria per session_id: {session_id}")
        _session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            # output_key='answer' # Aggiungere se necessario per la chain specifica
        )
    return _session_memories[session_id]

def clear_session_memory(session_id: str):
    """Funzione opzionale per pulire esplicitamente la memoria di una sessione."""
    if session_id in _session_memories:
        logger.info(f"Pulizia memoria per session_id: {session_id}")
        del _session_memories[session_id]