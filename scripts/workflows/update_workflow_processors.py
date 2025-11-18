#!/usr/bin/env python3
"""
Aggiornamento workflow: Sostituzione processori stub con implementazioni reali

Questo script aggiorna i workflow CRUD PDF sostituendo i processori stub
con le implementazioni reali complete.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "backend/db/database.db"

# Mapping stub -> processore reale
PROCESSOR_MAPPING = {
    # StubProcessor rimosso - non più necessario
    'EventInputProcessor': 'EventInputProcessor',  # Già giusto se presente
    'FileParsingProcessor': 'FileParsingProcessor', 
    'MetadataManagerProcessor': 'MetadataManagerProcessor',
    'DocumentProcessorProcessor': 'DocumentProcessorProcessor',
    'VectorStoreOperationsProcessor': 'VectorStoreOperationsProcessor', 
    'EventLoggerProcessor': 'EventLoggerProcessor'
}

# Configurazioni specifiche per processori
PROCESSOR_CONFIGS = {
    'FileParsingProcessor': {
        'supported_formats': ['.pdf'],
        'extraction_method': 'dual',  # PyPDF2 + pdfplumber
        'clean_text': True
    },
    'DocumentProcessorProcessor': {
        'chunk_size': 512,
        'chunk_overlap': 50,
        'chunking_strategy': 'sliding_window'
    },
    'VectorStoreOperationsProcessor': {
        'embedding_model': 'all-MiniLM-L6-v2',
        'collection_name': 'prama_documents',
        'persist_directory': './chroma_db'
    },
    'EventLoggerProcessor': {
        'log_to_file': True,
        'log_to_db': True,
        'log_level': 'info',
        'event_level': 'info'
    }
}

def connect_db():
    """Connessione al database."""
    if not Path(DB_PATH).exists():
        raise FileNotFoundError(f"Database non trovato: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def get_workflows_with_stubs():
    """Trova tutti i workflow che usano processori stub."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Prima verifica quali tabelle esistono
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"📋 Tabelle trovate nel database: {tables}")
    
    # Verifica workflow_nodes
    if 'workflow_nodes' not in tables:
        logger.warning("⚠️  Tabella workflow_nodes non trovata. Recupero tutti i workflow per ora.")
        # Recupera tutti i workflow
        cursor.execute("SELECT workflow_id, name, description FROM workflows ORDER BY name")
    else:
        logger.info("📦 Usando tabella: workflow_nodes")
        # Query per trovare workflow con nodi che usano processori stub specifici
        stub_types = [
            'event_input_node', 'file_parsing', 'metadata_manager', 
            'document_processor', 'vector_store_operations', 'event_logger'
        ]
        placeholders = ','.join(['?' for _ in stub_types])
        
        cursor.execute(f"""
            SELECT DISTINCT w.workflow_id, w.name, w.description
            FROM workflows w
            JOIN workflow_nodes n ON w.workflow_id = n.workflow_id
            WHERE n.node_type IN ({placeholders})
            ORDER BY w.name
        """, stub_types)
    
    workflows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'workflow_id': row[0],
            'name': row[1], 
            'description': row[2]
        }
        for row in workflows
    ]

def get_workflow_nodes(workflow_id: str):
    """Ottiene tutti i nodi di un workflow."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Usa workflows_nodes direttamente
    
    cursor.execute("""
        SELECT node_id, name, node_type, config, position_x, position_y
        FROM workflow_nodes
        WHERE workflow_id = ?
        ORDER BY name
    """, (workflow_id,))
    
    nodes = cursor.fetchall()
    conn.close()
    
    return [
        {
            'node_id': row[0],
            'name': row[1],
            'processor_type': row[2],  # Manteniamo processor_type per compatibilità
            'config': json.loads(row[3]) if row[3] else {},
            'position_x': row[4],
            'position_y': row[5]
        }
        for row in nodes
    ]

def update_node_processor(node_id: str, new_processor_type: str, new_config: dict):
    """Aggiorna il tipo di processore e configurazione di un nodo."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Usa workflows_nodes direttamente
    
    cursor.execute("""
        UPDATE workflow_nodes
        SET node_type = ?, config = ?, updated_at = ?
        WHERE node_id = ?
    """, (
        new_processor_type,
        json.dumps(new_config),
        datetime.now().isoformat(),
        node_id
    ))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0

def determine_new_processor(node_name: str, current_processor: str) -> str:
    """Determina il processore reale basato sul nome del nodo e processore corrente."""
    
    # Se è già mappato esplicitamente
    if current_processor in PROCESSOR_MAPPING:
        return PROCESSOR_MAPPING[current_processor]
    
    # Inferenze basate sul nome del nodo
    node_name_lower = node_name.lower()
    
    if 'event' in node_name_lower and ('input' in node_name_lower or 'trigger' in node_name_lower):
        return 'EventInputProcessor'
    elif 'parse' in node_name_lower or 'extract' in node_name_lower or 'pdf' in node_name_lower:
        return 'FileParsingProcessor'
    elif 'metadata' in node_name_lower or 'meta' in node_name_lower:
        return 'MetadataManagerProcessor'
    elif 'document' in node_name_lower and ('process' in node_name_lower or 'chunk' in node_name_lower):
        return 'DocumentProcessorProcessor'
    elif 'vector' in node_name_lower or 'embedding' in node_name_lower or 'index' in node_name_lower or 'search' in node_name_lower:
        return 'VectorStoreOperationsProcessor'
    elif 'log' in node_name_lower or 'audit' in node_name_lower or 'event' in node_name_lower:
        return 'EventLoggerProcessor'
    else:
        # Default fallback
        logger.warning(f"🤔 Impossibile determinare processore per '{node_name}', usando EventInputProcessor")
        return 'EventInputProcessor'

