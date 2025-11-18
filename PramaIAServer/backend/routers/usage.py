from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
import json
import logging

from backend.core.config import TOKEN_LOG_PATH # Importa il percorso del file di log
from backend.auth.dependencies import get_current_user, get_current_admin_user # Non importare User da qui
from backend.schemas.user_schemas import UserInToken # Per il type hinting dell'utente autenticato

# Crea un'istanza di APIRouter
# Puoi specificare un prefix e dei tags che verranno applicati a tutte le route in questo router
usage_router = APIRouter(
    # prefix="/usage", # Il prefisso è già gestito in main.py
    tags=["Usage"],   # Raggruppa queste API sotto "Usage" nella documentazione Swagger/OpenAPI
)

logger = logging.getLogger(__name__)

# Un modello Pydantic per i dati di esempio (opzionale, ma buona pratica)
class UsageStats(BaseModel):
    user_id: str
    tokens_used: int

@usage_router.get("/{user_id}", response_model=UsageStats) # type: ignore
async def get_user_usage(user_id: str, current_user: UserInToken = Depends(get_current_user)):
    """
    Recupera i token totali utilizzati da un utente specifico.
    Gli amministratori possono visualizzare l'utilizzo di qualsiasi utente.
    Gli utenti normali possono visualizzare solo il proprio utilizzo.
    """
    if current_user.role != "admin" and current_user.user_id != user_id:
        logger.warning(f"User '{current_user.user_id}' (role: {current_user.role}) attempted to access usage data for user '{user_id}'. Access denied.")
        raise HTTPException(status_code=403, detail="Not authorized to access this user's usage data.")

    total_tokens = 0
    user_found = False
    if TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("user_id") == user_id:
                        user_found = True
                        total_tokens += entry.get("tokens", 0)
                except json.JSONDecodeError:
                    logger.error(f"Errore durante il parsing di una riga del log dei token: {line.strip()}", exc_info=True)
                except Exception as e: # Cattura altre eccezioni impreviste per riga
                    logger.error(f"Errore imprevisto durante l'elaborazione della riga del log: {line.strip()} - {e}", exc_info=True)
    
    if not user_found and total_tokens == 0: # Se l'utente non è mai apparso nei log
        raise HTTPException(status_code=404, detail=f"Usage data not found for user '{user_id}'.")
        
    return UsageStats(user_id=user_id, tokens_used=total_tokens)

@usage_router.get("/all/", response_model=List[UsageStats])
async def get_all_users_usage(_: UserInToken = Depends(get_current_admin_user)):
    logger.info("Richiesta ricevuta per /usage/all/") # <-- LOG DI DEBUG
    """
    Recupera i token totali utilizzati da tutti gli utenti.
    Richiede privilegi di amministratore.
    """
    usage_summary: Dict[str, int] = {}
    if TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    uid = entry.get("user_id")
                    tokens = entry.get("tokens", 0)
                    if uid and tokens > 0: # Considera solo entry con user_id e tokens
                        usage_summary[uid] = usage_summary.get(uid, 0) + tokens
                except json.JSONDecodeError:
                    logger.error(f"Errore durante il parsing di una riga del log dei token: {line.strip()}", exc_info=True)
                except Exception as e:
                    logger.error(f"Errore imprevisto durante l'elaborazione della riga del log: {line.strip()} - {e}", exc_info=True)

    if not usage_summary:
        return []
        
    return [UsageStats(user_id=uid, tokens_used=total) for uid, total in usage_summary.items()]