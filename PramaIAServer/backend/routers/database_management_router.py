"""
Router per la gestione dei database e reset del sistema
"""
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel
import logging
import os
import sqlite3
import shutil
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.db.database import get_db
from backend.core import rag_vectorstore
from backend.core.config import PDF_EVENTS_MAX_AGE_HOURS, PDF_EVENTS_MAX_COUNT, PDF_EVENTS_AUTO_CLEANUP
from backend.core.config import VECTORSTORE_SERVICE_BASE_URL, USE_VECTORSTORE_SERVICE
from backend.auth.dependencies import get_current_user
from backend.app.clients.vectorstore_client import VectorstoreServiceClient

router = APIRouter(prefix="/api/database-management", tags=["Database Management"])
logger = logging.getLogger(__name__)

class ResetResponse(BaseModel):
    success: bool
    message: str
    details: Dict[str, Any] = {}

def get_vectorstore_client() -> VectorstoreServiceClient:
    """
    Dependency per ottenere un client VectorstoreService.
    """
    if not USE_VECTORSTORE_SERVICE:
        logger.warning("VectorstoreService non è abilitato. Utilizzando il servizio integrato.")
        return None
        
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

@router.post("/reset/vectorstore", response_model=ResetResponse)
async def reset_vectorstore():
    """
    Reset completo del vector store ChromaDB
    """
    # Se il servizio VectorstoreService è abilitato, usa quello
    if USE_VECTORSTORE_SERVICE:
        try:
            client = get_vectorstore_client()
            
            # Ottieni info sullo stato attuale
            collections = client.list_collections()
            total_docs = 0
            
            # Per ogni collezione, ottieni il conteggio dei documenti e poi elimina tutti i documenti
            for collection_name in collections:
                stats = client.get_collection_stats(collection_name)
                total_docs += stats.get("document_count", 0)
                
                # Ottieni tutti i documenti della collezione
                documents = client.list_documents(collection_name, limit=1000, offset=0)
                doc_ids = [doc.get("id") for doc in documents.get("documents", [])]
                
                if doc_ids:
                    # Elimina tutti i documenti dalla collezione uno alla volta
                    for doc_id in doc_ids:
                        client.delete_document(collection_name, doc_id)
            
            # Verifica reset
            new_total = 0
            for collection_name in collections:
                stats = client.get_collection_stats(collection_name)
                new_total += stats.get("document_count", 0)
            
            return ResetResponse(
                success=True,
                message="Vector store resettato con successo",
                details={
                    "documents_removed": total_docs,
                    "new_count": new_total,
                    "service": "VectorstoreService"
                }
            )
        except Exception as e:
            logger.error(f"Errore durante reset VectorstoreService: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Errore durante reset VectorstoreService: {str(e)}")
            
    # Altrimenti usa il vecchio metodo integrato
    try:
        # Ottieni info sullo stato attuale
        status = rag_vectorstore.get_vectorstore_status()
        
        # Reset del vector store
        if rag_vectorstore.chroma_client and rag_vectorstore.chroma_collection:
            # Elimina tutti i documenti dalla collezione
            all_docs = rag_vectorstore.chroma_collection.get()
            if all_docs['ids']:
                rag_vectorstore.chroma_collection.delete(ids=all_docs['ids'])
                logger.info(f"Eliminati {len(all_docs['ids'])} documenti dal vector store")
        
        # Verifica reset
        new_status = rag_vectorstore.get_vectorstore_status()
        
        return ResetResponse(
            success=True,
            message="Vector store resettato con successo",
            details={
                "documents_removed": status.get("documents_in_index", 0),
                "new_count": new_status.get("documents_in_index", 0),
                "service": "Integrato"
            }
        )
    except Exception as e:
        logger.error(f"Errore durante reset vector store: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore durante reset vector store: {str(e)}")

