"""
Migrazione per aggiungere il campo target_node_id alla tabella workflow_triggers
"""
from sqlalchemy import create_engine, text
import os
import sys

# Aggiungi la directory radice al path di Python per importare i moduli
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)
print(f"Added {project_root} to Python path")

from backend.db.database import engine

def run_migration():
    try:
        with engine.connect() as conn:
            # Verifica se la colonna esiste già
            result = conn.execute(text("PRAGMA table_info(workflow_triggers)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'target_node_id' not in columns:
                # Aggiungi la nuova colonna
                conn.execute(text("""
                    ALTER TABLE workflow_triggers 
                    ADD COLUMN target_node_id VARCHAR(100) DEFAULT NULL
                """))
                print("✅ Colonna target_node_id aggiunta con successo")
                
                # Aggiungi un indice per migliorare le prestazioni
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_trigger_target_node 
                    ON workflow_triggers(target_node_id)
                """))
                print("✅ Indice idx_trigger_target_node creato con successo")
                
                conn.commit()
            else:
                print("ℹ️ Colonna target_node_id già esistente")
                
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        raise

if __name__ == "__main__":
    print("Avvio migrazione: aggiunta target_node_id a workflow_triggers")
    run_migration()
    print("✅ Migrazione completata")
