from fastapi import APIRouter, Depends, Query, HTTPException, status, Body, Path
from typing import Optional, List
from datetime import datetime
import json
import logging # Importa il modulo logging
from sqlalchemy.orm import Session
from backend.auth.dependencies import get_current_user
from backend.schemas.user_schemas import UserInToken # Importa il modello corretto per l'utente autenticato
from backend.core.config import TOKEN_LOG_PATH # Importa il percorso configurato
from backend.db.database import get_db
from backend.db.models import ChatSession

router = APIRouter()
logger = logging.getLogger(__name__) # Configura un logger per questo modulo

@router.get("/history")
def get_session_history(
    user: UserInToken = Depends(get_current_user),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    target_user: Optional[str] = Query(None, description="Solo per admin: filtra per utente specifico")
):
    logger.info(f"GET /sessions/history requested by user: {user.user_id} (role: {user.role})")
    
    if not TOKEN_LOG_PATH.exists():
        logger.info(f"File di log non trovato in {TOKEN_LOG_PATH}")
        return {}

    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    logger.info(f"Read {len(lines)} lines from token log file")

    history = []
    for line_num, line in enumerate(lines, 1):
        try:
            entry = json.loads(line)
            timestamp = datetime.fromisoformat(entry["timestamp"])

            if from_date and timestamp < datetime.fromisoformat(from_date):
                continue
            if to_date and timestamp > datetime.fromisoformat(to_date):
                continue

            # Filtro utente
            if user.role == "admin":
                if target_user and entry.get("user_id") != target_user:
                    continue
                # Admin può vedere tutto se non specifica target_user
            else:
                if entry.get("user_id") != user.user_id:
                    continue

            history.append(entry)
        except Exception as e:
            logger.error(f"Errore durante il parsing di una riga del log: {e} - Riga: {line.strip()}", exc_info=True)

    # Raggruppa per session_id
    sessions = {}
    for entry in history:
        sid = entry.get("session_id", "unknown")
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(entry)

    # Se è admin e non ha specificato target_user, aggiungi info sugli owner
    if user.role == "admin" and not target_user:
        enhanced_sessions = {}
        for session_id, entries in sessions.items():
            if session_id != "unknown":
                first_entry = entries[0] if entries else {}
                session_owner = first_entry.get("user_id")
                enhanced_sessions[session_id] = {
                    "entries": entries,
                    "owner": session_owner,
                    "title": first_entry.get("title", "Notebook senza titolo"),
                    "created_at": first_entry.get("timestamp"),
                    "entry_count": len(entries)
                }
        logger.info(f"Returning {len(enhanced_sessions)} sessions with owner info to admin {user.user_id}")
        return {"sessions": enhanced_sessions, "view_type": "admin_enhanced"}
    
    logger.info(f"Returning {len(sessions)} sessions to user {user.user_id}: {list(sessions.keys())}")
    return sessions