@router.post("/reset/pdf-monitor-events", response_model=ResetResponse)
async def reset_pdf_monitor_events():
    """
    Reset degli eventi del PDF Monitor - sia nel database principale che nei client monitor
    """
    try:
        # Path del database principale
        db_path = os.path.join("backend", "data", "database.db")
        if not os.path.exists(db_path):
            # Prova percorso relativo alternativo
            alt_path = os.path.join(".", "backend", "data", "database.db")
            if os.path.exists(alt_path):
                db_path = alt_path
            else:
                # Prova percorso assoluto
                abs_path = os.path.abspath(os.path.join("backend", "data", "database.db"))
                if os.path.exists(abs_path):
                    db_path = abs_path
        
        if not os.path.exists(db_path):
            return ResetResponse(
                success=False,
                message=f"Database principale non trovato: {db_path}"
            )
        
        # Conta eventi attuali
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
        if not cursor.fetchone():
            conn.close()
            return ResetResponse(
                success=False,
                message="Tabella pdf_monitor_events non trovata nel database principale"
            )
        
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        events_count = cursor.fetchone()[0]
        
        # Reset degli eventi
        cursor.execute("DELETE FROM pdf_monitor_events")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Resetta anche gli eventi nei client PDF Monitor
        # Ottieni tutti i client PDF Monitor registrati
        client_results = {"success": True, "clients_reset": 0, "errors": []}
        
        try:
            # Ottieni i client dal router dei plugin
            from backend.routers.plugins_router import registered_plugins
            
            # Per ogni client, invia richiesta di reset degli eventi
            for client_id, client in registered_plugins.items():
                try:
                    # Chiama l'endpoint di reset eventi del client
                    endpoint = client.get("endpoint", "").rstrip("/")
                    if endpoint:
                        response = requests.post(
                            f"{endpoint}/monitor/events/reset",
                            timeout=5,  # Timeout breve
                            json={"force": True}
                        )
                        
                        if response.status_code == 200:
                            client_results["clients_reset"] += 1
                        else:
                            client_results["errors"].append({
                                "client": client.get("name", "Unknown"),
                                "error": f"Status code: {response.status_code}"
                            })
                except Exception as client_error:
                    client_results["errors"].append({
                        "client": client.get("name", "Unknown"),
                        "error": str(client_error)
                    })
        except Exception as client_list_error:
            logger.error(f"Errore durante il recupero dei client PDF Monitor: {client_list_error}")
            client_results["success"] = False
            client_results["error"] = str(client_list_error)
        
        return ResetResponse(
            success=True,
            message=f"Reset eventi PDF Monitor completato",
            details={
                "events_deleted": deleted_count,
                "events_before": events_count,
                "database_path": db_path,
                "clients_reset": client_results
            }
        )
        
    except Exception as e:
        logger.error(f"Errore durante reset PDF Monitor events: {e}", exc_info=True)
        return ResetResponse(
            success=False,
            message=f"Errore durante reset: {str(e)}"
        )

@router.post("/reset/all", response_model=ResetResponse)
async def reset_all():
    """
    Reset completo di tutto il sistema
    """
    try:
        results = {}
        
        # Reset vector store
        try:
            vectorstore_result = await reset_vectorstore()
            results["vectorstore"] = vectorstore_result.details
        except Exception as e:
            results["vectorstore"] = {"error": str(e)}
        
        # Reset eventi PDF Monitor
        try:
            events_result = await reset_pdf_monitor_events()
            results["pdf_monitor_events"] = events_result.details
        except Exception as e:
            results["pdf_monitor_events"] = {"error": str(e)}
        
        return ResetResponse(
            success=True,
            message="Reset completo del sistema completato",
            details=results
        )
    except Exception as e:
        logger.error(f"Errore durante reset completo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore durante reset completo: {str(e)}")

@router.get("/test")
async def test_endpoint():
    """
    Endpoint di test per verificare che il router funzioni
    """
    return {"message": "Database management router funziona!", "status": "ok"}

