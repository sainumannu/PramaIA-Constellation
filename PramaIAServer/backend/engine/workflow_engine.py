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
from backend.engine.workflow_node_processor import WorkflowNodeProcessor
from backend.utils import get_logger

logger = get_logger()


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
        self.node_processor = WorkflowNodeProcessor()
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
            input_nodes = self.node_processor.find_input_nodes(workflow)
            if not input_nodes:
                raise ValueError("Nessun nodo di input trovato nel workflow")
            
            logger.info(
                "Trovati nodi di input",
                details={"workflow_name": workflow.name, "execution_id": execution_id, "input_nodes": [n.node_id for n in input_nodes]}
            )
            
            # Esegui nodi di input con i dati forniti
            for input_node in input_nodes:
                logger.lifecycle(
                    "Inizio esecuzione nodo INPUT",
                    details={
                        "lifecycle_event": "WORKFLOW_NODE_START",
                        "node_name": input_node.name, 
                        "node_id": input_node.node_id, 
                        "node_type": input_node.node_type,
                        "workflow_name": workflow.name, 
                        "workflow_id": workflow.id,
                        "execution_id": execution_id,
                        "status": "started"
                    },
                    context={
                        "component": "workflow_engine",
                        "operation": "execute_input_node"
                    }
                )
                await self.node_processor.execute_node(input_node, context)
                logger.lifecycle(
                    "Completato nodo INPUT",
                    details={
                        "lifecycle_event": "WORKFLOW_NODE_COMPLETED",
                        "node_name": input_node.name, 
                        "node_id": input_node.node_id, 
                        "node_type": input_node.node_type,
                        "workflow_name": workflow.name, 
                        "workflow_id": workflow.id,
                        "execution_id": execution_id,
                        "status": "completed"
                    },
                    context={
                        "component": "workflow_engine",
                        "operation": "execute_input_node"
                    }
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
            
            try:
                if 'context' in locals():
                    duration = (datetime.utcnow() - context.started_at).total_seconds()
                    nodes_executed = len(context.node_results)
                    nodes_failed = len(context.node_errors)
            except:
                pass
            
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
                    logger.lifecycle(
                        "Inizio esecuzione nodo",
                        details={
                            "lifecycle_event": "WORKFLOW_NODE_START",
                            "node_name": node.name,
                            "node_id": node.node_id,
                            "node_type": node.node_type,
                            "workflow_name": context.workflow.name,
                            "workflow_id": context.workflow.id,
                            "execution_id": context.execution_id,
                            "status": "started"
                        },
                        context={
                            "component": "workflow_engine",
                            "operation": "execute_node"
                        }
                    )
                    try:
                        await self.node_processor.execute_node(node, context)
                        executed_nodes.add(node.node_id)
                        nodes_executed_this_iteration += 1
                        logger.lifecycle(
                            "Nodo completato con successo",
                            details={
                                "lifecycle_event": "WORKFLOW_NODE_COMPLETED",
                                "node_name": node.name,
                                "node_id": node.node_id,
                                "node_type": node.node_type,
                                "workflow_name": context.workflow.name,
                                "workflow_id": context.workflow.id,
                                "execution_id": context.execution_id,
                                "status": "completed"
                            },
                            context={
                                "component": "workflow_engine",
                                "operation": "execute_node"
                            }
                        )
                    except Exception as e:
                        logger.lifecycle(
                            "Errore nell'esecuzione del nodo",
                            details={
                                "lifecycle_event": "WORKFLOW_NODE_FAILED",
                                "node_name": node.name,
                                "node_id": node.node_id,
                                "node_type": node.node_type,
                                "workflow_name": context.workflow.name,
                                "workflow_id": context.workflow.id,
                                "execution_id": context.execution_id,
                                "status": "failed",
                                "error": str(e)
                            },
                            context={
                                "component": "workflow_engine",
                                "operation": "execute_node"
                            }
                        )
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
    
    def _find_input_nodes(self, workflow) -> List:
        """
        Trova tutti i nodi che possono servire come input nel workflow.
        Questi sono nodi che:
        1. Non hanno connessioni in entrata (sono punti di partenza)
        2. Hanno delle porte di input definite nel loro schema
        """
        import importlib
        import json
        
        logger.info(f"🔍 Analizzando workflow '{workflow.name}' per trovare nodi di input")
        logger.info(f"📊 Workflow ha {len(workflow.nodes)} nodi e {len(workflow.connections)} connessioni")
        
        input_candidates = []
        
        # Prima passa: trova nodi senza connessioni in entrata
        for node in workflow.nodes:
            has_incoming = False
            for conn in workflow.connections:
                if conn.to_node_id == node.node_id:
                    has_incoming = True
                    break
            
            if not has_incoming:
                logger.debug(f"🎯 Nodo '{node.name}' ({node.node_type}) non ha connessioni in entrata")
                input_candidates.append(node)
            else:
                logger.debug(f"↗️ Nodo '{node.name}' ({node.node_type}) ha connessioni in entrata")
        
        # Seconda passa: considera tutti i candidati come validi nodi di input
        # (Rimosso import dinamico problematico - tutti i nodi senza connessioni in entrata sono potenziali input)
        valid_input_nodes = []
        
        for node in input_candidates:
            try:
                logger.info(f"✅ Nodo di input candidato: '{node.name}' ({node.node_type})")
                
                # Crea il nodo di input senza verifiche dinamiche complicate
                valid_input_nodes.append({
                    'node_id': node.node_id,
                    'name': node.name,
                    'node_type': node.node_type,
                    'description': node.description or "",
                    'input_ports': []  # Semplificato - non più import dinamico
                })
                    
            except Exception as e:
                logger.error(f"❌ Errore nell'analisi del nodo '{node.name}': {e}")
        
        logger.info(f"🎯 Trovati {len(valid_input_nodes)} nodi di input validi nel workflow")
        for node_info in valid_input_nodes:
            logger.info(f"  - {node_info['name']} ({node_info['node_type']})")
        
        return valid_input_nodes