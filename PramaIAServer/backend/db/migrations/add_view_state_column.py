"""
Migrazione per aggiungere la colonna view_state alla tabella workflows
"""
from sqlalchemy import create_engine, text
import os
import sys
import json

# Aggiungi la directory radice al path di Python per importare i moduli
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)
print(f"Added {project_root} to Python path")

from backend.db.database import Base, engine
from backend.db.workflow_models import Workflow

def run_migration():
    try:
        # Verifica se la colonna esiste già
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(workflows)"))
            columns = {col[1] for col in result}
            
            if 'view_state' not in columns:
                # SQLite non supporta ALTER TABLE ADD COLUMN con DEFAULT JSON
                # quindi dobbiamo creare una nuova tabella e migrare i dati
                
                # 1. Crea una tabella temporanea con la nuova struttura
                conn.execute(text("""
                    CREATE TABLE workflows_new (
                        id INTEGER PRIMARY KEY,
                        workflow_id VARCHAR(50) NOT NULL,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        created_by VARCHAR(100) NOT NULL,
                        created_at DATETIME,
                        updated_at DATETIME,
                        is_active BOOLEAN,
                        is_public BOOLEAN,
                        assigned_groups JSON,
                        tags JSON,
                        category VARCHAR(100),
                        priority INTEGER,
                        color VARCHAR(7),
                        view_state JSON
                    )
                """))
                
                # 2. Copia i dati esistenti nella nuova tabella
                conn.execute(text("""
                    INSERT INTO workflows_new (
                        id, workflow_id, name, description, created_by,
                        created_at, updated_at, is_active, is_public,
                        assigned_groups, tags, category, priority, color,
                        view_state
                    )
                    SELECT
                        id, workflow_id, name, description, created_by,
                        created_at, updated_at, is_active, is_public,
                        assigned_groups, tags, category, priority, color,
                        json('{}')
                    FROM workflows
                """))
                
                # 3. Elimina la vecchia tabella
                conn.execute(text("DROP TABLE workflows"))
                
                # 4. Rinomina la nuova tabella
                conn.execute(text("ALTER TABLE workflows_new RENAME TO workflows"))
                
                # 5. Ricrea gli indici
                conn.execute(text("CREATE INDEX ix_workflows_workflow_id ON workflows (workflow_id)"))
                conn.execute(text("CREATE INDEX ix_workflows_id ON workflows (id)"))
                
                print("✅ Migrazione completata: aggiunta colonna view_state alla tabella workflows")
            else:
                print("ℹ️ La colonna view_state esiste già nella tabella workflows")
    
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        raise

if __name__ == "__main__":
    run_migration()
