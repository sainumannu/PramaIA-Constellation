import json
from datetime import datetime
from backend.core.config import TOKEN_LOG_PATH # Importa il percorso del file di log da config

def log_interaction_tokens(
    user_id: str,
    prompt: str,
    answer: str,
    source: str,
    session_id: str,
    tokens: int
):
    """Logs the details of a user interaction and token usage."""
    TOKEN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True) # Assicura che la directory logs esista
    log_entry = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "answer": answer,
        "source": source,
        "session_id": session_id,
        "tokens": tokens,
    }
    with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")