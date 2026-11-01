import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    mobile TEXT,
    address TEXT,
    password TEXT,
    role TEXT
)
""")

# COMPLAINTS TABLE
cursor.execute("""
CREATE TABLE complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    description TEXT,
    category TEXT,
    status TEXT DEFAULT 'Submitted',
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER,
    file_name TEXT
)
""")


conn.commit()
conn.close()

print("✅ Database initialized successfully")
