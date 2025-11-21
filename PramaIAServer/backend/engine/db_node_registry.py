"""
Database-based Node Registry

Sostituisce il NodeRegistry in-memory con un sistema basato su database
per maggiore flessibilità, scalabilità e gestione runtime.
"""

import asyncio
from typing import Dict, Type, Any, List, Optional
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.node_registry_models import NodeType, PluginRegistry, NodeExecutionLog
from backend.db.database import SessionLocal
from backend.engine.execution_context import ExecutionContext
from backend.utils import get_logger

logger = get_logger(__name__)


class BaseNodeProcessor(ABC):
    """
    Classe base per tutti i processori di nodi.
    Interfaccia invariata per compatibilità.
    """
    
    @abstractmethod
    async def execute(self, node, context: ExecutionContext) -> Any:
        """Esegue la logica specifica del nodo."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida la configurazione del nodo."""
        pass


class DatabaseNodeRegistry:
    """
    Registry di nodi basato su database.
    
    Sostituisce completamente il vecchio NodeRegistry con:
    - Gestione runtime dei tipi di nodo
    - Auto-discovery da plugin PDK
    - Mapping automatico legacy → modern
    - Analytics e monitoring
    """
    
    def __init__(self):
        self._processor_cache: Dict[str, BaseNodeProcessor] = {}
        self._plugin_cache: Dict[str, Dict] = {}
        
        logger.info("🗃️ DatabaseNodeRegistry inizializzato")
    
    def get_db(self) -> Session:
        """Ottieni sessione database"""
        return SessionLocal()
    
    async def initialize(self):
        """Inizializza il registry con i processori di base"""
        await self._populate_default_nodes()
        await self._discover_pdk_plugins()
        logger.info(f"🔧 DatabaseNodeRegistry inizializzato con {self.count_active_nodes()} nodi")
    
    async def _populate_default_nodes(self):
        """Popola il database con i nodi predefiniti se non esistono"""
        db = self.get_db()
        
        # Controlla se i nodi di base esistono già
        existing_count = db.query(NodeType).filter(NodeType.plugin_id.is_(None)).count()
        if existing_count > 0:
            logger.info(f"📋 {existing_count} nodi di base già presenti nel database")
            return
        
        # Definizione nodi di base (nativi Python)
        base_nodes = [
            # Input processors
            {
                "node_type": "input_user",
                "processor_class": "UserInputProcessor",
                "display_name": "User Input",
                "description": "Raccoglie input dall'utente",
                "category": "input",
                "plugin_id": None
            },
            {
                "node_type": "input_file", 
                "processor_class": "FileInputProcessor",
                "display_name": "File Input",
                "description": "Legge file dal filesystem",
                "category": "input",
                "plugin_id": None
            },
            
            # LLM processors
            {
                "node_type": "llm_openai",
                "processor_class": "OpenAIProcessor", 
                "display_name": "OpenAI LLM",
                "description": "Processore per modelli OpenAI",
                "category": "llm",
                "plugin_id": None
            },
            {
                "node_type": "llm_ollama",
                "processor_class": "OllamaProcessor",
                "display_name": "Ollama LLM", 
                "description": "Processore per modelli Ollama",
                "category": "llm",
                "plugin_id": None
            },
            
            # Output processors
            {
                "node_type": "output_text",
                "processor_class": "TextOutputProcessor",
                "display_name": "Text Output",
                "description": "Output testuale",
                "category": "output", 
                "plugin_id": None
            },
            
            # Processing nodes
            {
                "node_type": "processing_text",
                "processor_class": "TextProcessor",
                "display_name": "Text Processor",
                "description": "Processamento testo generico",
                "category": "processing",
                "plugin_id": None,
                "is_legacy": True
            }
        ]
        
        # Inserisci nodi nel database
        for node_def in base_nodes:
            node_type = NodeType(**node_def)
            db.add(node_type)
        
        db.commit()
        logger.info(f"✅ Inseriti {len(base_nodes)} nodi di base nel database")
    
    async def _discover_pdk_plugins(self):
        """Scopre automaticamente i plugin PDK e registra i loro nodi"""
        try:
            import httpx
            
            # Query PDK server per plugin disponibili
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:3001/api/plugins")
                if response.status_code == 200:
                    plugins = response.json()
                    await self._register_pdk_plugins(plugins)
                else:
                    logger.warning(f"⚠️ PDK Server non risponde: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Impossibile contattare PDK Server: {e}")
    
    async def _register_pdk_plugins(self, plugins: List[Dict]):
        """Registra i plugin PDK e i loro nodi nel database"""
        db = self.get_db()
        
        for plugin_data in plugins:
            plugin_id = plugin_data.get("id")
            if not plugin_id:
                continue
                
            # Registra o aggiorna plugin
            plugin = db.query(PluginRegistry).filter_by(plugin_id=plugin_id).first()
            if not plugin:
                plugin = PluginRegistry(
                    plugin_id=plugin_id,
                    plugin_name=plugin_data.get("name", plugin_id),
                    plugin_version=plugin_data.get("version", "1.0.0"),
                    description=plugin_data.get("description"),
                    is_active=True,
                    status="online"
                )
                db.add(plugin)
            
            # Registra nodi del plugin
            nodes = plugin_data.get("nodes", [])
            for node_data in nodes:
                node_type_name = node_data.get("type") or node_data.get("id")
                if not node_type_name:
                    continue
                
                # Controlla se il nodo esiste già
                existing_node = db.query(NodeType).filter_by(
                    node_type=node_type_name,
                    plugin_id=plugin_id
                ).first()
                
                if not existing_node:
                    node_type = NodeType(
                        node_type=node_type_name,
                        plugin_id=plugin_id,
                        processor_class="PDKProxyProcessor",
                        display_name=node_data.get("name", node_type_name),
                        description=node_data.get("description"),
                        category=node_data.get("category", "processing"),
                        input_schema=node_data.get("input_schema"),
                        output_schema=node_data.get("output_schema"),
                        is_active=True
                    )
                    db.add(node_type)
        
        db.commit()
        logger.info(f"🔌 Registrati plugin PDK nel database")
    
    def get_processor(self, node_type: str) -> BaseNodeProcessor:
        """
        Ottieni processore per tipo nodo - SOLO NODI MODERNI!
        
        NO LEGACY MAPPING! Se il nodo non esiste, errore chiaro.
        """
        # Cache check
        if node_type in self._processor_cache:
            return self._processor_cache[node_type]
        
        db = self.get_db()
        
        try:
            # Cerca SOLO il nodo diretto - NO MAPPING LEGACY!
            node = db.query(NodeType).filter_by(
                node_type=node_type,
                is_active=True
            ).first()
            
            if not node:
                # NESSUN FALLBACK! Errore chiaro!
                logger.error(f"🚨 NODO NON SUPPORTATO: {node_type}")
                logger.error(f"💡 Usa solo nodi moderni dal PDK!")
                
                # Mostra nodi moderni disponibili
                available_nodes = db.query(NodeType.node_type).filter_by(is_active=True).all()
                logger.error(f"🔧 Nodi moderni disponibili:")
                for (available,) in available_nodes:
                    logger.error(f"  - {available}")
                
                raise ValueError(f"Nodo non supportato: {node_type}. Usa SOLO nodi moderni PDK!")
            
            # Crea il processore
            processor = self._create_processor(node)
            
            # Cache
            self._processor_cache[node_type] = processor
            
            return processor
            
        finally:
            db.close()
    
    def _create_processor(self, node_type_record: NodeType) -> BaseNodeProcessor:
        """Crea il processore appropriato per il tipo di nodo"""
        
        if node_type_record.plugin_id is None:
            # Nodo nativo Python
            return self._create_native_processor(node_type_record)
        else:
            # Nodo PDK
            return self._create_pdk_processor(node_type_record)
    
    def _create_native_processor(self, node: NodeType) -> BaseNodeProcessor:
        """Crea processore nativo Python"""
        # Import dinamico dei processori
        processor_map = {
            "UserInputProcessor": "backend.engine.processors.input_processors:UserInputProcessor",
            "FileInputProcessor": "backend.engine.processors.input_processors:FileInputProcessor", 
            "OpenAIProcessor": "backend.engine.processors.llm_processors:OpenAIProcessor",
            "OllamaProcessor": "backend.engine.processors.llm_processors:OllamaProcessor",
            "TextOutputProcessor": "backend.engine.processors.output_processors:TextOutputProcessor",
            "TextProcessor": "backend.engine.processors.processing_processors:TextProcessor"
        }
        
        processor_path = processor_map.get(str(node.processor_class))
        if not processor_path:
            raise ValueError(f"Processore sconosciuto: {node.processor_class}")
        
        # Import dinamico
        module_path, class_name = processor_path.split(":")
        module = __import__(module_path, fromlist=[class_name])
        processor_class = getattr(module, class_name)
        
        return processor_class()
    
    def _create_pdk_processor(self, node: NodeType) -> BaseNodeProcessor:
        """Crea processore PDK proxy"""
        from backend.engine.processors.pdk_proxy_processors import PDKProxyProcessor
        return PDKProxyProcessor(str(node.plugin_id), str(node.node_type))
    
    def is_node_type_supported(self, node_type: str) -> bool:
        """Verifica se un tipo di nodo è supportato"""
        try:
            self.get_processor(node_type)
            return True
        except ValueError:
            return False
    
    def get_supported_node_types(self) -> List[str]:
        """Ottieni tutti i tipi di nodo supportati"""
        db = self.get_db()
        try:
            results = db.query(NodeType.node_type).filter_by(is_active=True).all()
            return [result[0] for result in results]
        finally:
            db.close()
    
    def count_active_nodes(self) -> int:
        """Conta i nodi attivi"""
        db = self.get_db()
        try:
            return db.query(NodeType).filter_by(is_active=True).count()
        finally:
            db.close()
    
    def validate_config(self, node_type: str, config: Dict[str, Any]) -> bool:
        """Valida la configurazione di un nodo."""
        try:
            processor = self.get_processor(node_type)
            return processor.validate_config(config)
        except ValueError:
            return False
    
    async def register_node_type(
        self,
        node_type: str,
        processor_class: str,
        plugin_id: Optional[str] = None,
        **kwargs
    ):
        """Registra un nuovo tipo di nodo runtime"""
        db = self.get_db()
        
        # Controlla se esiste già
        existing = db.query(NodeType).filter_by(node_type=node_type).first()
        if existing:
            raise ValueError(f"Tipo di nodo già esistente: {node_type}")
        
        node = NodeType(
            node_type=node_type,
            processor_class=processor_class,
            plugin_id=plugin_id,
            **kwargs
        )
        
        db.add(node)
        db.commit()
        
        # Invalida cache
        if node_type in self._processor_cache:
            del self._processor_cache[node_type]
        
        logger.info(f"✅ Registrato nuovo tipo di nodo: {node_type}")
    
    # RIMOSSO: create_legacy_mapping() - NON PIÙ NECESSARIO!
    # Il sistema usa SOLO nodi moderni PDK


# Istanza globale del registry
db_node_registry = DatabaseNodeRegistry()