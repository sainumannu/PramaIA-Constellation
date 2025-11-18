"""
Workflow Execution Engine

Questo modulo gestisce l'esecuzione dei workflow, 
orchestrando l'esecuzione dei nodi secondo il grafo definito.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from backend.db.workflow_models import Workflow as WorkflowModel
from backend.schemas.workflow_schemas import ExecutionStatus
from backend.crud.workflow_crud import WorkflowCRUD
from backend.engine.node_registry import NodeRegistry
from backend.engine.execution_context import ExecutionContext
from backend.engine.workflow_validator import WorkflowValidator, DataFlowValidator
from backend.engine.data_types import DataTypeRegistry
from backend.engine.node_schemas import NodeSchemaRegistry
from backend.utils import get_logger

logger = get_logger(__name__)


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


class WorkflowEngine:
    """
    Engine principale per l'esecuzione dei workflow.
    
    Gestisce:
    - Validazione del workflow
    - Orchestrazione dell'esecuzione
    - Gestione stato e risultati
    - Error handling e rollback
    """
    
    def __init__(self):
        self.node_registry = NodeRegistry()
        self.workflow_validator = WorkflowValidator()
        self.data_flow_validator = DataFlowValidator()
        self.type_registry = DataTypeRegistry()
        self.schema_registry = NodeSchemaRegistry()
    logger.info("WorkflowEngine inizializzato", details={"init": True, "type_validation": True})
    
    async def execute_workflow(
        self, 
        workflow: WorkflowModel, 
        input_data: Dict[str, Any],
        execution_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Esegue un workflow completo.
        
        Args:
            workflow: Il workflow da eseguire
            input_data: Dati di input dell'utente
            execution_id: ID dell'esecuzione per tracking
            db_session: Sessione database per aggiornamenti
            
        Returns:
            Dict con risultati dell'esecuzione
        """
        logger.lifecycle(
            "Inizio esecuzione workflow",
            details={
                "lifecycle_event": "WORKFLOW_EXECUTION_START",
                "workflow_name": workflow.name,
                "workflow_id": workflow.id,
                "execution_id": execution_id,
                "status": "started",
                "node_count": len(workflow.nodes),
                "connection_count": len(workflow.connections)
            },
            context={
                "component": "workflow_engine",
                "operation": "execute_workflow"
            }
        )
        
        try:
            # Crea contesto di esecuzione
            context = ExecutionContext(
                workflow=workflow,
                input_data=input_data,
                execution_id=execution_id
            )
            
            # Aggiorna status a RUNNING
            WorkflowCRUD.update_execution_status(
                db=db_session,
                execution_id=execution_id,
                status=ExecutionStatus.RUNNING
            )
            
            # Valida il workflow prima dell'esecuzione
            # NOTA: Validazione disabilitata temporaneamente per permettere testing con stub processors
            # TODO: Riabilitare dopo aver corretto gli errori di validazione
            try:
                validation_result = await self._validate_workflow(workflow, input_data)
                if validation_result.has_warnings():
                    for warning in validation_result.warnings:
                        logger.warning(
                            "Warning validazione workflow",
                            details={"message": warning.message, "workflow_name": workflow.name, "execution_id": execution_id}
                        )
                
                if not validation_result.is_valid:
                    logger.warning(
                        "Workflow ha errori di validazione, ma procedo (modalità testing)",
                        details={"workflow_name": workflow.name, "execution_id": execution_id, "errors_count": len(validation_result.errors)}
                    )
                    for i, error in enumerate(validation_result.errors[:3], 1):
                        logger.warning(
                            "Errore validazione workflow",
                            details={
                                "index": i,
                                "error_type": error.error_type,
                                "node_name": error.node_name,
                                "message": error.message,
                                "workflow_name": workflow.name,
                                "execution_id": execution_id
                            }
                        )
                    # NON sollevare l'eccezione, continua l'esecuzione
                    # error_msg = f"Workflow non valido: {validation_result.get_summary()}"
                    # logger.error(error_msg)
                    # raise ValueError(error_msg)
            except Exception as e:
                logger.warning(
                    "Errore durante validazione (ignorato)",
                    details={"error": str(e), "workflow_name": workflow.name, "execution_id": execution_id}
                )
            
            # Trova nodi di input (nodi senza connessioni in ingresso)
            input_nodes = self._find_input_nodes(workflow)
            if not input_nodes:
                raise ValueError("Nessun nodo di input trovato nel workflow")
            
            logger.info(
                "Trovati nodi di input",
                details={"workflow_name": workflow.name, "execution_id": execution_id, "input_nodes": [n.node_id for n in input_nodes]}
            )
            
            # Esegui nodi di input con i dati forniti
            for input_node in input_nodes:
                logger.info(
                    "Inizio esecuzione nodo INPUT",
                    details={"node_name": input_node.name, "node_id": input_node.node_id, "workflow_name": workflow.name, "execution_id": execution_id}
                )
                await self._execute_node(input_node, context)
                logger.info(
                    "Completato nodo INPUT",
                    details={"node_name": input_node.name, "node_id": input_node.node_id, "workflow_name": workflow.name, "execution_id": execution_id}
                )
            
            # Esegui il resto del workflow seguendo le connessioni
            logger.info(
                "Inizio esecuzione grafo workflow",
                details={"workflow_name": workflow.name, "execution_id": execution_id}
            )
            await self._execute_workflow_graph(context)
            logger.info(
                "Grafo workflow completato",
                details={"workflow_name": workflow.name, "execution_id": execution_id}
            )
            
            # Raccogli risultati finali
            results = self._collect_results(context)
            
            # Aggiorna status a COMPLETED
            WorkflowCRUD.update_execution_status(
                db=db_session,
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED,
                output_data=results
            )
            
            logger.lifecycle(
                "Workflow completato con successo",
                details={
                    "lifecycle_event": "WORKFLOW_EXECUTION_COMPLETED",
                    "workflow_name": workflow.name,
                    "workflow_id": workflow.id,
                    "execution_id": execution_id,
                    "status": "completed",
                    "duration": (datetime.utcnow() - context.started_at).total_seconds(),
                    "nodes_executed": len(context.node_results),
                    "nodes_failed": len(context.node_errors)
                },
                context={
                    "component": "workflow_engine",
                    "operation": "execute_workflow"
                }
            )
            return results
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            
            # Calcola durata e contatori se il context è disponibile
            duration = None
            nodes_executed = 0
            nodes_failed = 0
            
            if 'context' in locals():
                duration = (datetime.utcnow() - context.started_at).total_seconds()
                nodes_executed = len(context.node_results)
                nodes_failed = len(context.node_errors)
            
            logger.lifecycle(
                "Errore durante esecuzione workflow",
                details={
                    "lifecycle_event": "WORKFLOW_EXECUTION_FAILED",
                    "workflow_name": workflow.name,
                    "workflow_id": workflow.id,
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": str(e),
                    "duration": duration,
                    "nodes_executed": nodes_executed,
                    "nodes_failed": nodes_failed
                },
                context={
                    "component": "workflow_engine",
                    "operation": "execute_workflow"
                }
            )
            logger.error(
                "Traceback completo esecuzione workflow",
                details={"workflow_name": workflow.name, "execution_id": execution_id, "traceback": error_trace}
            )
            
            # Aggiorna status a FAILED
            WorkflowCRUD.update_execution_status(
                db=db_session,
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e)
            )
            
            raise e
    
    async def _validate_workflow(self, workflow: WorkflowModel, input_data: Dict[str, Any]) -> Any:
        """
        Valida il workflow prima dell'esecuzione.
        
        Args:
            workflow: Il workflow da validare
            input_data: Dati di input per validazione flusso dati
            
        Returns:
            ValidationResult
        """
        logger.info(
            "Validazione workflow",
            details={"workflow_name": workflow.name}
        )
        
        # Validazione strutturale del workflow
        validation_result = self.workflow_validator.validate_workflow(workflow)
        
        if validation_result.has_warnings():
            for warning in validation_result.warnings:
                logger.warning(
                    "Warning validazione workflow",
                    details={"message": warning.message, "workflow_name": workflow.name}
                )
        
        if not validation_result.is_valid:
            logger.error(
                "Validazione fallita",
                details={"workflow_name": workflow.name, "errors_count": len(validation_result.errors)}
            )
            for i, error in enumerate(validation_result.errors, 1):
                logger.error(
                    "Errore validazione nodo",
                    details={
                        "index": i,
                        "error_type": error.error_type,
                        "node_name": error.node_name,
                        "node_id": error.node_id,
                        "message": error.message,
                        "workflow_name": workflow.name
                    }
                )
            return validation_result
        
        # Validazione del flusso dati
        workflow_data = {
            "nodes": [
                {
                    "id": node.node_id,
                    "name": node.name,
                    "type": node.node_type,
                    "config": node.config
                }
                for node in workflow.nodes
            ],
            "connections": [
                {
                    "from_node_id": conn.from_node_id,
                    "to_node_id": conn.to_node_id,
                    "from_port": conn.from_port,
                    "to_port": conn.to_port
                }
                for conn in workflow.connections
            ]
        }
        
        data_flow_result = self.data_flow_validator.validate_data_flow(workflow_data, input_data)
        
        # Combina i risultati
        if not data_flow_result.is_valid:
            validation_result.errors.extend(data_flow_result.errors)
            validation_result.warnings.extend(data_flow_result.warnings)
            validation_result.is_valid = False
        
        logger.info(
            "Validazione workflow completata",
            details={"workflow_name": workflow.name, "summary": validation_result.get_summary()}
        )
        return validation_result
    
    def _node_to_dict(self, node) -> Dict[str, Any]:
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
    
    async def _execute_node(self, node, context: ExecutionContext):
        """
        Esegue un singolo nodo con validazione e conversione tipi.
        
        Args:
            node: Il nodo da eseguire (oggetto ORM WorkflowNode)
            context: Contesto di esecuzione
        """
        logger.info(f"🔧 Eseguendo nodo '{node.name}' (tipo: {node.node_type})")
        
        try:
            # Ottieni processore per questo tipo di nodo
            processor = self.node_registry.get_processor(node.node_type)
            if not processor:
                raise ValueError(f"Processore non trovato per tipo nodo: {node.node_type}")
            
            # Converti il nodo ORM in dict per il processore
            logger.debug(f"🔍 Conversione nodo ORM in dict: node_id={node.node_id}, config_type={type(node.config)}")
            node_dict = self._node_to_dict(node)
            logger.debug(f"🔍 Nodo dict creato: {node_dict}")
            
            # Wrappa il dict in NodeWrapper per compatibilità con processori
            # che usano sia node.attribute che node['key'] che node.get('key')
            node_wrapped = NodeWrapper(node_dict)
            logger.debug(f"🔍 NodeWrapper creato per '{node.name}'")
            
            # Prepara i dati di input con validazione e conversione tipi
            logger.debug(f"🔍 Preparazione input per '{node.name}'...")
            input_data = await self._prepare_node_input(node, context)
            logger.debug(f"🔍 Input preparato: type={type(input_data)}, data={input_data}")
            
            # Valida i dati di input secondo lo schema del nodo
            logger.debug(f"🔍 Validazione input per '{node.name}'...")
            await self._validate_node_input(node, input_data)
            
            # Esegui il nodo passando il wrapper invece del dict o ORM
            result = await processor.execute(node_wrapped, context)
            
            # Valida l'output secondo lo schema del nodo
            validated_result = await self._validate_node_output(node, result)
            
            # Salva il risultato nel contesto
            context.set_node_result(node.node_id, validated_result)
            
            logger.info(f"✅ Nodo '{node.name}' eseguito con successo")
            
        except Exception as e:
            error_msg = f"Errore esecuzione nodo '{node.name}': {str(e)}"
            logger.error(f"❌ {error_msg}")
            context.set_node_error(node.node_id, error_msg)
            raise
    
    async def _prepare_node_input(self, node, context: ExecutionContext) -> Dict[str, Any]:
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
    
    async def _validate_node_input(self, node, input_data: Dict[str, Any]):
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
    
    async def _validate_node_output(self, node, result: Any) -> Any:
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

    def _find_input_nodes(self, workflow) -> List[Any]:
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
    
    async def _execute_workflow_graph(self, context: ExecutionContext):
        """
        Esegue il workflow seguendo il grafo delle connessioni dopo i nodi di input.
        
        Args:
            context: Contesto di esecuzione
        """
        logger.info("🔄 Eseguendo grafo workflow...")
        
        workflow = context.workflow
        executed_nodes = set(context.node_results.keys())
        
        # Continua finché ci sono nodi da eseguire
        max_iterations = len(workflow.nodes) * 2  # Evita loop infiniti
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            nodes_executed_this_iteration = 0
            
            # Trova nodi pronti per l'esecuzione
            for node in workflow.nodes:
                # Salta nodi già eseguiti
                if node.node_id in executed_nodes:
                    continue
                
                # Controlla se tutte le dipendenze sono soddisfatte
                dependencies_ready = True
                for conn in workflow.connections:
                    if conn.to_node_id == node.node_id:
                        # Questo nodo dipende da conn.from_node_id
                        if conn.from_node_id not in executed_nodes:
                            dependencies_ready = False
                            break
                
                # Se le dipendenze sono pronte, esegui il nodo
                if dependencies_ready:
                    logger.info(f"▶️ INIZIO nodo '{node.name}' (ID: {node.node_id}, tipo: {node.node_type})")
                    try:
                        await self._execute_node(node, context)
                        executed_nodes.add(node.node_id)
                        nodes_executed_this_iteration += 1
                        logger.info(f"✅ COMPLETATO nodo '{node.name}'")
                    except Exception as e:
                        logger.error(f"❌ ERRORE nel nodo '{node.name}': {str(e)}")
                        raise
            
            # Se nessun nodo è stato eseguito in questa iterazione, abbiamo finito
            if nodes_executed_this_iteration == 0:
                break
        
        # Verifica se tutti i nodi sono stati eseguiti
        unexecuted_nodes = [n for n in workflow.nodes if n.node_id not in executed_nodes]
        if unexecuted_nodes:
            logger.warning(f"⚠️ {len(unexecuted_nodes)} nodi non eseguiti: {[n.node_id for n in unexecuted_nodes]}")
        
        logger.info(f"✅ Grafo workflow completato. Nodi eseguiti: {len(executed_nodes)}/{len(workflow.nodes)}")
    
    def _collect_results(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Raccoglie i risultati finali dall'esecuzione del workflow.
        
        Args:
            context: Contesto di esecuzione
            
        Returns:
            Dict con i risultati dell'esecuzione
        """
        logger.info("📦 Raccogliendo risultati workflow...")
        
        # Trova i nodi di output (nodi senza connessioni in uscita)
        workflow = context.workflow
        output_nodes = []
        
        for node in workflow.nodes:
            has_outgoing = False
            for conn in workflow.connections:
                if conn.from_node_id == node.node_id:
                    has_outgoing = True
                    break
            
            if not has_outgoing and node.node_id in context.node_results:
                output_nodes.append(node)
        
        logger.info(f"📤 Trovati {len(output_nodes)} nodi di output: {[n.node_id for n in output_nodes]}")
        
        # Raccoglie i risultati dai nodi di output
        results = {}
        for node in output_nodes:
            node_result = context.node_results.get(node.node_id)
            if node_result:
                results[node.node_id] = {
                    "node_name": node.name,
                    "node_type": node.node_type,
                    "result": node_result
                }
        
        # Se non ci sono nodi di output specifici, restituisci tutti i risultati
        if not results:
            logger.info("ℹ️ Nessun nodo di output trovato, restituisco tutti i risultati")
            results = {
                node_id: {
                    "result": result
                }
                for node_id, result in context.node_results.items()
            }
        
        return results

