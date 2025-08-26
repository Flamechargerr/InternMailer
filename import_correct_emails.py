#!/usr/bin/env python3
"""
Import the correct 635 emails from email_logs section into tracking database
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def import_correct_emails():
    """Import the actual 635 emails from followups.json email_logs"""
    
    # Connect to tracking database
    db_path = Path('campaign_results/email_tracking.db')
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Clear existing data
    print("🧹 Clearing existing incorrect data...")
    cursor.execute("DELETE FROM sent_emails")
    conn.commit()
    
    # Load followups.json
    followup_file = Path('data/followups.json')
    with open(followup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    emails_imported = 0
    
    # Import from email_logs section
    if 'email_logs' in data:
        email_logs = data['email_logs']
        print(f"📧 Importing {len(email_logs)} emails from email_logs...")
        
        for entry in email_logs:
            if isinstance(entry, dict):
                email = entry.get('email', '')
                campaign_id = entry.get('campaign_id', 'unknown')
                subject = entry.get('subject', 'Research Inquiry')
                sent_at = entry.get('sent_at', datetime.now().isoformat())
                
                # Basic email validation
                if email and '@' in email and '.' in email and email.count('@') == 1:
                    # Extract name from email (simple approach)
                    name_part = email.split('@')[0]
                    name = name_part.replace('.', ' ').title()
                    
                    cursor.execute('''
                        INSERT INTO sent_emails 
                        (email, recipient_name, subject, contact_type, confidence_score, sent_date, campaign_name, delivery_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        email,
                        name,
                        subject,
                        'professor',
                        95,
                        sent_at,
                        f'historical_campaign_{campaign_id[:8]}',
                        'sent'
                    ))
                    emails_imported += 1
    
    # Also import the 44 emails from emailed_professors.json if they're not duplicates
    prof_file = Path('data/emailed_professors.json')
    if prof_file.exists():
        with open(prof_file, 'r', encoding='utf-8') as f:
            professors = json.load(f)
        
        print(f"📧 Checking {len(professors)} emails from emailed_professors.json for duplicates...")
        
        additional_emails = 0
        for prof in professors:
            email = prof.get('recipient_email', '')
            
            # Skip invalid emails
            if not email or '@' not in email or email.endswith('.pdf'):
                continue
            
            # Check if this email is already in the database
            cursor.execute('SELECT COUNT(*) FROM sent_emails WHERE email = ?', (email,))
            if cursor.fetchone()[0] == 0:  # Not a duplicate
                name = prof.get('recipient_name', 'Unknown')
                timestamp = prof.get('timestamp', datetime.now().isoformat())
                
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
                additional_emails += 1
                emails_imported += 1
        
        print(f"   📝 Added {additional_emails} additional non-duplicate emails")
    
    conn.commit()
    
    # Get final statistics
    cursor.execute('SELECT COUNT(*) FROM sent_emails')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT email) FROM sent_emails')
    unique_count = cursor.fetchone()[0]
    
    print(f"\n✅ DATABASE UPDATED SUCCESSFULLY:")
    print(f"   📧 Emails imported: {emails_imported}")
    print(f"   📊 Total in database: {total_count}")
    print(f"   🎯 Unique emails: {unique_count}")
    
    # Show sample of imported emails
    cursor.execute('SELECT email, recipient_name, campaign_name FROM sent_emails LIMIT 10')
    samples = cursor.fetchall()
    print(f"\n📧 SAMPLE OF IMPORTED EMAILS:")
    for email, name, campaign in samples:
        print(f"   • {email} ({name})")
    
    # Show campaign breakdown
    cursor.execute('''
        SELECT 
            CASE 
                WHEN campaign_name LIKE 'historical_campaign_%' THEN 'Email Logs'
                WHEN campaign_name = 'historical_professors' THEN 'Professors File'
                ELSE campaign_name
            END as source,
            COUNT(*) as count
        FROM sent_emails 
        GROUP BY source
        ORDER BY count DESC
    ''')
    
    print(f"\n📊 BREAKDOWN BY SOURCE:")
    for source, count in cursor.fetchall():
        print(f"   • {source}: {count} emails")
    
    conn.close()
    
    print(f"\n🎉 SUCCESS! Your {unique_count} historical emails are now properly tracked.")
    print(f"   The system will prevent duplicates when you run future campaigns.")

if __name__ == "__main__":
    import_correct_emails()