@router.delete("/delete_entries")
def delete_session_entries(
    message_ids_to_delete: List[str] = Body(...), # Aspetta una lista di stringhe nel corpo della richiesta
    current_user: UserInToken = Depends(get_current_user)
):
    logger.info(f"User {current_user.user_id} attempting to delete messages. IDs received: {message_ids_to_delete}")

    if not TOKEN_LOG_PATH.exists():
        logger.warning(f"Tentativo di eliminare messaggi ma il file di log non esiste: {TOKEN_LOG_PATH}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File di log non trovato.")

    kept_lines = []
    deleted_count = 0
    processed_lines = 0

    try:
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        logger.info(f"Read {len(lines)} lines from log file.")

        for i, line in enumerate(lines):
            processed_lines += 1
            try:
                entry = json.loads(line)
                entry_user_id = entry.get("user_id")
                entry_session_id = entry.get("session_id", "unknown")
                entry_timestamp = entry.get("timestamp")

                if not entry_timestamp: # Salta se il timestamp manca, non si può formare l'ID
                    logger.warning(f"Log line {i+1} missing timestamp: {line.strip()}")
                    kept_lines.append(line)
                    continue

                # Costruisci l'ID del messaggio come fa il frontend per il confronto
                message_id_from_log = f"{entry_session_id}___{entry_timestamp}"
                
                # Logging dettagliato per il confronto
                is_id_match = message_id_from_log in message_ids_to_delete
                is_user_match = entry_user_id == current_user.user_id
                
                logger.debug(
                    f"Line {i+1}: LogMsgID='{message_id_from_log}', EntryUserID='{entry_user_id}', CurrentUserID='{current_user.user_id}'"
                )
                logger.debug(f"Line {i+1}: ID in delete list? {is_id_match}. User matches? {is_user_match}.")

                # Modifica la condizione: l'admin può eliminare qualsiasi messaggio se l'ID corrisponde,
                # altrimenti l'utente normale può eliminare solo i propri.
                if is_id_match and (is_user_match or current_user.role == "admin"):
                    deleted_count += 1
                    logger.info(f"Line {i+1}: DELETING entry: {message_id_from_log}")
                    # Non aggiungere questa riga a kept_lines, quindi viene eliminata
                else:
                    kept_lines.append(line)
                    if is_id_match and not is_user_match and current_user.role != "admin": # Logga solo se non è un admin che bypassa il controllo utente
                        logger.warning(f"Line {i+1}: ID matched but user did not (and user is not admin). LogUID: {entry_user_id}, RequesterUID: {current_user.user_id}. Entry: {message_id_from_log}")

            except json.JSONDecodeError as je:
                logger.error(f"JSONDecodeError on line {i+1}: {je} - Line: {line.strip()}")
                kept_lines.append(line) # Mantieni le righe malformate o che non possiamo processare
            except Exception as e_inner:
                logger.error(f"Generic error processing line {i+1}: {e_inner} - Line: {line.strip()}", exc_info=True)
                kept_lines.append(line)

        logger.info(f"Processed {processed_lines} lines. Kept {len(kept_lines)} lines. Intended to delete {deleted_count} lines.")

        with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
            f.writelines(kept_lines)

        logger.info(f"Utente {current_user.user_id} ha eliminato {deleted_count} messaggi.")
        if deleted_count == 0 and len(message_ids_to_delete) > 0:
            logger.warning(f"User {current_user.user_id} attempted to delete {len(message_ids_to_delete)} messages, but 0 were actually deleted. Check matching logic.")
        
        return {"message": f"{deleted_count} messaggi eliminati con successo."}
    except Exception as e:
        logger.error(f"Errore durante l'eliminazione dei messaggi per l'utente {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Errore durante l'eliminazione dei messaggi.")

@router.get("/usage_ranking")
def usage_ranking(
    user: UserInToken = Depends(get_current_user),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None)
):
    """
    Restituisce una classifica degli utenti per token usati nel periodo selezionato.
    Solo admin può vedere tutti gli utenti, gli altri solo se stessi.
    """
    if not TOKEN_LOG_PATH.exists():
        logger.info(f"File di log non trovato in {TOKEN_LOG_PATH}")
        return []

    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    usage = {}
    for line in lines:
        try:
            entry = json.loads(line)
            timestamp = datetime.fromisoformat(entry["timestamp"])
            if from_date and timestamp < datetime.fromisoformat(from_date):
                continue
            if to_date and timestamp > datetime.fromisoformat(to_date):
                continue

            entry_user_id = entry.get("user_id")
            if user.role != "admin" and entry_user_id != user.user_id:
                continue

            usage.setdefault(entry_user_id, 0)
            usage[entry_user_id] += entry.get("tokens", 0)
        except Exception as e:
            logger.error(f"Errore durante il parsing di una riga del log: {e} - Riga: {line.strip()}", exc_info=True)

    # Ordina per token decrescente
    ranking = sorted(
        [{"user_id": uid, "tokens_used": tokens} for uid, tokens in usage.items()],
        key=lambda x: x["tokens_used"],
        reverse=True
    )
    return ranking

