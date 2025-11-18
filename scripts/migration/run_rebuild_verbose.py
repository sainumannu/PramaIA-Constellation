import sqlite3
import sys

try:
    # Connetti al database
    conn = sqlite3.connect('backend/db/database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Leggi SQL
    with open('rebuild_workflows_v2.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Esegui statement per statement per catturare errori
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    
    for i, statement in enumerate(statements, 1):
        try:
            conn.execute(statement)
            if 'INSERT INTO workflows' in statement:
                print(f"✅ Statement {i}: Workflow inserito")
            elif 'INSERT INTO workflow_nodes' in statement:
                print(f"✅ Statement {i}: Nodo inserito")
            elif 'INSERT INTO workflow_triggers' in statement:
                print(f"✅ Statement {i}: Trigger inserito")
        except Exception as e:
            print(f"❌ ERRORE Statement {i}: {e}")
            print(f"   Statement: {statement[:100]}...")
            
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
    
    print(f"\n📊 Statistiche finali:")
    print(f"  Workflows:    {workflows_count}")
    print(f"  Nodi:         {nodes_count}")
    print(f"  Connessioni:  {connections_count}")
    print(f"  Trigger:      {triggers_count}")
    
    # Dettaglio per workflow
    cur.execute('''
        SELECT w.workflow_id, COUNT(n.id) as node_count 
        FROM workflows w 
        LEFT JOIN workflow_nodes n ON w.id = n.workflow_id 
        GROUP BY w.id, w.workflow_id
    ''')
    print(f"\n📋 Nodi per workflow:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} nodi")
    
    conn.close()
    print("\n✅ Ricostruzione completata!")
    
except Exception as e:
    print(f"❌ ERRORE FATALE: {e}")
    sys.exit(1)
