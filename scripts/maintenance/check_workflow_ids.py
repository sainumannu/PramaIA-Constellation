import sqlite3

conn = sqlite3.connect('backend/db/database.db')
cur = conn.cursor()

# Verifica workflows
cur.execute('SELECT id, workflow_id, name FROM workflows')
print('Workflows nel database:')
for row in cur.fetchall():
    print(f'  ID={row[0]}, workflow_id="{row[1]}", name="{row[2]}"')

print()

# Verifica trigger e workflow_id a cui puntano
cur.execute('SELECT id, name, event_type, workflow_id FROM workflow_triggers')
print('Trigger e workflow_id a cui puntano:')
for row in cur.fetchall():
    print(f'  Trigger ID={row[0]}, name="{row[1]}"')
    print(f'    event_type="{row[2]}", workflow_id={row[3]}')
    
    # Verifica se workflow esiste
    cur.execute('SELECT id, workflow_id, name FROM workflows WHERE id = ?', (row[3],))
    wf = cur.fetchone()
    if wf:
        print(f'    ✅ Workflow trovato: "{wf[2]}"')
    else:
        print(f'    ❌ Workflow NON TROVATO!')
    print()

conn.close()
