import sqlite3

# Connetti al database
conn = sqlite3.connect('backend/db/database.db')

# Leggi e esegui SQL
with open('rebuild_workflows_corrected.sql', 'r', encoding='utf-8') as f:
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

conn.close()

print("✅ Ricostruzione completata con successo!")
print(f"\n📊 Statistiche:")
print(f"  Workflows:    {workflows_count}")
print(f"  Nodi:         {nodes_count}")
print(f"  Connessioni:  {connections_count}")
print(f"  Trigger:      {triggers_count}")
