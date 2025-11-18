from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime
import json
import logging
from backend.auth.dependencies import get_current_user
from backend.schemas.user_schemas import UserInToken
from backend.core.config import TOKEN_LOG_PATH

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/usage_ranking")
def usage_ranking(
    user: UserInToken = Depends(get_current_user),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None)
):
    """
    Classifica degli utenti per token usati.
    """
    if not TOKEN_LOG_PATH.exists():
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
            logger.error(f"Errore parsing log: {e}", exc_info=True)

    ranking = sorted(
        [{"user_id": uid, "tokens_used": tokens} for uid, tokens in usage.items()],
        key=lambda x: x["tokens_used"],
        reverse=True
    )
    return ranking

@router.get("/debug/raw-log")
def debug_raw_log():
    """
    DEBUG: Mostra il contenuto raw del log.
    """
    if not TOKEN_LOG_PATH.exists():
        return {"error": "Log not found", "path": str(TOKEN_LOG_PATH)}
    
    try:
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
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
    DEBUG: Mostra le sessioni come le vede il frontend.
    """
    if not TOKEN_LOG_PATH.exists():
        return {"error": "Log not found"}
    
    try:
        with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        history = []
        for line in lines:
            try:
                entry = json.loads(line)
                history.append(entry)
            except Exception:
                continue
        
        sessions = {}
        for entry in history:
            sid = entry.get("session_id", "unknown")
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(entry)

        result = {}
        for session_id, entries in sessions.items():
            if session_id != "unknown":
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
