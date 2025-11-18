"""
Estensione modello Workflow per gestione utenti
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.database import Base

class WorkflowUserAssignment(Base):
    """
    Modello per assegnare workflow a utenti specifici.
    Complementa il campo assigned_groups con assegnazioni dirette.
    """
    __tablename__ = "workflow_user_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(50), ForeignKey("workflows.workflow_id"), nullable=False)
    user_id = Column(String(100), nullable=False)  # ID utente (username/email)
    assigned_by = Column(String(100), nullable=False)  # Chi ha fatto l'assegnazione
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Permette di disabilitare senza cancellare
    can_execute = Column(Boolean, default=True)  # Permesso di esecuzione
    can_modify = Column(Boolean, default=False)  # Permesso di modifica
    can_share = Column(Boolean, default=False)  # Permesso di condivisione
    
    # Relazioni
    workflow = relationship("Workflow", backref="user_assignments")

class WorkflowPermission(Base):
    """
    Modello per gestire permessi granulari sui workflow.
    """
    __tablename__ = "workflow_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(50), ForeignKey("workflows.workflow_id"), nullable=False)
    user_id = Column(String(100), nullable=False)
    permission_type = Column(String(50), nullable=False)  # "view", "execute", "edit", "admin"
    granted_by = Column(String(100), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Permesso temporaneo
    is_active = Column(Boolean, default=True)
    
    # Relazioni
    workflow = relationship("Workflow", backref="permissions")
