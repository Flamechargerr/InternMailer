#!/usr/bin/env python3
"""
Import missing emails from backup database to current database
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def import_missing_emails():
    """Import emails from backup that are missing in current database"""
    
    backup_db_path = r"C:\Users\anama\OneDrive\Desktop\internmailing - Copy\backup_20250826_111813\campaign_results\email_tracking.db"
    current_db_path = "campaign_results/email_tracking.db"
    
    print("🔄 IMPORTING MISSING EMAILS FROM BACKUP")
    print("=" * 50)
    
    if not Path(backup_db_path).exists():
        print("❌ Backup database not found")
        return
    
    if not Path(current_db_path).exists():
        print("❌ Current database not found")
        return
    
    # Connect to both databases
    backup_conn = sqlite3.connect(backup_db_path)
    backup_cursor = backup_conn.cursor()
    
    current_conn = sqlite3.connect(current_db_path)
    current_cursor = current_conn.cursor()
    
    try:
        # Get all emails from backup
        backup_cursor.execute('SELECT DISTINCT email, name, sent_date, subject, campaign_id FROM sent_emails')
        backup_emails = backup_cursor.fetchall()
        
        # Get all emails from current database
        current_cursor.execute('SELECT DISTINCT email FROM sent_emails')
        current_emails = set(row[0] for row in current_cursor.fetchall())
        
        print(f"📧 Backup database has {len(backup_emails)} emails")
        print(f"📧 Current database has {len(current_emails)} emails")
        
        # Find missing emails
        missing_count = 0
        imported_count = 0
        
        for email, name, sent_date, subject, campaign_id in backup_emails:
            if email not in current_emails:
                missing_count += 1
                
                # Import missing email
                try:
                    current_cursor.execute('''
                        INSERT INTO sent_emails 
                        (email, recipient_name, subject, contact_type, confidence_score, sent_date, campaign_name, delivery_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        email,
                        name or 'Unknown',
                        subject or 'Research Inquiry',
                        'professor',
                        95,
                        sent_date or datetime.now().isoformat(),
                        f'backup_import_{campaign_id[:8] if campaign_id else "unknown"}',
                        'sent'
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to import {email}: {e}")
        
        current_conn.commit()
        
        # Get final counts
        current_cursor.execute('SELECT COUNT(*) FROM sent_emails')
        final_total = current_cursor.fetchone()[0]
        
        current_cursor.execute('SELECT COUNT(DISTINCT email) FROM sent_emails')
        final_unique = current_cursor.fetchone()[0]
        
        print(f"\n✅ IMPORT COMPLETED:")
        print(f"   📧 Missing emails found: {missing_count}")
        print(f"   📧 Successfully imported: {imported_count}")
        print(f"   📊 Final database total: {final_total}")
        print(f"   🎯 Final unique emails: {final_unique}")
        
        # Show sample of imported emails
        current_cursor.execute('''
            SELECT email, recipient_name 
            FROM sent_emails 
            WHERE campaign_name LIKE 'backup_import_%' 
            LIMIT 10
        ''')
        samples = current_cursor.fetchall()
        
        if samples:
            print(f"\n📧 SAMPLE IMPORTED EMAILS:")
            for email, name in samples:
                print(f"   • {email} ({name})")
        
        # Show final breakdown
        current_cursor.execute('''
            SELECT 
                CASE 
                    WHEN campaign_name LIKE 'backup_import_%' THEN 'Backup Import'
                    WHEN campaign_name LIKE 'historical_campaign_%' THEN 'Email Logs'
                    WHEN campaign_name = 'historical_professors' THEN 'Professors File'
                    ELSE campaign_name
                END as source,
                COUNT(*) as count
            FROM sent_emails 
            GROUP BY source
            ORDER BY count DESC
        ''')
        
        print(f"\n📊 FINAL BREAKDOWN BY SOURCE:")
        for source, count in current_cursor.fetchall():
            print(f"   • {source}: {count} emails")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
    
    finally:
        backup_conn.close()
        current_conn.close()
    
    print(f"\n🎉 SUCCESS! Your complete email history is now tracked.")
    print(f"   Total unique professors contacted: {final_unique}")

if __name__ == "__main__":
    import_missing_emails()