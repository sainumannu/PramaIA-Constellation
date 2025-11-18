from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Optional
from datetime import datetime
import json
import logging
import os
from sqlalchemy.orm import Session
from backend.auth.dependencies import get_current_user
from backend.schemas.user_schemas import UserInToken
from backend.core.config import TOKEN_LOG_PATH, DATA_DIR
from backend.db.database import get_db
from backend.db.models import ChatSession
from backend.services import document_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/users/{user_id}/sessions")
def get_user_sessions_admin(
    user_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Ottiene tutte le sessioni di un utente.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    
    if not TOKEN_LOG_PATH.exists():
        return {"user_id": user_id, "sessions": []}
    
    user_sessions = {}
    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("user_id") == user_id:
                    session_id = entry.get("session_id", "unknown")
                    if session_id != "unknown":
                        if session_id not in user_sessions:
                            user_sessions[session_id] = []
                        user_sessions[session_id].append(entry)
            except Exception:
                continue
    
    sessions_list = []
    for session_id, entries in user_sessions.items():
        first = entries[0] if entries else {}
        sessions_list.append({
            "session_id": session_id,
            "title": first.get("title", "Notebook senza titolo"),
            "created_at": first.get("timestamp"),
            "prompt": first.get("system_prompt"),
            "message_count": len(entries)
        })
    
    return {
        "user_id": user_id,
        "sessions": sessions_list,
        "total_sessions": len(sessions_list)
    }

@router.get("/users/{user_id}/documents")
def get_user_documents_admin(
    user_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Ottiene tutti i documenti di un utente.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    
    all_documents = document_service.load_file_metadata("admin", "admin")
    user_documents = [doc for doc in all_documents if doc.get("owner") == user_id]
    
    return {
        "user_id": user_id,
        "documents": user_documents,
        "total_documents": len(user_documents)
    }

@router.delete("/users/{user_id}/sessions/{session_id}")
def delete_user_session_admin(
    user_id: str = Path(..., min_length=1),
    session_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Elimina una sessione di un utente.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    
    if not TOKEN_LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="Nessuna sessione")
    
    all_entries = []
    remaining_entries = []
    deleted_count = 0
    
    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if (entry.get("session_id") == session_id and 
                    entry.get("user_id") == user_id):
                    deleted_count += 1
                else:
                    remaining_entries.append(entry)
            except Exception:
                continue
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
        for entry in remaining_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return {
        "message": f"Sessione eliminata con successo",
        "deleted_entries": deleted_count
    }

@router.delete("/users/{user_id}/documents/{filename}")
def delete_user_document_admin(
    user_id: str = Path(..., min_length=1),
    filename: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Elimina un documento di un utente.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    
    doc_details = document_service.get_file_details(filename)
    if not doc_details:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    if doc_details.get("owner") != user_id:
        raise HTTPException(status_code=400, detail="Documento non dell'utente")
    
    try:
        file_path = DATA_DIR / filename
        if file_path.exists():
            os.remove(file_path)
        
        document_service.delete_file_metadata(filename)
        
        try:
            from backend.core.rag_engine import remove_pdf as rag_remove_pdf
            rag_remove_pdf(filename)
        except Exception as e:
            logger.warning(f"Failed to remove from RAG: {e}")
        
        return {
            "message": f"Documento eliminato con successo"
        }
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Errore eliminazione")
