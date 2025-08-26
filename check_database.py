#!/usr/bin/env python3
"""
Check email tracking database contents
"""

import sqlite3
import json
from pathlib import Path

# Connect to tracking database
db_path = Path('campaign_results/email_tracking.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM sent_emails')
    total_count = cursor.fetchone()[0]
    print(f'Total emails in database: {total_count}')
    
    # Get breakdown by source
    cursor.execute('''
        SELECT 
            CASE 
                WHEN source LIKE '%followups%' THEN 'Followups'
                WHEN source LIKE '%professors%' THEN 'Professors' 
                WHEN source LIKE '%application%' THEN 'Applications'
                ELSE source
            END as source_type,
            COUNT(*) as count
        FROM sent_emails 
        GROUP BY source_type
        ORDER BY count DESC
    ''')
    
    print('\nBreakdown by source:')
    for source, count in cursor.fetchall():
        print(f'  {source}: {count} emails')
    
    # Show sample of each type
    print('\nSample emails from each source:')
    
    # Followups sample
    cursor.execute("SELECT email, sent_date, source FROM sent_emails WHERE source LIKE '%followups%' LIMIT 3")
    followup_samples = cursor.fetchall()
    if followup_samples:
        print('\nFollowup emails (sample):')
        for email, date, source in followup_samples:
            print(f'  {email} - {date}')
    
    # Professors sample  
    cursor.execute("SELECT email, sent_date, source FROM sent_emails WHERE source LIKE '%professors%' LIMIT 3")
    prof_samples = cursor.fetchall()
    if prof_samples:
        print('\nProfessor emails (sample):')
        for email, date, source in prof_samples:
            print(f'  {email} - {date}')
            
    # Applications sample
    cursor.execute("SELECT email, sent_date, source FROM sent_emails WHERE source LIKE '%application%' LIMIT 3")
    app_samples = cursor.fetchall()
    if app_samples:
        print('\nApplication log emails (sample):')
        for email, date, source in app_samples:
            print(f'  {email} - {date}')
    
    # Get date range
    cursor.execute("SELECT MIN(sent_date), MAX(sent_date) FROM sent_emails")
    min_date, max_date = cursor.fetchone()
    print(f'\nDate range: {min_date} to {max_date}')
    
    # Check for duplicates
    cursor.execute("SELECT email, COUNT(*) as count FROM sent_emails GROUP BY email HAVING count > 1 LIMIT 5")
    duplicates = cursor.fetchall()
    if duplicates:
        print('\nPotential duplicates found:')
        for email, count in duplicates:
            print(f'  {email}: {count} times')
    else:
        print('\nNo duplicates found')
    
    conn.close()
else:
    print('Database not found')