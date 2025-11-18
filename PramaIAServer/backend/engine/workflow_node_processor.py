"""
Workflow Node Processor

Questo modulo gestisce l'esecuzione e la validazione dei singoli nodi nei workflow,
inclusa la conversione dei tipi e la preparazione degli input/output.
"""

from typing import Dict, Any, List
from backend.engine.execution_context import ExecutionContext
from backend.engine.node_registry import NodeRegistry
from backend.engine.data_types import DataTypeRegistry
from backend.engine.node_schemas import NodeSchemaRegistry
from backend.utils import get_logger

logger = get_logger()


class NodeWrapper:
    """
    Wrapper per nodi che permette accesso sia come dict che come oggetto.
    Rende i processori compatibili indipendentemente dal formato del nodo.
    """
    def __init__(self, node_data: Dict[str, Any]):
        self._data = node_data
    
    def __getattr__(self, name: str):
        """Accesso come attributo: node.node_id"""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self._data.get(name)
    
    def __getitem__(self, key: str):
        """Accesso come dict: node['node_id']"""
        return self._data[key]
    
    def get(self, key: str, default=None):
        """Accesso sicuro: node.get('node_id')"""
        return self._data.get(key, default)
    
    def __contains__(self, key: str):
        """Supporto per 'in': 'node_id' in node"""
        return key in self._data


