import sqlite3
import os
import json
import sys

def fix_event_document_ids(input_file=None):
    """
    Aggiorna gli eventi esistenti con gli ID dei documenti forniti in un file JSON
    oppure richiede manualmente gli ID per gli eventi in stato 'completed' senza document_id.
    
    Formato del file JSON:
    {
        "filename1.pdf": "doc_id_1",
        "filename2.pdf": "doc_id_2",
        ...
    }
    """
    db_path = "event_buffer.db"
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return
    
    # Carica mapping da file se fornito
    mapping = {}
    if input_file and os.path.exists(input_file):
        try:
            with open(input_file, 'r') as f:
                mapping = json.load(f)
            print(f"Caricato mapping da file per {len(mapping)} documenti")
        except Exception as e:
            print(f"Errore nel caricamento del file: {e}")
            return
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Trova eventi completati senza document_id
    c.execute("""
        SELECT id, file_name, folder, timestamp 
        FROM events 
        WHERE status = 'completed' AND (document_id IS NULL OR document_id = '')
        ORDER BY timestamp DESC
    """)
    events = c.fetchall()
    
    if not events:
        print("Nessun evento completato senza document_id trovato.")
        
        # Verifichiamo anche gli eventi in stato pending
        c.execute("SELECT COUNT(*) FROM events WHERE status = 'pending'")
        pending_count = c.fetchone()[0]
        if pending_count > 0:
            print(f"\nTrovati {pending_count} eventi in stato 'pending'.")
            fix_pending = input("Vuoi impostare questi eventi in stato 'error'? (s/n): ").lower() == 's'
            if fix_pending:
                c.execute("""
                    UPDATE events 
                    SET status = 'error', error_message = 'Elaborazione non completata'
                    WHERE status = 'pending'
                """)
                conn.commit()
                print(f"Aggiornati {pending_count} eventi in stato 'error'")
        return
    
    print(f"Trovati {len(events)} eventi completati senza document_id")
    
    updated = 0
    for event in events:
        event_id, file_name, folder, timestamp = event
        
        if file_name in mapping:
            document_id = mapping[file_name]
            print(f"Trovato mapping per {file_name}: {document_id}")
        else:
            print(f"\nEvento ID: {event_id}")
            print(f"File: {file_name}")
            print(f"Cartella: {folder}")
            print(f"Timestamp: {timestamp}")
            document_id = input("Inserisci document_id (lascia vuoto per saltare): ").strip()
            if not document_id:
                continue
        
        # Aggiorna il document_id
        c.execute("""
            UPDATE events 
            SET document_id = ? 
            WHERE id = ?
        """, (document_id, event_id))
        updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nAggiornati {updated} eventi con document_id")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_event_document_ids(sys.argv[1])
    else:
        fix_event_document_ids()
