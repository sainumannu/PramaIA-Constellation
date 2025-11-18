"""
Router di compatibilità per gestire le richieste legacy a /api/pdf-monitor
Questo router inoltrerà le richieste al nuovo endpoint /api/document-monitor
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

import logging
import httpx
import aiohttp
import json

# Importa il router attuale per accedere ai dati registrati
from .plugins_router import registered_plugins, PluginRegistration
from backend.services.document_monitor_service import process_document_with_pdk

router = APIRouter(prefix="/api/pdf-monitor", tags=["pdf-monitor-legacy"])
logger = logging.getLogger(__name__)

@router.get("/clients")
async def get_registered_clients_legacy():
    """
    Endpoint di compatibilità: reindirizza a /api/document-monitor/clients
    """
    logger.warning("Richiesta legacy a /api/pdf-monitor/clients - Si consiglia di aggiornare all'endpoint /api/document-monitor/clients")
    return {"plugins": list(registered_plugins.values())}

@router.post("/clients/register")
async def register_pdf_monitor_client_legacy(registration: PluginRegistration):
    """
    Endpoint di compatibilità: reindirizza a /api/document-monitor/clients/register
    """
    logger.warning("Richiesta legacy a /api/pdf-monitor/clients/register - Si consiglia di aggiornare all'endpoint /api/document-monitor/clients/register")
    
    try:
        # Verifica se il plugin è già registrato con lo stesso endpoint
        if (registration.id in registered_plugins and 
            registered_plugins[registration.id]['endpoint'] == registration.endpoint):
            logger.info(f"Plugin già registrato (legacy): {registration.name} ({registration.id})")
            return {"status": "success", "message": "Plugin già registrato"}
        
        # Altrimenti, registra il plugin
        registered_plugins[registration.id] = registration.dict()
        logger.info(f"Plugin registrato (legacy): {registration.name} ({registration.id}) su {registration.endpoint}")
        return {"status": "success", "message": "Plugin registrato con successo"}
    except Exception as e:
        logger.error(f"Errore registrazione plugin (legacy): {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")

@router.delete("/clients/{client_id}")
async def unregister_client_legacy(client_id: str):
    """
    Endpoint di compatibilità: reindirizza a /api/document-monitor/clients/{client_id}
    """
    logger.warning(f"Richiesta legacy a /api/pdf-monitor/clients/{client_id} - Si consiglia di aggiornare all'endpoint /api/document-monitor/clients/{client_id}")
    
    if client_id in registered_plugins:
        del registered_plugins[client_id]
        return {"status": "success", "message": "Plugin rimosso"}
    raise HTTPException(status_code=404, detail="Plugin non trovato")

@router.post("/upload/")
async def upload_pdf_legacy(
    file: UploadFile = File(...),
    client_id: str = Form("system"),
    original_path: str = Form("")
):
    """
    Endpoint di compatibilità per upload PDF: reindirizza a document_monitor_service
    """
    logger.warning(f"Richiesta legacy a /api/pdf-monitor/upload - Si consiglia di aggiornare all'endpoint /api/document-monitor/upload")
    
    try:
        # Leggi il contenuto del file
        file_bytes = await file.read()
        
        # Usa lo stesso servizio document_monitor_service per processare il file
        result = await process_document_with_pdk(
            file_bytes=file_bytes,
            filename=file.filename or "documento_senza_nome.pdf",
            client_id=client_id,
            original_path=original_path
        )
        
        return result
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione del PDF (endpoint legacy): {str(e)}")
        return {
            "status": "error",
            "message": f"Errore durante l'elaborazione: {str(e)}"
        }

# Aggiungi altri endpoint di compatibilità secondo necessità
