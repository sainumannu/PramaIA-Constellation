import sqlite3

conn = sqlite3.connect('backend/db/database.db')
cur = conn.cursor()

cur.execute('SELECT name, event_type, source, active FROM workflow_triggers')
print('Trigger nel database:')
for row in cur.fetchall():
    print(f'  {row[0]}:')
    print(f'    event_type = "{row[1]}"')
    print(f'    source = "{row[2]}"')
    print(f'    active = {row[3]}')
    print()

conn.close()
