import sqlite3

conn = sqlite3.connect('data/clean_40k_professors.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cursor.fetchall())

# Get first table schema
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
table_name = cursor.fetchone()[0]
print(f"\nTable: {table_name}")
cursor.execute(f"PRAGMA table_info({table_name})")
cols = cursor.fetchall()
print("Columns:")
for c in cols:
    print(f"  {c[1]} ({c[2]})")

# Count rows
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
print("Row count:", cursor.fetchone()[0])

# Sample data
cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
print("Sample:", cursor.fetchall())

conn.close()
