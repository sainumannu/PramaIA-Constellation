#!/usr/bin/env python3
"""
Import CRUD Workflows - Importa i workflow JSON nel database

Questo script importa i 4 workflow CRUD PDF dal formato JSON 
nella struttura database di PramaIA per l'esecuzione.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Percorsi
DB_PATH = "backend/db/database.db"
WORKFLOWS_DIR = "PramaIA-PDK/workflows"

# Mapping file -> workflow info
WORKFLOW_FILES = {
    "pdf_document_create_pipeline.json": {
        "name": "PDF Document CREATE Pipeline",
        "description": "Workflow per creazione e indicizzazione documenti PDF",
        "trigger_type": "document_upload"
    },
    "pdf_document_read_pipeline.json": {
        "name": "PDF Document READ Pipeline", 
        "description": "Workflow per ricerca e recupero documenti PDF",
        "trigger_type": "search_query"
    },
    "pdf_document_update_pipeline.json": {
        "name": "PDF Document UPDATE Pipeline",
        "description": "Workflow per aggiornamento metadati documenti PDF",
        "trigger_type": "document_update"
    },
    "pdf_document_delete_pipeline.json": {
        "name": "PDF Document DELETE Pipeline",
        "description": "Workflow per eliminazione sicura documenti PDF",
        "trigger_type": "document_delete"
    }
}

def connect_db():
    """Connessione database."""
    return sqlite3.connect(DB_PATH)

def ensure_tables_exist():
    """Assicura che le tabelle necessarie esistano."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Verifica tabelle esistenti
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    logger.info(f"Tabelle esistenti: {tables}")
    
    # Crea tabelle se necessarie
    if 'workflows' not in tables:
        logger.error("❌ Tabella 'workflows' non trovata!")
        return False
        
    if 'workflow_nodes' not in tables:
        logger.error("❌ Tabella 'workflow_nodes' non trovata!")
        return False
        
    # Verifica se esiste tabella connections
    if 'workflow_connections' not in tables:
        logger.warning("⚠️ Tabella 'workflow_connections' non trovata, la creo...")
        cursor.execute("""
            CREATE TABLE workflow_connections (
                connection_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                source_node_id TEXT NOT NULL,
                target_node_id TEXT NOT NULL,
                source_handle TEXT,
                target_handle TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id),
                FOREIGN KEY (source_node_id) REFERENCES workflow_nodes(node_id),
                FOREIGN KEY (target_node_id) REFERENCES workflow_nodes(node_id)
            )
        """)
        conn.commit()
    
    conn.close()
    return True

