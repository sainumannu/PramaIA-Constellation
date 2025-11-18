"""
Modelli del database per il sistema di eventi e trigger
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from backend.db.database import Base


class EventTrigger(Base):
    """
    Modello per i trigger di eventi
    """
    __tablename__ = "event_triggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Configurazione del trigger
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=True, index=True)
    workflow_id = Column(String(255), nullable=False)
    
    # Condizioni del trigger (JSON)
    conditions = Column(JSON, nullable=True)
    
    # Stato del trigger
    active = Column(Boolean, default=True, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<EventTrigger(name='{self.name}', event_type='{self.event_type}', active={self.active})>"


class EventLog(Base):
    """
    Log degli eventi processati
    """
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Dettagli dell'evento
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=True, index=True)
    event_data = Column(JSON, nullable=False)
    event_metadata = Column(JSON, nullable=True)
    
    # Risultato del processing
    triggers_matched = Column(Integer, default=0)
    workflows_executed = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<EventLog(event_type='{self.event_type}', success={self.success})>"
