import sqlite3

conn = sqlite3.connect('backend/db/database.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(workflows)')
cols = cursor.fetchall()

print("Schema tabella workflows:")
for c in cols:
    print(f"  {c[1]:<20} {c[2]:<15} {'NOT NULL' if c[3] else ''} {'PRIMARY KEY' if c[5] else ''}")

conn.close()
