import sqlite3

conn = sqlite3.connect('backend/db/database.db')
cursor = conn.cursor()

# Elenco workflow
cursor.execute('SELECT workflow_id, name FROM workflows')
wfs = cursor.fetchall()
print("="*60)
print("WORKFLOWS NEL DATABASE")
print("="*60)
for w in wfs:
    print(f"  - {w[0]}: {w[1]}")

# Elenco trigger
cursor.execute('''
    SELECT t.name, t.event_type, t.source, w.name, t.active
    FROM workflow_triggers t 
    JOIN workflows w ON t.workflow_id = w.id
''')
triggers = cursor.fetchall()
print("\n" + "="*60)
print("TRIGGER NEL DATABASE")
print("="*60)
for t in triggers:
    status = "✅" if t[4] else "❌"
    print(f"  {status} {t[0]}")
    print(f"     Evento: {t[1]}")
    print(f"     Source: {t[2]}")
    print(f"     Workflow: {t[3]}")
    print()

conn.close()
