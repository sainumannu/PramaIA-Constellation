from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.database import Base

class Workflow(Base):
    """
    Modello per i workflow personalizzabili.
    Un workflow contiene nodi collegati che formano una pipeline di elaborazione.
    """
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(50), unique=True, index=True, nullable=False)  # es: "wf_123"
    name = Column(String(200), nullable=False)  # Nome del workflow
    description = Column(Text, nullable=True)  # Descrizione opzionale
    created_by = Column(String(100), nullable=False)  # User ID del creatore
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Se il workflow è attivo
    is_public = Column(Boolean, default=False)  # Se è pubblico o privato
    assigned_groups = Column(JSON, default=list)  # Lista di gruppi utenti autorizzati
    
    # Nuovi campi per organizzazione
    tags = Column(JSON, default=list)  # Lista di tag personalizzati
    category = Column(String(100), default="General")  # Categoria del workflow
    priority = Column(Integer, default=0)  # Priorità per ordinamento (0=normale, 1=alta, -1=bassa)
    color = Column(String(7), default="#3B82F6")  # Colore hex per visualizzazione
    
    # Stato dell'editor
    view_state = Column(JSON, default=dict)  # Stato del viewport {x, y, zoom}
    
    # Relazioni
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    connections = relationship("WorkflowConnection", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base):
    """
    Modello per i singoli nodi (blocchi) all'interno di un workflow.
    Ogni nodo ha un tipo specifico e una configurazione.
    """
    __tablename__ = "workflow_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), nullable=False)  # ID univoco nel workflow (es: "node_1")
    workflow_id = Column(String(50), ForeignKey("workflows.workflow_id"), nullable=False)
    node_type = Column(String(100), nullable=False)  # Tipo di nodo (es: "input_user", "llm_openai")
    name = Column(String(200), nullable=False)  # Nome del nodo
    description = Column(Text, nullable=True)  # Descrizione opzionale
    config = Column(JSON, default=dict)  # Configurazione specifica del nodo
    position = Column(JSON, default=dict)  # Posizione nell'editor visuale {"x": 100, "y": 200}
    width = Column(Float, default=200)  # Larghezza del nodo
    height = Column(Float, default=80)  # Altezza del nodo
    resizable = Column(Boolean, default=True)  # Se il nodo può essere ridimensionato
    icon = Column(String(10), nullable=True)  # Icona del nodo (emoji o testo breve)
    color = Column(String(10), nullable=True)  # Colore del nodo (hex o nome)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relazioni
    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowConnection(Base):
    """
    Modello per le connessioni tra nodi.
    Definisce il flusso di dati da un nodo all'altro.
    """
    __tablename__ = "workflow_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(50), ForeignKey("workflows.workflow_id"), nullable=False)
    from_node_id = Column(String(50), nullable=False)  # ID del nodo sorgente
    to_node_id = Column(String(50), nullable=False)    # ID del nodo destinazione
    from_port = Column(String(50), default="output")   # Porta di uscita del nodo sorgente
    to_port = Column(String(50), default="input")      # Porta di ingresso del nodo destinazione
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relazioni
    workflow = relationship("Workflow", back_populates="connections")


class WorkflowExecution(Base):
    """
    Modello per tenere traccia delle esecuzioni dei workflow.
    Utile per logging, debugging e analytics.
    """
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)
    workflow_id = Column(String(50), ForeignKey("workflows.workflow_id"), nullable=False)
    user_id = Column(String(100), nullable=False)  # Utente che ha eseguito il workflow
    status = Column(String(50), default="running")  # running, completed, failed, cancelled
    input_data = Column(JSON, default=dict)  # Dati di input forniti dall'utente
    output_data = Column(JSON, default=dict)  # Risultati dell'esecuzione
    error_message = Column(Text, nullable=True)  # Messaggio di errore se fallita
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Tempo di esecuzione in millisecondi
    
    # Relazioni
    workflow = relationship("Workflow", back_populates="executions")
