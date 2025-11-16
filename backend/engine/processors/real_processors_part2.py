"""
Real Processors - Parte 2
Processori per Document Processing, Vector Store Operations e Event Logging
"""

import logging
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# ChromaDB e embedding - Import diretti senza fallback
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# SQLite per metadati strutturati
import sqlite3

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext
from backend.utils import get_logger

logger = get_logger()


class DocumentProcessorProcessor(BaseNodeProcessor):
    """
    Processore reale per elaborazione avanzata documenti.
    
    Combina testo, metadati e analisi per preparare il documento
    per indicizzazione e archiviazione.
    """
    
    def __init__(self):
        self.chunk_size = 512  # Dimensione chunk default
        self.chunk_overlap = 50  # Overlap tra chunk
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Elabora il documento completo creando chunks e struttura finale.
        """
        logger.info(f"📝 Document Processor: '{node.name}'")
        
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai componenti documento
        text_content = input_data.get("text", "")
        metadata = input_data.get("processed_metadata", input_data.get("metadata", {}))
        file_path = input_data.get("file_path", "")
        
        # Configurazione da nodo
        node_config = getattr(node, 'config', {})
        chunk_size = node_config.get('chunk_size', self.chunk_size)
        chunk_overlap = node_config.get('chunk_overlap', self.chunk_overlap)
        
        # Genera ID documento univoco
        document_id = self._generate_document_id(text_content, file_path)
        
        # Suddividi testo in chunks
        text_chunks = self._create_text_chunks(text_content, chunk_size, chunk_overlap)
        
        # Arricchisci ogni chunk con metadati
        enriched_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "chunk_size": len(chunk_text),
                "document_id": document_id
            })
            
            enriched_chunks.append({
                "chunk_id": f"{document_id}_chunk_{i}",
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        # Preparazione documento strutturato
        processed_document = {
            "document_id": document_id,
            "original_text": text_content,
            "chunks": enriched_chunks,
            "metadata": metadata,
            "processing_info": {
                "chunk_count": len(text_chunks),
                "total_length": len(text_content),
                "processing_timestamp": datetime.now().isoformat(),
                "chunk_strategy": {
                    "size": chunk_size,
                    "overlap": chunk_overlap,
                    "method": "sliding_window"
                }
            }
        }
        
        # Statistiche processing
        processing_stats = {
            "chunks_created": len(text_chunks),
            "avg_chunk_size": sum(len(chunk["text"]) for chunk in enriched_chunks) / len(enriched_chunks) if enriched_chunks else 0,
            "metadata_fields": len(metadata),
            "processing_success": True
        }
        
        result = {
            "processed_document": processed_document,
            "document_id": document_id,
            "chunks": enriched_chunks,
            "processing_stats": processing_stats,
            "ready_for_storage": True
        }
        
        logger.info(f"  ✅ Documento processato: {len(text_chunks)} chunks, ID: {document_id[:8]}...")
        return result
    
    def _generate_document_id(self, content: str, file_path: str) -> str:
        """Genera ID univoco per il documento."""
        # Combina hash contenuto + timestamp + path per unicità
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        path_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"doc_{timestamp}_{content_hash[:8]}_{path_hash[:8]}"
    
    def _create_text_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Suddivide il testo in chunks con overlap."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calcola fine chunk
            end = min(start + chunk_size, text_length)
            
            # Se non è l'ultimo chunk, cerca un punto di separazione naturale
            if end < text_length:
                # Cerca l'ultimo spazio, punto o newline prima del limite
                for separator in ['\n\n', '. ', '! ', '? ', '\n', ' ']:
                    last_sep = text.rfind(separator, start, end)
                    if last_sep > start + chunk_size // 2:  # Almeno metà chunk
                        end = last_sep + len(separator)
                        break
            
            # Estrai chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calcola prossimo inizio con overlap
            if end >= text_length:
                break
                
            start = max(end - overlap, start + 1)
        
        return chunks
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del processore."""
        chunk_size = config.get('chunk_size', 512)
        chunk_overlap = config.get('chunk_overlap', 50)
        
        if not isinstance(chunk_size, int) or chunk_size < 100:
            return False
        if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
            return False
        if chunk_overlap >= chunk_size:
            return False
            
        return True


