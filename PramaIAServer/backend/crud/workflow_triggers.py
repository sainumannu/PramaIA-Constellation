"""
Operazioni CRUD per i trigger dei workflow
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import json
import uuid
import logging

from sqlalchemy import Boolean, Column, DateTime, String, Table, and_, delete, insert, select, update, MetaData, text
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.db.database import engine
from backend.schemas.workflow_triggers import WorkflowTriggerCreate, WorkflowTriggerUpdate, WorkflowTriggerBase, WorkflowTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definizione della tabella usando SQLAlchemy Core
metadata = MetaData()
workflow_triggers = Table(
    "workflow_triggers",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("event_type", String, nullable=False),
    Column("source", String, nullable=False),
    Column("workflow_id", String, nullable=False),
    Column("target_node_id", String, nullable=True),  # Nuovo campo per il nodo di destinazione
    Column("conditions", String, nullable=True),  # JSON as TEXT in SQLite
    Column("active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

def generate_trigger_id() -> str:
    """Genera un ID univoco per il trigger"""
    return str(uuid.uuid4())

def convert_db_row_to_dict(row) -> Optional[Dict[str, Any]]:
    """Converte una riga del database nel formato dict atteso dall'API"""
    if row is None:
        return None
    
    # Converte la riga SQLAlchemy in dict
    row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
    
    # Converte le condizioni da JSON string a dict
    if 'conditions' in row_dict and row_dict['conditions']:
        try:
            # Parse delle conditions da JSON string a dict
            parsed_conditions = json.loads(row_dict['conditions'])
            # Assicurati che sia un dizionario, non una lista
            if isinstance(parsed_conditions, list):
                logger.warning(f"⚠️ Le conditions per trigger {row_dict.get('id', 'unknown')} sono una lista, conversione a dict vuoto")
                row_dict['conditions'] = {}
            elif isinstance(parsed_conditions, dict):
                row_dict['conditions'] = parsed_conditions
            else:
                logger.warning(f"⚠️ Tipo non supportato per conditions: {type(parsed_conditions)}")
                row_dict['conditions'] = {}
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"⚠️ Errore nel parsing delle conditions per trigger {row_dict.get('id', 'unknown')}: {str(e)}")
            row_dict['conditions'] = {}
    else:
        row_dict['conditions'] = {}
    
    # Mappa is_active -> active per compatibilità con il frontend
    if 'is_active' in row_dict:
        row_dict['active'] = row_dict['is_active']
    
    return row_dict

def get_all_triggers(db: Session) -> List[Dict[str, Any]]:
    """Restituisce tutti i trigger"""
    try:
        # Log dell'operazione di accesso al DB
        from backend.db.database import engine
        db_path = engine.url.database if hasattr(engine.url, 'database') else str(engine.url)
        logger.info(f"📊 Accesso al DB per trigger: {db_path}")
        
        # Registra il percorso al file DB sqlite
        logger.info(f"📊 Percorso completo DB: {engine.url}")
        
        query = select(workflow_triggers)
        logger.info(f"🔍 Query per trigger: {str(query)}")
        
        result = db.execute(query)
        triggers = []
        for row in result:
            # Usa la funzione comune per convertire la riga
            row_dict = convert_db_row_to_dict(row)
            if row_dict:
                # Log dettagliato delle conditions
                logger.info(f"🔎 Trigger {row_dict.get('id')}: conditions={row_dict.get('conditions')} (tipo: {type(row_dict.get('conditions')).__name__})")
                triggers.append(row_dict)
        
        logger.info(f"✅ Trovati {len(triggers)} trigger nel database")
        # Log dettagliato dei trigger trovati
        for i, trigger in enumerate(triggers):
            logger.info(f"✅ Trigger {i+1}: ID={trigger.get('id')}, Nome={trigger.get('name')}, Tipo={trigger.get('event_type')}, Workflow={trigger.get('workflow_id')}")
        
        return triggers
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero dei trigger dal database: {str(e)}")
        # Stampa lo stack trace per debug
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        raise

