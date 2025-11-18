from sqlalchemy.orm import Session
from datetime import datetime
from backend.db import models # Aggiorna l'importazione dei modelli
from backend.db.models import Message  # Importa esplicitamente Message
# import uuid # uuid non sembra essere usato qui direttamente
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from backend.db.models import User as DBUser
# from backend.db.models import Message  # Import Message model
from backend.utils import get_logger

logger = get_logger()

# 🧠 Funzione per generare titolo sessione con GPT
def generate_session_title(prompt: str) -> str:
    llm = OpenAI()
    template = PromptTemplate.from_template(
        "Assegna un titolo breve e descrittivo alla seguente domanda:\n{prompt}\nTitolo:"
    )
    chain = template | llm
    result = chain.invoke({"prompt": prompt})
    return result  # <-- AGGIUNGI QUESTO

# ✅ Recupera o crea sessione per utente
from typing import Optional

def get_or_create_session(db: Session, user: models.User, session_id: str, first_prompt: Optional[str] = None, first_question: Optional[str] = None) -> models.ChatSession:
    session = db.query(models.ChatSession).filter_by(session_id=session_id).first()
    if session:
        return session
    # Usa la prima domanda dell'utente per il titolo, non il system prompt
    title = generate_session_title(first_question) if first_question else "Nuova conversazione"
    new_session = models.ChatSession(
        session_id=session_id,
        title=title,
        owner=user,
        created_at=datetime.utcnow(),
        system_prompt=first_prompt or ""  # Garantisce che sia sempre una stringa
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info("Nuova sessione creata", details={"session_id": new_session.session_id, "title": new_session.title, "owner": getattr(user, 'id', None)})
    return new_session

# 💬 Salva un messaggio
from typing import Optional

def save_message(db: Session, session: models.ChatSession, prompt: str, answer: str, tokens: int, session_uuid: Optional[str] = None):
    msg = Message(
        prompt=prompt,
        answer=answer,
        tokens=tokens,
        session_id=session.id,
        session_uuid=session_uuid,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    logger.info("Messaggio salvato", details={"session_id": session.session_id, "tokens": tokens})

def get_or_create_user(db, user_id):
    user = db.query(DBUser).filter_by(user_id=user_id).first()
    if not user:
        user = DBUser(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_sessions_by_user(db, user_id):
    # Usa models.ChatSession invece di ChatSession (che non è importato)
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id).all()

def get_history_for_session(db, session_id):
    """
    Restituisce la cronologia della sessione come lista di messaggi in formato OpenAI:
    [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}, ...]
    """
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    history = []
    for msg in messages:
        history.append({"role": "user", "content": msg.prompt})
        if msg.answer:
            history.append({"role": "assistant", "content": msg.answer})
    return history

def get_history_for_session_by_uuid(db, session_uuid):
    messages = (
        db.query(Message)
        .filter(Message.session_uuid == session_uuid)
        .order_by(Message.timestamp.asc())
        .all()
    )
    history = []
    for msg in messages:
        history.append({"role": "user", "content": msg.prompt})
        if msg.answer:
            history.append({"role": "assistant", "content": msg.answer})
    return history
