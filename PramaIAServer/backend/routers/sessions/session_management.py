from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Optional
from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session
from backend.auth.dependencies import get_current_user
from backend.schemas.user_schemas import UserInToken
from backend.core.config import TOKEN_LOG_PATH
from backend.db.database import get_db
from backend.db.models import ChatSession

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/new", response_model=dict)
def create_new_session(user: UserInToken = Depends(get_current_user)):
    """
    Crea una nuova sessione (notebook) vuota.
    """
    session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + str(hash(user.user_id))[-8:]
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "user_id": user.user_id,
        "role": user.role,
        "title": "Nuovo Notebook",
        "event": "session_created"
    }
    
    if not TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
            pass
            
    with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return {"session_id": session_id}

@router.get("/history")
def get_session_history(
    user: UserInToken = Depends(get_current_user),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    target_user: Optional[str] = None
):
    """
    Recupera la cronologia delle sessioni per l'utente.
    """
    logger.info(f"GET /sessions/history requested by user: {user.user_id} (role: {user.role})")
    
    if not TOKEN_LOG_PATH.exists():
        logger.info(f"File di log non trovato in {TOKEN_LOG_PATH}")
        return {}

    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    history = []
    for line in lines:
        try:
            entry = json.loads(line)
            timestamp = datetime.fromisoformat(entry["timestamp"])

            if from_date and timestamp < datetime.fromisoformat(from_date):
                continue
            if to_date and timestamp > datetime.fromisoformat(to_date):
                continue

            if user.role == "admin":
                if target_user and entry.get("user_id") != target_user:
                    continue
            else:
                if entry.get("user_id") != user.user_id:
                    continue

            history.append(entry)
        except Exception as e:
            logger.error(f"Errore parsing log: {e}", exc_info=True)

    sessions = {}
    for entry in history:
        sid = entry.get("session_id", "unknown")
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(entry)

    if user.role == "admin" and not target_user:
        enhanced_sessions = {}
        for session_id, entries in sessions.items():
            if session_id != "unknown":
                first_entry = entries[0] if entries else {}
                enhanced_sessions[session_id] = {
                    "entries": entries,
                    "owner": first_entry.get("user_id"),
                    "title": first_entry.get("title", "Notebook senza titolo"),
                    "created_at": first_entry.get("timestamp"),
                    "entry_count": len(entries)
                }
        return {"sessions": enhanced_sessions, "view_type": "admin_enhanced"}
    
    return sessions

@router.get("/{session_id}/status", response_model=dict)
async def get_session_status(
    session_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    Verifica lo stato di una sessione.
    """
    if not TOKEN_LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    session_exists = False
    for line in lines:
        try:
            entry = json.loads(line)
            if entry.get("session_id") == session_id:
                if user.role == "admin" or entry.get("user_id") == user.user_id:
                    session_exists = True
                    break
        except Exception:
            continue

    if not session_exists:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "ready", "session_id": session_id}

@router.delete("/{session_id}", response_model=dict)
async def delete_notebook(
    session_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    Elimina un notebook completo.
    """
    if not TOKEN_LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="No sessions found")
    
    all_entries = []
    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                all_entries.append(entry)
            except json.JSONDecodeError:
                continue
    
    remaining_entries = []
    deleted_count = 0
    access_denied = False
    
    for entry in all_entries:
        if entry.get("session_id") == session_id:
            entry_user_id = entry.get("user_id")
            
            if user.role == "admin" or entry_user_id == user.user_id:
                deleted_count += 1
            else:
                access_denied = True
                remaining_entries.append(entry)
        else:
            remaining_entries.append(entry)
    
    if access_denied:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this session"
        )
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
        for entry in remaining_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return {
        "message": f"Notebook '{session_id}' deleted successfully",
        "deleted_entries": deleted_count
    }
