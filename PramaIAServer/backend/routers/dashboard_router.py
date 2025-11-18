from fastapi import APIRouter, Depends
import json
import logging # Importa il modulo logging

from backend.core.config import DATA_INDEX_PATH, TOKEN_LOG_PATH # Importa i percorsi da config
from backend.auth.dependencies import get_current_admin_user # Per proteggere l'endpoint (non importare User da qui)
from backend.schemas.user_schemas import UserInToken # Per il type hinting dell'utente autenticato

router = APIRouter()
logger = logging.getLogger(__name__) # Configura un logger

@router.get("/summary") # Rimosso /dashboard dal prefisso della route, dato che il router avrà /dashboard
async def dashboard_summary(_: UserInToken = Depends(get_current_admin_user)): # Proteggi l'endpoint
    """
    Fornisce un riepilogo del numero di documenti e dei token utilizzati per utente.
    Richiede privilegi di amministratore.
    """
    summary = {}

    # Carica documenti
    if DATA_INDEX_PATH.exists():
        with open(DATA_INDEX_PATH, "r", encoding="utf-8") as f:
            entries = json.load(f)
            for entry in entries:
                user = entry["owner"]
                summary.setdefault(user, {"documents": 0, "tokens": 0})
                summary[user]["documents"] += 1
    # Carica token
    if TOKEN_LOG_PATH.exists(): # Assicurati che sia il file di log corretto
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    user = entry["user_id"]
                    summary.setdefault(user, {"documents": 0, "tokens": 0})
                    summary[user]["tokens"] += entry.get("tokens", 0)
                except Exception as e:
                    logger.error(f"Errore durante il parsing di una riga del log dei token: {e} - Riga: {line.strip()}", exc_info=True)

    return summary
