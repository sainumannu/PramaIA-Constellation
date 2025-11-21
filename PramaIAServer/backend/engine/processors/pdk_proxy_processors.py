"""
PDK Proxy Processors

Processori proxy che delegano l'esecuzione al PDK Server.
Fanno da bridge tra il NodeRegistry del backend e i nodi implementati nel PDK.
"""

import asyncio
import os
import httpx
from typing import Dict, Any, Optional

from backend.engine.db_node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext
from backend.utils import get_logger

logger = get_logger(__name__)


class PDKProxyProcessor(BaseNodeProcessor):
    """
    Processore proxy che delega l'esecuzione a un nodo PDK specifico.
    
    Questo processore:
    1. Riceve l'esecuzione dal WorkflowEngine
    2. Converte i dati in formato PDK
    3. Chiama il PDK Server per eseguire il nodo
    4. Converte la risposta PDK in formato WorkflowEngine
    """
    
    def __init__(self, plugin_id: str, node_id: str):
        """
        Args:
            plugin_id: ID del plugin PDK (es. "document-semantic-complete-plugin")
            node_id: ID del nodo nel plugin (es. "document_input_node")
        """
        self.plugin_id = plugin_id
        self.node_id = node_id
        self.pdk_base_url = os.getenv("PDK_SERVER_BASE_URL", "http://localhost:3001")
        
        logger.debug(
            f"PDKProxyProcessor creato",
            details={
                "plugin_id": plugin_id,
                "node_id": node_id,
                "pdk_url": self.pdk_base_url
            }
        )
    
    async def execute(self, node, context: ExecutionContext) -> Any:
        """
        Esegue il nodo delegando al PDK Server.
        
        Args:
            node: Nodo workflow (NodeWrapper)
            context: Contesto di esecuzione
            
        Returns:
            Risultato dell'esecuzione del nodo PDK
        """
        logger.info(
            f"🔌 Executing PDK node via proxy",
            details={
                "node_name": node.name,
                "node_id": node.node_id,
                "pdk_plugin": self.plugin_id,
                "pdk_node": self.node_id,
                "workflow_id": context.workflow.id if context.workflow else "unknown",
                "execution_id": context.execution_id
            }
        )
        
        try:
            # 1. Prepara input per PDK
            input_data = await self._prepare_pdk_input(node, context)
            
            # 2. Prepara config per PDK
            config = await self._prepare_pdk_config(node, context)
            
            # 3. Chiama PDK Server
            result = await self._call_pdk_server(input_data, config)
            
            # 4. Processa output per WorkflowEngine
            processed_result = await self._process_pdk_output(result, node, context)
            
            logger.info(
                f"✅ PDK node execution completed",
                details={
                    "node_name": node.name,
                    "pdk_plugin": self.plugin_id,
                    "pdk_node": self.node_id,
                    "result_type": type(processed_result).__name__,
                    "result_keys": list(processed_result.keys()) if isinstance(processed_result, dict) else "not_dict"
                }
            )
            
            return processed_result
            
        except Exception as e:
            logger.error(
                f"❌ PDK node execution failed",
                details={
                    "node_name": node.name,
                    "pdk_plugin": self.plugin_id,
                    "pdk_node": self.node_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise ValueError(f"PDK execution failed for {self.plugin_id}/{self.node_id}: {str(e)}")
    
    async def _prepare_pdk_input(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Prepara i dati di input per il formato PDK.
        
        Il PDK aspetta un formato specifico per ogni nodo.
        """
        # Ottieni input dal contesto workflow
        input_data = context.get_input_for_node(node.node_id)
        
        logger.debug(
            f"🔍 Preparing PDK input",
            details={
                "node": self.node_id,
                "raw_input_keys": list(input_data.keys()) if isinstance(input_data, dict) else "not_dict",
                "raw_input_type": type(input_data).__name__
            }
        )
        
        # Mapping specifici per node_id
        if self.node_id == "document_input_node":
            # Document input ha bisogno del percorso file
            if "file_path" in input_data:
                return {"file_path": input_data["file_path"]}
            elif "input" in input_data and isinstance(input_data["input"], dict):
                return input_data["input"]
            else:
                # Fallback per eventi di upload
                return {
                    "file_path": input_data.get("file_path", ""),
                    "filename": input_data.get("filename", ""),
                    "file_size": input_data.get("file_size", 0)
                }
                
        elif self.node_id == "pdf_text_extractor":
            # PDF extractor ha bisogno del file PDF
            return {
                "pdf_file": input_data.get("file_output", input_data.get("pdf_file", input_data.get("file_path", "")))
            }
            
        elif self.node_id == "text_chunker":
            # Text chunker ha bisogno del testo
            text_input = input_data.get("text_output", input_data.get("text", ""))
            return {"text_input": text_input}
            
        elif self.node_id == "text_embedder":
            # Text embedder ha bisogno dei chunks
            chunks = input_data.get("chunks_output", input_data.get("chunks", []))
            return {"text_chunks": chunks}
            
        elif self.node_id == "chroma_vector_store":
            # Vector store ha bisogno degli embeddings
            embeddings = input_data.get("embeddings_output", input_data.get("embeddings", []))
            return {"embeddings_input": embeddings}
            
        elif self.node_id == "query_input_node":
            # Query input per ricerca
            return {
                "query": input_data.get("query", input_data.get("question", ""))
            }
            
        elif self.node_id == "chroma_retriever":
            # Retriever ha bisogno della query
            return {
                "query_input": input_data.get("query_output", input_data.get("query", ""))
            }
            
        elif self.node_id == "llm_processor":
            # LLM processor ha bisogno di contesto e domanda
            return {
                "context_input": input_data.get("documents_output", input_data.get("context", [])),
                "question_input": input_data.get("query", input_data.get("question", ""))
            }
            
        elif self.node_id == "document_results_formatter":
            # Results formatter ha bisogno del contenuto
            return {
                "content_input": input_data.get("response_output", input_data.get("response", ""))
            }
        
        else:
            # Default: passa tutto l'input
            return input_data
    
    async def _prepare_pdk_config(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Prepara la configurazione per il nodo PDK.
        """
        # Ottieni config dal nodo
        config = node.get("config", {}) if hasattr(node, "get") else {}
        
        # Configurazioni di default per alcuni nodi
        default_configs = {
            "document_input_node": {
                "extract_text": True,
                "extract_images": False,
                "pages": "all"
            },
            "pdf_text_extractor": {
                "preserve_layout": True,
                "extraction_method": "text",
                "ocr_enabled": False,
                "pages": "all"
            },
            "text_chunker": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "separator": "\\n\\n"
            },
            "text_embedder": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "batch_size": 32,
                "normalize": True
            },
            "chroma_vector_store": {
                "collection_name": "documents",
                "embedding_model": "text-embedding-ada-002",
                "chunk_size": 1000
            },
            "chroma_retriever": {
                "collection_name": "documents",
                "top_k": 5,
                "similarity_threshold": 0.7
            },
            "llm_processor": {
                "model": "ollama/llama3.2",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "document_results_formatter": {
                "output_format": "markdown",
                "include_sources": True,
                "include_metadata": True
            }
        }
        
        # Combina config di default con config del nodo
        node_config = default_configs.get(self.node_id, {})
        node_config.update(config)
        
        return node_config
    
    async def _call_pdk_server(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chiama il PDK Server per eseguire il nodo.
        """
        payload = {
            "nodeId": self.node_id,
            "inputs": input_data,
            "config": config
        }
        
        endpoint = f"{self.pdk_base_url}/plugins/{self.plugin_id}/execute"
        
        logger.debug(
            f"🌐 Calling PDK Server",
            details={
                "endpoint": endpoint,
                "payload_keys": list(payload.keys()),
                "inputs_keys": list(input_data.keys()),
                "config_keys": list(config.keys())
            }
        )
        
        try:
            timeout = httpx.Timeout(120.0)  # 2 minuti timeout per operazioni pesanti
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                result = response.json()
            
            # Verifica successo PDK
            if not result.get("success", False):
                raise ValueError(f"PDK returned success=false: {result.get('error', 'Unknown error')}")
            
            return result.get("result", {})
            
        except httpx.TimeoutException:
            raise ValueError(f"PDK Server timeout for {self.plugin_id}/{self.node_id}")
        except httpx.HTTPError as e:
            raise ValueError(f"PDK Server HTTP error: {e}")
        except Exception as e:
            raise ValueError(f"PDK Server call failed: {e}")
    
    async def _process_pdk_output(self, pdk_result: Dict[str, Any], node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Processa l'output PDK per il formato WorkflowEngine.
        """
        logger.debug(
            f"🔄 Processing PDK output",
            details={
                "node": self.node_id,
                "pdk_result_keys": list(pdk_result.keys()) if isinstance(pdk_result, dict) else "not_dict",
                "pdk_result_type": type(pdk_result).__name__
            }
        )
        
        # Il PDK potrebbe restituire il risultato in vari formati
        # Standardizza per il WorkflowEngine
        
        if isinstance(pdk_result, dict):
            # Se il risultato ha chiavi riconosciute, le usa
            # Altrimenti passa tutto
            return pdk_result
        else:
            # Se non è un dict, wrappa in un dict
            return {"result": pdk_result}
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida la configurazione del nodo PDK.
        
        Per ora accetta qualsiasi configurazione - la validazione 
        specifica è delegata al PDK Server.
        """
        return isinstance(config, dict)


class PDKNodeUnavailableProcessor(BaseNodeProcessor):
    """
    Processore fallback per nodi PDK non disponibili.
    
    Usato quando un nodo è mappato a PDK ma il PDK Server non è disponibile
    o il nodo non esiste nel plugin.
    """
    
    def __init__(self, plugin_id: str, node_id: str):
        self.plugin_id = plugin_id
        self.node_id = node_id
    
    async def execute(self, node, context: ExecutionContext) -> Any:
        """
        Restituisce un errore informativo per nodi PDK non disponibili.
        """
        error_msg = f"PDK node {self.plugin_id}/{self.node_id} not available"
        
        logger.warning(
            f"⚠️ PDK node unavailable",
            details={
                "node_name": node.name,
                "pdk_plugin": self.plugin_id,
                "pdk_node": self.node_id,
                "suggestion": "Check PDK Server is running and plugin is loaded"
            }
        )
        
        # Per testing, restituisce un risultato dummy invece di fallire
        return {
            "status": "unavailable",
            "error": error_msg,
            "plugin_id": self.plugin_id,
            "node_id": self.node_id,
            "dummy_result": "PDK node not available - using fallback"
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True