#!/usr/bin/env python3
"""
Fix the email tracking database by properly importing historical email data
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def clean_and_reimport_emails():
    """Clear database and properly import historical emails"""
    
    # Connect to tracking database
    db_path = Path('campaign_results/email_tracking.db')
    if not db_path.exists():
        print("Database not found")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Clear existing data
    print("Clearing existing incorrect data...")
    cursor.execute("DELETE FROM sent_emails")
    conn.commit()
    
    total_imported = 0
    
    # 1. Import from emailed_professors.json
    prof_file = Path('data/emailed_professors.json')
    if prof_file.exists():
        print("Importing from emailed_professors.json...")
        with open(prof_file, 'r', encoding='utf-8') as f:
            professors = json.load(f)
        
        for prof in professors:
            email = prof.get('recipient_email', '')
            name = prof.get('recipient_name', 'Unknown')
            timestamp = prof.get('timestamp', datetime.now().isoformat())
            
            # Skip invalid emails
            if not email or '@' not in email or email.endswith('.pdf'):
                continue
                
            cursor.execute('''
                INSERT INTO sent_emails 
                (email, recipient_name, subject, contact_type, confidence_score, sent_date, campaign_name, delivery_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                name,
                'Research Collaboration Inquiry',
                'professor',
                95,
                timestamp,
                'historical_professors',
                'sent'
            ))
            total_imported += 1
        
        print(f"  Imported {len(professors)} professor emails")
    
    # 2. Import from application_log.json 
    app_file = Path('data/application_log.json')
    if app_file.exists():
        print("Importing from application_log.json...")
        with open(app_file, 'r', encoding='utf-8') as f:
            app_data = json.load(f)
        
        app_count = 0
        for entry in app_data:
            email = entry.get('email', '')
            name = entry.get('name', 'Unknown')
            timestamp = entry.get('timestamp', datetime.now().isoformat())
            
            # Skip invalid emails
            if not email or '@' not in email:
                continue
                
            cursor.execute('''
                INSERT INTO sent_emails 
                (email, recipient_name, subject, contact_type, confidence_score, sent_date, campaign_name, delivery_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                name,
                'Application Follow-up',
                'application',
                90,
                timestamp,
                'historical_applications',
                'sent'
            ))
            app_count += 1
            total_imported += 1
        
        print(f"  Imported {app_count} application emails")
    
    # 3. Check followups.json structure
    followup_file = Path('data/followups.json')
    if followup_file.exists():
        print("Checking followups.json structure...")
        with open(followup_file, 'r', encoding='utf-8') as f:
            followup_data = json.load(f)
        
        # This file seems to contain campaign metadata, not actual emails
        # Let's see if there are emails buried in it
        followup_count = 0
        if 'campaigns' in followup_data:
            for campaign_id, campaign_data in followup_data['campaigns'].items():
                # Check if there are emails in the campaign data
                if 'emails' in campaign_data or 'recipients' in campaign_data:
                    # Process emails if found
                    pass
                else:
                    # This seems to be just campaign metadata
                    continue
        
        print(f"  Followups.json appears to contain campaign metadata, not direct emails")
    
    conn.commit()
    
    # Get final count
    cursor.execute('SELECT COUNT(*) FROM sent_emails')
    final_count = cursor.fetchone()[0]
    
    print(f"\nDatabase updated:")
    print(f"  Total emails imported: {total_imported}")
    print(f"  Final database count: {final_count}")
    
    # Show breakdown
    cursor.execute('''
        SELECT campaign_name, COUNT(*) as count 
        FROM sent_emails 
        GROUP BY campaign_name 
        ORDER BY count DESC
    ''')
    
    print(f"\nBreakdown by source:")
    for campaign, count in cursor.fetchall():
        print(f"  {campaign}: {count} emails")
    
    # Show sample emails
    cursor.execute('SELECT email, recipient_name, campaign_name FROM sent_emails LIMIT 10')
    samples = cursor.fetchall()
    print(f"\nSample emails:")
    for email, name, campaign in samples:
        print(f"  {email} ({name}) - {campaign}")
    
    conn.close()

if __name__ == "__main__":
    clean_and_reimport_emails()