@router.get("/{session_id}/sources", include_in_schema=True)
def get_session_sources(
    session_id: str = Path(..., min_length=1), 
    user: UserInToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restituisce i documenti collegati a una sessione (notebook) specifica.
    Admin può vedere documenti di qualsiasi sessione, utenti normali solo le proprie.
    """
    logger.info(f"Getting sources for session {session_id} by user {user.user_id}")
    
    # Prima verifica nel database se la sessione esiste
    db_session = db.query(ChatSession).filter_by(session_id=session_id).first()
    
    session_owner = None
    session_found = False
    
    if db_session:
        logger.info(f"Session {session_id} found in database, owner: {db_session.user_id}")
        session_found = True
        session_owner = db_session.user_id
    else:
        logger.info(f"Session {session_id} not found in database, checking log file")
        # Se non è nel database, verifica nel file di log come fallback
        if TOKEN_LOG_PATH.exists():
            with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("session_id") == session_id:
                            session_found = True
                            if session_owner is None:  # Prendi il primo owner trovato
                                session_owner = entry.get("user_id")
                            break
                    except Exception:
                        continue
    
    # Controllo autorizzazioni
    if not session_found:
        logger.warning(f"Session {session_id} not found anywhere")
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    if user.role != "admin" and session_owner != user.user_id:
        logger.warning(f"User {user.user_id} not authorized for session {session_id} (owner: {session_owner})")
        raise HTTPException(status_code=403, detail="Non autorizzato ad accedere a questa sessione")
    
    # Trova documenti specificamente collegati a questa sessione
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
                        # Verifica che non sia già stato aggiunto e che non sia stato scollegato dopo
                        if doc_info not in session_documents:
                            # Controlla se c'è uno scollegamento successivo
                            is_unlinked = False
                            linked_timestamp = datetime.fromisoformat(entry.get("timestamp"))
                            
                            # Rileggi il file per cercare scollegamenti successivi
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
    
    # Ottieni documenti disponibili per collegamento (sistema misto: privati + pubblici)
    from backend.services import document_service
    # Utenti vedono i loro documenti privati + tutti i documenti pubblici
    available_docs = document_service.load_file_metadata(user.user_id, user.role)
    
    return session_documents

@router.post("/{session_id}/sources", include_in_schema=True)
def link_documents_to_session(
    session_id: str = Path(..., min_length=1), 
    request_data: dict = Body(...), 
    user: UserInToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Collega uno o più documenti a una sessione (notebook) specifica.
    """
    # Estrai il filename dal body della richiesta
    filename = request_data.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Nome file mancante")
    
    # Verifica accesso alla sessione (controlla prima nel database, poi nel log)
    session_owner = None
    session_found = False
    
    # Prima verifica nel database
    db_session = db.query(ChatSession).filter_by(session_id=session_id).first()
    if db_session:
        logger.info(f"Session {session_id} found in database, owner: {db_session.user_id}")
        session_found = True
        session_owner = db_session.user_id
    else:
        # Se non è nel database, verifica nel file di log come fallback
        logger.info(f"Session {session_id} not found in database, checking log file")
        if TOKEN_LOG_PATH.exists():
            with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("session_id") == session_id:
                            session_found = True
                            if session_owner is None:  # Prendi il primo owner trovato
                                session_owner = entry.get("user_id")
                            break
                    except Exception:
                        continue
    
    # Controllo autorizzazioni
    if not session_found:
        logger.warning(f"Session {session_id} not found anywhere")
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    if user.role != "admin" and session_owner != user.user_id:
        raise HTTPException(status_code=403, detail="Non autorizzato a modificare questa sessione")
    
    # Verifica che il documento esista e che sia visibile all'utente
    from backend.services import document_service
    
    doc_details = document_service.get_file_details(filename)
    if not doc_details:
        raise HTTPException(status_code=404, detail=f"Documento '{filename}' non trovato")
    
    # Controlla se l'utente può vedere questo documento (logica di visibilità mista)
    is_doc_visible = False
    if user.role == "admin":
        is_doc_visible = True
    elif doc_details.get("is_public", False):
        is_doc_visible = True
    elif doc_details.get("owner") == user.user_id:
        is_doc_visible = True
    
    if not is_doc_visible:
        raise HTTPException(status_code=403, detail=f"Non autorizzato ad accedere al documento '{filename}'")
    
    # Logga il collegamento del documento alla sessione
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
    
    logger.info(f"Document '{filename}' linked to session '{session_id}' by user {user.user_id}")
    return {"message": f"Documento '{filename}' collegato con successo", "linked_document": filename}

@router.delete("/{session_id}/sources/{filename}", include_in_schema=True)
def unlink_document_from_session(
    session_id: str = Path(..., min_length=1),
    filename: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Scollega un documento da una sessione (notebook) specifica.
    """
    # Verifica accesso alla sessione (controlla prima nel database, poi nel log)
    session_owner = None
    session_found = False
    
    # Prima verifica nel database
    db_session = db.query(ChatSession).filter_by(session_id=session_id).first()
    if db_session:
        session_found = True
        session_owner = db_session.user_id
    else:
        # Se non è nel database, verifica nel file di log come fallback
        if TOKEN_LOG_PATH.exists():
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
    
    # Controllo autorizzazioni
    if not session_found:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    if user.role != "admin" and session_owner != user.user_id:
        raise HTTPException(status_code=403, detail="Non autorizzato a modificare questa sessione")
    
    # Logga lo scollegamento del documento dalla sessione
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
    
    logger.info(f"Document '{filename}' unlinked from session '{session_id}' by user {user.user_id}")
    return {"message": f"Documento '{filename}' scollegato dalla sessione", "unlinked_document": filename}

@router.post("/new", response_model=dict)
def create_new_session(user: UserInToken = Depends(get_current_user)):
    """
    Crea una nuova sessione (notebook) vuota.
    """
    session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + str(hash(user.user_id))[-8:]
    
    # Crea una entry iniziale nel log per la nuova sessione
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "user_id": user.user_id,
        "role": user.role,
        "title": "Nuovo Notebook",
        "event": "session_created"
    }
    
    # Assicurati che il file di log esista
    if not TOKEN_LOG_PATH.exists():
        with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
            pass
            
    # Aggiungi l'entry al log
    with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return {"session_id": session_id}

@router.get("/{session_id}/status", response_model=dict)
async def get_session_status(
    session_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    Verifica lo stato di una sessione (notebook).
    Restituisce 'ready' se la sessione esiste ed è pronta per l'uso.
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
                # Verifica che l'utente abbia accesso a questa sessione
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
    Elimina un notebook (sessione) rimuovendo tutte le entry associate dal log.
    """
    if not TOKEN_LOG_PATH.exists():
        logger.error(f"Token log path does not exist: {TOKEN_LOG_PATH}")
        raise HTTPException(status_code=404, detail="No sessions found")
    
    # Leggi tutte le entry esistenti
    all_entries = []
    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                all_entries.append(entry)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {line_num}: {e}")
                continue
    
    # Filtra le entry: mantieni solo quelle che NON appartengono alla sessione da eliminare
    remaining_entries = []
    deleted_count = 0
    access_denied = False
    
    for entry in all_entries:
        if entry.get("session_id") == session_id:
            entry_user_id = entry.get("user_id")
            
            # Admin può eliminare qualsiasi sessione
            if user.role == "admin":
                deleted_count += 1
            # Utente normale può eliminare solo le proprie sessioni o quelle senza proprietario
            elif entry_user_id is None or entry_user_id == user.user_id:
                deleted_count += 1
            else:
                # Utente normale che prova ad eliminare sessione di altri
                logger.warning(f"Access denied: user {user.user_id} tried to delete session owned by {entry_user_id}")
                access_denied = True
                remaining_entries.append(entry)  # Keep the entry
        else:
            remaining_entries.append(entry)
    
    if access_denied:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this session"
        )
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Riscrivi il file senza le entry della sessione eliminata
    try:
        with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
            for entry in remaining_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")
        raise HTTPException(status_code=500, detail="Error updating log file")
    
    logger.info(f"Notebook '{session_id}' deleted successfully by user {user.user_id} (role: {user.role})")
    return {
        "message": f"Notebook '{session_id}' deleted successfully",
        "deleted_entries": deleted_count
    }

@router.get("/debug/raw-log")
def debug_raw_log():
    """
    ENDPOINT DI DEBUG - Mostra il contenuto raw del log (SOLO PER DEBUG)
    """
    if not TOKEN_LOG_PATH.exists():
        return {"error": "Log file not found", "path": str(TOKEN_LOG_PATH)}
    
    try:
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Prendi solo le ultime 20 righe per non sovraccaricare
        recent_lines = lines[-20:] if len(lines) > 20 else lines
        
        entries = []
        for i, line in enumerate(recent_lines):
            try:
                entry = json.loads(line.strip())
                entries.append({
                    "line_number": len(lines) - len(recent_lines) + i + 1,
                    "entry": entry
                })
            except json.JSONDecodeError as e:
                entries.append({
                    "line_number": len(lines) - len(recent_lines) + i + 1,
                    "error": str(e),
                    "raw_line": line.strip()
                })
        
        return {
            "total_lines": len(lines),
            "recent_entries": entries,
            "log_path": str(TOKEN_LOG_PATH)
        }
    except Exception as e:
        return {"error": str(e), "path": str(TOKEN_LOG_PATH)}

@router.get("/debug/sessions-grouped")
def debug_sessions_grouped():
    """
    ENDPOINT DI DEBUG - Mostra le sessioni come le vede il frontend
    """
    if not TOKEN_LOG_PATH.exists():
        return {"error": "Log file not found"}
    
    try:
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Simula la logica dell'endpoint /history
        history = []
        for line in lines:
            try:
                entry = json.loads(line)
                history.append(entry)
            except Exception:
                continue
        
        # Raggruppa per session_id
        sessions = {}
        for entry in history:
            sid = entry.get("session_id", "unknown")
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(entry)

        # Simula la logica del frontend
        result = {}
        for session_id, entries in sessions.items():
            if session_id != "unknown":  # Filtra unknown come fa il frontend
                first = entries[0] if entries else {}
                result[session_id] = {
                    "title": first.get("title", "Notebook senza titolo"),
                    "createdAt": first.get("timestamp"),
                    "prompt": first.get("system_prompt"),
                    "sources": list(set(e.get("source") for e in entries if e.get("source"))),
                    "entry_count": len(entries)
                }
        
        return {
            "total_sessions": len(sessions),
            "sessions_filtered": len(result),
            "sessions": result
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/admin/users/{user_id}/sessions", include_in_schema=True)
def get_user_sessions_admin(
    user_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Ottieni tutte le sessioni di un utente specifico.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono accedere a questa funzione")
    
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
    
    # Formatta le sessioni come nell'endpoint normale
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

@router.get("/admin/users/{user_id}/documents", include_in_schema=True)
def get_user_documents_admin(
    user_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Ottieni tutti i documenti di un utente specifico.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono accedere a questa funzione")
    
    from backend.services import document_service
    
    # Carica tutti i documenti e filtra per utente
    all_documents = document_service.load_file_metadata("admin", "admin")
    user_documents = [doc for doc in all_documents if doc.get("owner") == user_id]
    
    return {
        "user_id": user_id,
        "documents": user_documents,
        "total_documents": len(user_documents)
    }

@router.delete("/admin/users/{user_id}/sessions/{session_id}", include_in_schema=True)
def delete_user_session_admin(
    user_id: str = Path(..., min_length=1),
    session_id: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Elimina una sessione specifica di un utente.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono accedere a questa funzione")
    
    if not TOKEN_LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="Nessuna sessione trovata")
    
    # Leggi tutte le entry esistenti
    all_entries = []
    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                all_entries.append(entry)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {line_num}: {e}")
                continue
    
    # Filtra le entry: mantieni solo quelle che NON appartengono alla sessione da eliminare
    remaining_entries = []
    deleted_count = 0
    
    for entry in all_entries:
        if (entry.get("session_id") == session_id and 
            entry.get("user_id") == user_id):
            deleted_count += 1
        else:
            remaining_entries.append(entry)
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sessione non trovata per questo utente")
    
    # Riscrivi il file senza le entry della sessione eliminata
    try:
        with open(TOKEN_LOG_PATH, "w", encoding="utf-8") as f:
            for entry in remaining_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")
        raise HTTPException(status_code=500, detail="Error updating log file")
    
    logger.info(f"Admin {user.user_id} deleted session '{session_id}' belonging to user '{user_id}'")
    return {
        "message": f"Sessione '{session_id}' dell'utente '{user_id}' eliminata con successo",
        "deleted_entries": deleted_count
    }

@router.delete("/admin/users/{user_id}/documents/{filename}", include_in_schema=True)
def delete_user_document_admin(
    user_id: str = Path(..., min_length=1),
    filename: str = Path(..., min_length=1),
    user: UserInToken = Depends(get_current_user)
):
    """
    ADMIN ONLY: Elimina un documento specifico di un utente.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono accedere a questa funzione")
    
    from backend.services import document_service
    from backend.core.config import DATA_DIR
    import os
    
    # Verifica che il documento esista e appartenga all'utente
    doc_details = document_service.get_file_details(filename)
    if not doc_details:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    if doc_details.get("owner") != user_id:
        raise HTTPException(status_code=400, detail="Il documento non appartiene all'utente specificato")
    
    try:
        # Rimuovi il file fisico
        file_path = DATA_DIR / filename
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"Physical file '{filename}' deleted by admin {user.user_id}")
        
        # Rimuovi dai metadati
        document_service.delete_file_metadata(filename)
        
        # Rimuovi dal sistema RAG se implementato
        try:
            from backend.core.rag_engine import remove_pdf as rag_remove_pdf
            rag_remove_pdf(filename)
        except Exception as e:
            logger.warning(f"Failed to remove from RAG system: {e}")
        
        logger.info(f"Admin {user.user_id} deleted document '{filename}' belonging to user '{user_id}'")
        return {
            "message": f"Documento '{filename}' dell'utente '{user_id}' eliminato con successo"
        }
    except Exception as e:
        logger.error(f"Error deleting document '{filename}': {e}")
        raise HTTPException(status_code=500, detail="Errore durante l'eliminazione del documento")