@router.get("/status", response_model=Dict[str, Any])
async def get_database_status():
    """
    Ottieni lo stato di tutti i database (senza autenticazione per test)
    """
    try:
        # Definisci il percorso del database principale
        db_path = "backend/db/database.db"
        # Se il database non esiste nel percorso backend/db, prova i percorsi alternativi
        if not os.path.exists(db_path):
            # Prova il percorso legacy
            legacy_path = "backend/data/database.db"
            if os.path.exists(legacy_path):
                db_path = legacy_path
            else:
                db_path = "database.db"
            
        status = {}
        
        # Stato vector store
        try:
            # Se il servizio VectorstoreService è abilitato, usa quello
            if USE_VECTORSTORE_SERVICE:
                try:
                    client = get_vectorstore_client()
                    
                    # Ottieni informazioni sullo stato del servizio
                    health = client._request("GET", "/health")
                    
                    # Ottieni statistiche per ogni collezione
                    collections = client.list_collections()
                    collection_stats = {}
                    
                    for collection_name in collections:
                        collection_stats[collection_name] = client.get_collection_stats(collection_name)
                    
                    status["vectorstore"] = {
                        "service": "VectorstoreService",
                        "status": health.get("status", "unknown"),
                        "version": health.get("version", "unknown"),
                        "collections": collection_stats
                    }
                except Exception as vs_error:
                    status["vectorstore"] = {
                        "service": "VectorstoreService",
                        "status": "error",
                        "error": str(vs_error)
                    }
            else:
                # Altrimenti usa il vecchio metodo integrato
                vectorstore_status = rag_vectorstore.get_vectorstore_status()
                status["vectorstore"] = vectorstore_status
        except Exception as e:
            status["vectorstore"] = {"error": str(e)}
        
        # Stato database principale
        try:
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                
                # Conta tabelle e record
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Lista tabelle
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                
                conn.close()
                
                status["main_database"] = {
                    "path": db_path,
                    "size_bytes": db_size,
                    "tables": table_counts
                }
            else:
                status["main_database"] = {"error": "Database non trovato"}
        except Exception as e:
            status["main_database"] = {"error": str(e)}
        
        # Stato PDF Monitor events (ora nel database principale)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verifica se la tabella esiste
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
                total_events = cursor.fetchone()[0]
                
                cursor.execute("SELECT status, COUNT(*) FROM pdf_monitor_events GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                # Aggiungi informazioni aggiuntive
                cursor.execute("SELECT COUNT(DISTINCT file_name) FROM pdf_monitor_events")
                unique_files = cursor.fetchone()[0]
                
                status["pdf_monitor_events"] = {
                    "path": db_path,
                    "total_events": total_events,
                    "unique_files": unique_files,
                    "by_status": status_counts
                }
            else:
                status["pdf_monitor_events"] = {"error": "Tabella pdf_monitor_events non trovata"}
            
            conn.close()
        except Exception as e:
            status["pdf_monitor_events"] = {"error": str(e)}
        
        return status
    except Exception as e:
        logger.error(f"Errore durante recupero stato database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore durante recupero stato: {str(e)}")

@router.get("/vectorstore/documents")
async def get_vectorstore_documents(current_user = Depends(get_current_user)):
    """
    Ottieni dettagli sui documenti nel vector store
    """
    # Se il servizio VectorstoreService è abilitato, usa quello
    if USE_VECTORSTORE_SERVICE:
        try:
            client = get_vectorstore_client()
            
            # Usa il metodo dedicato per ottenere i documenti nel formato compatibile con il frontend
            try:
                # Prima prova con il nuovo metodo diretto
                response = client.get_vectorstore_documents()
                logger.info("Documenti del vectorstore ottenuti tramite endpoint frontend-compatibile")
                return response
            except Exception as e1:
                # Se fallisce, prova con il vecchio metodo
                logger.warning(f"Fallimento endpoint compatibile: {str(e1)}, provo con metodo tradizionale")
                
                collection_name = "pdf_documents"  # Nome della collezione predefinita
                limit = 100  # Numero massimo di documenti da restituire
                offset = 0   # Offset per la paginazione
                
                # Ottieni documenti dalla collezione
                response = client.list_documents(collection_name, limit, offset)
                
                # Formatta la risposta
                documents = []
                for doc in response.get("documents", []):
                    documents.append({
                        "id": doc.get("id", ""),
                        "source": doc.get("metadata", {}).get("source", "Unknown"),
                        "source_filename": doc.get("metadata", {}).get("source_filename", "Unknown"),
                        "page": doc.get("metadata", {}).get("page", "Unknown"),
                        "ingest_time": doc.get("metadata", {}).get("ingest_time_utc", "Unknown"),
                        "content_preview": doc.get("document", "")[:200] + "..." if len(doc.get("document", "")) > 200 else doc.get("document", ""),
                        "metadata": doc.get("metadata", {})
                    })
                
                # Ottieni statistiche della collezione
                stats = client.get_collection_stats(collection_name)
                
                return {
                    "success": True,
                    "documents": documents,
                    "total": stats.get("document_count", 0),
                    "message": f"Trovati {len(documents)} documenti nel vector store"
                }
        except Exception as e:
            logger.error(f"Errore durante recupero documenti da VectorstoreService: {e}", exc_info=True)
            return {
                "success": False,
                "documents": [],
                "total": 0,
                "error": str(e)
            }
    
    # Altrimenti usa il vecchio metodo integrato
    try:
        # Accesso al client ChromaDB
        if not rag_vectorstore.chroma_client:
            return {
                "success": False,
                "documents": [],
                "total": 0,
                "message": "Vector store non inizializzato"
            }
        
        # Ottieni la collezione
        collection = rag_vectorstore.chroma_client.get_collection(name=rag_vectorstore.CHROMA_COLLECTION_NAME)
        
        # Ottieni tutti i documenti
        all_docs = collection.get(include=["metadatas", "documents"])
        
        documents = []
        metadatas = all_docs.get('metadatas', []) or []
        docs_content = all_docs.get('documents', []) or []
        
        for i, doc_id in enumerate(all_docs['ids']):
            metadata = metadatas[i] if i < len(metadatas) else {}
            document = docs_content[i] if i < len(docs_content) else ""
            
            documents.append({
                "id": doc_id,
                "source": metadata.get("source", "Unknown"),
                "source_filename": metadata.get("source_filename", "Unknown"),
                "page": metadata.get("page", "Unknown"),
                "ingest_time": metadata.get("ingest_time_utc", "Unknown"),
                "content_preview": document[:200] + "..." if len(document) > 200 else document,
                "metadata": metadata
            })
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents),
            "message": f"Trovati {len(documents)} documenti nel vector store"
        }
    except Exception as e:
        logger.error(f"Errore durante recupero documenti vector store: {e}", exc_info=True)
        return {
            "success": False,
            "documents": [],
            "total": 0,
            "error": str(e)
        }

