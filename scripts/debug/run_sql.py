import sqlite3
import sys

# Connetti al database
conn = sqlite3.connect('backend/db/database.db')
cursor = conn.cursor()

# Leggi ed esegui SQL
with open('rebuild_all_workflows.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    print("="*60)
    print("RICOSTRUZIONE COMPLETA WORKFLOW")
    print("="*60)
    print("\n🗑️  Eliminazione workflow/trigger esistenti...")
    
    conn.executescript(sql)
    conn.commit()
    
    print("✅ SQL eseguito con successo!")
    
    # Verifica workflows
    print("\n" + "="*60)
    print("VERIFICA WORKFLOWS")
    print("="*60)
    cursor.execute("""
        SELECT w.workflow_id, w.name, 
               (SELECT COUNT(*) FROM workflow_nodes wn WHERE wn.workflow_id = w.id) as nodi,
               (SELECT COUNT(*) FROM workflow_connections wc WHERE wc.workflow_id = w.id) as connessioni
        FROM workflows w
    """)
    workflows = cursor.fetchall()
    
    for wf in workflows:
        print(f"\n✅ {wf[0]}")
        print(f"   Nome: {wf[1]}")
        print(f"   Nodi: {wf[2]}")
        print(f"   Connessioni: {wf[3]}")
    
    # Verifica trigger
    print("\n" + "="*60)
    print("VERIFICA TRIGGER")
    print("="*60)
    cursor.execute("""
        SELECT t.name, t.event_type, t.source, w.name, t.active
        FROM workflow_triggers t
        JOIN workflows w ON t.workflow_id = w.id
    """)
    triggers = cursor.fetchall()
    
    for tr in triggers:
        status = "✅" if tr[4] else "❌"
        print(f"\n{status} {tr[0]}")
        print(f"   Evento: {tr[1]}")
        print(f"   Source: {tr[2]}")
        print(f"   Workflow: {tr[3]}")
    
    print("\n" + "="*60)
    print("RIEPILOGO")
    print("="*60)
    print(f"Workflows creati: {len(workflows)}")
    print(f"Trigger creati: {len(triggers)}")
    print("\n✅ Ricostruzione completata con successo!")
    print("="*60)
        
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    conn.close()