class WorkflowNodeProcessor:
    """
    Processore specializzato per l'esecuzione e validazione dei singoli nodi nei workflow.
    
    Gestisce:
    - Preparazione input nodi con conversione tipi
    - Esecuzione nodi con error handling
    - Validazione output nodi
    - Ricerca nodi di input nel workflow
    """
    
    def __init__(self):
        self.node_registry = NodeRegistry()
        self.type_registry = DataTypeRegistry()
        self.schema_registry = NodeSchemaRegistry()
        logger.info("WorkflowNodeProcessor inizializzato", details={"init": True})
    
    def node_to_dict(self, node) -> Dict[str, Any]:
        """
        Converte un oggetto ORM WorkflowNode in un dict per i processori.
        
        Args:
            node: Oggetto WorkflowNode ORM
            
        Returns:
            Dict con i dati del nodo
        """
        return {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "name": node.name,
            "description": node.description if hasattr(node, 'description') else "",
            "config": node.config if hasattr(node, 'config') else {},
            "position": node.position if hasattr(node, 'position') else {},
            "width": node.width if hasattr(node, 'width') else 200,
            "height": node.height if hasattr(node, 'height') else 80
        }
    
    async def execute_node(self, node, context: ExecutionContext):
        """
        Esegue un singolo nodo con validazione e conversione tipi.
        
        Args:
            node: Il nodo da eseguire (oggetto ORM WorkflowNode)
            context: Contesto di esecuzione
        """
        logger.info(
            "Inizio esecuzione nodo",
            details={
                "node_name": node.name,
                "node_id": node.node_id,
                "node_type": node.node_type,
                "workflow_id": context.workflow.id,
                "execution_id": context.execution_id
            },
            context={
                "component": "workflow_node_processor",
                "operation": "execute_node"
            }
        )
        
        try:
            # Ottieni processore per questo tipo di nodo
            processor = self.node_registry.get_processor(node.node_type)
            if not processor:
                raise ValueError(f"Processore non trovato per tipo nodo: {node.node_type}")
            
            # Converti il nodo ORM in dict per il processore
            logger.debug(f"🔍 Conversione nodo ORM in dict: node_id={node.node_id}, config_type={type(node.config)}")
            node_dict = self.node_to_dict(node)
            logger.debug(f"🔍 Nodo dict creato: {node_dict}")
            
            # Wrappa il dict in NodeWrapper per compatibilità con processori
            # che usano sia node.attribute che node['key'] che node.get('key')
            node_wrapped = NodeWrapper(node_dict)
            logger.debug(f"🔍 NodeWrapper creato per '{node.name}'")
            
            # Prepara i dati di input con validazione e conversione tipi
            logger.debug(f"🔍 Preparazione input per '{node.name}'...")
            input_data = await self.prepare_node_input(node, context)
            logger.debug(f"🔍 Input preparato: type={type(input_data)}, data={input_data}")
            
            # Valida i dati di input secondo lo schema del nodo
            logger.debug(f"🔍 Validazione input per '{node.name}'...")
            await self.validate_node_input(node, input_data)
            
            # Esegui il nodo passando il wrapper invece del dict o ORM
            result = await processor.execute(node_wrapped, context)
            
            # Valida l'output secondo lo schema del nodo
            validated_result = await self.validate_node_output(node, result)
            
            # Salva il risultato nel contesto
            context.set_node_result(node.node_id, validated_result)
            
            logger.info(
                "Nodo eseguito con successo",
                details={
                    "node_name": node.name,
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "result_type": type(validated_result).__name__,
                    "workflow_id": context.workflow.id,
                    "execution_id": context.execution_id
                },
                context={
                    "component": "workflow_node_processor",
                    "operation": "execute_node"
                }
            )
            
        except Exception as e:
            error_msg = f"Errore esecuzione nodo '{node.name}': {str(e)}"
            logger.error(
                "Errore durante esecuzione nodo",
                details={
                    "node_name": node.name,
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "error": str(e),
                    "workflow_id": context.workflow.id,
                    "execution_id": context.execution_id
                },
                context={
                    "component": "workflow_node_processor",
                    "operation": "execute_node"
                }
            )
            context.set_node_error(node.node_id, error_msg)
            raise
    
    async def prepare_node_input(self, node, context: ExecutionContext) -> Dict[str, Any]:
        """
        Prepara i dati di input per un nodo con conversione automatica dei tipi.
        
        Args:
            node: Il nodo per cui preparare i dati
            context: Contesto di esecuzione
            
        Returns:
            Dati di input validati e convertiti
        """
        # Ottieni i dati grezzi per il nodo
        raw_input_data = context.get_input_for_node(node.node_id)
        
        # Ottieni lo schema delle porte di input
        node_schema = self.schema_registry.get_schema(node.node_type)
        if not node_schema:
            return raw_input_data
        
        input_ports = node_schema.get("input_ports", [])
        if not input_ports:
            return raw_input_data
        
        converted_data = {}
        
        # Converti ogni input secondo il suo schema
        for input_port in input_ports:
            port_name = input_port.name
            port_schema = input_port.schema
            
            # Cerca il valore nei dati grezzi
            raw_value = None
            
            # Prova varie strategie per trovare il valore
            if port_name in raw_input_data:
                raw_value = raw_input_data[port_name]
            else:
                # Cerca per chiavi simili o patterns comuni
                similar_keys = [
                    key for key in raw_input_data.keys()
                    if port_name.lower() in key.lower() or key.lower() in port_name.lower()
                ]
                if similar_keys:
                    raw_value = raw_input_data[similar_keys[0]]
                elif len(raw_input_data) == 1:
                    # Se c'è un solo valore, usalo
                    raw_value = next(iter(raw_input_data.values()))
            
            # Gestisci campi richiesti
            if raw_value is None:
                if port_schema.required:
                    logger.warning(f"⚠️ Input richiesto '{port_name}' non trovato per nodo '{node.name}'")
                    # Non solleva errore qui, lascia che il processore gestisca
                    continue
                else:
                    converted_data[port_name] = None
                    continue
            
            # Converti il tipo se necessario
            try:
                if self.type_registry.validate_value(raw_value, port_schema):
                    converted_data[port_name] = raw_value
                else:
                    # Prova a convertire
                    converted_value = self.type_registry.convert_value(raw_value, port_schema)
                    converted_data[port_name] = converted_value
                    logger.info(f"🔄 Convertito input '{port_name}': {type(raw_value).__name__} -> {port_schema.data_type.value}")
            
            except Exception as e:
                logger.warning(f"⚠️ Errore conversione input '{port_name}' per nodo '{node.name}': {str(e)}")
                # Usa il valore originale e lascia che il processore gestisca
                converted_data[port_name] = raw_value
        
        # Mantieni anche i dati originali per compatibilità
        for key, value in raw_input_data.items():
            if key not in converted_data:
                converted_data[key] = value
        
        return converted_data
    
    async def validate_node_input(self, node, input_data: Dict[str, Any]):
        """
        Valida i dati di input di un nodo.
        
        Args:
            node: Il nodo da validare
            input_data: Dati di input da validare
        """
        node_schema = self.schema_registry.get_schema(node.node_type)
        if not node_schema:
            return
        
        input_ports = node_schema.get("input_ports", [])
        
        for input_port in input_ports:
            port_name = input_port.name
            port_schema = input_port.schema
            
            if port_name in input_data:
                value = input_data[port_name]
                if not self.type_registry.validate_value(value, port_schema):
                    error_msg = self.type_registry.get_conversion_error(value, port_schema)
                    raise ValueError(f"Input non valido '{port_name}' per nodo '{node.name}': {error_msg}")
    
    async def validate_node_output(self, node, result: Any) -> Any:
        """
        Valida l'output di un nodo e lo converte se necessario.
        
        Args:
            node: Il nodo che ha prodotto l'output
            result: Il risultato da validare
            
        Returns:
            Risultato validato/convertito
        """
        node_schema = self.schema_registry.get_schema(node.node_type)
        if not node_schema:
            return result
        
        output_ports = node_schema.get("output_ports", [])
        
        # Se il nodo ha una sola porta di output, valida direttamente
        if len(output_ports) == 1:
            output_port = output_ports[0]
            port_schema = output_port.schema
            
            try:
                if self.type_registry.validate_value(result, port_schema):
                    return result
                else:
                    # Prova a convertire
                    converted_result = self.type_registry.convert_value(result, port_schema)
                    logger.info(f"🔄 Convertito output nodo '{node.name}': {type(result).__name__} -> {port_schema.data_type.value}")
                    return converted_result
            
            except Exception as e:
                logger.warning(f"⚠️ Errore validazione output nodo '{node.name}': {str(e)}")
                return result
        
        # Se il nodo ha multiple porte, il risultato dovrebbe essere un dict
        elif len(output_ports) > 1:
            if isinstance(result, dict):
                validated_result = {}
                for output_port in output_ports:
                    port_name = output_port.name
                    port_schema = output_port.schema
                    
                    if port_name in result:
                        value = result[port_name]
                        try:
                            if self.type_registry.validate_value(value, port_schema):
                                validated_result[port_name] = value
                            else:
                                converted_value = self.type_registry.convert_value(value, port_schema)
                                validated_result[port_name] = converted_value
                        except Exception as e:
                            logger.warning(f"⚠️ Errore validazione output '{port_name}': {str(e)}")
                            validated_result[port_name] = value
                    else:
                        if port_schema.required:
                            logger.warning(f"⚠️ Output richiesto '{port_name}' mancante da nodo '{node.name}'")
                
                return validated_result
        
        return result

    def find_input_nodes(self, workflow) -> List[Any]:
        """
        Trova automaticamente i nodi di input candidati nel workflow.
        
        Un nodo è considerato di input se:
        1. Non ha connessioni in ingresso
        2. Ha input_ports definiti nel suo schema
        
        Args:
            workflow: Il workflow da analizzare
            
        Returns:
            Lista dei nodi candidati come input con informazioni sui tipi supportati
        """
        input_candidates = []
        
        try:
            logger.info(f"🔍 Analizzando workflow '{workflow.name}' con {len(workflow.nodes)} nodi e {len(workflow.connections)} connessioni")
            
            # Raccogli tutti gli ID dei nodi che ricevono connessioni
            nodes_with_input_connections = set()
            for connection in workflow.connections:
                nodes_with_input_connections.add(connection.to_node_id)
                logger.debug(f"🔗 Connessione: {connection.from_node_id} -> {connection.to_node_id}")
            
            logger.info(f"📊 Nodi con connessioni in ingresso: {nodes_with_input_connections}")
            
            # Esamina ogni nodo per vedere se può essere un input
            for node in workflow.nodes:
                logger.debug(f"🔍 Analizzando nodo: {node.node_id} ({node.node_type})")
                
                # Se il nodo non ha connessioni in ingresso, è un candidato
                if node.node_id not in nodes_with_input_connections:
                    logger.info(f"🎯 Nodo candidato (senza connessioni in ingresso): {node.node_id}")
                    
                    try:
                        # Verifica se il nodo ha input_ports definiti nel suo schema
                        node_schema = self.schema_registry.get_schema(node.node_type)
                        logger.debug(f"📋 Schema per {node.node_type}: {node_schema is not None}")
                        
                        input_ports = node_schema.get("input_ports", []) if node_schema else []
                        logger.info(f"🔌 Input ports per {node.node_id}: {input_ports}")
                        
                        if input_ports:
                            # Raccogli i tipi di dati supportati dal nodo
                            compatible_types = []
                            for port in input_ports:
                                port_type = port.get("type", "any")
                                compatible_types.append(port_type)
                            
                            # Aggiungi informazioni aggiuntive per il debugging
                            logger.info(f"✅ Nodo di input candidato: {node.node_id} ({node.node_type}) - Tipi: {compatible_types}")
                            
                            input_candidates.append(node)
                        else:
                            # Nodo senza connessioni in ingresso ma senza input_ports
                            # Potrebbe essere un nodo di trigger o di configurazione
                            logger.info(f"⚠️ Nodo senza input ports ma candidato: {node.node_id} ({node.node_type})")
                            # Include comunque il nodo come candidato
                            input_candidates.append(node)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Errore nell'analisi del nodo {node.node_id}: {str(e)}")
                        # In caso di errore, includiamo comunque il nodo come candidato
                        input_candidates.append(node)
                else:
                    logger.debug(f"🔗 Nodo con connessioni in ingresso (non candidato): {node.node_id}")
                        
        except Exception as e:
            logger.error(f"❌ Errore nell'identificazione dei nodi di input: {str(e)}")
            # Fallback: restituisci tutti i nodi senza connessioni in ingresso
            nodes_with_input_connections = set()
            for connection in workflow.connections:
                nodes_with_input_connections.add(connection.to_node_id)
            
            input_candidates = [
                node for node in workflow.nodes 
                if node.node_id not in nodes_with_input_connections
            ]
            
        logger.info(f"📋 Trovati {len(input_candidates)} nodi di input candidati: {[n.node_id for n in input_candidates]}")
        return input_candidates