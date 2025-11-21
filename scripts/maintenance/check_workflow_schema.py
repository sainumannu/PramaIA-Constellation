#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('PramaIAServer/backend/db/database.db')
cursor = conn.cursor()

# Get all workflow-related tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%workflow%'")
tables = [row[0] for row in cursor.fetchall()]

print("🔍 TABELLE WORKFLOW:")
print("="*50)

for table in tables:
    print(f"\n📋 {table}:")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Show row count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  Righe: {count}")

# Let's also check if there are node-related tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%node%' OR name LIKE '%connection%')")
node_tables = [row[0] for row in cursor.fetchall()]

if node_tables:
    print(f"\n🔗 TABELLE NODI/CONNESSIONI:")
    print("="*50)
    for table in node_tables:
        print(f"\n📋 {table}:")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  Righe: {count}")

conn.close()