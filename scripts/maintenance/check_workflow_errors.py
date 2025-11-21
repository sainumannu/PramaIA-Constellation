#!/usr/bin/env python3
"""
Script per analizzare gli errori dei workflow eseguiti
"""

import sqlite3
import json
from datetime import datetime

def main():
    # Connessione al database
    db_path = 'PramaIAServer/backend/db/database.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== ANALISI WORKFLOW EXECUTIONS ===\n")

    # Prima vediamo tutte le esecuzioni
    cursor.execute("""
        SELECT 
            id, 
            workflow_id,
            status, 
            started_at, 
            ended_at,
            error_message,
            input_data
        FROM workflow_executions 
        ORDER BY started_at DESC
        LIMIT 5
    """)

    results = cursor.fetchall()
    print(f"=== ULTIMI {len(results)} WORKFLOW ESEGUITI ===")
    
    for i, row in enumerate(results, 1):
        wf_exec_id, wf_id, status, started, ended, error, input_data = row
        print(f"\n{i}. Execution ID: {wf_exec_id}")
        print(f"   Workflow ID: {wf_id}")
        print(f"   Status: {status}")
        print(f"   Started: {started}")
        print(f"   Ended: {ended}")
        
        if error:
            print(f"   ERROR: {error}")
        else:
            print(f"   ERROR: None")
        
        if input_data and len(input_data.strip()) > 0:
            try:
                input_obj = json.loads(input_data)
                print(f"   Input Data Keys: {list(input_obj.keys()) if isinstance(input_obj, dict) else 'Non dict'}")
            except:
                input_preview = input_data[:150] if len(input_data) > 150 else input_data
                print(f"   Input (raw): {input_preview}")
        
        print("-" * 60)

    # Ora vediamo i dettagli sui nodi di questi workflow
    if results:
        print(f"\n=== DETTAGLI NODI DEI WORKFLOW ===")
        
        # Prendi i workflow_id dalle esecuzioni
        executed_workflow_ids = [row[1] for row in results]
        
        for wf_id in set(executed_workflow_ids):
            cursor.execute("""
                SELECT node_type, COUNT(*) as count
                FROM workflow_nodes 
                WHERE workflow_id = ?
                GROUP BY node_type
                ORDER BY count DESC
            """, (wf_id,))
            
            node_types = cursor.fetchall()
            print(f"\nWorkflow {wf_id}:")
            for node_type, count in node_types:
                print(f"  - {node_type}: {count} nodi")

    conn.close()

if __name__ == "__main__":
    main()