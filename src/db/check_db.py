import sqlite3

conn = sqlite3.connect("db/nifty100.db")

cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name;
""")

tables = cursor.fetchall()

print("Tables in database:\n")

for table in tables:
    print(table[0])

conn.close()
