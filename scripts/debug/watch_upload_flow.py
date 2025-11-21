"""
Script per monitorare il flusso di upload di un file in tempo reale
"""
import sqlite3
import time
import sys
from pathlib import Path

def watch_monitor_buffer():
    """Monitora gli eventi nel buffer del monitor"""
    db_path = Path("PramaIA-Agents/document-folder-monitor-agent/event_buffer.db")
    
    if not db_path.exists():
        print(f"❌ Database non trovato: {db_path}")
        return
    
    print("🔍 Monitoraggio eventi in corso... (Ctrl+C per uscire)")
    print("=" * 70)
    
    last_id = 0
    
    try:
        while True:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Recupera nuovi eventi
            cursor.execute("""
                SELECT id, file_path, event_type, status, error_message, 
                       created_at, last_updated, document_id
                FROM event_buffer 
                WHERE id > ?
                ORDER BY id DESC
            """, (last_id,))
            
            events = cursor.fetchall()
            conn.close()
            
            for event in reversed(events):
                event_id, file_path, event_type, status, error, created, updated, doc_id = event
                
                print(f"\n📄 Nuovo evento #{event_id}")
                print(f"   File: {Path(file_path).name}")
                print(f"   Type: {event_type or '?'}")
                print(f"   Status: {status}")
                if error:
                    print(f"   ❌ Error: {error}")
                if doc_id:
                    print(f"   📎 Doc ID: {doc_id}")
                print(f"   ⏰ Created: {created}")
                print(f"   🔄 Updated: {updated}")
                
                last_id = max(last_id, event_id)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoraggio terminato")

def check_triggers():
    """Verifica i trigger configurati nel backend"""
    db_path = Path("PramaIAServer/backend/db/database.db")
    
    if not db_path.exists():
        print(f"❌ Database backend non trovato: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, event_type, is_active, workflow_id
        FROM triggers
        WHERE is_active = 1
    """)
    
    triggers = cursor.fetchall()
    
    print("\n🎯 TRIGGER ATTIVI NEL SISTEMA")
    print("=" * 70)
    
    if not triggers:
        print("⚠️  Nessun trigger attivo!")
    else:
        for trigger in triggers:
            trigger_id, name, event_type, is_active, workflow_id = trigger
            print(f"\n✅ Trigger: {name}")
            print(f"   ID: {trigger_id}")
            print(f"   Event Type: {event_type}")
            print(f"   Workflow ID: {workflow_id}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "triggers":
        check_triggers()
    else:
        watch_monitor_buffer()
