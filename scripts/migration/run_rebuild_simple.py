import sqlite3
import sys

try:
    # Connetti al database
    conn = sqlite3.connect('backend/db/database.db')
    
    # Leggi e esegui SQL
    with open('rebuild_workflows_v2.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
        conn.executescript(sql_script)
    
    conn.commit()
    
    # Verifica risultati
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM workflows')
    workflows_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM workflow_nodes')
    nodes_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM workflow_connections')
    connections_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM workflow_triggers')
    triggers_count = cur.fetchone()[0]
    
    print(f"Ricostruzione completata!")
    print(f"Workflows:    {workflows_count}")
    print(f"Nodi:         {nodes_count}")
    print(f"Connessioni:  {connections_count}")
    print(f"Trigger:      {triggers_count}")
    
    # Dettaglio per workflow
    cur.execute('''
        SELECT w.workflow_id, w.name, COUNT(n.id) as node_count 
        FROM workflows w 
        LEFT JOIN workflow_nodes n ON w.id = n.workflow_id 
        GROUP BY w.id, w.workflow_id, w.name
    ''')
    print(f"\nDettaglio workflows:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[2]} nodi - {row[1]}")
    
    # Dettaglio trigger
    cur.execute('SELECT name, event_type FROM workflow_triggers WHERE active = 1')
    print(f"\nTrigger attivi:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()
    
except Exception as e:
    print(f"ERRORE: {e}")
    sys.exit(1)
