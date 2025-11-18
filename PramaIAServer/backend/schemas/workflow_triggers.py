from datetime import datetime
from typing import Dict, Optional, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field, validator


class ConditionsModel(BaseModel):
    """Modello per le condizioni di filtro dei trigger."""
    filename_pattern: Optional[str] = None
    max_size_kb: Optional[int] = None
    min_size_kb: Optional[int] = None
    content_type: Optional[str] = None
    metadata_contains: Optional[Dict[str, str]] = None
    # Campi per eventi schedule
    cron: Optional[str] = None
    timezone: Optional[str] = None
    # Campi per filtro path
    path_contains: Optional[str] = None
    path_regex: Optional[str] = None
    

class WorkflowTriggerBase(BaseModel):
    """Modello base per i trigger dei workflow."""
    name: str = Field(..., min_length=3, max_length=255, description="Nome descrittivo del trigger")
    event_type: str = Field(..., min_length=1, max_length=100, description="Tipo di evento (es. pdf_upload, file_created)")
    source: str = Field(..., min_length=1, max_length=100, description="Sorgente dell'evento (es. pdf-monitor, scheduler)")
    workflow_id: str = Field(..., min_length=1, description="ID del workflow da eseguire")
    target_node_id: Optional[str] = Field(None, description="ID del nodo di destinazione specifico nel workflow")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condizioni opzionali per filtrare gli eventi")
    active: bool = Field(True, description="Stato attivo/inattivo del trigger")

    @validator('event_type')
    def validate_event_type(cls, v):
        # Temporaneamente disabilitato per permettere tipi dinamici dal PDK
        # valid_event_types = [
        #     'pdf_upload', 'file_created', 'schedule', 
        #     'api_call', 'document_processed'
        # ]
        # if v not in valid_event_types:
        #     raise ValueError(f"Tipo di evento non valido. Valori consentiti: {', '.join(valid_event_types)}")
        if not v or len(v.strip()) == 0:
            raise ValueError("Tipo di evento non può essere vuoto")
        return v
    
    @validator('source')
    def validate_source(cls, v):
        # Temporaneamente disabilitato per permettere sorgenti dinamiche dal PDK
        # valid_sources = [
        #     'pdf-monitor', 'scheduler', 'api', 'ui', 'system'
        # ]
        # if v not in valid_sources:
        #     raise ValueError(f"Sorgente non valida. Valori consentiti: {', '.join(valid_sources)}")
        if not v or len(v.strip()) == 0:
            raise ValueError("Sorgente non può essere vuota")
        return v
    
    @validator('conditions')
    def validate_conditions(cls, v, values):
        event_type = values.get('event_type')
        
        # Validazione per evento pdf_upload
        if event_type == 'pdf_upload':
            valid_keys = ['file_type', 'filename_pattern', 'max_size_kb', 'min_size_kb', 
                         'content_type', 'metadata_contains', 'path_contains', 'path_regex']
            for key in v.keys():
                if key not in valid_keys:
                    raise ValueError(f"Chiave di condizione non valida per evento pdf_upload: {key}")
        
        # Validazione per evento schedule
        elif event_type == 'schedule':
            if 'cron' not in v and v:  # Solo se ci sono condizioni specificate
                raise ValueError("La condizione 'cron' è consigliata per eventi di tipo schedule")
        
        return v


class WorkflowTriggerCreate(WorkflowTriggerBase):
    """Modello per la creazione di un nuovo trigger."""
    pass


class WorkflowTriggerUpdate(BaseModel):
    """Modello per l'aggiornamento di un trigger esistente."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    event_type: Optional[str] = Field(None, min_length=1, max_length=100)
    source: Optional[str] = Field(None, min_length=1, max_length=100)
    workflow_id: Optional[str] = Field(None, min_length=1)
    target_node_id: Optional[str] = Field(None, description="ID del nodo di destinazione specifico nel workflow")
    conditions: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None

    @validator('event_type')
    def validate_event_type(cls, v):
        if v is None:
            return v
        if not v or len(v.strip()) == 0:
            raise ValueError("Tipo di evento non può essere vuoto")
        return v
    
    @validator('source')
    def validate_source(cls, v):
        if v is None:
            return v
        if not v or len(v.strip()) == 0:
            raise ValueError("Sorgente non può essere vuota")
        return v


class WorkflowTrigger(WorkflowTriggerBase):
    """Modello completo per un trigger di workflow."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class WorkflowTriggerToggle(BaseModel):
    """Modello per attivare/disattivare un trigger."""
    active: bool = Field(..., description="Stato attivo/inattivo del trigger")


class WorkflowTriggerList(BaseModel):
    """Schema per la risposta con una lista di trigger."""
    items: List[WorkflowTrigger] = Field(..., description="Lista dei trigger")
    count: int = Field(..., description="Numero totale di trigger")
    
    class Config:
        orm_mode = True


def generate_trigger_id() -> str:
    """Genera un ID univoco per un nuovo trigger."""
    return str(uuid4())
