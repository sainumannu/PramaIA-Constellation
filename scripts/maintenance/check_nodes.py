#!/usr/bin/env python3
"""Script per analizzare i nodi di input dei workflow"""
import sqlite3
import json

db_path = 'PramaIAServer/backend/db/database.db'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Analizza i nodi del workflow del primo trigger
print("=== NODI DEL WORKFLOW 'PDF Document CREATE Pipeline' ===\n")

cursor.execute("""
    SELECT node_id, node_type, name, config 
    FROM workflow_nodes 
    WHERE workflow_id = 'wf_bd11290f923b'
    ORDER BY node_id
""")

nodes = cursor.fetchall()
for i, node in enumerate(nodes, 1):
    print(f"\nNodo #{i}:")
    print(f"  node_id: {node[0]}")
    print(f"  node_type: {node[1]}")
    print(f"  name: {node[2]}")
    
    # Prova a parsare il config
    try:
        config = json.loads(node[3]) if node[3] else {}
        print(f"  config: {json.dumps(config, indent=4)}")
    except:
        print(f"  config: {node[3]}")

# Mostra anche i workflow trigger e il loro target_node_id
print("\n\n=== WORKFLOW TRIGGER ===\n")
cursor.execute("SELECT id, name, workflow_id, target_node_id FROM workflow_triggers ORDER BY name")
triggers = cursor.fetchall()
for trigger in triggers:
    print(f"Trigger: {trigger[1]}")
    print(f"  workflow_id: {trigger[2]}")
    print(f"  target_node_id: {trigger[3]}")

conn.close()
