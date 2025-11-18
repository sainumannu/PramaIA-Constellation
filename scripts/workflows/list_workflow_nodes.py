import sqlite3

conn = sqlite3.connect('backend/db/database.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT wn.name, wn.node_type, wn.config
    FROM workflow_nodes wn 
    JOIN workflows w ON wn.workflow_id = w.id 
    WHERE w.workflow_id = 'pdf_document_add_workflow'
''')
nodes = cursor.fetchall()

print("Nodi workflow pdf_document_add_workflow:")
for n in nodes:
    print(f"  - {n[1]}: {n[0]}")
    if n[2]:
        print(f"    Config: {n[2][:80]}...")

conn.close()
