"""
Workflow Processors

Processori reali per i nodi dei workflow PDF.
"""

import os
import re
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import uuid

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext
from backend.utils import get_logger

logger = get_logger(__name__)


class EventInputProcessor(BaseNodeProcessor):
    """
    Processore per nodi di input eventi.
    Riceve l'evento e lo passa al workflow.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """Restituisce i dati di input del workflow (l'evento)."""
        logger.info(
            f"📨 Event Input Node: '{node.name}'",
            details={"node_id": node.node_id, "event_keys": list(context.input_data.keys())}
        )
        
        # Restituisci tutti i dati di input del workflow
        return context.input_data
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Event input non richiede configurazione speciale."""
        return True


class FileParsingProcessor(BaseNodeProcessor):
    """
    Processore per parsing file PDF tramite PDK.
    Chiama il nodo PDK file_parsing per estrarre testo e metadati.
    """
    
    def __init__(self):
        self.pdk_base_url = os.getenv("PDK_SERVER_BASE_URL", "http://localhost:3001")
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """Chiama il nodo PDK file_parsing per parsare il file PDF."""
        config = node.config or {}
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai il percorso del file
        file_path = input_data.get("file_path", "")
        if not file_path:
            raise ValueError("file_path mancante nell'input")
        
        logger.info(
            f"📄 Parsing PDF via PDK: {file_path}",
            details={
                "node": node.name,
                "extract_text": config.get("extract_text", True),
                "extract_metadata": config.get("extract_metadata", True),
                "ocr_enabled": config.get("ocr_enabled", False),
                "pdk_url": f"{self.pdk_base_url}/plugins/pdf-monitor-plugin/execute"
            }
        )
        
        # Prepara richiesta al nodo PDK
        # Endpoint: POST /plugins/:id/execute
        payload = {
            "nodeId": "file_parsing",
            "inputs": {
                "file_path": file_path.replace("\\", "/")  # Usa forward slash per Windows
            },
            "config": {
                "extract_text": config.get("extract_text", True),
                "extract_metadata": config.get("extract_metadata", True),
                "extract_images": config.get("extract_images", False),
                "ocr_enabled": config.get("ocr_enabled", False)
            }
        }
        
        logger.debug(f"PDK Request payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.pdk_base_url}/plugins/pdf-monitor-plugin/execute",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            # Verifica successo
            if not result.get("success"):
                raise ValueError(f"PDK error: {result.get('error', 'Unknown error')}")
            
            # Estrai i dati dall'output del nodo PDK
            node_result = result.get("result", {})
            
            logger.debug(
                f"PDK Response: success={node_result.get('success')}, keys={list(node_result.keys())}"
            )
            
            # Il PDK ritorna "text_content" e non "text"
            text_content = node_result.get("text_content", "")
            metadata = node_result.get("metadata", {})
            
            logger.info(
                f"✅ PDF parsed successfully via PDK",
                details={
                    "file": file_path,
                    "text_length": len(text_content),
                    "has_text_content": "text_content" in node_result,
                    "node_result_keys": list(node_result.keys()),
                    "metadata_keys": list(metadata.keys()) if metadata else []
                }
            )
            
            return {
                "text": text_content,  # Mappa text_content → text
                "metadata": metadata,
                "file_path": file_path,
                "parse_status": "success"
            }
            
        except httpx.HTTPError as e:
            logger.error(
                f"❌ Errore chiamata PDK per parsing: {str(e)}",
                details={"file": file_path, "error": str(e)}
            )
            raise ValueError(f"Errore parsing PDF: {str(e)}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configurazione parsing."""
        return True


class MetadataManagerProcessor(BaseNodeProcessor):
    """
    Processore per gestione metadati.
    Estrae, normalizza e arricchisce metadati del documento.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """Processa i metadati del documento."""
        config = node.config or {}
        input_data = context.get_input_for_node(node.node_id)
        
        print(f"\n🔍🔍🔍 MetadataManager ESEGUITO!")
        print(f"🔍 input_data keys: {list(input_data.keys())}")
        print(f"🔍 input_data type: {type(input_data)}")
        print(f"🔍 input_data: {input_data}")
        logger.info(f"🔍 MetadataManager input_data keys: {list(input_data.keys())}")
        
        # Estrai dati da vari possibili percorsi
        metadata = input_data.get("metadata", {})
        file_path = input_data.get("file_path", "")
        text = input_data.get("text", "")
        
        # Se non trovato, cerca in "input" (risultato nodo precedente)
        if not text and "input" in input_data:
            input_result = input_data["input"]
            logger.info(f"🔍 Found 'input' key, type: {type(input_result)}")
            if isinstance(input_result, dict):
                text = input_result.get("text", "")
                logger.info(f"🔍 Extracted text from input: {len(text)} chars")
                if not metadata:
                    metadata = input_result.get("metadata", {})
                if not file_path:
                    file_path = input_result.get("file_path", "")
        
        # Se ancora non trovato, cerca in tutti i valori dict
        if not text:
            logger.info("🔍 Searching for text in all dict values...")
            for key, value in input_data.items():
                if isinstance(value, dict) and "text" in value and value["text"]:
                    text = value["text"]
                    logger.info(f"🔍 Found text in input_data['{key}']['text']: {len(text)} chars")
                    if not metadata:
                        metadata = value.get("metadata", {})
                    if not file_path:
                        file_path = value.get("file_path", "")
                    break
        
        logger.info(
            f"🏷️ Processing metadata",
            details={
                "node": node.name,
                "file": file_path,
                "text_length": len(text),
                "text_found": bool(text),
                "operations": {
                    "extract_standard": config.get("extract_standard_fields", True),
                    "normalize_dates": config.get("normalize_dates", True),
                    "generate_id": config.get("generate_id", True)
                }
            }
        )
        
        processed_metadata = metadata.copy()
        
        # Generate ID se richiesto
        if config.get("generate_id", True):
            # Usa hash del file path come ID
            doc_id = hashlib.sha256(file_path.encode()).hexdigest()[:16]
            processed_metadata["document_id"] = doc_id
        
        # Estrai campi standard
        if config.get("extract_standard_fields", True):
            processed_metadata["source_path"] = file_path
            processed_metadata["filename"] = os.path.basename(file_path)
            processed_metadata["processed_at"] = datetime.utcnow().isoformat()
        
        # Normalizza date
        if config.get("normalize_dates", True):
            for key in ["created", "modified", "CreationDate", "ModDate"]:
                if key in processed_metadata:
                    # Semplice normalizzazione - in produzione usare dateutil
                    date_val = processed_metadata[key]
                    if isinstance(date_val, str):
                        processed_metadata[f"{key}_normalized"] = date_val
        
        logger.info(
            f"✅ Metadata processed",
            details={
                "document_id": processed_metadata.get("document_id"),
                "fields_count": len(processed_metadata)
            }
        )
        
        return {
            "metadata": processed_metadata,
            "file_path": file_path,
            "text": text,  # Pass through extracted text
            "metadata_status": "processed"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configurazione metadati."""
        return True


class DocumentProcessorProcessor(BaseNodeProcessor):
    """
    Processore per chunking e processing documento.
    Divide il testo in chunks per l'embedding.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """Divide il documento in chunks."""
        config = node.config or {}
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai text da vari possibili percorsi
        text = ""
        
        # 1. Cerca direttamente in input_data
        text = input_data.get("text", "")
        
        # 2. Se non trovato, cerca in input (risultato nodo precedente)
        if not text and "input" in input_data:
            input_result = input_data["input"]
            if isinstance(input_result, dict):
                text = input_result.get("text", "")
        
        # 3. Se ancora non trovato, cerca in tutti i valori dict
        if not text:
            for key, value in input_data.items():
                if isinstance(value, dict) and "text" in value and value["text"]:
                    text = value["text"]
                    logger.debug(f"Found text in input_data['{key}']['text']")
                    break
        
        metadata = input_data.get("metadata", {})
        # Anche metadata potrebbe essere nested
        if not metadata and "input" in input_data:
            input_result = input_data["input"]
            if isinstance(input_result, dict):
                metadata = input_result.get("metadata", {})
        
        file_path = input_data.get("file_path", "")
        
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 200)
        
        logger.info(
            f"📝 Document chunking",
            details={
                "node": node.name,
                "text_length": len(text),
                "text_source": "found" if text else "not_found",
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
        )
        
        # Normalizza testo se richiesto
        if config.get("normalize_text", True):
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)  # Normalizza whitespace
        
        # Chunking semplice
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Prova a trovare un punto di interruzione naturale
            if end < len(text) and config.get("extract_headings", False):
                # Cerca ultimo punto, newline o spazio
                last_break = max(
                    chunk_text.rfind('.'),
                    chunk_text.rfind('\n'),
                    chunk_text.rfind(' ')
                )
                if last_break > chunk_size // 2:  # Solo se non troppo indietro
                    end = start + last_break + 1
                    chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text.strip(),
                "index": chunk_index,
                "start": start,
                "end": end,
                "metadata": metadata.copy()
            })
            
            chunk_index += 1
            start = end - chunk_overlap if chunk_overlap > 0 else end
        
        logger.info(
            f"✅ Document chunked",
            details={
                "file": file_path,
                "total_chunks": len(chunks),
                "avg_chunk_size": sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0
            }
        )
        
        return {
            "chunks": chunks,
            "metadata": metadata,
            "file_path": file_path,
            "text": text,  # Pass through original text
            "processing_status": "chunked"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configurazione chunking."""
        return True


class VectorStoreOperationsProcessor(BaseNodeProcessor):
    """
    Processore per operazioni VectorStore.
    Chiama il VectorstoreService per aggiungere documenti.
    """
    
    def __init__(self):
        self.vectorstore_url = os.getenv("VECTORSTORE_SERVICE_URL", "http://localhost:8090")
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """Aggiunge documenti al vectorstore."""
        config = node.config or {}
        input_data = context.get_input_for_node(node.node_id)
        
        operation = config.get("operation", "add")
        collection_name = config.get("collection_name", "documents")
        chunks = input_data.get("chunks", [])
        metadata = input_data.get("metadata", {})
        file_path = input_data.get("file_path", "")
        
        logger.info(
            f"🗄️ VectorStore operation: {operation}",
            details={
                "node": node.name,
                "collection": collection_name,
                "chunks_count": len(chunks),
                "file": file_path
            }
        )
        
        if operation == "add":
            # Prepara documenti per vectorstore (uno alla volta)
            results = []
            
            for chunk in chunks:
                doc = {
                    "id": f"{metadata.get('document_id', 'unknown')}_{chunk['index']}",
                    "content": chunk["text"],  # VectorStore usa "content" non "text"
                    "metadata": {
                        **metadata,
                        **chunk.get("metadata", {}),
                        "chunk_index": chunk["index"],
                        "source": file_path,
                        "file_name": os.path.basename(file_path)
                    }
                }
                
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{self.vectorstore_url}/vectorstore/documents",  # Endpoint corretto
                            json=doc  # Invia singolo documento, non array
                        )
                        response.raise_for_status()
                        results.append(response.json())
                
                except httpx.HTTPError as e:
                    logger.error(
                        f"❌ Errore aggiunta chunk {chunk['index']} al vectorstore: {str(e)}",
                        details={"chunk": chunk['index'], "error": str(e)}
                    )
                    raise ValueError(f"Errore aggiunta vectorstore: {str(e)}")
            
            logger.info(
                f"✅ Aggiunti {len(results)} chunks al vectorstore",
                details={
                    "collection": collection_name,
                    "document_id": metadata.get('document_id'),
                    "chunks_added": len(results)
                }
            )
            
            return {
                "vectorstore_results": results,
                "chunks_added": len(results),
                "collection": collection_name,
                "status": "success"
            }
        
        elif operation == "delete":
            # Elimina documenti dal vectorstore
            document_id = metadata.get("document_id") or input_data.get("document_id")
            
            if not document_id:
                raise ValueError("document_id richiesto per operazione delete")
            
            # Se ci sono chunks, elimina tutti i chunk del documento
            # Altrimenti elimina solo il documento base
            deleted_count = 0
            
            if chunks:
                # Elimina ogni chunk
                for chunk in chunks:
                    chunk_id = f"{document_id}_{chunk['index']}"
                    
                    try:
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            response = await client.delete(
                                f"{self.vectorstore_url}/documents/{chunk_id}"
                            )
                            response.raise_for_status()
                            deleted_count += 1
                    
                    except httpx.HTTPError as e:
                        logger.warning(
                            f"⚠️ Errore eliminazione chunk {chunk_id}: {str(e)}",
                            details={"chunk_id": chunk_id, "error": str(e)}
                        )
                        # Continua comunque con gli altri chunk
            else:
                # Elimina solo il documento base
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.delete(
                            f"{self.vectorstore_url}/documents/{document_id}"
                        )
                        response.raise_for_status()
                        deleted_count = 1
                
                except httpx.HTTPError as e:
                    logger.error(
                        f"❌ Errore eliminazione documento {document_id}: {str(e)}",
                        details={"document_id": document_id, "error": str(e)}
                    )
                    raise ValueError(f"Errore eliminazione vectorstore: {str(e)}")
            
            logger.info(
                f"🗑️ Eliminati {deleted_count} documenti dal vectorstore",
                details={
                    "collection": collection_name,
                    "document_id": document_id,
                    "chunks_deleted": deleted_count
                }
            )
            
            return {
                "chunks_deleted": deleted_count,
                "document_id": document_id,
                "collection": collection_name,
                "status": "deleted"
            }
        
        elif operation == "update":
            # Update = Delete + Add (il VectorStore non ha endpoint PUT)
            document_id = metadata.get("document_id") or input_data.get("document_id")
            
            if not document_id:
                raise ValueError("document_id richiesto per operazione update")
            
            logger.info(
                f"🔄 Update documento via delete+add",
                details={"document_id": document_id}
            )
            
            # Prima trova ed elimina tutti i vecchi chunks
            deleted_count = 0
            try:
                # Query VectorStore per trovare tutti i chunks esistenti
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Cerca con metadata filter per document_id
                    search_response = await client.post(
                        f"{self.vectorstore_url}/vectorstore/search",
                        json={
                            "query": document_id,
                            "n_results": 1000,  # Max chunks possibili
                            "where": {"document_id": document_id}
                        }
                    )
                    
                    if search_response.status_code == 200:
                        search_results = search_response.json()
                        chunk_ids = search_results.get("ids", [])
                        
                        # Elimina tutti i chunks trovati
                        for chunk_id in chunk_ids:
                            try:
                                delete_response = await client.delete(
                                    f"{self.vectorstore_url}/documents/{chunk_id}"
                                )
                                if delete_response.status_code == 200:
                                    deleted_count += 1
                            except Exception as delete_err:
                                logger.warning(
                                    f"⚠️ Impossibile eliminare chunk {chunk_id}: {delete_err}"
                                )
                    else:
                        # Fallback: prova con loop sequenziale
                        logger.info("⚠️ Search non disponibile, uso fallback loop")
                        for i in range(100):
                            chunk_id = f"{document_id}_{i}"
                            try:
                                response = await client.delete(
                                    f"{self.vectorstore_url}/documents/{chunk_id}"
                                )
                                if response.status_code == 200:
                                    deleted_count += 1
                                elif response.status_code == 404:
                                    break
                            except:
                                break
                
                logger.info(
                    f"🗑️ Eliminati {deleted_count} vecchi chunks per update",
                    details={"document_id": document_id, "deleted": deleted_count}
                )
            
            except Exception as e:
                logger.warning(
                    f"⚠️ Errore durante eliminazione vecchi chunks: {str(e)}",
                    details={"document_id": document_id, "error": str(e)}
                )
            
            # Poi aggiungi i nuovi chunks con retry automatico
            results = []
            failed_chunks = []
            
            for chunk in chunks:
                if not chunk.get("text", "").strip():
                    logger.warning(
                        f"⚠️ Chunk {chunk.get('index', 'unknown')} vuoto, skip",
                        details={"chunk_index": chunk.get('index')}
                    )
                    continue
                
                doc = {
                    "id": f"{document_id}_{chunk['index']}",
                    "content": chunk["text"],
                    "metadata": {
                        **metadata,
                        **chunk.get("metadata", {}),
                        "chunk_index": chunk["index"],
                        "source": file_path,
                        "file_name": os.path.basename(file_path),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
                
                # Retry fino a 3 volte per gestire timeout/errori temporanei
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            response = await client.post(
                                f"{self.vectorstore_url}/vectorstore/documents",
                                json=doc
                            )
                            response.raise_for_status()
                            results.append(response.json())
                            break  # Successo, esci dal retry loop
                    
                    except httpx.TimeoutException as e:
                        if retry < max_retries - 1:
                            logger.warning(
                                f"⏱️ Timeout chunk {chunk['index']}, retry {retry + 1}/{max_retries}",
                                details={"chunk": chunk['index'], "retry": retry + 1}
                            )
                            await asyncio.sleep(2 ** retry)  # Exponential backoff
                            continue
                        else:
                            logger.error(
                                f"❌ Timeout definitivo chunk {chunk['index']} dopo {max_retries} tentativi",
                                details={"chunk": chunk['index'], "error": str(e)}
                            )
                            failed_chunks.append(chunk['index'])
                    
                    except httpx.HTTPError as e:
                        logger.error(
                            f"❌ Errore aggiunta chunk {chunk['index']} durante update: {str(e)}",
                            details={"chunk": chunk['index'], "error": str(e), "retry": retry}
                        )
                        if retry == max_retries - 1:
                            failed_chunks.append(chunk['index'])
                        else:
                            await asyncio.sleep(1)
            
            result_status = "updated" if not failed_chunks else "partially_updated"
            
            if failed_chunks:
                logger.warning(
                    f"⚠️ Update parziale - alcuni chunks falliti",
                    details={
                        "document_id": document_id,
                        "total_chunks": len(chunks),
                        "success_chunks": len(results),
                        "failed_chunks": failed_chunks
                    }
                )
            else:
                logger.info(
                    f"✅ Documento aggiornato completamente nel vectorstore",
                    details={
                        "collection": collection_name,
                        "document_id": document_id,
                        "deleted_chunks": deleted_count,
                        "added_chunks": len(results)
                    }
                )
            
            return {
                "vectorstore_results": results,
                "chunks_updated": len(results),
                "chunks_deleted": deleted_count,
                "failed_chunks": failed_chunks,
                "document_id": document_id,
                "collection": collection_name,
                "status": result_status
            }
        
        else:
            raise ValueError(f"Operazione non supportata: {operation}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configurazione vectorstore."""
        required = ["operation", "collection_name"]
        return all(k in config for k in required)


class EventLoggerProcessor(BaseNodeProcessor):
    """
    Processore per logging eventi.
    Logga il completamento del workflow.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """Logga l'evento di completamento."""
        config = node.config or {}
        input_data = context.get_input_for_node(node.node_id)
        
        event_type = config.get("event_type", "workflow_completed")
        log_level = config.get("log_level", "INFO")
        include_metadata = config.get("include_metadata", True)
        
        # Prepara messaggio log
        file_path = input_data.get("file_path", "unknown")
        metadata = input_data.get("metadata", {})
        
        log_message = f"Workflow completato per: {file_path}"
        log_details = {
            "event_type": event_type,
            "file": file_path,
            "workflow_id": context.workflow.workflow_id,
            "execution_id": context.execution_id
        }
        
        if include_metadata:
            log_details["metadata"] = metadata
        
        # Log usando il logger unificato (andrà al LogService)
        if log_level == "INFO":
            logger.info(log_message, details=log_details)
        elif log_level == "WARNING":
            logger.warning(log_message, details=log_details)
        elif log_level == "ERROR":
            logger.error(log_message, details=log_details)
        else:
            logger.debug(log_message, details=log_details)
        
        return {
            "logged": True,
            "log_status": "success",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configurazione logger."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        log_level = config.get("log_level", "INFO")
        return log_level in valid_levels

