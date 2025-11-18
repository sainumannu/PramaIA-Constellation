"""
Node Registry

Registro di tutti i tipi di nodi disponibili e i loro processori.
"""

from typing import Dict, Type, Any, List
from abc import ABC, abstractmethod

from backend.engine.execution_context import ExecutionContext
from backend.utils import get_logger

logger = get_logger(__name__)


class BaseNodeProcessor(ABC):
    """
    Classe base per tutti i processori di nodi.
    
    Ogni tipo di nodo deve implementare questa interfaccia.
    """
    
    @abstractmethod
    async def execute(self, node, context: ExecutionContext) -> Any:
        """
        Esegue la logica specifica del nodo.
        
        Args:
            node: Il nodo da eseguire (contiene tipo, config, etc.)
            context: Contesto di esecuzione con stato e dati
            
        Returns:
            Risultato dell'esecuzione del nodo
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida la configurazione del nodo.
        
        Args:
            config: Configurazione del nodo
            
        Returns:
            True se la configurazione è valida
        """
        pass


class NodeRegistry:
    """
    Registro centrale per tutti i tipi di nodi supportati.
    
    Gestisce:
    - Registrazione dei processori
    - Lookup dei processori per tipo
    - Validazione tipi supportati
    """
    
    def __init__(self):
        self._processors: Dict[str, BaseNodeProcessor] = {}
        self._node_info: Dict[str, Dict[str, Any]] = {}
        # Lista di nodi deprecati (migrati al PDK)
        self._deprecated_nodes = [
            # Input processors (migrati a core-input-plugin)
            "input_user",
            "input_file",
            
            # LLM processors (migrati a core-llm-plugin)
            "llm_openai",
            "llm_anthropic",
            "llm_gemini",
            "llm_ollama",
            
            # Output processors (migrati a core-output-plugin)
            "output_text",
            "output_file",
            "output_email",
            
            # Data processing processors (migrati a core-data-plugin)
            "data_transform",
            "text_processor",
            "json_processor",
            
            # API processors (migrati a core-api-plugin)
            "http_request",
            "webhook",
            "api_call",
            
            # RAG processors (migrati a core-rag-plugin)
            "rag_query",
            "document_index",
            "rag_generation",
            
            # Legacy processors
            "processing_text",
        ]
        self._register_default_processors()
        logger.info(f"🔧 NodeRegistry inizializzato con {len(self._processors)} processori")
    
    def _register_default_processors(self):
        """Registra i processori di default per i tipi di nodo standard."""
        from backend.engine.processors.input_processors import UserInputProcessor, FileInputProcessor
        from backend.engine.processors.llm_processors import OpenAIProcessor, AnthropicProcessor, OllamaProcessor
        from backend.engine.processors.output_processors import TextOutputProcessor, FileOutputProcessor, EmailOutputProcessor
        from backend.engine.processors.data_processors import DataTransformProcessor, TextProcessor, JSONProcessor
        from backend.engine.processors.api_processors import HTTPRequestProcessor, WebhookProcessor, APICallProcessor
        from backend.engine.processors.rag_processors import RAGQueryProcessor, DocumentIndexProcessor, RAGGenerationProcessor
        from backend.engine.processors.pdk_processors import PDKNodeProcessor
        # Importa i processori workflow REALI invece degli stub
        from backend.engine.processors.workflow_processors import (
            EventInputProcessor, FileParsingProcessor, MetadataManagerProcessor,
            DocumentProcessorProcessor, VectorStoreOperationsProcessor, EventLoggerProcessor
        )
        
        # Input processors
        self.register_processor("input_user", UserInputProcessor())
        self.register_processor("input_file", FileInputProcessor())
        
        # LLM processors
        self.register_processor("llm_openai", OpenAIProcessor())
        self.register_processor("llm_anthropic", AnthropicProcessor())
        self.register_processor("llm_gemini", OpenAIProcessor())  # Placeholder, usa OpenAI per ora
        self.register_processor("llm_ollama", OllamaProcessor())
        
        # Output processors
        self.register_processor("output_text", TextOutputProcessor())
        self.register_processor("output_file", FileOutputProcessor())
        self.register_processor("output_email", EmailOutputProcessor())
        
        # Data processing processors
        self.register_processor("data_transform", DataTransformProcessor())
        self.register_processor("text_processor", TextProcessor())
        self.register_processor("json_processor", JSONProcessor())
        
        # API processors
        self.register_processor("http_request", HTTPRequestProcessor())
        self.register_processor("webhook", WebhookProcessor())
        self.register_processor("api_call", APICallProcessor())
        
        # RAG processors
        self.register_processor("rag_query", RAGQueryProcessor())
        self.register_processor("document_index", DocumentIndexProcessor())
        self.register_processor("rag_generation", RAGGenerationProcessor())
        
        # STUB processors per workflow esistenti
        # TODO: Implementare processori reali
        self.register_processor("event_input_node", EventInputProcessor())
        self.register_processor("file_parsing", FileParsingProcessor())
        self.register_processor("metadata_manager", MetadataManagerProcessor())
        self.register_processor("document_processor", DocumentProcessorProcessor())
        self.register_processor("vector_store_operations", VectorStoreOperationsProcessor())
        self.register_processor("event_logger", EventLoggerProcessor())
        
        # PDF processors migrati al PDK - rimossi i processori legacy
        # I nodi PDF sono ora gestiti tramite l'architettura PDK
        # Vedere PramaIA-PDK/plugins/ per le implementazioni attuali
        
        # Processing processors (legacy)
        # Usano i processori esistenti invece di importare file non esistenti
        self.register_processor("processing_text", TextProcessor())
        
        # PDF Semantic Workflow processors - RIMOSSO: ora gestito da PramaIA-PDK
        # I nodi PDF semantici sono ora dinamicamente caricati dal PDK server
        # self.register_processor("pdf_input_node", FileInputProcessor())  
        # self.register_processor("pdf_text_extractor", TextProcessor())   
        # self.register_processor("text_chunker", TextProcessor())         
        # self.register_processor("text_embedder", TextProcessor())        
        # self.register_processor("chroma_vector_store", TextProcessor())  
        # self.register_processor("query_input_node", UserInputProcessor()) 
        # self.register_processor("chroma_retriever", TextProcessor())     
        # self.register_processor("llm_processor", OpenAIProcessor())      
        # self.register_processor("pdf_results_formatter", PDFResultsFormatterProcessor())
    
    def register_processor(self, node_type: str, processor: BaseNodeProcessor):
        """Registra un processore per un tipo di nodo."""
        self._processors[node_type] = processor
        logger.info(f"📝 Registrato processore per tipo '{node_type}': {processor.__class__.__name__}")
    
    def get_processor(self, node_type: str) -> BaseNodeProcessor:
        """Ottieni il processore per un tipo di nodo."""
        if node_type not in self._processors:
            raise ValueError(f"Tipo di nodo non supportato: {node_type}")
        return self._processors[node_type]
    
    def is_node_type_supported(self, node_type: str) -> bool:
        """Verifica se un tipo di nodo è supportato."""
        return node_type in self._processors
    
    def get_supported_node_types(self) -> list[str]:
        """Ottieni tutti i tipi di nodo supportati."""
        return list(self._processors.keys())
    
    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> bool:
        """Valida la configurazione di un nodo."""
        if not self.is_node_type_supported(node_type):
            return False
        
        processor = self.get_processor(node_type)
        return processor.validate_config(config)
    
    def register_pdk_node(self, plugin_id: str, node_info: Dict[str, Any]):
        """
        Registra un nodo PDK nel registro.
        
        Args:
            plugin_id: ID del plugin PDK
            node_info: Informazioni sul nodo dal plugin
        """
        # Import locale per evitare errori di circolarità
        from backend.engine.processors.pdk_processors import PDKNodeProcessor
        
        node_id = node_info["id"]
        node_type = f"pdk_{plugin_id}_{node_id}"
        
        # Crea e registra il processore per questo nodo
        processor = PDKNodeProcessor(plugin_id, node_id)
        self.register_processor(node_type, processor)
        
        # Salva le informazioni complete del nodo
        self._node_info[node_type] = {
            **node_info,
            "type": node_type,
            "plugin_id": plugin_id
        }
        
        logger.info(f"Registrato nodo PDK: {node_type}")
        return node_type
        
    def get_all_nodes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ottiene tutti i nodi registrati, raggruppati per plugin/categoria.
        
        Returns:
            Dict con chiave = plugin/categoria e valore = lista di nodi
        """
        nodes_by_category = {}
        
        # Raggruppa i nodi PDK per plugin
        for node_type, info in self._node_info.items():
            plugin_id = info.get("plugin_id", "core")
            if plugin_id not in nodes_by_category:
                nodes_by_category[plugin_id] = []
            nodes_by_category[plugin_id].append(info)
            
        # Aggiungi i nodi core 
        nodes_by_category["core"] = []
        for node_type in self._processors.keys():
            # Salta i nodi deprecati (migrati al PDK)
            if node_type in self._deprecated_nodes:
                logger.info(f"⚠️ Nodo deprecato saltato: {node_type} (è stato migrato al PDK)")
                continue
                
            # Salta i nodi PDK che hanno già un proprio gruppo
            if node_type.startswith("pdk_"):
                continue
                
            nodes_by_category["core"].append({
                "id": node_type,
                "name": node_type.replace("_", " ").title(),
                "type": node_type,
                "description": "Core workflow node",
                "inputs": [],
                "outputs": [],
                "plugin_id": "core"
            })
                
        return nodes_by_category
