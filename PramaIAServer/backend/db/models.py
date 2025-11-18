# backend/db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable per utenti OAuth
    user_id = Column(String(255), nullable=True)  # Per OAuth providers (Azure AD OID, etc.)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relazione con ChatSession
    sessions = relationship("ChatSession", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"

# Modello base per ChatSession
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=True, default="Nuova conversazione")
    system_prompt = Column(Text, nullable=True)  # Prompt personalizzato della sessione
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relazione con User
    owner = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"

# Modello per i messaggi di chat
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    session_uuid = Column(String(255), nullable=True)  # UUID della sessione per compatibilità
    prompt = Column(Text, nullable=False)  # Domanda dell'utente
    answer = Column(Text, nullable=True)   # Risposta dell'assistente
    tokens = Column(Integer, default=0)    # Token utilizzati
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Message(id={self.id}, session_id={self.session_id}, prompt='{self.prompt[:50]}...')>"
