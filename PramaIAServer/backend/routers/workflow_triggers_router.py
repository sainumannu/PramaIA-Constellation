from backend.utils import get_logger
from typing import List, Optional
import traceback
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status, Request

from backend.auth.dependencies import get_current_user
from backend.crud import workflow_triggers as crud
from backend.schemas.user_schemas import UserInToken
from backend.schemas.workflow_triggers import (
    WorkflowTrigger,
    WorkflowTriggerCreate,
    WorkflowTriggerUpdate,
)
from backend.db.database import get_db

router = APIRouter(
    tags=["workflow_triggers"],
    responses={404: {"description": "Non trovato"}},
)

logger = get_logger()


@router.get(
    "/",
    response_model=List[WorkflowTrigger],
    summary="Ottieni tutte le associazioni eventi-workflow"
)
def get_triggers(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user),
    debug: bool = False
):
    """
    Recupera tutte le associazioni eventi-workflow configurate nel sistema.
    
    Richiede autenticazione con un utente valido.
    """
    try:
        # Log di informazioni sulla richiesta
        logger.info("Richiesta GET /api/workflows/triggers/", details={"headers": dict(request.headers), "client": str(request.client)})
        if current_user:
            logger.info("Utente autenticato", details={"username": current_user.username})
        logger.info("Diagnostica tabella workflow_triggers")
        crud.check_table_structure(db)
        logger.info("Recupero trigger dal database")
        triggers = crud.get_all_triggers(db)
        logger.info("Trigger recuperati", details={"count": len(triggers)})
        for i, trigger in enumerate(triggers):
            logger.info("Verifica trigger", details={"index": i+1, "conditions_type": type(trigger.get('conditions')).__name__})
            if not isinstance(trigger.get('conditions'), dict):
                logger.warning("Trigger ha conditions non dict", details={"index": i+1, "actual_type": type(trigger.get('conditions')).__name__})
                trigger['conditions'] = {}
        return triggers
    except Exception as e:
        logger.error("Errore nel recupero dei trigger", details={"error": str(e)}, context={"trace": traceback.format_exc()})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero dei trigger dal database: {str(e)}"
        )


@router.get(
    "/{trigger_id}",
    response_model=WorkflowTrigger,
    summary="Ottieni un trigger specifico"
)
def get_trigger(
    trigger_id: str,
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera i dettagli di un trigger specifico dato il suo ID.
    
    Richiede autenticazione con un utente valido.
    """
    try:
        trigger = crud.get_trigger_by_id(db, trigger_id)
        if not trigger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger con ID {trigger_id} non trovato"
            )
        return trigger
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore nel recupero trigger", details={"trigger_id": trigger_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore nel recupero del trigger dal database"
        )


@router.post(
    "/",
    response_model=WorkflowTrigger,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuovo trigger"
)
def create_trigger(
    trigger: WorkflowTriggerCreate,
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Crea una nuova associazione evento-workflow.
    
    Richiede autenticazione con un utente valido.
    """
    try:
        return crud.create_trigger(db, trigger)
    except Exception as e:
        logger.error("Errore creazione trigger", details={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore nella creazione del trigger"
        )


@router.put(
    "/{trigger_id}",
    response_model=WorkflowTrigger,
    summary="Aggiorna un trigger esistente"
)
def update_trigger(
    trigger_id: str,
    trigger_update: WorkflowTriggerUpdate,
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Aggiorna un'associazione evento-workflow esistente.
    
    Richiede autenticazione con un utente valido.
    """
    try:
        updated_trigger = crud.update_trigger(db, trigger_id, trigger_update)
        if not updated_trigger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger con ID {trigger_id} non trovato"
            )
        return updated_trigger
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore aggiornamento trigger", details={"trigger_id": trigger_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore nell'aggiornamento del trigger"
        )


@router.delete(
    "/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina un trigger"
)
def delete_trigger(
    trigger_id: str,
    db: Session = Depends(get_db),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Elimina un'associazione evento-workflow esistente.
    
    Richiede autenticazione con un utente valido.
    """
    try:
        success = crud.delete_trigger(db, trigger_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger con ID {trigger_id} non trovato"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore eliminazione trigger", details={"trigger_id": trigger_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore nell'eliminazione del trigger"
        )


# L'endpoint di debug è stato rimosso per sicurezza

# L'endpoint pubblico è stato rimosso per sicurezza

# NOTA: L'endpoint /workflows/{workflow_id}/input-nodes è stato RIMOSSO da questo router
# perché duplicava quello presente in workflow_router.py, causando confusione.
# 
# ✅ ENDPOINT CORRETTO: GET /api/workflows/{workflow_id}/input-nodes (workflow_router.py)
# ❌ ENDPOINT RIMOSSO: GET /api/workflows/triggers/workflows/{workflow_id}/input-nodes
#
# Il frontend ora utilizza l'endpoint corretto nel workflow_router.py che è stato
# sistemato per gestire nodi personalizzati senza dipendere da import dinamici.