def load_workflow_json(filepath: str) -> dict:
    """Carica workflow da file JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Errore caricamento {filepath}: {e}")
        return None

def import_workflow(workflow_data: dict, workflow_info: dict) -> str:
    """Importa un singolo workflow nel database."""
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Genera workflow ID univoco
        workflow_id = f"wf_{str(uuid.uuid4()).replace('-', '')[:12]}"
        
        # Inserisci workflow principale
        cursor.execute("""
            INSERT INTO workflows (
                workflow_id, name, description, created_by,
                created_at, updated_at, is_active, is_public,
                category, priority, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_id,
            workflow_info["name"],
            workflow_info["description"], 
            "system",
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            True,
            False,
            "PDF Processing",
            1,
            json.dumps([workflow_info["trigger_type"], "CRUD", "Real_Processors"])
        ))
        
        # Inserisci nodi
        nodes_inserted = 0
        for node in workflow_data.get("nodes", []):
            node_id = node.get("id", str(uuid.uuid4()))
            
            # Mappa i tipi di nodo dal JSON ai nomi del registry
            node_type = map_node_type(node.get("type", "unknown"))
            
            # Prepara posizione come JSON
            position = json.dumps({
                "x": node.get("position", {}).get("x", 0),
                "y": node.get("position", {}).get("y", 0)
            })
            
            cursor.execute("""
                INSERT INTO workflow_nodes (
                    node_id, workflow_id, node_type, name, description, 
                    config, position, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node_id,
                workflow_id,
                node_type,
                node.get("data", {}).get("name", f"Node {node_id}"),
                node.get("data", {}).get("description", ""),
                json.dumps(node.get("data", {})),
                position,
                datetime.now().isoformat()
            ))
            nodes_inserted += 1
        
        # Inserisci connessioni
        connections_inserted = 0
        for edge in workflow_data.get("edges", []):
            connection_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO workflow_connections (
                    connection_id, workflow_id, source_node_id, target_node_id,
                    source_handle, target_handle, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                connection_id,
                workflow_id,
                edge.get("source"),
                edge.get("target"),
                edge.get("sourceHandle"),
                edge.get("targetHandle"),
                datetime.now().isoformat()
            ))
            connections_inserted += 1
        
        conn.commit()
        
        logger.info(f"✅ Importato workflow '{workflow_info['name']}':")
        logger.info(f"   - ID: {workflow_id}")
        logger.info(f"   - Nodi: {nodes_inserted}")
        logger.info(f"   - Connessioni: {connections_inserted}")
        
        return workflow_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Errore importazione workflow: {e}")
        return None
        
    finally:
        conn.close()

def map_node_type(json_type: str) -> str:
    """Mappa i tipi di nodo JSON ai nomi del registry."""
    mapping = {
        "eventInputNode": "event_input_node",
        "fileParsingNode": "file_parsing", 
        "metadataManagerNode": "metadata_manager",
        "documentProcessorNode": "document_processor",
        "vectorStoreOperationsNode": "vector_store_operations",
        "eventLoggerNode": "event_logger",
        
        # Fallback per tipi non mappati
        "customNode": "event_input_node",
        "startNode": "event_input_node",
        "endNode": "event_logger"
    }
    
    mapped = mapping.get(json_type, json_type)
    if mapped != json_type:
        logger.info(f"   🔄 Mappato {json_type} → {mapped}")
    
    return mapped

def verify_import():
    """Verifica che l'importazione sia andata a buon fine."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Conta workflow
    cursor.execute("SELECT COUNT(*) FROM workflows")
    workflow_count = cursor.fetchone()[0]
    
    # Conta nodi
    cursor.execute("SELECT COUNT(*) FROM workflow_nodes")
    node_count = cursor.fetchone()[0]
    
    # Conta connessioni
    cursor.execute("SELECT COUNT(*) FROM workflow_connections")
    connection_count = cursor.fetchone()[0]
    
    # Lista workflow
    cursor.execute("SELECT workflow_id, name, category FROM workflows")
    workflows = cursor.fetchall()
    
    conn.close()
    
    logger.info("📊 RIEPILOGO IMPORTAZIONE:")
    logger.info(f"   Workflow: {workflow_count}")
    logger.info(f"   Nodi: {node_count}")
    logger.info(f"   Connessioni: {connection_count}")
    logger.info("")
    logger.info("📋 Workflow importati:")
    for wf_id, name, category in workflows:
        logger.info(f"   - {name} ({wf_id}) - {category}")

def main():
    """Funzione principale di importazione."""
    print("""
🔄 IMPORTAZIONE WORKFLOW CRUD PDF
================================

Importa i 4 workflow JSON nel database per l'esecuzione.
""")
    
    # Verifica prerequisiti
    if not Path(DB_PATH).exists():
        logger.error(f"❌ Database non trovato: {DB_PATH}")
        return
    
    if not Path(WORKFLOWS_DIR).exists():
        logger.error(f"❌ Directory workflow non trovata: {WORKFLOWS_DIR}")
        return
    
    # Verifica tabelle
    if not ensure_tables_exist():
        logger.error("❌ Struttura database non valida")
        return
    
    # Importa workflow
    imported_count = 0
    imported_workflows = []
    
    for filename, workflow_info in WORKFLOW_FILES.items():
        filepath = Path(WORKFLOWS_DIR) / filename
        
        if not filepath.exists():
            logger.warning(f"⚠️ File non trovato: {filepath}")
            continue
        
        logger.info(f"🔄 Importando {filename}...")
        
        # Carica JSON
        workflow_data = load_workflow_json(str(filepath))
        if not workflow_data:
            continue
        
        # Importa nel database
        workflow_id = import_workflow(workflow_data, workflow_info)
        if workflow_id:
            imported_count += 1
            imported_workflows.append((workflow_id, workflow_info["name"]))
    
    # Verifica risultati
    logger.info("")
    verify_import()
    
    if imported_count > 0:
        logger.info(f"✅ IMPORTAZIONE COMPLETATA: {imported_count} workflow")
        
        # Suggerimenti next steps
        logger.info("")
        logger.info("🚀 NEXT STEPS:")
        logger.info("   1. Eseguire test_workflow_execution.py per testare i workflow")
        logger.info("   2. Verificare i log per eventuali errori")
        logger.info("   3. Testare l'esecuzione end-to-end")
    else:
        logger.error("❌ Nessun workflow importato!")

if __name__ == "__main__":
    main()