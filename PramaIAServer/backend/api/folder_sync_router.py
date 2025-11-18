"""
Router API per la gestione della sincronizzazione cartelle e query strutturali
Espone endpoint per interrogare metadati directory e statistiche file
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel

from backend.services.folder_sync_service import (
    folder_monitor_service,
    query_folder_information,
    get_folder_statistics,
    search_files_by_path
)

router = APIRouter(prefix="/api/folder-sync", tags=["folder-sync"])

# --- Models ---

class FolderMonitorRequest(BaseModel):
    folder_path: str
    user_id: str = "system"

class FolderQueryRequest(BaseModel):
    query: str

class PathSearchRequest(BaseModel):
    path_query: str

# --- Monitoring Endpoints ---

@router.post("/start-monitoring/")
async def start_folder_monitoring(request: FolderMonitorRequest):
    """
    Avvia il monitoraggio automatico di una cartella
    """
    try:
        success = folder_monitor_service.start_monitoring(
            folder_path=request.folder_path,
            user_id=request.user_id
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Monitoraggio avviato per '{request.folder_path}'",
                "folder_path": request.folder_path,
                "user_id": request.user_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Impossibile avviare monitoraggio per '{request.folder_path}'"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore avvio monitoraggio: {str(e)}")

@router.post("/stop-monitoring/")
async def stop_folder_monitoring(folder_path: str):
    """
    Ferma il monitoraggio di una cartella specifica
    """
    try:
        success = folder_monitor_service.stop_monitoring(folder_path)
        
        if success:
            return {
                "status": "success",
                "message": f"Monitoraggio fermato per '{folder_path}'",
                "folder_path": folder_path
            }
        else:
            return {
                "status": "warning",
                "message": f"Cartella '{folder_path}' non era monitorata",
                "folder_path": folder_path
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore stop monitoraggio: {str(e)}")

@router.get("/monitored-folders/")
async def get_monitored_folders():
    """
    Ottieni lista delle cartelle attualmente monitorate
    """
    try:
        monitored = folder_monitor_service.get_monitored_folders()
        
        return {
            "status": "success",
            "monitored_folders": monitored,
            "count": len(monitored)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ottenimento cartelle monitorate: {str(e)}")

@router.post("/stop-all-monitoring/")
async def stop_all_monitoring():
    """
    Ferma il monitoraggio di tutte le cartelle
    """
    try:
        folder_monitor_service.stop_all_monitoring()
        
        return {
            "status": "success",
            "message": "Monitoraggio fermato per tutte le cartelle"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore stop di tutto il monitoraggio: {str(e)}")

# --- Query Endpoints ---

@router.post("/query-folder-info/")
async def query_folder_info(request: FolderQueryRequest):
    """
    Query specializzata per informazioni strutturali su cartelle
    
    Esempi di query:
    - "quanti file ci sono nella cartella documenti?"
    - "cosa contiene la cartella progetti?"
    - "dimensione della cartella immagini"
    """
    try:
        result = query_folder_information(request.query)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore query folder info: {str(e)}")

@router.get("/folder-statistics/")
async def get_folder_stats(
    folder_path: Optional[str] = Query(None, description="Percorso specifico della cartella (opzionale)")
):
    """
    Ottieni statistiche dettagliate di una cartella specifica o di tutte le cartelle monitorate
    
    Se folder_path non è specificato, restituisce statistiche aggregate di tutte le cartelle.
    """
    try:
        result = get_folder_statistics(folder_path)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ottenimento statistiche: {str(e)}")

@router.post("/search-files-by-path/")
async def search_files_path(request: PathSearchRequest):
    """
    Cerca file basandosi sul percorso o nome
    
    Esempi:
    - "trova tutti i file nella cartella documenti/2025"
    - "file PDF in progetti"
    - "immagini nella cartella foto"
    """
    try:
        result = search_files_by_path(request.path_query)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ricerca file per path: {str(e)}")

# --- Utility Endpoints ---

@router.get("/system-info/")
async def get_sync_system_info():
    """
    Informazioni sullo stato del sistema di sincronizzazione
    """
    try:
        monitored = folder_monitor_service.get_monitored_folders()
        
        # Ottieni statistiche globali
        global_stats = get_folder_statistics()
        
        return {
            "status": "success",
            "system_info": {
                "monitored_folders_count": len(monitored),
                "monitored_folders": monitored,
                "global_statistics": global_stats
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ottenimento info sistema: {str(e)}")

@router.get("/health/")
async def health_check():
    """
    Health check per il sistema di sincronizzazione
    """
    try:
        from backend.core.rag_vectorstore import get_vectorstore_status
        
        vectorstore_status = get_vectorstore_status()
        monitored_count = len(folder_monitor_service.get_monitored_folders())
        
        return {
            "status": "healthy",
            "vectorstore": vectorstore_status,
            "monitored_folders": monitored_count,
            "timestamp": "2025-08-16T10:30:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-08-16T10:30:00Z"
        }