@router.get("/vectorstore/statistics")
async def get_vectorstore_statistics(current_user = Depends(get_current_user)):
    """
    Ottieni le statistiche del vectorstore per l'elaborazione dei documenti
    """
    # Se il servizio VectorstoreService è abilitato, usa quello
    if USE_VECTORSTORE_SERVICE:
        try:
            client = get_vectorstore_client()
            
            # Usa il metodo dedicato per ottenere le statistiche nel formato compatibile con il frontend
            try:
                # Prima prova con il nuovo metodo diretto
                response = client.get_vectorstore_statistics()
                logger.info("Statistiche del vectorstore ottenute tramite endpoint frontend-compatibile")
                return response
            except Exception as e1:
                # Se fallisce, prova con il vecchio metodo
                logger.warning(f"Fallimento endpoint compatibile: {str(e1)}, provo con metodo tradizionale")
                
                # Ottieni statistiche del processing
                response = client.get_processing_stats()
                return response
                
        except Exception as e:
            logger.error(f"Errore durante recupero statistiche da VectorstoreService: {e}", exc_info=True)
            return {
                "success": False,
                "documents_in_queue": 0,
                "documents_in_coda": 0,
                "documents_processed_today": 0,
                "total_documents": 0,
                "error": str(e)
            }
    
    # Altrimenti usa statistiche fittizie
    return {
        "success": True,
        "documents_in_queue": 0,
        "documents_in_coda": 0,
        "documents_processed_today": 0,
        "total_documents": 0,
        "message": "Vector store non supporta statistiche dettagliate"
    }

