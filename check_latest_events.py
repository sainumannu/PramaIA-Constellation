import sqlite3
from pathlib import Path

db_path = Path("PramaIA-Agents/document-folder-monitor-agent/event_buffer.db")

if not db_path.exists():
    print(f"Database non trovato: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Prima verifica le tabelle disponibili
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nTabelle nel database: {[t[0] for t in tables]}\n")

if not tables:
    print("Nessuna tabella trovata!")
    conn.close()
    exit(1)

# Usa la prima tabella disponibile
table_name = tables[0][0]
print(f"Leggo dalla tabella: {table_name}\n")

cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10")
events = cursor.fetchall()

# Ottieni i nomi delle colonne
column_names = [description[0] for description in cursor.description]
print(f"Colonne: {column_names}\n")
print("=" * 80)

conn.close()

for event in events:
    print(f"\nEvento: {dict(zip(column_names, event))}")
    print("-" * 80)
