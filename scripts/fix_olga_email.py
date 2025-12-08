
import sqlite3
import os

DB_PATH = 'data/clean_40k_professors.db'

def fix_olga():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if Olga exists
        c.execute("SELECT rowid, name, email FROM verified_contacts WHERE name LIKE '%Olga Russakovsky%' OR email LIKE '%or@cs.princeton.edu%'")
        rows = c.fetchall()
        
        if not rows:
            print("Olga not found in DB.")
            return

        print(f"Found {len(rows)} entries for Olga:")
        for row in rows:
            print(row)
            
        # Update
        c.execute("UPDATE verified_contacts SET email = 'olgarus@cs.princeton.edu' WHERE name LIKE '%Olga Russakovsky%' OR email LIKE '%or@cs.princeton.edu%'")
        conn.commit()
        print(f"Updated {c.rowcount} rows to use 'olgarus@cs.princeton.edu'.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_olga()
