"""
Sistema generico di gestione eventi e trigger.
Questo modulo fornisce un'infrastruttura per associare qualsiasi tipo di evento 
a uno o più workflow basati su condizioni configurabili.

NOTA: Questo file rappresenta uno sviluppo futuro pianificato del sistema di trigger.
      Implementa un sistema di gestione eventi generico che può essere utilizzato
      per qualsiasi tipo di evento, non solo per l'upload di PDF.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import logging
import json
import uuid
import os

from backend.auth.dependencies import get_current_user, get_current_user_optional
from backend.db.database import get_db
from sqlalchemy.orm import Session
from backend.schemas.user_schemas import UserInToken
from backend.services.trigger_service import TriggerService, create_trigger, get_active_triggers
from backend.models.trigger_models import EventTrigger

router = APIRouter(prefix="/api/events", tags=["events"])
logger = logging.getLogger(__name__)

# Modelli per gestione eventi
class EventMetadata(BaseModel):
    """Metadati generici per un evento"""
    source: str = Field(..., description="Sorgente dell'evento (es. pdf-monitor, scheduler, api)")
    timestamp: Optional[str] = None
    user_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EventPayload(BaseModel):
    """Contenuto dell'evento"""
    event_type: str = Field(..., description="Tipo di evento (es. file_upload, timer_tick, api_call)")
    data: Dict[str, Any] = Field(..., description="Dati dell'evento")
    metadata: EventMetadata

class TriggerResult(BaseModel):
    """Risultato dell'elaborazione di un trigger"""
    trigger_id: str
    trigger_name: str
    workflow_id: str
    workflow_name: Optional[str] = None
    status: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class EventProcessingResponse(BaseModel):
    """Risposta all'elaborazione di un evento"""
    event_id: str
    status: str
    message: str
    results: List[TriggerResult] = []


@router.post("/process", response_model=EventProcessingResponse, summary="Elabora un evento generico")
async def process_generic_event(
    payload: EventPayload,
    db: Session = Depends(get_db),
    current_user: Optional[UserInToken] = Depends(get_current_user_optional)
):
    """
    Riceve ed elabora un evento generico, attivando i trigger appropriati.
    
    Questo endpoint è il punto centrale per l'elaborazione di tutti gli eventi nel sistema.
    Qualsiasi componente può inviare eventi qui, e il sistema di trigger si occuperà
    di determinare quali workflow devono essere eseguiti.
    
    L'autenticazione è opzionale - se non fornita, l'evento viene comunque elaborato
    ma senza associazione utente.
    """
    try:
        # Genera un ID univoco per l'evento
        event_id = str(uuid.uuid4())
        
        # Aggiungi informazioni utente se disponibili
        if current_user and not payload.metadata.user_id:
            payload.metadata.user_id = getattr(current_user, 'id', None)
        
        # Log dell'evento ricevuto
        logger.info(f"Ricevuto evento {payload.event_type} da {payload.metadata.source} [ID: {event_id}]")
        
        # Processa l'evento usando il servizio trigger
        trigger_service = TriggerService(db)
        result = await trigger_service.process_event(
            event_type=payload.event_type,
            data=payload.data,
            metadata=payload.metadata.dict()
        )
        
        # Converti il risultato nel formato dell'API
        status = "processed" if result["success"] else "error"
        message = result.get("error", f"Evento processato. Trigger attivati: {result['triggers_matched']}, Workflow eseguiti: {result['workflows_executed']}")
        
        return EventProcessingResponse(
            event_id=event_id,
            status=status,
            message=message,
            results=result.get("results", [])
        )
    except Exception as e:
        logger.error(f"Errore nell'elaborazione dell'evento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.post("/pdf-upload", summary="Endpoint per upload PDF (compatibilità legacy)")
async def pdf_upload_event(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[UserInToken] = Depends(get_current_user)
):
    """
    Endpoint specifico per l'upload di PDF, che converte la richiesta in un evento generico.
    
    Questo endpoint è fornito per compatibilità con i client esistenti. Internamente
    converte la richiesta in un evento generico che viene poi elaborato dal sistema di trigger.
    """
    try:
        # Leggi il form multipart (file PDF)
        form = await request.form()
        
        if "file" not in form:
            raise HTTPException(status_code=400, detail="Nessun file fornito")
            
        file = form["file"]
        
        # Crea un payload di evento generico
        event_payload = EventPayload(
            event_type="file_upload",
            data={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": 0  # Verrà calcolato dopo la lettura del file
            },
            metadata=EventMetadata(
                source="pdf-monitor",
                user_id=current_user.id if current_user else None,
                additional_data={
                    "upload_method": "api_endpoint",
                    "client_info": str(request.client)
                }
            )
        )
        
        # TODO: Implementare la gestione del file e l'inoltro al sistema di eventi
        # Questo richiede di leggere il file, salvarlo temporaneamente e aggiungere
        # il percorso ai dati dell'evento
        
        return {
            "status": "received",
            "message": "PDF ricevuto. L'elaborazione tramite il nuovo sistema di trigger è in fase di implementazione.",
            "filename": file.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nell'elaborazione dell'upload PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


# Endpoint di amministrazione

@router.get("/triggers", summary="Recupera tutti i trigger configurati")
async def get_all_triggers(
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera tutti i trigger configurati nel sistema.
    Richiede autenticazione con un utente amministratore.
    """
    # TODO: Implementare la logica per recuperare i trigger
    # triggers = await get_active_triggers(db)
    
    return {
        "status": "ok",
        "message": "Funzionalità in fase di implementazione",
        "triggers": []
    }


@router.get("/triggers/{event_type}", summary="Recupera i trigger per un tipo di evento")
async def get_triggers_by_event_type(
    event_type: str,
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera tutti i trigger configurati per un tipo specifico di evento.
    Richiede autenticazione con un utente amministratore.
    """
    try:
        triggers = await get_active_triggers(db, event_type=event_type)
        
        return {
            "event_type": event_type,
            "triggers": [
                {
                    "id": trigger.id,
                    "name": trigger.name,
                    "description": trigger.description,
                    "workflow_id": trigger.workflow_id,
                    "conditions": trigger.conditions,
                    "active": trigger.active,
                    "created_at": trigger.created_at.isoformat() if trigger.created_at is not None else None
                }
                for trigger in triggers
            ]
        }
    except Exception as e:
        logger.error(f"Errore nel recupero dei trigger per {event_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/triggers", summary="Crea un nuovo trigger")
async def create_event_trigger(
    trigger_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Crea un nuovo trigger per eventi.
    Richiede autenticazione con un utente amministratore.
    """
    try:
        trigger = await create_trigger(db, trigger_data)
        
        return {
            "success": True,
            "trigger": {
                "id": trigger.id,
                "name": trigger.name,
                "description": trigger.description,
                "event_type": trigger.event_type,
                "source": trigger.source,
                "workflow_id": trigger.workflow_id,
                "conditions": trigger.conditions,
                "active": trigger.active
            }
        }
    except Exception as e:
        logger.error(f"Errore nella creazione del trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "status": "ok",
        "event_type": event_type,
        "message": "Funzionalità in fase di implementazione",
        "triggers": []
    }