@router.get("/vectorstore/settings")
async def get_vectorstore_settings(current_user = Depends(get_current_user)):
    """
    Ottiene le impostazioni del servizio VectorstoreService.
    """
    if USE_VECTORSTORE_SERVICE:
        try:
            client = get_vectorstore_client()
            
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
            
            return {
                "success": True,
                "settings": formatted_settings
            }
        except Exception as e:
            logger.error(f"Errore nel recuperare le impostazioni del VectorstoreService: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    else:
        # Impostazioni di default per il servizio integrato
        return {
            "success": True,
            "settings": {
                "schedule_enabled": False,
                "schedule_time": "03:00",
                "chroma_host": "localhost",
                "chroma_port": 8000,
                "max_worker_threads": 4,
                "batch_size": 100
            },
            "message": "VectorstoreService non abilitato. Utilizzando il servizio integrato."
        }

@router.post("/vectorstore/settings")
async def update_vectorstore_settings(
    settings: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Aggiorna le impostazioni del servizio VectorstoreService.
    """
    if USE_VECTORSTORE_SERVICE:
        try:
            client = get_vectorstore_client()
            
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
            return {
                "success": False,
                "error": str(e)
            }
    else:
        return {
            "success": False,
            "message": "VectorstoreService non abilitato. Impossibile aggiornare le impostazioni."
        }

@router.post("/vectorstore/query")
async def query_vectorstore(
    query_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Esegue una query semantica nel VectorstoreService.
    """
    if USE_VECTORSTORE_SERVICE:
        try:
            client = get_vectorstore_client()
            
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
                    "document_id": match.get("id", "")
                })
            
            return {
                "success": True,
                "results": results,
                "total": len(results),
                "query": query_text
            }
        except Exception as e:
            logger.error(f"Errore nell'eseguire la query semantica: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    else:
        try:
            # Utilizza il metodo integrato
            # TODO: Implementare la query integrata
            return {
                "success": False,
                "message": "Query sul servizio integrato non ancora implementata"
            }
        except Exception as e:
            logger.error(f"Errore nell'eseguire la query semantica integrata: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

def cleanup_pdf_events(db_path, max_age_hours=PDF_EVENTS_MAX_AGE_HOURS, max_events=PDF_EVENTS_MAX_COUNT):
    """
    Pulisce automaticamente gli eventi PDF più vecchi di un certo periodo o in eccesso rispetto al limite massimo
    
    Args:
        db_path (str): Percorso del database
        max_age_hours (int): Età massima degli eventi in ore
        max_events (int): Numero massimo di eventi da mantenere
        
    Returns:
        dict: Statistiche del cleanup
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "reason": "table_not_found"}
        
        # Conteggio iniziale
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        initial_count = cursor.fetchone()[0]
        
        # Timestamp minimo (eventi più vecchi di questo saranno eliminati)
        min_timestamp = (datetime.now() - timedelta(hours=max_age_hours)).strftime('%Y-%m-%dT%H:%M:%S')
        
        # 1. Prima eliminiamo per età
        cursor.execute(
            "DELETE FROM pdf_monitor_events WHERE timestamp < ?",
            (min_timestamp,)
        )
        deleted_by_age = cursor.rowcount
        
        # 2. Poi verifico quanti eventi rimangono
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        remaining_events = cursor.fetchone()[0]
        
        deleted_by_count = 0
        # 3. Se ci sono ancora troppi eventi, eliminiamo i più vecchi
        if remaining_events > max_events:
            # Troviamo il timestamp dell'evento N-esimo più recente
            cursor.execute(
                "SELECT timestamp FROM pdf_monitor_events ORDER BY timestamp DESC LIMIT 1 OFFSET ?", 
                (max_events,)
            )
            result = cursor.fetchone()
            if result:
                cutoff_timestamp = result[0]
                # Eliminiamo tutti gli eventi più vecchi di questo
                cursor.execute(
                    "DELETE FROM pdf_monitor_events WHERE timestamp <= ?",
                    (cutoff_timestamp,)
                )
                deleted_by_count = cursor.rowcount
        
        # Commit delle modifiche
        conn.commit()
        
        # Statistiche finali
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        final_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "initial_count": initial_count,
            "deleted_by_age": deleted_by_age,
            "deleted_by_count": deleted_by_count,
            "final_count": final_count,
            "max_age_hours": max_age_hours,
            "max_events": max_events
        }
        
    except Exception as e:
        logger.error(f"Errore durante cleanup eventi PDF: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@router.post("/pdf-events/cleanup", response_model=Dict)
async def execute_pdf_events_cleanup(
    max_age_hours: int = PDF_EVENTS_MAX_AGE_HOURS, 
    max_events: int = PDF_EVENTS_MAX_COUNT,
    current_user = Depends(get_current_user)
):
    """
    Esegue la pulizia automatica degli eventi PDF
    """
    try:
        # Percorso del database principale
        db_path = "backend/db/database.db"
        if not os.path.exists(db_path):
            # Prova il percorso legacy
            legacy_path = "backend/data/database.db"
            if os.path.exists(legacy_path):
                db_path = legacy_path
            else:
                db_path = "database.db"
            
        if not os.path.exists(db_path):
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
        logger.error(f"Errore durante pulizia eventi PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore durante pulizia eventi PDF: {str(e)}")

@router.get("/pdf-events/details")
async def get_pdf_events_details(current_user = Depends(get_current_user)):
    """
    Ottieni dettagli degli eventi PDF dal database principale
    """
    try:
        # Percorso del database principale
        db_path = "backend/db/database.db"
        if not os.path.exists(db_path):
            # Prova il percorso legacy
            legacy_path = "backend/data/database.db"
            if os.path.exists(legacy_path):
                db_path = legacy_path
            else:
                db_path = "database.db"
            
        if not os.path.exists(db_path):
            return {
                "success": False,
                "total_events": 0,
                "message": "Database principale non trovato"
            }
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
        if not cursor.fetchone():
            conn.close()
            return {
                "success": False,
                "total_events": 0,
                "message": "Tabella pdf_monitor_events non trovata"
            }
        
        # Conta totale eventi
        cursor.execute("SELECT COUNT(*) FROM pdf_monitor_events")
        total_events = cursor.fetchone()[0]
        
        # Ottieni date min e max
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM pdf_monitor_events")
        oldest_event, newest_event = cursor.fetchone()
        
        # Numero di eventi per tipo
        cursor.execute("""
            SELECT event_type, COUNT(*) 
            FROM pdf_monitor_events 
            GROUP BY event_type
        """)
        event_types = {event_type: count for event_type, count in cursor.fetchall()}
        
        # Statistiche per cartella
        cursor.execute("""
            SELECT folder_path, COUNT(*) 
            FROM pdf_monitor_events 
            GROUP BY folder_path
        """)
        folders = {folder or "N/A": count for folder, count in cursor.fetchall()}
        
        # Statistiche per file
        cursor.execute('''
            SELECT file_name, COUNT(*) as count, 
                   GROUP_CONCAT(DISTINCT status) as statuses,
                   COUNT(DISTINCT document_id) as unique_document_ids
            FROM pdf_monitor_events 
            GROUP BY file_name
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        file_stats = cursor.fetchall()
        
        # Formatta le statistiche per file
        file_statistics = []
        for stat in file_stats:
            file_statistics.append({
                "file_name": stat[0],
                "event_count": stat[1],
                "statuses": stat[2].split(",") if stat[2] else [],
                "unique_document_ids": stat[3]
            })
        
        conn.close()
        
        return {
            "success": True,
            "total_events": total_events,
            "oldest_event": oldest_event,
            "newest_event": newest_event,
            "event_types": event_types,
            "folders": folders,
            "file_statistics": file_statistics
        }
            
    except Exception as e:
        logger.error(f"Errore durante recupero dettagli eventi PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore durante recupero dettagli eventi PDF: {str(e)}")

