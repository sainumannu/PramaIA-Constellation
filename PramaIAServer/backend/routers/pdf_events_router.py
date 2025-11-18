"""
Router per gestire gli endpoint relativi agli eventi del monitor PDF.
Questo modulo contiene tutti gli endpoint per il cleanup e la gestione degli eventi PDF.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
import os
from typing import Dict, Any

from backend.auth.dependencies import get_current_user
from backend.core.config import PDF_EVENTS_MAX_AGE_HOURS, PDF_EVENTS_MAX_COUNT
from backend.utils.cleanup_utils import cleanup_pdf_events, get_pdf_events_statistics, find_database_path

logger = logging.getLogger(__name__)

# Creiamo un router separato per i PDF events endpoints
router = APIRouter(tags=["pdf-events"])

@router.post("/cleanup", response_model=Dict)
async def execute_pdf_events_cleanup(
    max_age_hours: int = PDF_EVENTS_MAX_AGE_HOURS, 
    max_events: int = PDF_EVENTS_MAX_COUNT,
    current_user = Depends(get_current_user)
):
    """
    Esegue la pulizia automatica degli eventi PDF
    """
    try:
        # Trova il percorso del database
        db_path = find_database_path()
        
        if not db_path:
            raise HTTPException(
                status_code=404,
                detail="Database principale non trovato"
            )
            
        cleanup_results = cleanup_pdf_events(db_path, max_age_hours, max_events)
        
        if cleanup_results["success"]:
            return {
                "success": True,
                "message": "Pulizia eventi PDF completata con successo",
                "deleted": cleanup_results["deleted_by_age"] + cleanup_results["deleted_by_count"],
                "remaining": cleanup_results["final_count"],
                "details": cleanup_results
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Errore durante pulizia eventi PDF: {cleanup_results.get('error', 'Errore sconosciuto')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore imprevisto durante cleanup PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore imprevisto: {str(e)}"
        )

@router.get("/details")
async def get_pdf_events_details(current_user = Depends(get_current_user)):
    """
    Ottiene informazioni dettagliate sugli eventi PDF memorizzati nel database
    """
    try:
        # Trova il percorso del database
        db_path = find_database_path()
        
        if not db_path:
            return {
                "success": False,
                "error": "Database principale non trovato",
                "statistics": {}
            }
        
        # Ottieni le statistiche degli eventi PDF
        stats_result = get_pdf_events_statistics(db_path)
        
        if stats_result["success"]:
            return {
                "success": True,
                "database_path": db_path,
                "statistics": stats_result["statistics"]
            }
        else:
            return {
                "success": False,
                "error": stats_result.get("error", "Errore nel recupero delle statistiche"),
                "database_path": db_path
            }
            
    except Exception as e:
        logger.error(f"Errore nel recupero dei dettagli eventi PDF: {e}")
        return {
            "success": False,
            "error": str(e)
        }