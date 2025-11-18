"""
Router per gestire tutti gli endpoint relativi al VectorStore Service.
Questo modulo contiene tutti gli endpoint che comunicano con il VectorStore Service.
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.auth.dependencies import get_current_user
from backend.app.clients.vectorstore_client import VectorstoreServiceClient
from backend.core.config import VECTORSTORE_SERVICE_BASE_URL

logger = logging.getLogger(__name__)

# Creiamo un router separato per i vectorstore endpoints
router = APIRouter(tags=["vectorstore"])

def get_vectorstore_client() -> VectorstoreServiceClient:
    """
    Ottiene un client per il servizio VectorStore.
    Il client gestisce la comunicazione HTTP con il VectorStore Service.
    """
    base_url = VECTORSTORE_SERVICE_BASE_URL
    if not base_url:
        raise HTTPException(
            status_code=500,
            detail="VECTORSTORE_SERVICE_BASE_URL non configurato"
        )
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = f"http://{base_url}"
    
    # Rimuovi trailing slash se presente
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    logger.info(f"Creazione client VectorStore con base URL: {base_url}")
    return VectorstoreServiceClient(base_url)

class QueryRequest(BaseModel):
    collection_name: str = "pdf_documents"
    query: str
    top_k: int = 5
    include_metadata: bool = True
    
@router.get("/documents")
async def get_vectorstore_documents(
    limit: int = Query(default=50, description="Numero massimo di documenti da restituire"),
    offset: int = Query(default=0, description="Numero di documenti da saltare"),
    search: str = Query(default="", description="Termine di ricerca nel nome del file"),
    current_user = Depends(get_current_user)
):
    """
    Ottiene la lista dei documenti presenti nel vectorstore.
    
    Args:
        limit: Numero massimo di documenti da restituire
        offset: Numero di documenti da saltare per la paginazione
        search: Termine di ricerca opzionale per filtrare per nome file
        
    Returns:
        Lista dei documenti con metadati
    """
    try:
        client = get_vectorstore_client()
        
        # Costruisci i parametri della query
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if search.strip():
            params["search"] = search.strip()
        
        # Effettua la richiesta al VectorStore Service
        response = client._request("GET", "/documents", params=params)
        
        if response is None:
            logger.warning("Il VectorStore Service ha restituito una risposta vuota")
            return {
                "success": True,
                "documents": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
        
        # Se la risposta non ha la struttura attesa, proviamo a normalizzarla
        if isinstance(response, list):
            logger.info(f"Ricevuti {len(response)} documenti dal VectorStore Service")
            return {
                "success": True,
                "documents": response,
                "total": len(response),
                "limit": limit,
                "offset": offset
            }
        elif isinstance(response, dict):
            # Il VectorStore Service restituisce {message: "...", documents: [...]}
            documents = response.get("documents", response.get("data", []))
            total = response.get("total", len(documents))
            
            logger.info(f"Ricevuti {len(documents)} documenti dal VectorStore Service")
            return {
                "success": True,
                "documents": documents,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        else:
            logger.error(f"Formato di risposta inaspettato dal VectorStore Service: {type(response)}")
            return {
                "success": False,
                "error": "Formato di risposta inaspettato dal VectorStore Service",
                "documents": [],
                "total": 0
            }
            
    except Exception as e:
        logger.error(f"Errore nella richiesta dei documenti dal VectorStore: {e}")
        return {
            "success": False,
            "error": str(e),
            "documents": [],
            "total": 0
        }

@router.get("/statistics")
async def get_vectorstore_statistics(current_user = Depends(get_current_user)):
    """
    Ottiene le statistiche del vectorstore (numero di documenti, dimensioni, ecc.).
    """
    try:
        client = get_vectorstore_client()
        response = client._request("GET", "/stats")
        
        if response is None:
            # Se non otteniamo risposta, restituiamo statistiche di base
            return {
                "success": True,
                "statistics": {
                    "total_documents": 0,
                    "collections": [],
                    "status": "unavailable"
                }
            }
        
        return {
            "success": True,
            "statistics": response
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero delle statistiche VectorStore: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/settings")
async def get_vectorstore_settings(current_user = Depends(get_current_user)):
    """
    Ottiene le impostazioni correnti del VectorStore Service.
    """
    try:
        client = get_vectorstore_client()
        response = client._request("GET", "/settings")
        
        return {
            "success": True,
            "settings": response or {}
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero delle impostazioni VectorStore: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/settings")
async def update_vectorstore_settings(
    settings: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Aggiorna le impostazioni del VectorStore Service.
    """
    try:
        client = get_vectorstore_client()
        
        # Valida le impostazioni di base
        service_settings = {
            "chunk_size": settings.get("chunk_size", 1000),
            "chunk_overlap": settings.get("chunk_overlap", 200),
            "embedding_model": settings.get("embedding_model", "all-MiniLM-L6-v2")
        }
        
        response = client._request("POST", "/settings", data=service_settings)
        
        return {
            "success": True,
            "message": "Impostazioni aggiornate con successo",
            "updated_settings": response or service_settings
        }
        
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento delle impostazioni VectorStore: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/status")
async def get_vectorstore_status(current_user = Depends(get_current_user)):
    """
    Controlla lo stato del VectorStore Service e restituisce informazioni di salute.
    """
    try:
        client = get_vectorstore_client()
        
        # Prova una richiesta semplice per verificare la connessione
        response = client._request("GET", "/health")
        
        if response is None:
            # Se non c'è risposta, proviamo con un endpoint alternativo
            response = client._request("GET", "/")
        
        # Determina lo stato basato sulla risposta
        is_healthy = response is not None
        
        status = {
            "service_name": "VectorStore Service",
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "base_url": client.base_url if hasattr(client, 'base_url') else VECTORSTORE_SERVICE_BASE_URL,
            "response": response
        }
        
        if is_healthy:
            logger.info("VectorStore Service è disponibile e funzionante")
        else:
            logger.warning("VectorStore Service non risponde o non è disponibile")
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Errore nel controllo dello stato VectorStore: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": {
                "service_name": "VectorStore Service",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error_message": str(e)
            }
        }

@router.post("/query")
async def query_vectorstore(
    query_data: QueryRequest,
    current_user = Depends(get_current_user)
):
    """
    Esegue una query semantica nel vectorstore per trovare documenti simili.
    """
    try:
        client = get_vectorstore_client()
        
        # Prepara i dati della query
        payload = {
            "collection_name": query_data.collection_name,
            "query": query_data.query,
            "top_k": query_data.top_k,
            "include_metadata": query_data.include_metadata
        }
        
        logger.info(f"Esecuzione query vectorstore: {query_data.query[:100]}...")
        
        # Esegui la query
        response = client._request("POST", "/query", data=payload)
        
        if not response:
            return {
                "success": False,
                "error": "Nessuna risposta dal VectorStore Service"
            }
        
        # Processa la risposta
        results = response.get("results", [])
        
        logger.info(f"Query completata, trovati {len(results)} risultati")
        
        return {
            "success": True,
            "query": query_data.query,
            "results": results,
            "total_results": len(results),
            "collection": query_data.collection_name
        }
        
    except Exception as e:
        logger.error(f"Errore nell'esecuzione della query vectorstore: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/document/{document_id}/content")
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
            # Usa il metodo dedicato del client per recuperare il contenuto da ChromaDB
            content_response = client.get_document_content(document_id, collection_name="prama_documents", max_chunks=20)
            
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
            # Prima prova l'endpoint /document/{document_id}
            document_info = client._request("GET", f"/document/{document_id}")
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