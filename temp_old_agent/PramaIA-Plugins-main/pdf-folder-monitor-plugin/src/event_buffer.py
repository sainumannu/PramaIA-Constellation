import sqlite3
import threading
import os
from datetime import datetime

class EventBuffer:
    def __init__(self, db_path="event_buffer.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    folder TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sent INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    document_id TEXT,
                    error_message TEXT
                )
            ''')
            # Migrazione: se la tabella esistente non ha le nuove colonne, le aggiungiamo
            # Questo è sicuro anche se le colonne esistono già
            try:
                c.execute('ALTER TABLE events ADD COLUMN status TEXT DEFAULT "pending"')
            except sqlite3.OperationalError:
                pass  # Colonna già esistente
            try:
                c.execute('ALTER TABLE events ADD COLUMN document_id TEXT')
            except sqlite3.OperationalError:
                pass  # Colonna già esistente
            try:
                c.execute('ALTER TABLE events ADD COLUMN error_message TEXT')
            except sqlite3.OperationalError:
                pass  # Colonna già esistente
            conn.commit()

    def add_event(self, event_type, file_name, folder):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO events (event_type, file_name, folder, timestamp, sent)
                VALUES (?, ?, ?, ?, 0)
            ''', (event_type, file_name, folder, datetime.utcnow().isoformat()))
            conn.commit()

    def get_unsent_events(self, limit=100):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT id, event_type, file_name, folder, timestamp, status, document_id, error_message 
                FROM events WHERE sent=0 ORDER BY id ASC LIMIT ?
            ''', (limit,))
            rows = c.fetchall()
            return [
                {
                    "id": row[0], 
                    "event_type": row[1], 
                    "file_name": row[2], 
                    "folder": row[3], 
                    "timestamp": row[4],
                    "status": row[5],
                    "document_id": row[6],
                    "error_message": row[7]
                }
                for row in rows
            ]
    
    def get_recent_events(self, limit=100):
        """
        Restituisce gli eventi più recenti, inclusi quelli già inviati.
        """
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT id, event_type, file_name, folder, timestamp, status, document_id, error_message 
                FROM events ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            rows = c.fetchall()
            return [
                {
                    "id": row[0], 
                    "event_type": row[1], 
                    "file_name": row[2], 
                    "folder": row[3], 
                    "timestamp": row[4],
                    "status": row[5],
                    "document_id": row[6],
                    "error_message": row[7]
                }
                for row in rows
            ]

    def mark_events_as_sent(self, event_ids):
        if not event_ids:
            return
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(f'''UPDATE events SET sent=1 WHERE id IN ({','.join(['?']*len(event_ids))})''', event_ids)
            conn.commit()

    def count_unsent(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM events WHERE sent=0')
            return c.fetchone()[0]
    
    def update_event_status(self, event_id, status, document_id=None, error_message=None):
        """
        Aggiorna lo stato di un evento specifico.
        Stati possibili: 'pending', 'processing', 'completed', 'error'
        """
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Costruiamo l'update in base ai parametri forniti
            update_fields = ['status = ?']
            params = [status]
            
            if document_id is not None:
                update_fields.append('document_id = ?')
                params.append(document_id)
            
            if error_message is not None:
                update_fields.append('error_message = ?')
                params.append(error_message)
            
            # Completiamo i parametri con l'id dell'evento
            params.append(event_id)
            
            query = f'UPDATE events SET {", ".join(update_fields)} WHERE id = ?'
            c.execute(query, params)
            conn.commit()
            return c.rowcount > 0
    
    def find_event_by_filename(self, file_name):
        """
        Cerca un evento per nome file.
        """
        with self.lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT id FROM events WHERE file_name = ? ORDER BY timestamp DESC LIMIT 1
            ''', (file_name,))
            row = c.fetchone()
            return row[0] if row else None
