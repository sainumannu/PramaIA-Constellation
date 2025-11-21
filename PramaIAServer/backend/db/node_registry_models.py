"""
Database Models per Node Registry

Sostituisce il NodeRegistry in-memory con tabelle DB per maggiore flessibilità.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.db.database import Base


class NodeType(Base):
    """
    Tabella per i tipi di nodi disponibili nel sistema.
    SOLO NODI MODERNI PDK - NO LEGACY!
    """
    __tablename__ = "node_types"
    
    id = Column(Integer, primary_key=True, index=True)
    node_type = Column(String(100), unique=True, nullable=False, index=True)
    plugin_id = Column(String(100), nullable=True)  # NULL per nodi nativi
    processor_class = Column(String(200), nullable=False)  # Nome classe processore
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Schema di configurazione per validazione
    config_schema = Column(JSON, nullable=True)
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)
    
    # Metadati aggiuntivi
    category = Column(String(50), nullable=True)  # input, output, processing, llm, etc.
    version = Column(String(20), default="1.0.0")
    author = Column(String(100), nullable=True)


# RIMOSSO: NodeTypeMapping - NON PIÙ NECESSARIO!
# Il sistema usa SOLO nodi moderni dal PDK


class NodeExecutionLog(Base):
    """
    Log delle esecuzioni dei nodi per debug e analytics.
    """
    __tablename__ = "node_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    node_type = Column(String(100), nullable=False, index=True)
    execution_id = Column(String(50), nullable=False, index=True)
    workflow_id = Column(String(50), nullable=False)
    
    # Risultato esecuzione
    status = Column(String(20), nullable=False)  # success, failed, timeout
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Dati input/output (per debug)
    input_data_hash = Column(String(64), nullable=True)  # Hash per privacy
    output_data_hash = Column(String(64), nullable=True)
    
    # Metadati
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processor_version = Column(String(20), nullable=True)
    
    
class PluginRegistry(Base):
    """
    Registry dei plugin PDK attivi nel sistema.
    """
    __tablename__ = "plugin_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(String(100), unique=True, nullable=False, index=True)
    plugin_name = Column(String(200), nullable=False)
    plugin_version = Column(String(20), nullable=False)
    
    # Configurazione plugin
    base_url = Column(String(500), nullable=True)  # URL del plugin PDK
    api_key = Column(String(100), nullable=True)
    config = Column(JSON, nullable=True)
    
    # Stato
    is_active = Column(Boolean, default=True, nullable=False)
    last_ping = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="unknown")  # online, offline, error
    
    # Metadati
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_by = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)