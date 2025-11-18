"""
Servizio per la gestione dei trigger e l'esecuzione dei workflow
"""

import re
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# Usa il CRUD workflow_triggers invece dei modelli EventTrigger/EventLog
from backend.crud import workflow_triggers as crud
from backend.crud.workflow_crud import WorkflowCRUD
from backend.engine.workflow_engine import WorkflowEngine
from backend.schemas.workflow_schemas import ExecutionStatus
from backend.utils import get_logger

logger = get_logger(__name__)


class TriggerService:
    """
    Servizio principale per la gestione dei trigger di eventi
    
    Esegue workflow LOCALMENTE usando WorkflowEngine quando viene rilevato un evento.
    I workflow possono poi chiamare nodi PDK via API quando necessario.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow_engine = WorkflowEngine()
        logger.info("🚀 TriggerService inizializzato con WorkflowEngine")
    
    async def process_event(self, event_type: str, data: Dict[str, Any], 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa un evento e attiva i trigger corrispondenti
        """
        try:
            # Log dell'evento ricevuto
            logger.info(f"Processing event: {event_type}")
            
            # Trova i trigger corrispondenti
            matching_triggers = await self._find_matching_triggers(event_type, data, metadata)
            
            # Esegui i workflow per ogni trigger
            execution_results = []
            for trigger in matching_triggers:
                result = await self._execute_workflow(trigger, data, metadata)
                execution_results.append(result)
            
            # Salva il log dell'evento
            workflows_executed = len([r for r in execution_results if r.get("success", False)])
            await self._log_event(event_type, data, metadata, len(matching_triggers), 
                                workflows_executed, True, None)
            
            return {
                "success": True,
                "triggers_matched": len(matching_triggers),
                "workflows_executed": workflows_executed,
                "results": execution_results
            }
            
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {str(e)}")
            
            # Salva il log dell'errore
            await self._log_event(event_type, data, metadata, 0, 0, False, str(e))
            
            return {
                "success": False,
                "error": str(e),
                "triggers_matched": 0,
                "workflows_executed": 0
            }
    
    async def _find_matching_triggers(self, event_type: str, data: Dict[str, Any], 
                                    metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Trova i trigger che corrispondono all'evento
        """
        source = metadata.get("source") if metadata else None
        
        # Ottieni tutti i trigger attivi
        all_triggers = crud.get_all_triggers(self.db)
        
        # Filtra per event_type e source
        matching_triggers = []
        for trigger in all_triggers:
            # Controlla se il trigger è attivo
            if not trigger.get("active", True):
                continue
            
            # Controlla event_type
            if trigger.get("event_type") != event_type:
                continue
            
            # Controlla source (None significa qualsiasi source)
            trigger_source = trigger.get("source")
            if trigger_source and source and trigger_source != source:
                continue
            
            # Valuta le condizioni
            if self._evaluate_trigger_conditions(trigger, data, metadata):
                matching_triggers.append(trigger)
        
        return matching_triggers
    
    def _evaluate_trigger_conditions(self, trigger: Dict[str, Any], data: Dict[str, Any], 
                                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Valuta se un trigger soddisfa le condizioni per l'evento
        """
        conditions = trigger.get("conditions", {})
        if not conditions:
            return True
        
        # Verifica pattern del filename
        if "filename_pattern" in conditions and "filename" in data:
            pattern = str(conditions["filename_pattern"])
            filename = str(data["filename"])
            if not re.search(pattern, filename):
                return False
        
        # Verifica contenuto dei metadata
        if "metadata_contains" in conditions and metadata:
            metadata_conditions = conditions["metadata_contains"]
            for key, value in metadata_conditions.items():
                if key not in metadata or metadata[key] != value:
                    return False
        
        # Verifica dimensione file
        if "min_size" in conditions and "size" in data:
            if data["size"] < conditions["min_size"]:
                return False
        
        if "max_size" in conditions and "size" in data:
            if data["size"] > conditions["max_size"]:
                return False
        
        return True
    
    async def _execute_workflow(self, trigger: Dict[str, Any], data: Dict[str, Any], 
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Esegue un workflow LOCALMENTE usando WorkflowEngine
        
        Il workflow viene eseguito nel server, non nel PDK.
        I nodi del workflow possono chiamare il PDK quando necessario.
        """
        trigger_id = trigger.get("id", "unknown")
        trigger_name = trigger.get("name", "unknown")
        workflow_id = trigger.get("workflow_id", "unknown")
        target_node_id = trigger.get("target_node_id")
        
        logger.info(f"🚀 Eseguendo workflow {workflow_id} per trigger '{trigger_name}'")
        if target_node_id:
            logger.info(f"   ⚠️ Target node specificato: {target_node_id} (funzionalità parzialmente implementata)")
        
        try:
            # 1. Recupera il workflow dal database
            workflow = WorkflowCRUD.get_workflow(self.db, workflow_id)
            
            if not workflow:
                error_msg = f"Workflow {workflow_id} non trovato nel database"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "trigger_id": trigger_id,
                    "trigger_name": trigger_name,
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "error": error_msg
                }
            
            logger.info(f"✅ Workflow trovato: {workflow.name} (nodi: {len(workflow.nodes)}, connessioni: {len(workflow.connections)})")
            
            # 2. Prepara i dati di input per il workflow
            input_data = self._prepare_workflow_input(data, metadata, trigger)
            
            logger.info(f"📥 Input data preparati: {list(input_data.keys())}")
            logger.debug(f"   Dettagli: {input_data}")
            
            # 3. Crea record di esecuzione nel database
            # Usa "system" come user_id per esecuzioni trigger-based
            execution_record = WorkflowCRUD.create_execution(
                db=self.db,
                workflow_id=workflow_id,
                user_id="system",
                input_data=input_data
            )
            
            logger.info(f"📝 Creato record esecuzione: {execution_record.execution_id}")
            
            # 4. Esegui il workflow usando WorkflowEngine
            logger.info(f"⚙️ Avvio esecuzione workflow con WorkflowEngine...")
            
            result = await self.workflow_engine.execute_workflow(
                workflow=workflow,
                input_data=input_data,
                execution_id=execution_record.execution_id,
                db_session=self.db
            )
            
            logger.info(f"✅ Workflow completato con successo")
            logger.debug(f"   Risultati: {result}")
            
            return {
                "success": True,
                "trigger_id": trigger_id,
                "trigger_name": trigger_name,
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "execution_id": execution_record.execution_id,
                "status": "executed",
                "details": {
                    "result": result,
                    "message": "Workflow executed successfully via WorkflowEngine"
                }
            }
                
        except Exception as e:
            error_msg = f"Errore esecuzione workflow: {str(e)}"
            logger.error(f"❌ {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Aggiorna lo stato del workflow a FAILED se esiste un record di esecuzione
            try:
                if 'execution_record' in locals() and execution_record:
                    WorkflowCRUD.update_execution_status(
                        db=self.db,
                        execution_id=execution_record.execution_id,
                        status=ExecutionStatus.FAILED,
                        error_message=error_msg
                    )
            except Exception as update_error:
                logger.error(f"❌ Errore aggiornamento status esecuzione: {str(update_error)}")
            
            return {
                "success": False,
                "trigger_id": trigger_id,
                "trigger_name": trigger_name,
                "workflow_id": workflow_id,
                "status": "error",
                "error": error_msg
            }
    
    def _prepare_workflow_input(
        self, 
        event_data: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]],
        trigger: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepara i dati di input per il workflow mappando i dati dell'evento
        
        Strategia di mappatura:
        1. Includi tutti i dati dell'evento come top-level keys
        2. Aggiungi metadata come oggetto separato  
        3. Aggiungi informazioni sul trigger
        4. Aggiungi contesto temporale
        """
        logger.info("🔄 Preparando input data per workflow")
        
        # Struttura base
        input_data = {
            # Dati evento top-level (per facile accesso dai nodi)
            **event_data,
            
            # Metadata separato per informazioni sistema
            "metadata": metadata or {},
            
            # Informazioni trigger
            "trigger": {
                "id": trigger.get("id"),
                "name": trigger.get("name"),
                "event_type": trigger.get("event_type"),
                "source": trigger.get("source")
            },
            
            # Contesto temporale
            "execution_context": {
                "triggered_at": datetime.utcnow().isoformat(),
                "trigger_mode": "event_driven"
            }
        }
        
        # Log della mappatura per debug
        logger.info(f"📋 Mappatura completata:")
        logger.info(f"   - Campi evento: {list(event_data.keys())}")
        logger.info(f"   - Metadata keys: {list((metadata or {}).keys())}")
        logger.info(f"   - Trigger: {trigger.get('name')}")
        
        return input_data
    
    async def _log_event(self, event_type: str, data: Dict[str, Any], 
                        metadata: Optional[Dict[str, Any]], triggers_matched: int,
                        workflows_executed: int, success: bool, error_message: Optional[str]):
        """
        Salva il log dell'evento processato
        
        NOTA: La tabella event_logs non esiste ancora. Per ora logghiamo solo su file.
        TODO: Implementare event logging nel database quando la tabella sarà creata.
        """
        try:
            source = metadata.get("source") if metadata else None
            log_entry = {
                "event_type": event_type,
                "source": source,
                "triggers_matched": triggers_matched,
                "workflows_executed": workflows_executed,
                "success": success,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Event processed: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")


# Funzioni di utilità per la compatibilità con l'API esistente
async def get_active_triggers(db: Session, event_type: Optional[str] = None,
                             source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Recupera i trigger attivi filtrati per tipo ed eventualmente sorgente
    """
    all_triggers = crud.get_all_triggers(db)
    
    # Filtra per attivi
    active_triggers = [t for t in all_triggers if t.get("active", True)]
    
    # Filtra per event_type se specificato
    if event_type:
        active_triggers = [t for t in active_triggers if t.get("event_type") == event_type]
    
    # Filtra per source se specificato
    if source:
        active_triggers = [
            t for t in active_triggers 
            if not t.get("source") or t.get("source") == source
        ]
    
    return active_triggers


async def create_trigger(db: Session, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un nuovo trigger usando il CRUD workflow_triggers
    """
    from backend.schemas.workflow_triggers import WorkflowTriggerCreate
    
    # Converte il dict in WorkflowTriggerCreate schema
    trigger_create = WorkflowTriggerCreate(**trigger_data)
    
    # Usa il CRUD per creare il trigger
    return crud.create_trigger(db, trigger_create)
