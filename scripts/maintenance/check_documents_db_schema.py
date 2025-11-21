import sqlite3

db = sqlite3.connect('PramaIA-VectorstoreService/data/documents.db')
c = db.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]

print("=" * 100)
print("DOCUMENTS DATABASE SCHEMA (documents.db in VectorstoreService)")
print("=" * 100)

for table in sorted(tables):
    print(f"\n📋 TABLE: {table}")
    print("-" * 100)
    c.execute(f"PRAGMA table_info({table})")
    columns = c.fetchall()
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        nullable = "NOT NULL" if not_null else "NULL"
        print(f"  {col_name:30} {col_type:20} {nullable}")
    
    # Show row count
    c.execute(f"SELECT COUNT(*) FROM {table}")
    count = c.fetchone()[0]
    print(f"  └─ Rows: {count}")

db.close()
