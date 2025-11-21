#!/usr/bin/env python3
"""Script per verificare i trigger nel database"""
import sqlite3
import os
import time
import json

def main():
    db_path = 'PramaIAServer/backend/db/database.db'
    
    # Aspetta che il database esista
    for i in range(15):
        if os.path.exists(db_path):
            print(f"✓ Database trovato: {db_path}")
            break
        print(f"Aspetto database... {i+1}/15")
        time.sleep(1)
    else:
        print(f"✗ Database non trovato in {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Tabelle disponibili
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    print("\n=== TABELLE DISPONIBILI ===")
    for t in tables:
        print(f"  - {t}")
    
    # 2. Cerca trigger
    print("\n=== RICERCA TRIGGER ===")
    
    # Se esiste tabella 'workflow_triggers'
    if 'workflow_triggers' in tables:
        print("✓ Tabella 'workflow_triggers' trovata")
        
        cursor.execute("PRAGMA table_info(workflow_triggers)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  Colonne: {columns}")
        
        cursor.execute("SELECT COUNT(*) FROM workflow_triggers")
        count = cursor.fetchone()[0]
        print(f"  Totale record: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM workflow_triggers")
            triggers = cursor.fetchall()
            print(f"\n=== DETTAGLI TRIGGER ({count} totali) ===")
            for i, trigger in enumerate(triggers, 1):
                t_dict = dict(trigger)
                print(f"\n  Trigger #{i}:")
                for key, value in t_dict.items():
                    # Tranca valori lunghi
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {key}: {value}")
        else:
            print("  (nessun trigger trovato)")
    else:
        print("✗ Tabella 'workflow_triggers' NON trovata")
    
    # 3. Verifica altre tabelle correlate
    print("\n=== ALTRE TABELLE CORRELATE ===")
    
    for table_name in ['workflows', 'workflow_executions', 'workflow_nodes', 'workflow_connections', 'pdf_monitor_events']:
        if table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table_name}: {count} record")
        else:
            print(f"  ✗ {table_name}: NON ESISTE")
    
    # 4. Mostra i workflow disponibili
    if 'workflows' in tables:
        print("\n=== WORKFLOW DISPONIBILI ===")
        cursor.execute("SELECT id, name, description FROM workflows LIMIT 10")
        workflows = cursor.fetchall()
        if workflows:
            for wf in workflows:
                print(f"  - ID: {wf[0]}, Nome: {wf[1]}")
        else:
            print("  (nessun workflow trovato)")
    
    conn.close()

if __name__ == "__main__":
    main()