class VectorStoreOperationsProcessor(BaseNodeProcessor):
    """
    Processore reale per operazioni ChromaDB vector store.
    
    Gestisce embedding, indicizzazione e ricerca nel vector database.
    """
    
    def __init__(self):
        self.chroma_client = None
        self.collection_name = "prama_documents"
        
        # Inizializza modello embedding
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Modello embedding caricato: all-MiniLM-L6-v2")
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Esegue operazioni vector store basate sulla configurazione nodo.
        """
        logger.info(f"🔍 Vector Store Processor: '{node.name}'")
        

        
        input_data = context.get_input_for_node(node.node_id)
        node_config = getattr(node, 'config', {})
        
        # Determina operazione
        operation = node_config.get('operation', 'index')  # index, search, update, delete
        
        # Inizializza client ChromaDB se necessario
        if not self.chroma_client:
            await self._initialize_chroma_client()
        
        # Esegui operazione specifica
        if operation == 'index':
            result = await self._index_document(input_data, node_config)
        elif operation == 'search':
            result = await self._search_documents(input_data, node_config)
        elif operation == 'update':
            result = await self._update_document(input_data, node_config)
        elif operation == 'delete':
            result = await self._delete_document(input_data, node_config)
        else:
            raise ValueError(f"Operazione vector store non supportata: {operation}")
        
        logger.info(f"  ✅ Operazione '{operation}' completata")
        return result
    
    async def _initialize_chroma_client(self):
        """Inizializza client ChromaDB."""
        try:
            # Configurazione ChromaDB (nuova API v1.3+)
            persist_dir = Path(__file__).parent.parent / "chromadb_data"
            persist_dir.mkdir(exist_ok=True)
            
            # Nuova sintassi per ChromaDB 1.3+
            self.chroma_client = chromadb.PersistentClient(path=str(persist_dir))
            
            # Ottieni o crea collection
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
                logger.info(f"📚 Collection esistente caricata: {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(self.collection_name)
                logger.info(f"📚 Nuova collection creata: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione ChromaDB: {e}")
            raise
    
    async def _index_document(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Indicizza documento nel vector store."""
        chunks = input_data.get("chunks", [])
        document_id = input_data.get("document_id")
        
        if not chunks:
            return {"status": "no_chunks", "indexed_count": 0}
        
        # Prepara dati per ChromaDB
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [chunk["chunk_id"] for chunk in chunks]
        
        # Genera embeddings
        logger.info(f"  🔄 Generando embeddings per {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Indicizza in ChromaDB
        try:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )
            
            indexed_count = len(chunks)
            logger.info(f"  ✅ Indicizzati {indexed_count} chunks")
            
            return {
                "status": "success",
                "operation": "index",
                "document_id": document_id,
                "indexed_count": indexed_count,
                "chunk_ids": ids
            }
            
        except Exception as e:
            logger.error(f"❌ Errore indicizzazione: {e}")
            return {
                "status": "error",
                "operation": "index",
                "error": str(e),
                "indexed_count": 0
            }
    
    async def _search_documents(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Cerca documenti nel vector store."""
        query_text = input_data.get("query", input_data.get("search_query", ""))
        limit = config.get("limit", 10)
        
        if not query_text:
            return {"status": "no_query", "results": []}
        
        try:
            # Genera embedding per query
            query_embedding = self.embedding_model.encode([query_text]).tolist()
            
            # Cerca in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=limit
            )
            
            # Formatta risultati
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    search_results.append({
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i],
                        "id": results['ids'][0][i]
                    })
            
            logger.info(f"  🔍 Trovati {len(search_results)} risultati")
            
            return {
                "status": "success",
                "operation": "search",
                "query": query_text,
                "results": search_results,
                "total_found": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore ricerca: {e}")
            return {
                "status": "error",
                "operation": "search",
                "query": query_text,
                "error": str(e),
                "results": []
            }
    
    async def _update_document(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggiorna documento nel vector store."""
        # Per semplicità, implementiamo update come delete + add
        delete_result = await self._delete_document(input_data, config)
        if delete_result["status"] == "success":
            return await self._index_document(input_data, config)
        return delete_result
    
    async def _delete_document(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina documento dal vector store."""
        document_id = input_data.get("document_id")
        chunk_ids = input_data.get("chunk_ids", [])
        
        if not document_id and not chunk_ids:
            return {"status": "no_identifiers", "deleted_count": 0}
        
        try:
            # Se abbiamo chunk_ids specifici, usa quelli
            if chunk_ids:
                ids_to_delete = chunk_ids
            else:
                # Altrimenti cerca tutti i chunk del documento
                search_results = self.collection.get(
                    where={"document_id": document_id}
                )
                ids_to_delete = search_results['ids'] if search_results['ids'] else []
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                deleted_count = len(ids_to_delete)
                logger.info(f"  🗑️ Eliminati {deleted_count} chunks")
            else:
                deleted_count = 0
                logger.info("  ℹ️ Nessun chunk da eliminare trovato")
            
            return {
                "status": "success",
                "operation": "delete",
                "document_id": document_id,
                "deleted_count": deleted_count,
                "deleted_ids": ids_to_delete
            }
            
        except Exception as e:
            logger.error(f"❌ Errore eliminazione: {e}")
            return {
                "status": "error",
                "operation": "delete",
                "document_id": document_id,
                "error": str(e),
                "deleted_count": 0
            }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del processore."""
        operation = config.get('operation', 'index')
        valid_operations = ['index', 'search', 'update', 'delete']
        
        if operation not in valid_operations:
            return False
        
        # Validazioni specifiche per operazione
        if operation == 'search':
            limit = config.get('limit', 10)
            if not isinstance(limit, int) or limit < 1 or limit > 100:
                return False
        
        return True


class EventLoggerProcessor(BaseNodeProcessor):
    """
    Processore reale per logging eventi e audit trail.
    
    Registra tutte le operazioni di workflow per monitoraggio e debug.
    """
    
    def __init__(self):
        self.log_file = "workflow_events.log"
        self.audit_db = "workflow_audit.db"
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Registra evento di workflow nel sistema di logging.
        """
        logger.info(f"📋 Event Logger Processor: '{node.name}'")
        
        input_data = context.get_input_for_node(node.node_id)
        node_config = getattr(node, 'config', {})
        
        # Prepara evento da loggare
        event = self._prepare_event_data(input_data, context, node_config)
        
        # Log in file
        if node_config.get('log_to_file', True):
            await self._log_to_file(event)
        
        # Log in database per audit
        if node_config.get('log_to_db', True):
            await self._log_to_database(event)
        
        # Log applicativo
        log_level = node_config.get('log_level', 'info')
        self._log_to_application(event, log_level)
        
        # Statistiche logging
        logging_stats = {
            "event_logged": True,
            "timestamp": event["timestamp"],
            "event_id": event["event_id"],
            "logged_to": []
        }
        
        if node_config.get('log_to_file', True):
            logging_stats["logged_to"].append("file")
        if node_config.get('log_to_db', True):
            logging_stats["logged_to"].append("database")
        
        result = {
            "event": event,
            "logging_stats": logging_stats,
            "status": "logged"
        }
        
        logger.info(f"  ✅ Evento loggato: {event['event_id']}")
        return result
    
    def _prepare_event_data(self, input_data: Dict[str, Any], context: ExecutionContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara i dati dell'evento per il logging."""
        
        # Genera ID evento univoco
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Estrai informazioni workflow
        workflow_info = {
            "workflow_id": context.workflow.workflow_id,
            "workflow_name": context.workflow.name,
            "execution_id": context.execution_id,
            "node_id": context.current_node_id if hasattr(context, 'current_node_id') else None
        }
        
        # Estrai dati rilevanti dall'input (filtrati per sicurezza)
        safe_input_data = self._sanitize_for_logging(input_data)
        
        # Informazioni di sistema
        system_info = {
            "user_id": getattr(context, 'user_id', 'system'),
            "source_ip": getattr(context, 'source_ip', 'localhost'),
            "user_agent": getattr(context, 'user_agent', 'PramaIA-Workflow')
        }
        
        # Determina livello evento e categoria
        event_level = config.get('event_level', 'info')
        event_category = config.get('event_category', self._infer_category(input_data))
        
        return {
            "event_id": event_id,
            "timestamp": timestamp,
            "level": event_level,
            "category": event_category,
            "workflow_info": workflow_info,
            "system_info": system_info,
            "data": safe_input_data,
            "metadata": {
                "processor": "EventLoggerProcessor",
                "version": "1.0.0"
            }
        }
    
    def _sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rimuove dati sensibili dal logging."""
        sanitized = {}
        
        # Campi sicuri da loggare
        safe_fields = [
            'document_id', 'operation', 'status', 'processing_stats',
            'chunk_count', 'file_size', 'event_type', 'timestamp',
            'metadata_fields', 'search_query', 'results_count'
        ]
        
        for field in safe_fields:
            if field in data:
                sanitized[field] = data[field]
        
        # Aggiungi contatori senza contenuto sensibile
        if 'text' in data:
            sanitized['text_length'] = len(data['text'])
        if 'chunks' in data:
            sanitized['chunks_count'] = len(data['chunks'])
        if 'results' in data:
            sanitized['results_count'] = len(data['results'])
        
        return sanitized
    
    def _infer_category(self, data: Dict[str, Any]) -> str:
        """Inferisce la categoria dell'evento dai dati."""
        if 'operation' in data:
            operation = data['operation']
            if operation in ['index', 'search', 'update', 'delete']:
                return 'vector_store'
            elif operation in ['create', 'read', 'update', 'delete']:
                return 'crud'
        
        if 'document_id' in data:
            return 'document_processing'
        
        if 'event_type' in data:
            return 'system_event'
        
        return 'workflow'
    
    async def _log_to_file(self, event: Dict[str, Any]):
        """Scrive evento nel file di log."""
        try:
            log_entry = json.dumps(event, ensure_ascii=False, separators=(',', ':'))
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
                
        except Exception as e:
            logger.error(f"❌ Errore logging su file: {e}")
    
    async def _log_to_database(self, event: Dict[str, Any]):
        """Salva evento nel database di audit."""
        try:
            # Inizializza database se non existe
            await self._ensure_audit_db()
            
            conn = sqlite3.connect(self.audit_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO workflow_events (
                    event_id, timestamp, level, category,
                    workflow_id, execution_id, user_id,
                    event_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event['event_id'],
                event['timestamp'],
                event['level'],
                event['category'],
                event['workflow_info']['workflow_id'],
                event['workflow_info']['execution_id'],
                event['system_info']['user_id'],
                json.dumps(event['data'])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Errore logging su database: {e}")
    
    async def _ensure_audit_db(self):
        """Assicura che il database di audit esista."""
        try:
            conn = sqlite3.connect(self.audit_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    timestamp TEXT,
                    level TEXT,
                    category TEXT,
                    workflow_id TEXT,
                    execution_id TEXT,
                    user_id TEXT,
                    event_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crea indici per performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_id ON workflow_events(workflow_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON workflow_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON workflow_events(category)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione audit database: {e}")
    
    def _log_to_application(self, event: Dict[str, Any], level: str):
        """Log nell'application logger."""
        message = f"[{event['category']}] {event['workflow_info']['workflow_name']} - {event['event_id']}"
        
        if level == 'debug':
            logger.debug(message)
        elif level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del processore."""
        valid_levels = ['debug', 'info', 'warning', 'error']
        level = config.get('log_level', 'info')
        
        if level not in valid_levels:
            return False
        
        return True