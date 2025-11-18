from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
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
from backend.services import document_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{session_id}/sources")
def get_session_sources(
    session_id: str = Path(..., min_length=1), 
    user: UserInToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restituisce i documenti collegati a una sessione.
    """
    logger.info(f"Getting sources for session {session_id} by user {user.user_id}")
    
    db_session = db.query(ChatSession).filter_by(session_id=session_id).first()
    session_owner = None
    session_found = False
    
    if db_session:
        session_found = True
        session_owner = db_session.user_id
    elif TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("session_id") == session_id:
                        session_found = True
                        if session_owner is None:
                            session_owner = entry.get("user_id")
                        break
                except Exception:
                    continue
    
    if not session_found:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    if user.role != "admin" and session_owner != user.user_id:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    session_documents = []
    if TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if (entry.get("session_id") == session_id and 
                        entry.get("event") == "document_linked"):
                        doc_info = {
                            "filename": entry.get("document_filename"),
                            "linked_at": entry.get("timestamp"),
                            "linked_by": entry.get("user_id")
                        }
                        if doc_info not in session_documents:
                            is_unlinked = False
                            linked_timestamp = datetime.fromisoformat(entry.get("timestamp"))
                            
                            with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f2:
                                for line2 in f2:
                                    try:
                                        entry2 = json.loads(line2)
                                        if (entry2.get("session_id") == session_id and 
                                            entry2.get("event") == "document_unlinked" and
                                            entry2.get("document_filename") == entry.get("document_filename")):
                                            unlink_timestamp = datetime.fromisoformat(entry2.get("timestamp"))
                                            if unlink_timestamp > linked_timestamp:
                                                is_unlinked = True
                                                break
                                    except Exception:
                                        continue
                            
                            if not is_unlinked:
                                session_documents.append(doc_info)
                except Exception:
                    continue
    
    return session_documents

@router.post("/{session_id}/sources")
def link_documents_to_session(
    session_id: str = Path(..., min_length=1), 
    request_data: dict = Body(...), 
    user: UserInToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Collega documenti a una sessione.
    """
    filename = request_data.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Nome file mancante")
    
    session_owner = None
    session_found = False
    
    db_session = db.query(ChatSession).filter_by(session_id=session_id).first()
    if db_session:
        session_found = True
        session_owner = db_session.user_id
    elif TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("session_id") == session_id:
                        session_found = True
                        if session_owner is None:
                            session_owner = entry.get("user_id")
                        break
                except Exception:
                    continue
    
    if not session_found:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    if user.role != "admin" and session_owner != user.user_id:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    doc_details = document_service.get_file_details(filename)
    if not doc_details:
        raise HTTPException(status_code=404, detail=f"Documento non trovato")
    
    is_doc_visible = (user.role == "admin" or 
                     doc_details.get("is_public", False) or 
                     doc_details.get("owner") == user.user_id)
    
    if not is_doc_visible:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    log_entry = {
        "event": "document_linked",
        "session_id": session_id,
        "document_filename": filename,
        "user_id": user.user_id,
        "role": user.role,
        "timestamp": datetime.utcnow().isoformat(),
        "session_owner": session_owner
    }
    
    with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return {"message": "Documento collegato con successo", "linked_document": filename}

@router.delete("/{session_id}/sources/{filename}")
def unlink_document_from_session(
    session_id: str = Path(..., min_length=1),
    filename: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Scollega un documento da una sessione.
    """
    session_owner = None
    session_found = False
    
    db_session = db.query(ChatSession).filter_by(session_id=session_id).first()
    if db_session:
        session_found = True
        session_owner = db_session.user_id
    elif TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("session_id") == session_id:
                        session_found = True
                        if session_owner is None:
                            session_owner = entry.get("user_id")
                        break
                except Exception:
                    continue
    
    if not session_found:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    if user.role != "admin" and session_owner != user.user_id:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    log_entry = {
        "event": "document_unlinked",
        "session_id": session_id,
        "document_filename": filename,
        "user_id": user.user_id,
        "role": user.role,
        "timestamp": datetime.utcnow().isoformat(),
        "session_owner": session_owner
    }
    
    with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return {"message": "Documento scollegato", "unlinked_document": filename}
