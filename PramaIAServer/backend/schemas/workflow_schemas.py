from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enum per le categorie di workflow
class WorkflowCategory(str, Enum):
    GENERAL = "General"
    BUSINESS_PROCESS = "Business Process"
    DATA_ANALYSIS = "Data Analysis"
    CONTENT_GENERATION = "Content Generation"
    CUSTOMER_SERVICE = "Customer Service"
    MARKETING = "Marketing"
    DEVELOPMENT = "Development"
    RESEARCH = "Research"
    AUTOMATION = "Automation"
    INTEGRATION = "Integration"

# Enum per i tipi di nodi
class NodeType(str, Enum):
    INPUT_USER = "input_user"
    INPUT_FILE = "input_file" 
    INPUT_URL = "input_url"
    PROCESSING_TEXT = "processing_text"
    PROCESSING_SUMMARIZE = "processing_summarize"
    PROCESSING_EXTRACT = "processing_extract"
    LLM_OPENAI = "llm_openai"
    LLM_ANTHROPIC = "llm_anthropic"
    LLM_GEMINI = "llm_gemini"
    LLM_OLLAMA = "llm_ollama"
    OUTPUT_TEXT = "output_text"
    OUTPUT_FILE = "output_file"
    OUTPUT_EMAIL = "output_email"
    OUTLOOK_EMAIL = "outlook_email"

# Enum per lo status delle esecuzioni
class ExecutionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Schema per posizione nel canvas
class NodePosition(BaseModel):
    x: float = Field(..., description="Posizione X nel canvas")
    y: float = Field(..., description="Posizione Y nel canvas")

# Schema base per WorkflowNode
class WorkflowNodeBase(BaseModel):
    node_id: str = Field(..., description="ID univoco del nodo nel workflow")
    node_type: str = Field(..., description="Tipo del nodo")  # Temporaneamente cambiato a str
    name: str = Field(..., max_length=200, description="Nome del nodo")
    description: Optional[str] = Field(None, description="Descrizione opzionale")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configurazione del nodo")
    position: NodePosition = Field(..., description="Posizione nel canvas")
    width: Optional[float] = Field(200, description="Larghezza del nodo")
    height: Optional[float] = Field(80, description="Altezza del nodo")
    resizable: Optional[bool] = Field(True, description="Se il nodo pu├▓ essere ridimensionato")

class WorkflowNodeCreate(WorkflowNodeBase):
    pass

class WorkflowNodeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    position: Optional[NodePosition] = None
    width: Optional[float] = None
    height: Optional[float] = None
    resizable: Optional[bool] = None

class WorkflowNode(WorkflowNodeBase):
    id: int
    workflow_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Schema base per WorkflowConnection
class WorkflowConnectionBase(BaseModel):
    from_node_id: str = Field(..., description="ID del nodo sorgente")
    to_node_id: str = Field(..., description="ID del nodo destinazione")
    from_port: str = Field(default="output", description="Porta di uscita")
    to_port: str = Field(default="input", description="Porta di ingresso")

class WorkflowConnectionCreate(WorkflowConnectionBase):
    pass

class WorkflowConnection(WorkflowConnectionBase):
    id: int
    workflow_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Schema base per Workflow
class WorkflowBase(BaseModel):
    name: str = Field(..., max_length=200, description="Nome del workflow")
    description: Optional[str] = Field(None, description="Descrizione opzionale")
    is_active: bool = Field(default=True, description="Se il workflow ├¿ attivo")
    is_public: bool = Field(default=False, description="Se il workflow ├¿ pubblico")
    assigned_groups: List[str] = Field(default_factory=list, description="Gruppi autorizzati")
    tags: List[str] = Field(default_factory=list, description="Tag personalizzati")
    category: str = Field(default="General", description="Categoria del workflow")
    priority: int = Field(default=0, description="Priorit├á (-1=bassa, 0=normale, 1=alta)")
    color: str = Field(default="#3B82F6", description="Colore hex per visualizzazione")

class WorkflowCreate(WorkflowBase):
    nodes: List[WorkflowNodeCreate] = Field(default_factory=list, description="Nodi del workflow")
    connections: List[WorkflowConnectionCreate] = Field(default_factory=list, description="Connessioni tra nodi")

class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    assigned_groups: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    color: Optional[str] = None
    nodes: Optional[List[WorkflowNodeCreate]] = Field(None, description="Nodi del workflow")
    connections: Optional[List[WorkflowConnectionCreate]] = Field(None, description="Connessioni tra nodi")

class Workflow(WorkflowBase):
    id: int
    workflow_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    nodes: List[WorkflowNode] = []
    connections: List[WorkflowConnection] = []

    class Config:
        from_attributes = True

# Schema per WorkflowExecution
class WorkflowExecutionBase(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Dati di input")

class WorkflowExecutionCreate(WorkflowExecutionBase):
    pass

class WorkflowExecution(WorkflowExecutionBase):
    id: int
    execution_id: str
    workflow_id: str
    user_id: str
    status: ExecutionStatus
    output_data: Dict[str, Any] = {}
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None

    class Config:
        from_attributes = True

# Schema per la lista dei workflow
class WorkflowList(BaseModel):
    id: int
    workflow_id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_public: bool
    nodes_count: int = 0
    last_execution: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list, description="Tag personalizzati")
    category: str = Field(default="General", description="Categoria del workflow")
    priority: int = Field(default=0, description="Priorit├á (-1=bassa, 0=normale, 1=alta)")
    color: str = Field(default="#3B82F6", description="Colore hex per visualizzazione")

    class Config:
        from_attributes = True

# Schema per le risposte API
class WorkflowResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class WorkflowExecutionResponse(BaseModel):
    success: bool
    execution_id: str
    status: ExecutionStatus
    message: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
