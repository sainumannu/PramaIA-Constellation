"""
Router per le API vectorstore.

Questo modulo gestisce le route per interagire con il VectorstoreService.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.clients.vectorstore_client import VectorstoreServiceClient
from core.config import VECTORSTORE_SERVICE_BASE_URL, USE_VECTORSTORE_SERVICE

router = APIRouter(prefix="/vectorstore", tags=["vectorstore"])

logger = logging.getLogger(__name__)

def get_vectorstore_client() -> VectorstoreServiceClient:
    """
    Dependency per ottenere un client VectorstoreService.
    """
    try:
        # Crea una nuova istanza del client con l'URL configurato
        client = VectorstoreServiceClient(base_url=VECTORSTORE_SERVICE_BASE_URL)
        return client
    except ConnectionError as e:
        logger.error(f"Impossibile connettersi al VectorstoreService: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Servizio VectorstoreService non disponibile: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione del client VectorstoreService: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore nell'inizializzazione del client: {str(e)}"
        )

@router.get("/status")
async def get_status(client: VectorstoreServiceClient = Depends(get_vectorstore_client)):
    """
    Ottiene lo stato del servizio VectorstoreService.
    """
    try:
        # Usa l'endpoint health del servizio
        health = client._request("GET", "/health")
        
        # Recupera anche lo stato della riconciliazione
        reconciliation = client.get_reconciliation_status()
        
        # Formatta la risposta
        response = {
            "status": health.get("status", "error"),
            "version": health.get("version", "unknown"),
            "dependencies": health.get("dependencies", {}),
            "scheduler_enabled": reconciliation.get("scheduler_enabled", False),
            "next_reconciliation": reconciliation.get("next_scheduled", "N/A")
        }
        
        return response
    except Exception as e:
        logger.error(f"Errore nel recuperare lo stato del VectorstoreService: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/settings")
async def get_settings(client: VectorstoreServiceClient = Depends(get_vectorstore_client)):
    """
    Ottiene le impostazioni del servizio VectorstoreService.
    """
    try:
        # Ottieni impostazioni dal servizio
        settings = client._request("GET", "/settings")
        
        # Formatta la risposta per essere compatibile con il frontend
        formatted_settings = {
            "schedule_enabled": settings.get("scheduler", {}).get("enabled", False),
            "schedule_time": settings.get("scheduler", {}).get("schedule_time", "03:00"),
            "chroma_host": settings.get("vectorstore", {}).get("host", "localhost"),
            "chroma_port": settings.get("vectorstore", {}).get("port", 8000),
            "max_worker_threads": settings.get("processing", {}).get("max_workers", 4),
            "batch_size": settings.get("processing", {}).get("batch_size", 100)
        }
        
        return formatted_settings
    except Exception as e:
        logger.error(f"Errore nel recuperare le impostazioni del VectorstoreService: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel recuperare le impostazioni: {str(e)}"
        )

@router.post("/settings")
async def update_settings(
    settings: Dict[str, Any] = Body(...),
    client: VectorstoreServiceClient = Depends(get_vectorstore_client)
):
    """
    Aggiorna le impostazioni del servizio VectorstoreService.
    """
    try:
        # Converti le impostazioni nel formato atteso dal servizio
        service_settings = {
            "scheduler": {
                "enabled": settings.get("schedule_enabled", False),
                "schedule_time": settings.get("schedule_time", "03:00")
            },
            "vectorstore": {
                "host": settings.get("chroma_host", "localhost"),
                "port": settings.get("chroma_port", 8000)
            },
            "processing": {
                "max_workers": settings.get("max_worker_threads", 4),
                "batch_size": settings.get("batch_size", 100)
            }
        }
        
        # Invia le impostazioni al servizio
        response = client._request("POST", "/settings", data=service_settings)
        
        return {"success": True, "message": "Impostazioni aggiornate con successo"}
    except Exception as e:
        logger.error(f"Errore nell'aggiornare le impostazioni del VectorstoreService: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore nell'aggiornare le impostazioni: {str(e)}"
        )

@router.post("/reconciliation/start")
async def start_reconciliation(
    options: Dict[str, Any] = Body({"delete_missing": False}),
    client: VectorstoreServiceClient = Depends(get_vectorstore_client)
):
    """
    Avvia una riconciliazione manuale.
    """
    try:
        # Avvia la riconciliazione
        response = client.start_reconciliation()
        
        return {
            "success": True,
            "message": "Riconciliazione avviata con successo",
            "job_id": response.get("job_id", "unknown")
        }
    except Exception as e:
        logger.error(f"Errore nell'avviare la riconciliazione: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore nell'avviare la riconciliazione: {str(e)}"
        )

@router.get("/documents/list")
async def list_documents(
    collection_name: str = Query("pdf_documents", description="Nome della collezione"),
    limit: int = Query(100, description="Numero massimo di documenti da restituire"),
    offset: int = Query(0, description="Offset per la paginazione"),
    client: VectorstoreServiceClient = Depends(get_vectorstore_client)
):
    """
    Elenca i documenti nel vectorstore.
    """
    try:
        # Ottieni documenti dalla collezione
        response = client.list_documents(collection_name, limit, offset)
        
        # Formatta la risposta
        documents = []
        for doc in response.get("documents", []):
            documents.append({
                "id": doc.get("id", ""),
                "content_preview": doc.get("document", "")[:200] + "...",
                "content": doc.get("document", ""),
                "metadata": doc.get("metadata", {}),
                "source_filename": doc.get("metadata", {}).get("source", "Unknown"),
                "page": doc.get("metadata", {}).get("page", "N/A"),
                "ingest_time": doc.get("metadata", {}).get("created_at", "N/A")
            })
        
        # Ottieni statistiche della collezione
        stats = client.get_collection_stats(collection_name)
        
        return {
            "total": stats.get("document_count", 0),
            "documents": documents,
            "message": f"Mostrando {len(documents)} di {stats.get('document_count', 0)} documenti"
        }
    except Exception as e:
        logger.error(f"Errore nel recuperare i documenti: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel recuperare i documenti: {str(e)}"
        )

@router.post("/documents/query")
async def query_documents(
    query_data: Dict[str, Any] = Body(...),
    client: VectorstoreServiceClient = Depends(get_vectorstore_client)
):
    """
    Esegue una query semantica nel vectorstore.
    """
    try:
        collection_name = query_data.get("collection_name", "pdf_documents")
        query_text = query_data.get("query", "")
        top_k = query_data.get("top_k", 5)
        metadata_filter = query_data.get("metadata_filter", None)
        
        # Esegui la query
        response = client.query(collection_name, query_text, top_k, metadata_filter)
        
        # Formatta i risultati
        results = []
        for match in response.get("matches", []):
            results.append({
                "content": match.get("document", ""),
                "score": match.get("similarity_score", 0),
                "metadata": match.get("metadata", {}),
                "document_id": match.get("document_id", "")
            })
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Errore nell'eseguire la query semantica: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore nell'eseguire la query semantica: {str(e)}"
        )
