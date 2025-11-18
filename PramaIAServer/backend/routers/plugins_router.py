from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["plugins"])

# Modello per la registrazione dei plugin
class PluginRegistration(BaseModel):
    id: str
    name: str
    endpoint: str
    scanPaths: Optional[List[str]] = []
    online: bool = True

# Storage temporaneo per i plugin registrati (in memoria)
# In futuro si potrebbe spostare su database
registered_plugins = {}

@router.post("/document-monitor/clients/register")
async def register_pdf_monitor_client(registration: PluginRegistration):
    """Endpoint per la registrazione dei plugin PDF Monitor"""
    try:
        # Verifica se il plugin è già registrato con lo stesso endpoint
        if (registration.id in registered_plugins and 
            registered_plugins[registration.id]['endpoint'] == registration.endpoint):
            logger.info(f"Plugin già registrato: {registration.name} ({registration.id})")
            return {"status": "success", "message": "Plugin già registrato"}
        
        # Altrimenti, registra il plugin
        registered_plugins[registration.id] = registration.dict()
        logger.info(f"Plugin registrato: {registration.name} ({registration.id}) su {registration.endpoint}")
        return {"status": "success", "message": "Plugin registrato con successo"}
    except Exception as e:
        logger.error(f"Errore registrazione plugin: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")

@router.get("/document-monitor/clients")
async def get_registered_clients():
    """Ottieni la lista dei plugin registrati"""
    return {"plugins": list(registered_plugins.values())}

@router.delete("/document-monitor/clients/{client_id}")
async def unregister_client(client_id: str):
    """Rimuovi un plugin dalla registrazione"""
    if client_id in registered_plugins:
        del registered_plugins[client_id]
        return {"status": "success", "message": "Plugin rimosso"}
    raise HTTPException(status_code=404, detail="Plugin non trovato")
