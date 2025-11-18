import sqlite3
import json

conn = sqlite3.connect('backend/db/database.db')
cursor = conn.cursor()

cursor.execute('SELECT workflow_id, name, view_state FROM workflows')
workflows = cursor.fetchall()

print("="*60)
print("ANALISI VIEW_STATE WORKFLOWS")
print("="*60)

for wf in workflows:
    print(f"\nWorkflow: {wf[0]}")
    print(f"Nome: {wf[1]}")
    
    if wf[2]:
        print(f"view_state presente: {len(wf[2])} chars")
        print(f"Primi 200 chars: {wf[2][:200]}")
        
        # Tenta di parsare come JSON
        try:
            data = json.loads(wf[2])
            print(f"✅ JSON valido")
            print(f"   Keys: {list(data.keys())}")
            
            if 'nodes' in data:
                print(f"   Nodi trovati: {len(data['nodes'])}")
                for node in data['nodes'][:3]:  # Primi 3
                    print(f"     - {node.get('type', 'N/A')}: {node.get('data', {}).get('label', 'N/A')}")
                    
            if 'edges' in data:
                print(f"   Connessioni trovate: {len(data['edges'])}")
        except:
            print(f"❌ Non è JSON valido")
    else:
        print(f"view_state: NULL o vuoto")

conn.close()
