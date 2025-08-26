#!/usr/bin/env python3
import sqlite3
from pathlib import Path

# Check professor database
db_path = Path('data/clean_40k_professors.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Database Tables:', [t[0] for t in tables])
    
    # Check verified_contacts table
    cursor.execute('SELECT COUNT(*) FROM verified_contacts')
    count = cursor.fetchone()[0]
    print(f'Total Professors: {count:,}')
    
    # Check grade distribution
    try:
        cursor.execute('SELECT grade, COUNT(*) FROM verified_contacts GROUP BY grade ORDER BY COUNT(*) DESC LIMIT 3')
        grades = cursor.fetchall()
        print('Grade Distribution:')
        for grade, cnt in grades:
            print(f'  {grade}: {cnt:,} professors')
    except Exception as e:
        print('Grade data not available')
    
    conn.close()
else:
    print('Professor database not found')