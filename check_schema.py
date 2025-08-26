#!/usr/bin/env python3
"""
Check email tracking database schema and contents
"""

import sqlite3
from pathlib import Path

# Connect to tracking database
db_path = Path('campaign_results/email_tracking.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("PRAGMA table_info(sent_emails)")
    columns = cursor.fetchall()
    print("Database schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM sent_emails')
    total_count = cursor.fetchone()[0]
    print(f'\nTotal emails in database: {total_count}')
    
    # Show first few rows to understand the data
    cursor.execute('SELECT * FROM sent_emails LIMIT 10')
    rows = cursor.fetchall()
    print('\nFirst 10 entries:')
    for i, row in enumerate(rows, 1):
        print(f'  {i}. {row}')
    
    # Check for unique emails
    cursor.execute('SELECT COUNT(DISTINCT email) FROM sent_emails')
    unique_emails = cursor.fetchone()[0]
    print(f'\nUnique email addresses: {unique_emails}')
    
    # Check for duplicates
    cursor.execute('SELECT email, COUNT(*) as count FROM sent_emails GROUP BY email HAVING count > 1 LIMIT 10')
    duplicates = cursor.fetchall()
    if duplicates:
        print(f'\nDuplicates found: {len(duplicates)} emails appear multiple times')
        for email, count in duplicates[:5]:
            print(f'  {email}: {count} times')
    else:
        print('\nNo duplicates found')
    
    conn.close()
else:
    print('Database not found')