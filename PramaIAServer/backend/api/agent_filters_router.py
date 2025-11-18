"""
Router API per la gestione dei filtri degli agent
Consente agli agent di interrogare il server per sapere come gestire diversi tipi di file
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from backend.services.agent_filter_service import agent_filter_service, FilterAction

router = APIRouter(prefix="/api/agent-filters", tags=["agent-filters"])

# --- Models ---

class FileEvaluationRequest(BaseModel):
    file_path: str
    file_size_bytes: Optional[int] = None

class BatchFileEvaluationRequest(BaseModel):
    files: List[Dict[str, Any]]  # [{"file_path": "...", "file_size_bytes": 123}, ...]

class CustomFilterRequest(BaseModel):
    name: str
    description: str
    extensions: List[str]
    max_size_mb: Optional[int] = None
    min_size_mb: Optional[int] = None
    action: str  # "process_full", "metadata_only", "skip"
    extract_metadata: List[str] = []
    priority: int = 1000

class FilterUpdateRequest(BaseModel):
    filter_name: str
    updates: Dict[str, Any]

# --- Agent Query Endpoints ---

@router.post("/evaluate-file/")
async def evaluate_file(request: FileEvaluationRequest):
    """
    Valuta un singolo file per determinare come l'agent deve gestirlo
    
    Returns:
        - action: "process_full", "metadata_only", "skip"
        - should_process: bool - se elaborare il contenuto
        - should_upload: bool - se inviare al server
        - extract_metadata: list - metadati da estrarre
    """
    try:
        result = agent_filter_service.evaluate_file(
            file_path=request.file_path,
            file_size_bytes=request.file_size_bytes
        )
        
        return {
            "status": "success",
            "file_path": request.file_path,
            "evaluation": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore valutazione file: {str(e)}")

@router.post("/evaluate-batch/")
async def evaluate_batch_files(request: BatchFileEvaluationRequest):
    """
    Valuta un lotto di file per ottimizzare le chiamate API degli agent
    
    Utile quando l'agent ha scoperto molti file e vuole valutarli in una volta
    """
    try:
        results = []
        
        for file_info in request.files:
            file_path = file_info.get("file_path")
            file_size = file_info.get("file_size_bytes")
            
            if not file_path:
                results.append({
                    "file_path": "unknown",
                    "evaluation": {
                        "action": "skip",
                        "error": "file_path mancante"
                    }
                })
                continue
                
            try:
                evaluation = agent_filter_service.evaluate_file(file_path, file_size)
                results.append({
                    "file_path": file_path,
                    "evaluation": evaluation
                })
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "evaluation": {
                        "action": "skip",
                        "error": str(e)
                    }
                })
                
        # Statistiche del batch
        stats = {
            "total_files": len(results),
            "process_full": len([r for r in results if r["evaluation"].get("action") == "process_full"]),
            "metadata_only": len([r for r in results if r["evaluation"].get("action") == "metadata_only"]),
            "skip": len([r for r in results if r["evaluation"].get("action") == "skip"]),
            "errors": len([r for r in results if "error" in r["evaluation"]])
        }
        
        return {
            "status": "success",
            "batch_size": len(request.files),
            "results": results,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore valutazione batch: {str(e)}")

@router.get("/filters-summary/")
async def get_filters_summary():
    """
    Ottieni riassunto di tutti i filtri configurati
    
    Utile per gli agent per capire quali tipi di file sono supportati
    """
    try:
        summary = agent_filter_service.get_filters_summary()
        
        return {
            "status": "success",
            "summary": summary,
            "timestamp": "2025-08-16T10:30:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ottenimento summary filtri: {str(e)}")

@router.get("/supported-extensions/")
async def get_supported_extensions():
    """
    Ottieni lista di tutte le estensioni supportate organizzate per azione
    
    Endpoint ottimizzato per agent che vogliono fare pre-filtering locale
    """
    try:
        summary = agent_filter_service.get_filters_summary()
        
        extensions_by_action = {
            "process_full": [],
            "metadata_only": [],
            "skip": []
        }
        
        for filter_info in summary["filters"]:
            action = filter_info["action"]
            extensions = filter_info["extensions"]
            
            if action in extensions_by_action:
                extensions_by_action[action].extend(extensions)
                
        # Rimuovi duplicati e ordina
        for action in extensions_by_action:
            extensions_by_action[action] = sorted(list(set(extensions_by_action[action])))
            
        return {
            "status": "success",
            "extensions_by_action": extensions_by_action,
            "all_supported": summary["supported_extensions"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ottenimento estensioni: {str(e)}")

# --- Configuration Management Endpoints ---

@router.get("/filters/")
async def get_all_filters():
    """
    Ottieni configurazione completa di tutti i filtri
    """
    try:
        summary = agent_filter_service.get_filters_summary()
        
        return {
            "status": "success",
            "filters": summary["filters"],
            "total": summary["total_filters"],
            "by_action": summary["filters_by_action"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ottenimento filtri: {str(e)}")

@router.post("/filters/custom/")
async def add_custom_filter(request: CustomFilterRequest):
    """
    Aggiunge un filtro personalizzato
    
    Permette agli admin di configurare filtri specifici per le loro esigenze
    """
    try:
        # Valida action
        valid_actions = [action.value for action in FilterAction]
        if request.action not in valid_actions:
            raise HTTPException(
                status_code=400, 
                detail=f"Action '{request.action}' non valida. Valori possibili: {valid_actions}"
            )
            
        success = agent_filter_service.add_custom_filter({
            "name": request.name,
            "description": request.description,
            "extensions": request.extensions,
            "max_size_mb": request.max_size_mb,
            "min_size_mb": request.min_size_mb,
            "action": request.action,
            "extract_metadata": request.extract_metadata,
            "priority": request.priority
        })
        
        if success:
            return {
                "status": "success",
                "message": f"Filtro personalizzato '{request.name}' aggiunto",
                "filter_name": f"custom_{request.name}"
            }
        else:
            raise HTTPException(status_code=400, detail="Impossibile aggiungere filtro personalizzato")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore aggiunta filtro personalizzato: {str(e)}")

@router.delete("/filters/custom/{filter_name}")
async def remove_custom_filter(filter_name: str):
    """
    Rimuove un filtro personalizzato
    """
    try:
        success = agent_filter_service.remove_custom_filter(filter_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Filtro personalizzato '{filter_name}' rimosso"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Filtro personalizzato '{filter_name}' non trovato")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore rimozione filtro personalizzato: {str(e)}")

# --- Testing and Debug Endpoints ---

@router.post("/test-file/")
async def test_file_against_filters(
    file_path: str = Query(..., description="Percorso del file da testare"),
    file_size_mb: Optional[float] = Query(None, description="Dimensione del file in MB (opzionale)")
):
    """
    Testa un file ipotetico contro tutti i filtri per debugging
    """
    try:
        file_size_bytes = int(file_size_mb * 1024 * 1024) if file_size_mb else None
        
        result = agent_filter_service.evaluate_file(file_path, file_size_bytes)
        
        # Informazioni aggiuntive per debug
        from pathlib import Path
        extension = Path(file_path).suffix.lower()
        
        debug_info = {
            "file_path": file_path,
            "file_extension": extension,
            "file_size_mb": file_size_mb or 0,
            "evaluation_result": result,
            "explanation": f"File '{file_path}' ({extension}) "
                          f"→ Azione: {result['action']} "
                          f"→ Filtro: {result['filter_name']}"
        }
        
        return {
            "status": "success",
            "debug_info": debug_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore test file: {str(e)}")

@router.get("/health/")
async def filters_health_check():
    """
    Health check per il sistema di filtri
    """
    try:
        summary = agent_filter_service.get_filters_summary()
        
        return {
            "status": "healthy",
            "total_filters": summary["total_filters"],
            "filters_by_action": summary["filters_by_action"],
            "supported_extensions_count": len(summary["supported_extensions"]),
            "timestamp": "2025-08-16T10:30:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-08-16T10:30:00Z"
        }
