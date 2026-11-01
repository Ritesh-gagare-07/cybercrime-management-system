import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN report TEXT")
    print("✅ 'report' column added successfully")
except sqlite3.OperationalError as e:
    print("⚠️ Column already exists or error:", e)

conn.commit()
conn.close()