def merge_configs(existing_config: dict, processor_type: str) -> dict:
    """Unisce la configurazione esistente con quella specifica del processore."""
    merged = existing_config.copy()
    
    # Aggiungi configurazioni specifiche del processore se non presenti
    if processor_type in PROCESSOR_CONFIGS:
        for key, value in PROCESSOR_CONFIGS[processor_type].items():
            if key not in merged:
                merged[key] = value
    
    # Aggiungi metadati di aggiornamento
    merged['_processor_update'] = {
        'updated_at': datetime.now().isoformat(),
        'updated_by': 'real_processors_update_script',
        'version': '1.0.0'
    }
    
    return merged

def update_workflow_processors(workflow_id: str, dry_run: bool = True):
    """Aggiorna tutti i processori stub di un workflow."""
    logger.info(f"{'🧪 [DRY RUN]' if dry_run else '🔧'} Aggiornamento workflow: {workflow_id}")
    
    nodes = get_workflow_nodes(workflow_id)
    updates = []
    
    for node in nodes:
        current_processor = node['processor_type']
        
        # Controlla se è un processore stub che deve essere aggiornato
        needs_update = (
            current_processor in PROCESSOR_MAPPING or
            'Stub' in current_processor
        )
        
        if needs_update:
            new_processor = determine_new_processor(node['name'], current_processor)
            new_config = merge_configs(node['config'], new_processor)
            
            updates.append({
                'node_id': node['node_id'],
                'node_name': node['name'],
                'old_processor': current_processor,
                'new_processor': new_processor,
                'old_config': node['config'],
                'new_config': new_config
            })
            
            logger.info(f"  📝 {node['name']}: {current_processor} → {new_processor}")
            
            if not dry_run:
                success = update_node_processor(node['node_id'], new_processor, new_config)
                if success:
                    logger.info(f"    ✅ Aggiornato con successo")
                else:
                    logger.error(f"    ❌ Errore nell'aggiornamento")
        else:
            logger.info(f"  ⏭️  {node['name']}: {current_processor} (già corretto)")
    
    return updates

def main():
    """Funzione principale per aggiornamento processori."""
    print("""
🔧 AGGIORNAMENTO PROCESSORI STUB → REALI
=======================================

Questo script sostituisce i processori stub con implementazioni reali
nei workflow CRUD PDF.
""")
    
    try:
        # Trova workflow con stub
        workflows = get_workflows_with_stubs()
        
        if not workflows:
            logger.info("✅ Nessun workflow con processori stub trovato!")
            return
        
        logger.info(f"📋 Trovati {len(workflows)} workflow con processori stub:")
        for workflow in workflows:
            logger.info(f"  - {workflow['name']} ({workflow['workflow_id']})")
        
        print("\n" + "="*50)
        
        # Esecuzione DRY RUN prima
        logger.info("🧪 ESECUZIONE DRY RUN - Nessuna modifica al database")
        print("="*50)
        
        all_updates = []
        for workflow in workflows:
            updates = update_workflow_processors(workflow['workflow_id'], dry_run=True)
            all_updates.extend(updates)
            print()
        
        if not all_updates:
            logger.info("✅ Nessun aggiornamento necessario!")
            return
        
        # Riepilogo cambiamenti
        print("="*50)
        logger.info(f"📊 RIEPILOGO: {len(all_updates)} nodi da aggiornare")
        
        processor_counts = {}
        for update in all_updates:
            new_proc = update['new_processor']
            processor_counts[new_proc] = processor_counts.get(new_proc, 0) + 1
        
        for processor, count in processor_counts.items():
            logger.info(f"  - {processor}: {count} nodi")
        
        # Conferma per applicare modifiche
        print("\n" + "="*50)
        response = input("🤔 Applicare le modifiche al database? (y/N): ").lower().strip()
        
        if response == 'y' or response == 'yes':
            logger.info("🚀 APPLICAZIONE MODIFICHE AL DATABASE")
            print("="*50)
            
            for workflow in workflows:
                updates = update_workflow_processors(workflow['workflow_id'], dry_run=False)
                print()
            
            logger.info("✅ AGGIORNAMENTO COMPLETATO!")
            
            # Verifica finale
            remaining_stubs = get_workflows_with_stubs()
            if not remaining_stubs:
                logger.info("🎉 Tutti i processori stub sono stati sostituiti!")
            else:
                logger.warning(f"⚠️  Rimangono {len(remaining_stubs)} workflow con stub")
        else:
            logger.info("❌ Operazione annullata dall'utente")
    
    except Exception as e:
        logger.error(f"❌ Errore durante l'aggiornamento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()