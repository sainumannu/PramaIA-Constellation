"""
Migrazione per creare la tabella workflow_triggers
"""
from sqlalchemy import create_engine, text
import os
import sys
import json
import uuid

# Aggiungi la directory radice al path di Python per importare i moduli
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)
print(f"Added {project_root} to Python path")

from backend.db.database import engine

def run_migration():
    try:
        # Leggi il file SQL
        sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_workflow_triggers_table.sql')
        with open(sql_path, 'r') as f:
            sql_script = f.read()
        
        # Dividi lo script in istruzioni separate
        # Rimuovi i commenti e dividi le istruzioni
        statements = []
        current_statement = ""
        for line in sql_script.splitlines():
            line = line.strip()
            if line.startswith('--') or not line:  # Salta commenti e linee vuote
                continue
            current_statement += line + " "
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Esegui ogni istruzione separatamente
        with engine.connect() as conn:
            # Esegui prima la creazione della tabella
            create_table_stmt = [stmt for stmt in statements if stmt.startswith('CREATE TABLE')][0]
            conn.execute(text(create_table_stmt))
            print("Tabella workflow_triggers creata con successo")
            
            # Esegui gli indici
            index_stmts = [stmt for stmt in statements if stmt.startswith('CREATE INDEX')]
            for index_stmt in index_stmts:
                conn.execute(text(index_stmt))
            print("Indici creati con successo")
            
            # Creiamo un trigger di esempio per i test
            sample_trigger = {
                "id": str(uuid.uuid4()),
                "name": "Trigger di test PDF",
                "event_type": "pdf_upload",
                "source": "pdf-monitor",
                "workflow_id": "pdf_ingest_complete_pipeline",
                "conditions": json.dumps({"file_extension": "pdf", "min_size_kb": 10}),
                "active": True
            }
            
            # Verifica se ci sono già dei trigger
            result = conn.execute(text("SELECT COUNT(*) FROM workflow_triggers"))
            result_row = result.fetchone()
            count = result_row[0] if result_row else 0
            
            if count == 0:
                # Inserisci il trigger di esempio
                insert_query = text("""
                    INSERT INTO workflow_triggers 
                    (id, name, event_type, source, workflow_id, conditions, active)
                    VALUES (:id, :name, :event_type, :source, :workflow_id, :conditions, :active)
                """)
                conn.execute(insert_query, sample_trigger)
                print("Trigger di esempio creato con successo")
        
        return True
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        return False

if __name__ == "__main__":
    run_migration()
