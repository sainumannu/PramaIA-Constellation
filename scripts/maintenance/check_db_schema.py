#!/usr/bin/env python3
"""
Verifica schema database
"""
import sqlite3

DB_PATH = r"PramaIAServer\backend\db\database.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ottieni schema workflow_executions
print("Schema workflow_executions:")
cursor.execute("PRAGMA table_info(workflow_executions)")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print()

# Ottieni schema workflow_triggers
print("Schema workflow_triggers:")
cursor.execute("PRAGMA table_info(workflow_triggers)")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print()

# Elenco tutte le tabelle
print("Tabelle nel database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

conn.close()
