#!/usr/bin/env python3
import sqlite3
import json

print("=== EVENT BUFFER STATE ===\n")

# Leggi event buffer del Monitor
buffer_db = r'c:\PramaIA\PramaIA-Agents\document-folder-monitor-agent\event_buffer.db'
try:
    conn = sqlite3.connect(buffer_db)
    c = conn.cursor()
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(f"Event buffer tables: {tables}\n")
    
    if 'events' in tables:
        c.execute('SELECT COUNT(*) FROM events')
        count = c.fetchone()[0]
        print(f"Buffered events: {count}")
        
        if count > 0:
            c.execute('SELECT id, event_type, filename, status, created_at FROM events ORDER BY id DESC LIMIT 5')
            print("Recent events:")
            for row in c.fetchall():
                print(f"  ID:{row[0]}, Type:{row[1]}, File:{row[2]}, Status:{row[3]}, Created:{row[4]}")
    
    conn.close()
except Exception as e:
    print(f"Error reading event buffer: {e}")

print("\n=== BACKEND TRIGGERS STATE ===\n")

# Leggi trigger configuration dal backend
backend_db = r'c:\PramaIA\PramaIAServer\backend\db\database.db'
try:
    conn = sqlite3.connect(backend_db)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM workflow_triggers')
    trigger_count = c.fetchone()[0]
    print(f"Active triggers: {trigger_count}")
    
    if trigger_count > 0:
        c.execute('SELECT id, event_type, workflow_id, is_active FROM workflow_triggers LIMIT 5')
        print("Triggers:")
        for row in c.fetchall():
            print(f"  ID:{row[0]}, Event:{row[1]}, Workflow:{row[2]}, Active:{row[3]}")
    
    conn.close()
except Exception as e:
    print(f"Error reading triggers: {e}")
