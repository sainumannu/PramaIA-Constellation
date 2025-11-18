import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdk_proxy")

# Configurazione del router
pdk_router = APIRouter(prefix="/api/pdk", tags=["pdk"])

import os

# URL di base del server PDK (leggi da variabili d'ambiente se presenti)
PDK_BASE = os.getenv('PDK_SERVER_BASE_URL') or os.getenv('PDK_SERVER_URL') or 'http://localhost:3001'
PDK_SERVER_URL = PDK_BASE.rstrip('/') + '/api'

# Client HTTP asincrono
http_client = httpx.AsyncClient(timeout=30.0)

@pdk_router.get("/plugins")
async def get_plugins():
    """Proxy per la lista di plugin PDK"""
    try:
        response = await http_client.get(f"{PDK_SERVER_URL}/plugins")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Errore nella richiesta al server PDK: {e}")
        raise HTTPException(status_code=502, detail=f"Errore nel proxy PDK: {str(e)}")

@pdk_router.get("/plugins/{plugin_id}")
async def get_plugin_by_id(plugin_id: str):
    """Proxy per i dettagli di un plugin PDK specifico"""
    try:
        response = await http_client.get(f"{PDK_SERVER_URL}/plugins/{plugin_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Se non troviamo il plugin, proviamo a cercarlo come event source
            try:
                es_response = await http_client.get(f"{PDK_SERVER_URL}/event-sources/{plugin_id}")
                es_response.raise_for_status()
                return es_response.json()
            except httpx.HTTPError:
                pass  # Se anche questo fallisce, solleviamo l'errore originale
        logger.error(f"Errore nella richiesta al server PDK: {e}")
        raise HTTPException(
            status_code=e.response.status_code, 
            detail=f"Errore nel proxy PDK: {str(e)}"
        )
    except httpx.HTTPError as e:
        logger.error(f"Errore nella richiesta al server PDK: {e}")
        raise HTTPException(status_code=502, detail=f"Errore nel proxy PDK: {str(e)}")

@pdk_router.get("/event-sources")
async def get_event_sources():
    """Proxy per la lista di event sources PDK"""
    try:
        response = await http_client.get(f"{PDK_SERVER_URL}/event-sources")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Errore nella richiesta al server PDK: {e}")
        raise HTTPException(status_code=502, detail=f"Errore nel proxy PDK: {str(e)}")

@pdk_router.get("/event-sources/{source_id}")
async def get_event_source_by_id(source_id: str):
    """Proxy per i dettagli di un event source PDK specifico"""
    try:
        response = await http_client.get(f"{PDK_SERVER_URL}/event-sources/{source_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Errore nella richiesta al server PDK: {e}")
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, "response") else 502,
            detail=f"Errore nel proxy PDK: {str(e)}"
        )

@pdk_router.get("/tags")
async def get_tags():
    """Proxy per la lista di tag PDK"""
    try:
        response = await http_client.get(f"{PDK_SERVER_URL}/tags")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Errore nella richiesta al server PDK: {e}")
        raise HTTPException(status_code=502, detail=f"Errore nel proxy PDK: {str(e)}")

# Alla chiusura dell'applicazione, chiudi il client HTTP
@pdk_router.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

def get_pdk_router():
    """Restituisce il router configurato per il proxy PDK"""
    return pdk_router
