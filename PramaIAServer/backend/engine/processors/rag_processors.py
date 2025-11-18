"""
RAG (Retrieval-Augmented Generation) Node Processors

Processori per integrazione con il sistema RAG, recupero documenti e query semantiche.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext
from backend.core import rag_engine
from backend.app.clients.vectorstore_client import VectorstoreServiceClient

logger = logging.getLogger(__name__)


class RAGQueryProcessor(BaseNodeProcessor):
    """
    Processore per query RAG.
    Recupera documenti rilevanti dalla knowledge base.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Esegue query RAG.
        
        Configurazioni supportate:
        - query_type: "semantic", "keyword", "hybrid"
        - max_results: numero massimo di risultati
        - similarity_threshold: soglia di similarità
        """
        config = node.config or {}
        max_results = config.get("max_results", 5)
        
        # Ottieni input dai nodi predecessori
        input_data = context.get_input_for_node(node.node_id)
        query = self._extract_query(input_data)
        
        if not query:
            raise ValueError("Query non specificata o vuota")
        
        logger.info(f"🔍 Esecuzione query RAG: '{query}' (max_results: {max_results})")
        
        try:
            # Usa il VectorstoreService tramite il client
            client = VectorstoreServiceClient()
            
            # Esegui ricerca semantica tramite il servizio
            collection_name = "pdf_documents"
            response = client.query(collection_name, query, max_results)
            
            # Formatta risultati
            results = []
            for i, match in enumerate(response.get("matches", [])):
                result = {
                    "rank": i + 1,
                    "content": match.get("document", ""),
                    "metadata": match.get("metadata", {}),
                    "source": match.get("metadata", {}).get("source", "unknown"),
                    "score": match.get("similarity_score", 0)
                }
                results.append(result)
            
            logger.info(f"✅ Trovati {len(results)} documenti rilevanti")
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "results_count": len(results),
                "retrieved_documents": [match.get("document", "") for match in response.get("matches", [])]
            }
            
        except Exception as e:
            logger.error(f"❌ Errore query RAG: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "query": query,
                "results": []
            }
    
    def _extract_query(self, input_data: Dict[str, Any]) -> str:
        """Estrae la query dai dati di input."""
        # Priorità nella ricerca della query
        priority_keys = ["query", "question", "input", "text", "user_input"]
        
        for key in priority_keys:
            if key in input_data and input_data[key]:
                return str(input_data[key])
        
        # Se non trovata, prendi il primo valore stringa
        for value in input_data.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
        
        return ""
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo RAG."""
        if "max_results" in config:
            if not isinstance(config["max_results"], int) or config["max_results"] <= 0:
                return False
        
        return True


class RAGGenerationProcessor(BaseNodeProcessor):
    """
    Processore per generazione RAG.
    Combina documenti recuperati con LLM per generare risposte.
    """
    
    async def execute(self, node, context: ExecutionContext) -> str:
        """
        Esegue generazione RAG combinando documenti recuperati con prompt.
        """
        config = node.config or {}
        model = config.get("model", "gpt-4o")
        max_history = config.get("max_history", 5)
        system_prompt = config.get("system_prompt", None)
        
        # Ottieni input dai nodi predecessori
        input_data = context.get_input_for_node(node.node_id)
        
        # Estrai query e documenti
        query = input_data.get("query", input_data.get("input", ""))
        documents = input_data.get("retrieved_documents", [])
        
        if not query:
            raise ValueError("Nessuna query fornita per la generazione RAG")
        
        logger.info(f"🤖 Generazione RAG per query: '{query}' con {len(documents)} documenti")
        
        try:
            # Usa il sistema RAG esistente per la generazione
            response = rag_engine.process_question(
                question=query,
                user_id="workflow_system",  # User ID speciale per workflow
                session_id=context.execution_id,  # Usa execution_id come session
                model=model,
                db=None,  # Non abbiamo accesso al db qui, ma il RAG può gestirlo
                max_history=max_history,
                mode="rag",
                system_prompt=system_prompt
            )
            
            answer = response.answer
            logger.info(f"✅ Risposta RAG generata: {len(answer)} caratteri")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Errore generazione RAG: {str(e)}")
            raise ValueError(f"Errore nella generazione RAG: {str(e)}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo RAG Generation."""
        if "model" in config:
            # Lista modelli supportati
            supported_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "claude-3-sonnet-20240229"]
            if config["model"] not in supported_models:
                logger.warning(f"Modello non riconosciuto: {config['model']}")
        
        if "max_history" in config:
            if not isinstance(config["max_history"], int) or config["max_history"] < 0:
                return False
        
        return True


class DocumentIndexProcessor(BaseNodeProcessor):
    """
    Processore per indicizzazione documenti.
    Aggiunge documenti al sistema RAG.
    """
    
    async def execute(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Indicizza documenti nel sistema RAG.
        """
        config = node.config or {}

        # Ottieni input dai nodi predecessori
        input_data = context.get_input_for_node(node.node_id)

        # Estrai documenti da indicizzare
        documents = input_data.get("documents", [])
        if isinstance(documents, str):
            documents = [documents]

        if not documents:
            raise ValueError("Nessun documento fornito per l'indicizzazione")

        logger.info(f"📚 Indicizzazione di {len(documents)} documenti")

        try:
            # Usa il VectorstoreService per l'indicizzazione
            client = VectorstoreServiceClient()
            collection_name = "pdf_documents"
            
            indexed_count = 0
            errors = []
            
            for i, doc_content in enumerate(documents):
                try:
                    # Prepara metadati per il documento
                    metadata = {
                        "source": f"workflow_{context.execution_id}",
                        "index_time": datetime.utcnow().isoformat(),
                        "doc_id": f"workflow_{context.execution_id}_{i}"
                    }
                    
                    # Aggiungi il documento al vectorstore
                    response = client.add_document(
                        collection_name, 
                        {"text": doc_content}, 
                        metadata
                    )
                    
                    if response.get("success", False):
                        indexed_count += 1
                        logger.info(f"✅ Documento {i+1} indicizzato con ID: {response.get('document_id')}")
                    else:
                        error_msg = f"Errore nell'indicizzazione del documento {i+1}: {response.get('error', 'Errore sconosciuto')}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        
                except Exception as e:
                    error_msg = f"Errore documento {i+1}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            return {
                "status": "success" if indexed_count > 0 else "error",
                "indexed_count": indexed_count,
                "total_documents": len(documents),
                "errors": errors
            }

        except Exception as e:
            logger.error(f"❌ Errore indicizzazione: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "indexed_count": 0,
                "total_documents": len(documents)
            }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo Document Index."""
        return True
