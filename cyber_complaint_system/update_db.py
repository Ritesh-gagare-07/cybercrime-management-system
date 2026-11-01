import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1️⃣ OFFICERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    category TEXT
)
""")

# 2️⃣ MESSAGES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER,
    sender TEXT,      -- 'officer' or 'citizen'
    message TEXT,
    timestamp TEXT
)
""")

# 3️⃣ ADD officer_id COLUMN TO complaints TABLE (assigned officer)
try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN officer_id INTEGER")
except sqlite3.OperationalError:
    print("Column 'officer_id' already exists, skipping...")

# 4️⃣ ADD report_id COLUMN TO complaints TABLE (sequential official report)
try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN report_id TEXT")
except sqlite3.OperationalError:
    print("Column 'report_id' already exists, skipping...")

conn.commit()
conn.close()

print("✅ Database updated successfully with officer module support")
