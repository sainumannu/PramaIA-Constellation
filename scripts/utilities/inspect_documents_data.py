import sqlite3

db = sqlite3.connect('PramaIA-VectorstoreService/data/documents.db')
c = db.cursor()

print("=" * 100)
print("CURRENT DATA IN documents.db")
print("=" * 100)

print("\n📄 DOCUMENTS:")
print("-" * 100)
c.execute('SELECT id, filename, collection, created_at FROM documents')
docs = c.fetchall()
if docs:
    for doc in docs:
        print(f"  ID: {doc[0]}")
        print(f"  Filename: {doc[1]}")
        print(f"  Collection: {doc[2]}")
        print(f"  Created: {doc[3]}")
        print()
else:
    print("  (No documents)")

print("\n📋 DOCUMENT_METADATA:")
print("-" * 100)
c.execute('SELECT document_id, key, value, value_type FROM document_metadata ORDER BY document_id')
metadata = c.fetchall()
if metadata:
    current_doc_id = None
    for doc_id, key, value, vtype in metadata:
        if doc_id != current_doc_id:
            print(f"\n  Document: {doc_id}")
            current_doc_id = doc_id
        print(f"    {key}: {value} ({vtype})")
else:
    print("  (No metadata)")

db.close()
