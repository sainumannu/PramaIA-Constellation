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
from backend.core.config import PDF_EVENTS_MAX_AGE_HOURS, PDF_EVENTS_MAX_COUNT, PDF_EVENTS_AUTO_CLEANUP
from backend.core.config import VECTORSTORE_SERVICE_BASE_URL
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
    # Usa sempre il VectorstoreService
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
            # Usa il VectorstoreService
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
    # Usa sempre il VectorstoreService
    try:
        client = get_vectorstore_client()
        
        # Usa il metodo dedicato per ottenere i documenti nel formato compatibile con il frontend
        try:
            # Prima prova con il nuovo metodo diretto
            response = client.get_vectorstore_documents()
            logger.info("Documenti del vectorstore ottenuti tramite endpoint frontend-compatibile")
            
            # Riformatta i dati per adattarli alla struttura attesa dal frontend
            documents = []
            for doc in response.get("documents", []):
                # Ottiene metadati extra 
                metadata = doc.get("metadata", {})
                doc_id = doc.get("id", "")
                collection_name = "pdf_documents"  # Nome della collezione predefinita
                
                # Per l'anteprima, faremo una richiesta separata per ottenere il contenuto
                content_preview = "⏳ Caricamento anteprima in corso..."
                
                # Formatta il documento per rispettare la struttura attesa dal frontend
                documents.append({
                    "id": doc_id,
                    "source": "vectorstore",
                    "source_filename": doc.get("filename", "Unknown"),
                    "page": metadata.get("pages", "Unknown"),
                    "ingest_time": doc.get("created_at", "Unknown"),
                    "content_preview": content_preview,
                    "metadata": metadata
                })
                
            # Restituisce la risposta formattata
            return {
                "success": True,
                "documents": documents,
                "total": len(documents),
                "message": f"Trovati {len(documents)} documenti nel vector store"
            }
            
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

@router.get("/vectorstore/statistics")
async def get_vectorstore_statistics(current_user = Depends(get_current_user)):
    """
    Ottieni le statistiche del vectorstore per l'elaborazione dei documenti
    """
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

@router.get("/vectorstore/settings")
async def get_vectorstore_settings(current_user = Depends(get_current_user)):
    """
    Ottiene le impostazioni del servizio VectorstoreService.
    """
    try:
        client = get_vectorstore_client()
        
        # Ottieni impostazioni dal servizio
        settings = client._request("GET", "/settings")
        
        # Formatta la risposta per essere compatibile con il frontend
        formatted_settings = {
            "schedule_enabled": settings.get("scheduler", {}).get("enabled", False),
            "schedule_time": settings.get("scheduler", {}).get("schedule_time", "03:00"),
            "max_worker_threads": settings.get("processing", {}).get("max_workers", 4),
            "batch_size": settings.get("processing", {}).get("batch_size", 100)
        }
        
        return formatted_settings
    except Exception as e:
        logger.error(f"Errore nel recuperare le impostazioni del VectorstoreService: {str(e)}")
        return {
            "error": str(e)
        }

