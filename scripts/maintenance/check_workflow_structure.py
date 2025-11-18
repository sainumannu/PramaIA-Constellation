"""
Verifica nodi e connessioni nei workflow
"""
import sqlite3

conn = sqlite3.connect('backend/db/database.db')
cur = conn.cursor()

# Per ogni workflow
cur.execute('SELECT id, workflow_id, name FROM workflows')
workflows = cur.fetchall()

for wf_id, wf_workflow_id, wf_name in workflows:
    print(f"\n{'='*70}")
    print(f"Workflow: {wf_name} ({wf_workflow_id})")
    print(f"{'='*70}")
    
    # Nodi
    cur.execute('SELECT id, node_id, name, node_type FROM workflow_nodes WHERE workflow_id = ?', (wf_id,))
    nodes = cur.fetchall()
    print(f"\nNodi ({len(nodes)}):")
    for node in nodes:
        print(f"  [{node[0]}] {node[1]}: {node[2]} (type={node[3]})")
    
    # Connessioni
    cur.execute('SELECT from_node_id, to_node_id, from_port, to_port FROM workflow_connections WHERE workflow_id = ?', (wf_id,))
    connections = cur.fetchall()
    print(f"\nConnessioni ({len(connections)}):")
    for conn_data in connections:
        # Trova nomi nodi
        cur.execute('SELECT node_id FROM workflow_nodes WHERE id = ?', (conn_data[0],))
        from_result = cur.fetchone()
        from_node = from_result[0] if from_result else '?'
        
        cur.execute('SELECT node_id FROM workflow_nodes WHERE id = ?', (conn_data[1],))
        to_result = cur.fetchone()
        to_node = to_result[0] if to_result else '?'
        
        print(f"  {from_node} ({conn_data[2]}) -> {to_node} ({conn_data[3]})")
    
    # Nodi senza connessioni in ingresso
    cur.execute('''
        SELECT n.id, n.node_id, n.name 
        FROM workflow_nodes n 
        WHERE n.workflow_id = ?
        AND n.id NOT IN (
            SELECT to_node_id FROM workflow_connections WHERE workflow_id = ?
        )
    ''', (wf_id, wf_id))
    input_candidates = cur.fetchall()
    print(f"\nNodi senza connessioni in ingresso (candidati input): {len(input_candidates)}")
    for node in input_candidates:
        print(f"  [{node[0]}] {node[1]}: {node[2]}")

conn.close()
