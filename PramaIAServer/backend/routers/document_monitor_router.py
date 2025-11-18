"""
Router per gestire l'upload e l'interrogazione di documenti
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..services.document_monitor_service import (
    process_document_with_pdk,
    query_document_semantic_search,
    get_vectorstore_status,
    _get_file_type_name
)

router = APIRouter(prefix="/api/document-monitor", tags=["document-monitor"])
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    client_id: Optional[str] = Field(default="system", description="Identificativo del client che esegue la query")

class UpdateDocumentRequest(BaseModel):
    content: str
    metadata: dict = {}

class DirectoryMetadataRequest(BaseModel):
    folder_path: str
    full_path: str
    stats: dict
    timestamp: str

class RenameRequest(BaseModel):
    old_name: str
    new_name: str
    file_path: str
    event_id: int | None = None

class UploadFileMetadata(BaseModel):
    client_id: Optional[str] = Field(default="system", description="Identificativo del client che invia il file")
    original_path: Optional[str] = Field(default="", description="Percorso originale del file nel sistema client")
    meta: Optional[dict] = Field(default={}, description="Metadati aggiuntivi associati al file")

@router.post("/upload/", summary="Ricevi documento dal plugin Document Monitor e inoltra al workflow PDK")
async def receive_document_from_plugin(
    file: UploadFile = File(...),
    metadata: Optional[UploadFileMetadata] = None
):
    """
    Riceve un documento dal plugin Document Monitor e lo inoltra al workflow PDK di ingestione.
    Se il file è un duplicato, lo marca come tale ma mantiene il documento ID originale.
    
    - **file**: Il documento da caricare
    - **metadata**: Metadati opzionali sul file (client_id, original_path, altri metadati)
    """
    try:
        # Utilizza metadati predefiniti se non forniti
        client_id = "system"
        original_path = ""
        
        if metadata:
            client_id = metadata.client_id
            original_path = metadata.original_path
            logger.info(f"Metadati ricevuti: client_id={client_id}, original_path={original_path}")
        
        # Leggi il file ricevuto
        file_bytes = await file.read()
        filename = file.filename or f"unknown_file_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        logger.info(f"Ricevuto documento '{filename}' dal plugin Document Monitor. Dimensione: {len(file_bytes)} bytes, Client: {client_id}")
        
        # Processa il file con i metadati
        result = await process_document_with_pdk(file_bytes, filename, client_id, original_path)
        
        if result["status"] == "error":
            # Registra l'errore nel database di eventi
            try:
                # Usa il percorso corretto del database nella cartella data
                db_path = os.path.join("backend", "db", "database.db")
                # Se il database non esiste nel percorso backend/db, prova il percorso legacy
                if not os.path.exists(db_path):
                    db_path = os.path.join("backend", "data", "database.db")
                if not os.path.exists(db_path):
                    db_path = os.path.join(".", "backend", "data", "database.db")
                if not os.path.exists(db_path):
                    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.db"))
                    
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
                if cursor.fetchone():
                    
                    event_metadata = {
                        "error_details": result["message"],
                        "timestamp": datetime.now().isoformat(),
                        "file_size": len(file_bytes),
                        "source": "pdf_monitor_router",
                        "client_id": client_id,
                        "original_path": original_path
                    }
                    
                    cursor.execute('''
                    INSERT INTO pdf_monitor_events 
                    (file_name, file_path, folder_path, event_type, status, document_id, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        filename,
                        original_path,
                        os.path.dirname(original_path) if original_path else None,
                        "upload",
                        "error_pdk_unavailable",
                        None,
                        json.dumps(event_metadata)
                    ))
                    
                    conn.commit()
                    logger.info(f"Evento errore PDK registrato nel database")
                
                conn.close()
            except Exception as db_error:
                logger.error(f"Errore durante la registrazione dell'evento di errore: {db_error}")
            
            # Restituisci un errore esplicito
            raise HTTPException(
                status_code=503, 
                detail=result["message"]
            )
                
        # Restituisce il risultato dell'elaborazione
        return result
        
    except HTTPException:
        # Ripropaga le eccezioni HTTP specifiche
        raise
    except Exception as e:
        logger.error(f"Errore ricezione PDF dal plugin: {e}")
        logger.error(f"DEBUG: Traceback completo:", exc_info=True)
        raise HTTPException(status_code=500, detail="Errore interno durante la ricezione del PDF")

@router.post("/query/", summary="Interroga i documenti indicizzati tramite workflow PDK")
async def query_document_semantic(request: QueryRequest):
    """
    Esegue una query semantica sui documenti indicizzati tramite il workflow PDK.
    
    - **query**: Il testo della query da cercare
    - **top_k**: Numero di risultati da restituire
    - **client_id**: Identificativo del client che esegue la query
    """
    try:
        result = await query_document_semantic_search(request.query, request.top_k, request.client_id)
        
        if result["status"] == "error":
            # Registra l'errore nel database di eventi
            try:
                # Usa il percorso corretto del database nella cartella data
                db_path = os.path.join("backend", "db", "database.db")
                # Se il database non esiste nel percorso backend/db, prova il percorso legacy
                if not os.path.exists(db_path):
                    db_path = os.path.join("backend", "data", "database.db")
                if not os.path.exists(db_path):
                    db_path = os.path.join(".", "backend", "data", "database.db")
                if not os.path.exists(db_path):
                    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.db"))
                    
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
                if cursor.fetchone():
                    metadata = {
                        "query": request.query,
                        "top_k": request.top_k,
                        "client_id": request.client_id,
                        "error_details": result["message"],
                        "timestamp": datetime.now().isoformat(),
                        "source": "pdf_monitor_router"
                    }
                    
                    cursor.execute('''
                    INSERT INTO pdf_monitor_events 
                    (file_name, file_path, folder_path, event_type, status, document_id, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        None,
                        None,
                        "query",
                        "error_pdk_unavailable",
                        None,
                        json.dumps(metadata)
                    ))
                    
                    conn.commit()
                    logger.info(f"Evento errore query PDK registrato nel database")
                
                conn.close()
            except Exception as db_error:
                logger.error(f"Errore durante la registrazione dell'evento di errore query: {db_error}")
            
            # Restituisci un errore esplicito
            raise HTTPException(
                status_code=503, 
                detail=result["message"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Errore query semantica: {e}")
        raise HTTPException(status_code=500, detail="Errore interno durante la query semantica")


@router.put("/documents/{filename}", summary="Aggiorna il contenuto di un documento")
async def update_document_content(filename: str, request: UpdateDocumentRequest):
    """
    Aggiorna il contenuto di un documento esistente nel vectorstore.
    Rimuove la versione precedente e aggiunge quella nuova.
    """
    try:
        from backend.core.rag_vectorstore import remove_documents_from_vectorstore, add_documents_to_vectorstore
        from backend.core.rag_chains_prompts import get_openai_embeddings
        from langchain.docstore.document import Document
        
        logger.info(f"Aggiornamento documento '{filename}'")
        
        # 1. Rimuovi il documento esistente dal vectorstore
        removal_success = remove_documents_from_vectorstore(filename)
        if removal_success:
            logger.info(f"Documento '{filename}' rimosso dal vectorstore")
        else:
            logger.warning(f"Documento '{filename}' non trovato nel vectorstore per rimozione")
        
        # 2. Aggiungi il nuovo contenuto
        documents = [Document(
            page_content=request.content,
            metadata={
                "source_filename": filename,
                "document_type": "updated",
                "update_method": "content_update",
                **request.metadata
            }
        )]
        
        embeddings_service = get_openai_embeddings()
        add_documents_to_vectorstore(
            docs=documents,
            embeddings_service=embeddings_service,
            filename=filename
        )
        
        logger.info(f"✅ Documento '{filename}' aggiornato nel vectorstore")
        
        return {
            "status": "success",
            "message": f"Documento '{filename}' aggiornato con successo",
            "filename": filename,
            "content_length": len(request.content)
        }
        
    except Exception as e:
        logger.error(f"Errore aggiornamento documento '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno durante l'aggiornamento: {str(e)}")


@router.delete("/documents/{filename}", summary="Rimuove un documento dal vectorstore")
async def remove_document(filename: str):
    """
    Rimuove completamente un documento dal vectorstore.
    """
    try:
        from backend.core.rag_vectorstore import remove_documents_from_vectorstore
        
        logger.info(f"Rimozione documento '{filename}'")
        
        success = remove_documents_from_vectorstore(filename)
        
        if success:
            logger.info(f"✅ Documento '{filename}' rimosso dal vectorstore")
            return {
                "status": "success",
                "message": f"Documento '{filename}' rimosso con successo",
                "filename": filename
            }
        else:
            logger.warning(f"Documento '{filename}' non trovato nel vectorstore")
            raise HTTPException(status_code=404, detail=f"Documento '{filename}' non trovato")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore rimozione documento '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno durante la rimozione: {str(e)}")


@router.post("/sync/folder", summary="Sincronizza una cartella con il vectorstore")
async def sync_folder_to_vectorstore(folder_path: str, user_id: str = "system"):
    """
    Sincronizza completamente una cartella con il vectorstore.
    Aggiunge la struttura delle cartelle, i nomi dei file e i contenuti.
    """
    try:
        from backend.core.rag_vectorstore import add_documents_to_vectorstore
        from backend.core.rag_chains_prompts import get_openai_embeddings
        from langchain.docstore.document import Document
        import os
        from pathlib import Path
        
        logger.info(f"Sincronizzazione cartella '{folder_path}' per utente '{user_id}'")
        
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail=f"Cartella '{folder_path}' non trovata")
        
        documents_added = 0
        embeddings_service = get_openai_embeddings()
        
        # Percorri ricorsivamente la cartella
        for root, dirs, files in os.walk(folder_path):
            relative_root = os.path.relpath(root, folder_path)
            
            # 1. Aggiungi informazioni sulla struttura della cartella
            if relative_root != ".":
                folder_doc = Document(
                    page_content=f"Cartella: {relative_root}\nPercorso completo: {root}\nContiene sottocartelle: {', '.join(dirs) if dirs else 'Nessuna'}\nContiene file: {', '.join(files) if files else 'Nessuno'}",
                    metadata={
                        "source_filename": f"folder_structure_{relative_root.replace(os.sep, '_')}",
                        "document_type": "folder_structure",
                        "folder_path": relative_root,
                        "full_path": root,
                        "user_id": user_id,
                        "subdirs": dirs,
                        "files": files
                    }
                )
                
                add_documents_to_vectorstore(
                    docs=[folder_doc],
                    embeddings_service=embeddings_service,
                    filename=f"folder_structure_{relative_root.replace(os.sep, '_')}"
                )
                documents_added += 1
            
            # 2. Aggiungi informazioni sui file
            for file in files:
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, folder_path)
                
                try:
                    # Leggi il contenuto del file (se possibile)
                    file_content = ""
                    file_type = "unknown"
                    
                    # Determina il tipo di file
                    file_ext = Path(file).suffix.lower()
                    if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']:
                        file_type = "text"
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                        except:
                            try:
                                with open(file_path, 'r', encoding='latin-1') as f:
                                    file_content = f.read()
                            except:
                                file_content = "[Contenuto non leggibile]"
                    elif file_ext == '.pdf':
                        file_type = "pdf"
                        file_content = "[File PDF - contenuto da elaborare separatamente]"
                    elif file_ext in ['.doc', '.docx']:
                        file_type = "document"
                        file_content = "[Documento Office - contenuto da elaborare separatamente]"
                    else:
                        file_type = "binary"
                        file_content = "[File binario]"
                    
                    # Crea documento per il file
                    file_doc = Document(
                        page_content=f"File: {file}\nPercorso: {relative_file_path}\nTipo: {file_type}\nDimensione: {os.path.getsize(file_path)} bytes\n\nContenuto:\n{file_content[:2000]}{'...' if len(file_content) > 2000 else ''}",
                        metadata={
                            "source_filename": relative_file_path,
                            "document_type": "file_content",
                            "file_type": file_type,
                            "file_extension": file_ext,
                            "folder_path": os.path.dirname(relative_file_path),
                            "file_size": os.path.getsize(file_path),
                            "user_id": user_id,
                            "full_path": file_path
                        }
                    )
                    
                    add_documents_to_vectorstore(
                        docs=[file_doc],
                        embeddings_service=embeddings_service,
                        filename=relative_file_path
                    )
                    documents_added += 1
                    
                except Exception as file_error:
                    logger.warning(f"Errore elaborazione file '{file_path}': {file_error}")
                    continue
        
        logger.info(f"✅ Sincronizzazione completata: {documents_added} documenti aggiunti")
        
        return {
            "status": "success",
            "message": f"Cartella '{folder_path}' sincronizzata con successo",
            "documents_added": documents_added,
            "folder_path": folder_path,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore sincronizzazione cartella '{folder_path}': {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno durante la sincronizzazione: {str(e)}")


@router.get("/documents/list", summary="Lista tutti i documenti nel vectorstore")
async def list_documents_in_vectorstore():
    """
    Restituisce la lista di tutti i documenti presenti nel vectorstore.
    Include sia informazioni sui documenti vettorizzati che sui documenti registrati nel database.
    """
    try:
        status = get_vectorstore_status()
        
        # Estrai informazioni dettagliate sui documenti
        vectorized_docs_count = status.get("collection_stats", {}).get("count", 0)
        registered_docs = status.get("registered_files", {})
        unique_registered_docs = registered_docs.get("unique_files", 0)
        total_registered_entries = registered_docs.get("total_entries", 0)
        
        # TODO: Implementare una funzione per ottenere la lista effettiva dei documenti
        # Per ora restituiamo informazioni aggregate
        
        return {
            "status": "success",
            "document_counts": {
                "vectorized_documents": vectorized_docs_count,
                "unique_registered_documents": unique_registered_docs,
                "total_registered_entries": total_registered_entries,
                "duplicate_entries": total_registered_entries - unique_registered_docs
            },
            "vectorstore_status": status,
            "message": "Lista documenti ottenuta con distinzione tra documenti vettorizzati e registrati"
        }
        
    except Exception as e:
        logger.error(f"Errore lista documenti: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


class DeleteFileRequest(BaseModel):
    file_name: str
    folder: str
    action: str = "deleted"
    event_id: str | None = None

@router.post("/rename", summary="Gestisce la rinomina di un file da parte dell'agent PDF Monitor")
async def handle_file_rename(request: RenameRequest):
    """
    Endpoint per gestire la notifica di rinomina di un file da parte dell'agent PDF Monitor.
    Registra l'evento nel database e aggiorna i riferimenti nel vectorstore.
    """
    try:
        logger.info(f"Ricevuta notifica di rinomina file: {request.old_name} → {request.new_name}")
        
        # 1. Registra l'evento nel database
        try:
            # Usa il percorso corretto del database nella cartella data
            db_path = os.path.join("backend", "db", "database.db")
            # Se il database non esiste nel percorso backend/db, prova il percorso legacy
            if not os.path.exists(db_path):
                db_path = os.path.join("backend", "data", "database.db")
            if not os.path.exists(db_path):
                db_path = os.path.join(".", "backend", "data", "database.db")
            if not os.path.exists(db_path):
                db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.db"))
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verifica se la tabella esiste
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
            if cursor.fetchone():
                # Registra l'evento nella tabella
                cursor.execute(
                    """
                    INSERT INTO pdf_monitor_events 
                    (timestamp, event_type, file_name, old_name, folder, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, 
                    (
                        datetime.now().isoformat(),
                        'renamed',
                        request.new_name,
                        request.old_name,
                        os.path.dirname(request.file_path),
                        'completed',
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
                logger.info(f"Evento rinomina registrato nel database: {request.old_name} → {request.new_name}")
            else:
                logger.warning("La tabella pdf_monitor_events non esiste nel database")
            
            conn.close()
        except Exception as db_error:
            logger.error(f"Errore durante la registrazione dell'evento di rinomina: {db_error}")
        
        # 2. Aggiorna i riferimenti nel vectorstore
        # TODO: Implementare la logica per aggiornare i riferimenti nel vectorstore
        # (Dipende da come è implementato il tuo vectorstore, questa è una funzione segnaposto)
        
        return {
            "status": "success",
            "message": f"File rinominato con successo: {request.old_name} → {request.new_name}",
            "old_name": request.old_name,
            "new_name": request.new_name
        }
        
    except Exception as e:
        logger.error(f"Errore gestione rinomina file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante la gestione della rinomina: {str(e)}"
        )

@router.post("/delete/", summary="Gestisce la cancellazione di un file da parte dell'agent PDF Monitor")
async def handle_file_deletion(request: DeleteFileRequest):
    """
    Endpoint per gestire la notifica di cancellazione di un file da parte dell'agent PDF Monitor.
    Registra l'evento nel database e avvia il processo di rimozione dal vectorstore.
    """
    try:
        logger.info(f"Ricevuta notifica di cancellazione file: {request.file_name} da {request.folder}")
        
        # 1. Registra l'evento nel database
        try:
            # Usa il percorso corretto del database nella cartella data
            db_path = os.path.join("backend", "db", "database.db")
            # Se il database non esiste nel percorso backend/db, prova il percorso legacy
            if not os.path.exists(db_path):
                db_path = os.path.join("backend", "data", "database.db")
            if not os.path.exists(db_path):
                db_path = os.path.join(".", "backend", "data", "database.db")
            if not os.path.exists(db_path):
                db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.db"))
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verifica se la tabella esiste
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_monitor_events'")
            if cursor.fetchone():
                file_name = request.file_name
                folder_path = request.folder
                
                metadata = {
                    "action": request.action,
                    "timestamp": datetime.now().isoformat(),
                    "source": "pdf_monitor_router",
                    "agent_event_id": request.event_id
                }
                
                # Registra evento di cancellazione
                cursor.execute('''
                INSERT INTO pdf_monitor_events 
                (file_name, file_path, folder_path, event_type, status, document_id, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    file_name,
                    os.path.join(folder_path, file_name),
                    folder_path,
                    "deleted",
                    "completed",
                    None,
                    json.dumps(metadata)
                ))
                
                # Rimuovi anche dalla tabella file_hashes per evitare rilevamento duplicati in caso di re-upload
                cursor.execute('''
                DELETE FROM file_hashes 
                WHERE file_name = ? OR file_path LIKE ?
                ''', (
                    file_name,
                    f"%{file_name}%"
                ))
                deleted_count = cursor.rowcount
                logger.info(f"Hash del file '{file_name}' rimosso dalla tabella file_hashes (righe eliminate: {deleted_count})")
                
                conn.commit()
                logger.info(f"Evento cancellazione registrato nel database")
            else:
                logger.warning("Tabella pdf_monitor_events non trovata nel database")
            
            conn.close()
        except Exception as db_error:
            logger.error(f"Errore durante la registrazione dell'evento di cancellazione: {db_error}")
        
        # 2. Tenta di rimuovere il file dal vectorstore
        try:
            from backend.core.rag_vectorstore import remove_documents_from_vectorstore
            
            # Rimuovi il file dal vectorstore
            success = remove_documents_from_vectorstore(request.file_name)
            
            if success:
                logger.info(f"✅ File '{request.file_name}' rimosso dal vectorstore")
            else:
                logger.warning(f"File '{request.file_name}' non trovato nel vectorstore")
        except Exception as vs_error:
            logger.error(f"Errore rimozione dal vectorstore: {vs_error}")
        
        # 3. Restituisci esito positivo
        return {
            "status": "success",
            "message": f"Evento di cancellazione per '{request.file_name}' registrato correttamente",
            "file_name": request.file_name,
            "folder": request.folder,
            "event_id": request.event_id
        }
        
    except Exception as e:
        logger.error(f"❌ Errore gestione cancellazione file: {e}")
        return {
            "status": "error",
            "message": f"Errore durante la gestione della cancellazione: {str(e)}",
            "file_name": request.file_name
        }

@router.post("/directory-metadata/", summary="Aggiorna metadati directory nel vectorstore")
async def update_directory_metadata(request: DirectoryMetadataRequest):
    """
    Endpoint per aggiornare i metadati di una directory nel vectorstore.
    Utilizzato dall'agent di monitoraggio per mantenere informazioni strutturali.
    """
    try:
        from backend.core.rag_vectorstore import add_documents_to_vectorstore
        from backend.core.rag_chains_prompts import get_openai_embeddings
        from langchain.docstore.document import Document
        
        logger.info(f"Aggiornamento metadati directory: {request.folder_path}")
        
        # Crea contenuto descrittivo per embeddings semantici
        stats = request.stats
        total_files = stats.get('total_files', 0)
        file_types = stats.get('file_types', {})
        subfolders = stats.get('subfolders', [])
        total_size = stats.get('total_size', 0)
        
        content_parts = [f"Directory '{request.folder_path}'"]
        
        if total_files > 0:
            content_parts.append(f"contiene {total_files} file totali")
            
            # Dettagli per tipo di file
            if file_types:
                type_details = []
                for ext, count in file_types.items():
                    file_type_name = _get_file_type_name(ext)
                    type_details.append(f"{count} file {file_type_name}")
                content_parts.append("composti da: " + ", ".join(type_details))
        else:
            content_parts.append("è vuota")
            
        if subfolders:
            content_parts.append(f"Ha {len(subfolders)} sottocartelle: {', '.join(subfolders)}")
            
        if total_size > 0:
            size_mb = total_size / (1024 * 1024)
            if size_mb > 1024:
                size_str = f"{size_mb/1024:.1f} GB"
            else:
                size_str = f"{size_mb:.1f} MB"
            content_parts.append(f"Dimensione totale: {size_str}")
            
        content_parts.append(f"Ultimo aggiornamento: {request.timestamp}")
        
        page_content = ". ".join(content_parts) + "."
        
        # Metadati strutturati
        metadata = {
            "type": "directory_metadata",
            "document_type": "directory_metadata",
            "folder_path": request.folder_path,
            "full_path": request.full_path,
            "total_files": total_files,
            "file_types": file_types,
            "subfolders": subfolders,
            "total_size": total_size,
            "last_updated": request.timestamp,
            "source_filename": f"directory_metadata_{request.folder_path.replace('/', '_').replace('\\', '_')}"
        }
        
        # Crea documento
        doc = Document(
            page_content=page_content,
            metadata=metadata
        )
        
        # Aggiungi al vectorstore
        embeddings_service = get_openai_embeddings()
        add_documents_to_vectorstore(
            docs=[doc],
            embeddings_service=embeddings_service,
            filename=metadata["source_filename"]
        )
        
        logger.info(f"✅ Metadati directory '{request.folder_path}' aggiornati nel vectorstore")
        
        return {
            "status": "success",
            "message": f"Metadati directory '{request.folder_path}' aggiornati",
            "folder_path": request.folder_path,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Errore aggiornamento metadati directory: {e}")
        raise HTTPException(status_code=500, detail=f"Errore aggiornamento metadati: {str(e)}")

