"""
Modelli per la gestione dei gruppi utenti
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.database import Base

class UserGroup(Base):
    """
    Modello per i gruppi di utenti.
    Permette di organizzare utenti in gruppi per assegnazioni workflow.
    """
    __tablename__ = "user_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(50), unique=True, index=True, nullable=False)  # es: "sales_team"
    name = Column(String(200), nullable=False)  # Nome descrittivo del gruppo
    description = Column(Text, nullable=True)  # Descrizione del gruppo
    created_by = Column(String(100), nullable=False)  # Chi ha creato il gruppo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Se il gruppo è attivo
    color = Column(String(7), default="#3B82F6")  # Colore per UI (es: "#3B82F6")
    
    # Metadati aggiuntivi
    metadata_info = Column(JSON, default=dict)  # Info aggiuntive (permessi default, etc.)
    
    # Relazioni
    members = relationship("UserGroupMember", back_populates="group", cascade="all, delete-orphan")

class UserGroupMember(Base):
    """
    Modello per l'appartenenza degli utenti ai gruppi.
    Relazione many-to-many tra utenti e gruppi con metadati.
    """
    __tablename__ = "user_group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(50), ForeignKey("user_groups.group_id"), nullable=False)
    user_id = Column(String(100), nullable=False)  # ID utente (username/email)
    role_in_group = Column(String(50), default="member")  # "admin", "member", "viewer"
    added_by = Column(String(100), nullable=False)  # Chi ha aggiunto l'utente
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Permette di disabilitare senza rimuovere
    
    # Relazioni
    group = relationship("UserGroup", back_populates="members")

class GroupPermission(Base):
    """
    Modello per i permessi di gruppo.
    Definisce cosa può fare un gruppo nel sistema.
    """
    __tablename__ = "group_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(50), ForeignKey("user_groups.group_id"), nullable=False)
    permission_type = Column(String(100), nullable=False)  # "workflow_execute", "workflow_create", etc.
    resource_id = Column(String(100), nullable=True)  # ID risorsa specifica (opzionale)
    granted_by = Column(String(100), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Permesso temporaneo
    is_active = Column(Boolean, default=True)
    
    # Relazioni
    group = relationship("UserGroup", backref="permissions")