def get_trigger_by_id(db: Session, trigger_id: str) -> Optional[Dict[str, Any]]:
    """Restituisce un trigger dato il suo ID"""
    try:
        logger.info(f"🔍 Cerco trigger con ID: {trigger_id}")
        query = select(workflow_triggers).where(workflow_triggers.c.id == trigger_id)
        result = db.execute(query).first()
        
        if result:
            # Usa la funzione comune per convertire la riga
            row_dict = convert_db_row_to_dict(result)
            if row_dict:
                logger.info(f"✅ Trovato trigger: {row_dict.get('name')} (ID: {row_dict.get('id')})")
                return row_dict
            else:
                logger.warning(f"⚠️ Conversione trigger fallita per ID: {trigger_id}")
        
        logger.info(f"❌ Nessun trigger trovato con ID: {trigger_id}")
        return None
    except Exception as e:
        logger.error(f"❌ Errore nel recupero del trigger {trigger_id}: {str(e)}")
        return None

def get_active_triggers(db: Session, event_type: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """Restituisce i trigger attivi, filtrati per tipo di evento e sorgente se specificati"""
    try:
        logger.info(f"🔍 Recupero trigger attivi. Filtri: event_type={event_type}, source={source}")
        
        conditions = [workflow_triggers.c.active == True]
        
        if event_type:
            conditions.append(workflow_triggers.c.event_type == event_type)
        
        if source:
            conditions.append(workflow_triggers.c.source == source)
        
        query = select(workflow_triggers).where(and_(*conditions))
        logger.info(f"🔍 Query: {str(query)}")
        
        result = db.execute(query)
        triggers = []
        for row in result:
            # Usa la funzione comune per convertire la riga
            row_dict = convert_db_row_to_dict(row)
            if row_dict:
                triggers.append(row_dict)
        
        logger.info(f"✅ Trovati {len(triggers)} trigger attivi")
        return triggers
    except Exception as e:
        logger.error(f"❌ Errore nel recupero dei trigger attivi: {str(e)}")
        return []

def create_trigger(db: Session, trigger: WorkflowTriggerCreate) -> Dict[str, Any]:
    """Crea un nuovo trigger"""
    trigger_id = generate_trigger_id()
    
    # Converte le condizioni in JSON stringa per SQLite
    conditions_json = json.dumps(trigger.conditions) if trigger.conditions else '{}'
    
    # Gestisci i campi che potrebbero non esistere nel modello
    source = getattr(trigger, 'source', 'unknown')
    active = getattr(trigger, 'active', getattr(trigger, 'is_active', True))
    target_node_id = getattr(trigger, 'target_node_id', None)
    
    now = datetime.utcnow()
    query = insert(workflow_triggers).values(
        id=trigger_id,
        name=trigger.name,
        event_type=trigger.event_type,
        source=source,
        workflow_id=trigger.workflow_id,
        target_node_id=target_node_id,
        conditions=conditions_json,
        active=active,
        created_at=now,
        updated_at=now
    )
    
    db.execute(query)
    db.commit()
    
    # Recupera il trigger creato
    result = get_trigger_by_id(db, trigger_id)
    if not result:
        raise HTTPException(status_code=500, detail="Errore nella creazione del trigger")
    return result

def update_trigger(db: Session, trigger_id: str, trigger_update: WorkflowTriggerUpdate) -> Optional[Dict[str, Any]]:
    """Aggiorna un trigger esistente"""
    # Verifica che il trigger esista
    existing_trigger = get_trigger_by_id(db, trigger_id)
    if not existing_trigger:
        return None
    
    # Prepara i valori da aggiornare
    update_values = {}
    if trigger_update.name is not None:
        update_values["name"] = trigger_update.name
    if trigger_update.event_type is not None:
        update_values["event_type"] = trigger_update.event_type
    if hasattr(trigger_update, 'source') and trigger_update.source is not None:
        update_values["source"] = trigger_update.source
    if trigger_update.workflow_id is not None:
        update_values["workflow_id"] = trigger_update.workflow_id
    if hasattr(trigger_update, 'target_node_id') and trigger_update.target_node_id is not None:
        update_values["target_node_id"] = trigger_update.target_node_id
    if trigger_update.conditions is not None:
        update_values["conditions"] = json.dumps(trigger_update.conditions)
    
    # Gestisci active/is_active
    active_value = getattr(trigger_update, 'active', getattr(trigger_update, 'is_active', None))
    if active_value is not None:
        update_values["active"] = active_value
    
    update_values["updated_at"] = datetime.utcnow()
    
    query = update(workflow_triggers).where(workflow_triggers.c.id == trigger_id).values(**update_values)
    db.execute(query)
    db.commit()
    
    return get_trigger_by_id(db, trigger_id)

def delete_trigger(db: Session, trigger_id: str) -> bool:
    """Elimina un trigger dato il suo ID"""
    # Verifica che il trigger esista
    existing_trigger = get_trigger_by_id(db, trigger_id)
    if not existing_trigger:
        return False
    
    query = delete(workflow_triggers).where(workflow_triggers.c.id == trigger_id)
    db.execute(query)
    db.commit()
    
    return True

def check_table_structure(db: Session) -> None:
    """Funzione diagnostica per verificare la struttura della tabella workflow_triggers"""
    try:
        # Questo funziona per SQLite
        result = db.execute(text("PRAGMA table_info(workflow_triggers)"))
        columns = result.fetchall()
        
        logger.info("📊 Struttura tabella workflow_triggers:")
        for col in columns:
            logger.info(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {' DEFAULT=' + str(col[4]) if col[4] is not None else ''}")
        
        # Verifica la presenza di record
        count_result = db.execute(text("SELECT COUNT(*) FROM workflow_triggers"))
        count = count_result.scalar()
        logger.info(f"📊 Numero di trigger nel database: {count or 0}")
        
        # Se ci sono record, verifichiamo il primo
        if count and count > 0:
            first_row = db.execute(text("SELECT * FROM workflow_triggers LIMIT 1")).first()
            if first_row:
                logger.info(f"📊 Esempio di record:")
                row_dict = dict(first_row._mapping) if hasattr(first_row, '_mapping') else dict(first_row)
                for key, value in row_dict.items():
                    if key == 'conditions':
                        logger.info(f"   - {key}: {value} (tipo: {type(value).__name__})")
                        if value:
                            try:
                                parsed = json.loads(value) if isinstance(value, str) else value
                                logger.info(f"     - Parsed: {parsed} (tipo: {type(parsed).__name__})")
                            except Exception as e:
                                logger.warning(f"     - Errore parsing: {str(e)}")
                        else:
                            logger.info("     - Valore vuoto")
                    else:
                        logger.info(f"   - {key}: {value} (tipo: {type(value).__name__})")
    except Exception as e:
        logger.error(f"❌ Errore nell'analisi della struttura della tabella: {str(e)}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")


def evaluate_trigger_conditions(event_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
    """
    Valuta se un evento soddisfa le condizioni di un trigger
    
    Supporta operatori di confronto basilari su attributi dell'evento:
    - Uguaglianza (==)
    - Maggiore (>)
    - Minore (<)
    - Maggiore o uguale (>=)
    - Minore o uguale (<=)
    
    Esempio di conditions:
    {
        "file_extension": "pdf",
        "file_size_kb": {"$gt": 100},
        "metadata.type": "document"
    }
    """
    if not conditions:
        return True  # Nessuna condizione, trigger sempre valido
    
    # Appiattisci l'evento per accedere facilmente ai campi nidificati
    flat_event = {}
    
    def flatten_dict(d, parent_key=''):
        for k, v in d.items():
            key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict) and not any(op.startswith('$') for op in v.keys()):
                flatten_dict(v, key)
            else:
                flat_event[key] = v
    
    # Appiattisci l'evento principale
    flatten_dict(event_data)
    
    # Valuta ogni condizione
    for field, condition in conditions.items():
        # Se il campo non esiste nell'evento, la condizione fallisce
        if field not in flat_event and '.' not in field:
            return False
        
        event_value = flat_event.get(field)
        
        # Gestione dei diversi tipi di condizioni
        if isinstance(condition, dict) and any(op.startswith('$') for op in condition.keys()):
            # Condizione con operatori
            for op, value in condition.items():
                if op == "$gt":
                    if not event_value > value:
                        return False
                elif op == "$gte":
                    if not event_value >= value:
                        return False
                elif op == "$lt":
                    if not event_value < value:
                        return False
                elif op == "$lte":
                    if not event_value <= value:
                        return False
                elif op == "$ne":
                    if event_value == value:
                        return False
                elif op == "$in":
                    if not event_value in value:
                        return False
                elif op == "$nin":
                    if event_value in value:
                        return False
        else:
            # Condizione di uguaglianza semplice
            if event_value != condition:
                return False
    
    return True  # Tutte le condizioni sono soddisfatte
