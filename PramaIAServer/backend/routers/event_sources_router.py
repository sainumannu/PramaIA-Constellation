"""
Router per la gestione delle Event Sources
Espone API per ottenere sorgenti di eventi disponibili e i loro tipi
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.core.event_sources_registry import event_source_registry
from backend.schemas.user_schemas import UserInToken
from backend.db.database import get_db

router = APIRouter(
    prefix="/api/event-sources",
    tags=["event-sources"],
    responses={404: {"description": "Non trovato"}},
)

@router.get(
    "/",
    summary="Ottieni tutte le sorgenti di eventi disponibili"
)
def get_available_event_sources(
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera tutte le sorgenti di eventi disponibili nel sistema.
    Include sia sorgenti built-in che esterne.
    """
    try:
        sources = event_source_registry.get_available_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel recupero delle sorgenti: {str(e)}"
        )

@router.get(
    "/{source_id}",
    summary="Ottieni dettagli di una sorgente specifica"
)
def get_event_source(
    source_id: str,
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera i dettagli di una sorgente di eventi specifica.
    """
    source = event_source_registry.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=404,
            detail=f"Sorgente {source_id} non trovata"
        )
    return source

@router.get(
    "/{source_id}/events",
    summary="Ottieni tipi di eventi per una sorgente"
)
def get_event_types_for_source(
    source_id: str,
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera tutti i tipi di eventi supportati da una sorgente specifica.
    """
    event_types = event_source_registry.get_event_types_for_source(source_id)
    if not event_types:
        raise HTTPException(
            status_code=404,
            detail=f"Nessun tipo di evento trovato per la sorgente {source_id}"
        )
    return {"eventTypes": event_types}

@router.get(
    "/events/all",
    summary="Ottieni tutti i tipi di eventi disponibili"
)
def get_all_event_types(
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Recupera tutti i tipi di eventi disponibili da tutte le sorgenti.
    Utile per popolare dropdown nel frontend.
    """
    try:
        all_events = event_source_registry.get_all_event_types()
        return {"eventTypes": all_events}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel recupero dei tipi di eventi: {str(e)}"
        )

@router.post(
    "/register",
    summary="Registra una nuova sorgente di eventi"
)
def register_event_source(
    source_config: dict,
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Registra una nuova sorgente di eventi nel sistema.
    Richiede privilegi di amministratore.
    """
    # TODO: Aggiungere controllo ruolo admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo gli amministratori possono registrare nuove sorgenti"
        )
    
    try:
        success = event_source_registry.register_source(source_config)
        if success:
            return {
                "message": f"Sorgente {source_config.get('name', 'sconosciuta')} registrata con successo",
                "sourceId": source_config.get('id')
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Configurazione sorgente non valida"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nella registrazione: {str(e)}"
        )

@router.delete(
    "/{source_id}",
    summary="Rimuovi una sorgente di eventi"
)
def unregister_event_source(
    source_id: str,
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Rimuove una sorgente di eventi dal sistema.
    Richiede privilegi di amministratore.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo gli amministratori possono rimuovere sorgenti"
        )
    
    success = event_source_registry.unregister_source(source_id)
    if success:
        return {"message": f"Sorgente {source_id} rimossa con successo"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Sorgente {source_id} non trovata"
        )
