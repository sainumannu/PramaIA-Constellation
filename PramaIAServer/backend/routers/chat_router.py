from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv

from backend.db.database import get_db # Utility per ottenere la sessione DB
from backend.db.models import User as DBUser # Modello User SQLAlchemy
from backend.auth.dependencies import get_current_user
from backend.services import chat_service # Per gestione sessioni e messaggi
from backend.services import usage_service # Per logging token # type: ignore
from backend.core import rag_engine # Logica di processamento RAG
from langchain_openai import ChatOpenAI
from backend.schemas.session import ChatSessionOut

load_dotenv()  # Carica le variabili dal file .env

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

router = APIRouter()
logger = logging.getLogger(__name__)

# Inizializza il modello LLM con la chiave API di OpenAI
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o")

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    model: Optional[str] = "gpt-4o"
    max_history: Optional[int] = 100
    mode: Optional[str] = "rag"  # "rag" (solo fonti interne) o "gpt" (fallback GPT classico)
    first_prompt: Optional[str] = None  # Prompt personalizzato opzionale
    provider: Optional[str] = "openai"  # <--- AGGIUNTO: provider LLM (openai, ollama, anthropic, gemini)

@router.post("/ask/")
async def ask_question(
    request: ChatRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Processa una domanda dell'utente, interagisce con il RAG engine,
    salva la conversazione e logga l'utilizzo dei token.
    """
    try:
        rag_user_id = current_user.user_id

        rag_response = rag_engine.process_question(
            request.question,
            user_id=rag_user_id,
            session_id=request.session_id,
            model=request.model,
            db=db,
            max_history=request.max_history,
            mode=request.mode,  # Passa la modalità scelta dall'utente
            system_prompt=request.first_prompt,  # Passa il prompt personalizzato
            provider=request.provider  # <--- AGGIUNTO: provider LLM
        )

        returned_session_id = rag_response.session_id
        answer = rag_response.answer
        source = rag_response.source
        tokens_used = rag_response.tokens

        db_user = chat_service.get_or_create_user(db, user_id=rag_user_id)
        # Recupera la sessione già creata/aggiornata da process_question
        session = db.query(chat_service.models.ChatSession).filter_by(session_id=returned_session_id).first()
        logger.info(f"[DEBUG ROUTER] session type: {type(session)}, session: {session}")
        chat_service.save_message(
            db=db,
            session=session,
            prompt=request.question,
            answer=answer,
            tokens=tokens_used,
            session_uuid=session.session_id
        )
        logger.info(f"Messaggio salvato per session_id={returned_session_id}")

        logger.info(f"DEBUG: session={session}")

        history = chat_service.get_history_for_session(db, session.id)
        logger.info(f"History recuperata dal DB: {history}")

        usage_service.log_interaction_tokens(
            user_id=rag_user_id,
            prompt=request.question,
            answer=answer,
            source=source,
            session_id=returned_session_id,
            tokens=tokens_used
        )

        return {
            "answer": answer,
            "source": source,
            "session_id": returned_session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nell'endpoint /chat/ask/ per utente {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Si è verificato un errore imprevisto durante l'elaborazione della tua richiesta.")

@router.get("/sessions/", response_model=List[ChatSessionOut])
def get_user_sessions(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restituisce la lista delle sessioni chat dell'utente corrente.
    """
    sessions = chat_service.get_sessions_by_user(db, current_user.user_id)
    return [
        ChatSessionOut(
            session_id=s.session_id,
            user_id=s.user_id,
            question=s.question,
            answer=s.answer,
            tokens=s.tokens,      # Assicurati che il campo si chiami così nel tuo modello
            timestamp=str(s.timestamp)
        )
        for s in sessions
    ]