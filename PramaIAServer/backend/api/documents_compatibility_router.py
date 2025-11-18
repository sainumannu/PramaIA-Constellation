"""
Router per la gestione dei documenti nel database 
Questo file aggiunge un router di compatibilità per gli endpoint legacy
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
import logging
import os
import requests

# Import per la dipendenza di autenticazione
from backend.auth.dependencies import get_current_user
from backend.routers.database_management_router import get_vectorstore_statistics, get_vectorstore_documents
from backend.core.config import VECTORSTORE_SERVICE_BASE_URL, USE_VECTORSTORE_SERVICE

router = APIRouter(prefix="/api/database-management/documents", tags=["Documents Compatibility"])
logger = logging.getLogger(__name__)

# Versione autenticata
@router.get("/status/")
async def get_documents_status(current_user = Depends(get_current_user)):
    """
    Endpoint di compatibilità per il frontend. 
    Reindirizza a /api/database-management/vectorstore/statistics
    """
    logger.info("Richiesta a /api/database-management/documents/status/ reindirizzata a vectorstore/statistics")
    return await get_vectorstore_statistics(current_user)

# Versione autenticata
@router.get("/")
async def get_documents_list(current_user = Depends(get_current_user)):
    """
    Endpoint di compatibilità per il frontend.
    Reindirizza a /api/database-management/vectorstore/documents
    """
    logger.info("Richiesta a /api/database-management/documents/ reindirizzata a vectorstore/documents")
    return await get_vectorstore_documents(current_user)

# Versione pubblica - non richiede autenticazione
@router.get("/status/public/")
async def get_documents_status_public():
    """
    Endpoint pubblico di compatibilità per il frontend.
    Reindirizza a /api/database-management/vectorstore/statistics
    Non richiede autenticazione.
    """
    logger.info("Richiesta pubblica a /api/database-management/documents/status/public/ reindirizzata a vectorstore/statistics")
    try:
        if USE_VECTORSTORE_SERVICE:
            # Richiama direttamente il VectorstoreService
            try:
                response = requests.get(f"{VECTORSTORE_SERVICE_BASE_URL}/api/database-management/vectorstore/statistics", timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Errore nella richiesta al VectorstoreService: {str(e)}")
                return {
                    "success": False,
                    "documents_in_queue": 0,
                    "documents_in_coda": 0,
                    "documents_processed_today": 0,
                    "total_documents": 0,
                    "error": f"Errore di comunicazione con il VectorstoreService: {str(e)}"
                }
        else:
            # Usa le statistiche fittizie
            return {
                "success": True,
                "documents_in_queue": 0,
                "documents_in_coda": 0,
                "documents_processed_today": 0,
                "total_documents": 0,
                "message": "Vector store non supporta statistiche dettagliate"
            }
    except Exception as e:
        logger.error(f"Errore nel recupero delle statistiche pubbliche: {str(e)}")
        return {"error": f"Errore: {str(e)}"}

# Versione pubblica - non richiede autenticazione
@router.get("/public/")
async def get_documents_list_public():
    """
    Endpoint pubblico di compatibilità per il frontend.
    Reindirizza a /api/database-management/vectorstore/documents
    Non richiede autenticazione.
    """
    logger.info("Richiesta pubblica a /api/database-management/documents/public/ reindirizzata a vectorstore/documents")
    try:
        if USE_VECTORSTORE_SERVICE:
            # Richiama direttamente il VectorstoreService
            try:
                response = requests.get(f"{VECTORSTORE_SERVICE_BASE_URL}/api/database-management/vectorstore/documents", timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Errore nella richiesta al VectorstoreService: {str(e)}")
                return {
                    "success": False,
                    "documents": [],
                    "total": 0,
                    "error": f"Errore di comunicazione con il VectorstoreService: {str(e)}"
                }
        else:
            # Usa risposta vuota
            return {
                "success": True,
                "documents": [],
                "total": 0,
                "message": "Nessun documento trovato"
            }
    except Exception as e:
        logger.error(f"Errore nel recupero dei documenti pubblici: {str(e)}")
        return {"error": f"Errore: {str(e)}"}
