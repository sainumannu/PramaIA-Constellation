import sqlite3

db = sqlite3.connect('PramaIAServer/backend/db/database.db')
c = db.cursor()

print("=== Users in database ===")
c.execute("SELECT id, username, user_id, email, role FROM users")
for row in c.fetchall():
    print(f"ID: {row[0]}, Username: {row[1]}, user_id: {row[2]}, Email: {row[3]}, Role: {row[4]}")

db.close()
