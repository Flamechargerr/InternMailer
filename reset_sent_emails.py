#!/usr/bin/env python3
"""
Reset Sent Emails - Clear the email tracking database

This script clears all sent email records, allowing you to re-send
emails to contacts that have already been contacted.

Usage:
    python reset_sent_emails.py
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'campaign_results/email_tracking.db'
BACKUP_PATH = f'campaign_results/backups/email_tracking_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

def reset_sent_emails():
    """Reset the sent emails database"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    # Create backup directory
    os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
    
    # Backup the database
    print(f"📦 Creating backup: {BACKUP_PATH}")
    import shutil
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"✅ Backup created successfully")
    
    # Connect and check current state
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current count
    cursor.execute("SELECT COUNT(*) FROM sent_emails")
    count_before = cursor.fetchone()[0]
    print(f"\n📊 Current state:")
    print(f"   Total sent emails: {count_before}")
    
    if count_before == 0:
        print("\n✅ No emails to reset - database is already empty")
        conn.close()
        return True
    
    # Get unique contacts
    cursor.execute("SELECT COUNT(DISTINCT email) FROM sent_emails")
    unique_contacts = cursor.fetchone()[0]
    print(f"   Unique contacts: {unique_contacts}")
    
    # Confirm deletion
    print(f"\n⚠️  This will delete {count_before} email records")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Operation cancelled")
        conn.close()
        return False
    
    # Delete all records
    print("\n🗑️  Deleting sent email records...")
    cursor.execute("DELETE FROM sent_emails")
    conn.commit()
    
    # Verify deletion
    cursor.execute("SELECT COUNT(*) FROM sent_emails")
    count_after = cursor.fetchone()[0]
    
    if count_after == 0:
        print(f"✅ Successfully deleted {count_before} records")
        print(f"\n📧 You can now send emails to all {unique_contacts} contacts again")
        print(f"\n💡 Backup saved to: {BACKUP_PATH}")
    else:
        print(f"⚠️  Warning: {count_after} records remain")
    
    conn.close()
    return True

if __name__ == '__main__':
    print("="*60)
    print("🔄 RESET SENT EMAILS")
    print("="*60)
    print()
    
    success = reset_sent_emails()
    
    if success:
        print("\n" + "="*60)
        print("✅ RESET COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("1. Refresh your web browser (Ctrl+Shift+R or Cmd+Shift+R)")
        print("2. Click 'Send Emails' button")
        print("3. Emails will be sent to all contacts again")
    else:
        print("\n" + "="*60)
        print("❌ RESET FAILED")
        print("="*60)