@router.post("/vectorstore/settings")
async def update_vectorstore_settings(
    settings: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Aggiorna le impostazioni del servizio VectorstoreService.
    """
    try:
        client = get_vectorstore_client()
        
        # Converti le impostazioni nel formato atteso dal servizio
        service_settings = {
            "scheduler": {
                "enabled": settings.get("schedule_enabled", False),
                "schedule_time": settings.get("schedule_time", "03:00")
            },
            "processing": {
                "max_workers": settings.get("max_worker_threads", 4),
                "batch_size": settings.get("batch_size", 100)
            }
        }
        
        # Invia le impostazioni al servizio
        response = client._request("POST", "/settings", data=service_settings)
        
        return {"message": "Impostazioni aggiornate con successo"}
    except Exception as e:
        logger.error(f"Errore nell'aggiornare le impostazioni del VectorstoreService: {str(e)}")
        return {
            "error": str(e)
        }

@router.get("/vectorstore/status")
async def get_vectorstore_status(current_user = Depends(get_current_user)):
    """
    Ottiene lo stato del servizio VectorstoreService.
    """
    try:
        client = get_vectorstore_client()
        # Chiama l'endpoint /health/dependencies del VectorstoreService per ottenere info dettagliate
        health = client._request("GET", "/health/dependencies")
        
        # Aggiungiamo un flag specifico per la connessione ChromaDB quando usa modalità persistente locale
        if "dependencies" in health and "chroma" in health["dependencies"]:
            health["chroma_connected"] = health["dependencies"]["chroma"].get("connected", 
                                      health["dependencies"]["chroma"].get("status") == "healthy")
        
        try:
            # Otteniamo prima i documenti dall'endpoint frontend-compatibile
            # che sembra funzionare correttamente
            documents_response = client.get_vectorstore_documents()
            documents_in_index = len(documents_response.get("documents", []))
            
            # Otteniamo anche le statistiche generali se disponibili
            try:
                stats = client.get_stats()
            except Exception:
                stats = {}
            
            # Formato compatibile con risposta tradizionale
            return {
                "status": "ok" if documents_in_index > 0 else "empty",
                "documents_in_index": documents_in_index,
                "vector_store": "VectorstoreService",
                "service": "VectorstoreService",
                "chroma_connected": health.get("chroma_connected", True),
                "version": health.get("version", "unknown"),
                "health": health
            }
        except Exception as stats_error:
            logger.error(f"Errore nel recuperare statistiche collezioni: {stats_error}")
            # Continua comunque con le info di base
            return {
                "status": "partial",
                "documents_in_index": 0,  # Dato che non riusciamo a contarli
                "vector_store": "VectorstoreService",
                "service": "VectorstoreService", 
                "error_stats": str(stats_error),
                "chroma_connected": health.get("chroma_connected", False),
                "version": health.get("version", "unknown"),
                "health": health
            }
    except Exception as e:
        logger.error(f"Errore durante recupero stato VectorstoreService: {e}", exc_info=True)
        return {
            "status": "error",
            "documents_in_index": 0,
            "vector_store": "VectorstoreService",
            "service": "VectorstoreService",
            "error": str(e)
        }

@router.post("/vectorstore/query")
async def query_vectorstore(
    query_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Esegue una query semantica nel VectorstoreService.
    """
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

@router.get("/vectorstore/document/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """
    Ottiene il contenuto testuale di un documento nel vectorstore.
    Questo endpoint tenta diversi metodi per recuperare il contenuto:
    1. Recupera il contenuto dai chunk vettorizzati in ChromaDB tramite VectorstoreService
    2. Richiede direttamente il documento completo dal VectorstoreService  
    3. Recupera il testo dal file PDF originale se disponibile
    4. Esegue una query semantica nel vectorstore come ultima risorsa
    """
    try:
        client = get_vectorstore_client()
        
        # METODO 1: Prova a recuperare il contenuto dai chunk vettorizzati in ChromaDB
        try:
            # Usa il nuovo endpoint di query per recuperare il contenuto da ChromaDB
            content_response = client._request("GET", f"/query/document/{document_id}/content")
            
            if content_response and content_response.get("success") and content_response.get("content"):
                content = content_response["content"]
                chunks_count = content_response.get("total_chunks", 0)
                
                # Limita la lunghezza se necessario per l'anteprima
                preview_content = content
                if len(content) > 2000:  # Limita a ~2KB per anteprime veloci
                    preview_content = content[:2000] + "...[CONTENUTO TRONCATO - Mostra il contenuto completo]"
                
                logger.info(f"Contenuto del documento {document_id} recuperato da ChromaDB ({chunks_count} chunks)")
                return {
                    "success": True,
                    "document_id": document_id,
                    "content": preview_content,
                    "full_content_length": len(content),
                    "chunks_count": chunks_count,
                    "source": "chromadb_chunks"
                }
                
        except Exception as e:
            logger.warning(f"Errore nel recupero del contenuto da ChromaDB per {document_id}: {e}")

        # METODO 2: Prova a ottenere il documento direttamente dal VectorstoreService
        try:
            # Prima prova l'endpoint /documents/{document_id} che restituisce il documento completo
            document = client._request("GET", f"/documents/{document_id}")
            
            if document and "document" in document:
                # Alcuni sistemi memorizzano il contenuto completo nel campo "document"
                content = document.get("document", "")
                if content and len(content) > 10:  # Verifica che ci sia contenuto significativo
                    logger.info(f"Contenuto del documento {document_id} recuperato direttamente dal VectorstoreService")
                    return {
                        "success": True,
                        "document_id": document_id,
                        "content": content,
                        "source": "vectorstore_direct"
                    }
        except Exception as e:
            logger.warning(f"Errore nel recupero diretto del contenuto da VectorstoreService: {e}")
        
        # METODO 3: Ottieni i metadati e prova a recuperare il file originale
        try:
            # Prima prova l'endpoint /vectorstore/document/{document_id}
            document_info = client._request("GET", f"/vectorstore/document/{document_id}")
            if not document_info:
                # Se fallisce, prova con l'endpoint alternativo /documents/{document_id}
                document_info = client._request("GET", f"/documents/{document_id}")
            
            if not document_info:
                raise HTTPException(status_code=404, detail=f"Documento con ID {document_id} non trovato")
            
            # Verifica se il documento stesso contiene il testo completo
            if "document" in document_info and document_info["document"]:
                content = document_info["document"]
                if content and len(content) > 10:  # Verifica che ci sia contenuto significativo
                    logger.info(f"Contenuto del documento {document_id} recuperato dai metadati del VectorstoreService")
                    return {
                        "success": True,
                        "document_id": document_id,
                        "content": content,
                        "source": "document_metadata"
                    }
            
            # Cerca il file originale
            metadata = document_info.get("metadata", {})
            file_path = metadata.get("path")
            
            if not file_path or not os.path.exists(file_path):
                # Se il file non esiste più, prova a cercarlo in altre posizioni
                file_name = document_info.get("filename")
                if file_name:
                    # Cerca nei percorsi comuni
                    temp_dir = os.path.join("PramaIAServer", "temp_files")
                    alt_paths = [
                        os.path.join(temp_dir, file_name),
                        os.path.join("temp_files", file_name),
                        os.path.join("temp", file_name),
                        os.path.join("c:", "PramaIA", "temp", file_name)
                    ]
                    
                    for path in alt_paths:
                        if os.path.exists(path):
                            file_path = path
                            break
            
            # Se abbiamo trovato il file, estrai il testo
            if file_path and os.path.exists(file_path):
                import PyPDF2
                
                text_content = ""
                try:
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page_num in range(len(reader.pages)):
                            page = reader.pages[page_num]
                            text_content += page.extract_text() + "\n\n"
                    
                    # Limita la lunghezza se necessario
                    if len(text_content) > 10000:  # Limita a ~10KB per non appesantire troppo
                        text_content = text_content[:10000] + "...[TESTO TRONCATO]"
                    
                    logger.info(f"Contenuto del documento {document_id} estratto dal file PDF originale")
                    return {
                        "success": True,
                        "document_id": document_id,
                        "content": text_content,
                        "source": "pdf_file"
                    }
                except Exception as pdf_error:
                    logger.error(f"Errore nell'estrazione del testo dal PDF {file_path}: {pdf_error}")
            
            # METODO 4: Se non siamo riusciti a recuperare il contenuto, prova con una query semantica
            try:
                # Usa il nuovo endpoint di query semantica
                query_data = {
                    "query": f"document_id:{document_id}",
                    "top_k": 5,
                    "include_metadata": True
                }
                
                query_response = client._request("POST", "/query/query", data=query_data)
                
                if query_response and query_response.get("success") and query_response.get("results"):
                    results = query_response["results"]
                    
                    # Filtra per document_id esatto nei metadati se disponibili
                    matching_results = []
                    for result in results:
                        metadata = result.get("metadata", {})
                        if metadata.get("document_id") == document_id:
                            matching_results.append(result)
                    
                    if matching_results:
                        # Combina il contenuto dei chunk trovati
                        combined_content = "\n\n".join([result["content"] for result in matching_results])
                        
                        logger.info(f"Contenuto del documento {document_id} recuperato tramite query semantica ({len(matching_results)} chunks)")
                        return {
                            "success": True,
                            "document_id": document_id,
                            "content": combined_content,
                            "chunks_found": len(matching_results),
                            "source": "vectorstore_semantic_query"
                        }
            except Exception as query_error:
                logger.warning(f"Errore nel tentativo di query semantica per il documento {document_id}: {query_error}")
            
            # Se siamo arrivati qui, non abbiamo trovato il contenuto
            logger.warning(f"Impossibile recuperare il contenuto per il documento {document_id}")
            return {
                "success": False,
                "document_id": document_id,
                "error": "Contenuto del documento non disponibile"
            }
            
        except Exception as info_error:
            logger.error(f"Errore nel recupero delle informazioni sul documento {document_id}: {info_error}")
            return {
                "success": False,
                "document_id": document_id,
                "error": f"Errore nel recupero delle informazioni sul documento: {str(info_error)}"
            }
            
    except Exception as e:
        logger.error(f"Errore generale nel recupero del contenuto del documento {document_id}: {e}")
        return {
            "success": False,
            "document_id": document_id,
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

