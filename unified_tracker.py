"""
UNIFIED EMAIL TRACKER
=====================
Single source of truth for all email tracking across the system.
All scripts (turbo_sender, system.py, jarvis) use this module.

Database: campaign_results/unified_tracking.db
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional, List, Dict
import threading

# Single database path for all tracking
UNIFIED_DB_PATH = 'campaign_results/unified_tracking.db'

# Thread-local storage for connections
_local = threading.local()

def get_db_connection():
    """Get thread-safe database connection."""
    if not hasattr(_local, 'connection') or _local.connection is None:
        os.makedirs(os.path.dirname(UNIFIED_DB_PATH), exist_ok=True)
        _local.connection = sqlite3.connect(UNIFIED_DB_PATH, check_same_thread=False)
        _init_schema(_local.connection)
    return _local.connection

def _init_schema(conn):
    """Initialize unified tracking schema."""
    cursor = conn.cursor()
    
    # Main sent_emails table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            recipient_name TEXT,
            subject TEXT,
            sent_date TEXT NOT NULL,
            source TEXT,  -- 'turbo_sender', 'system.py', 'jarvis'
            status TEXT DEFAULT 'sent',
            response_status TEXT,
            notes TEXT
        )
    ''')
    
    # Daily stats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            emails_sent INTEGER DEFAULT 0,
            emails_failed INTEGER DEFAULT 0,
            responses_received INTEGER DEFAULT 0
        )
    ''')
    
    # Create index for fast date lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sent_date ON sent_emails(sent_date)
    ''')
    
    conn.commit()

def record_email_sent(email: str, recipient_name: str = "", subject: str = "", 
                      source: str = "unknown") -> bool:
    """
    Record an email as sent. Returns True if new, False if duplicate.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO sent_emails (email, recipient_name, subject, sent_date, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, recipient_name, subject, datetime.now().isoformat(), source))
        
        # Update daily stats
        today = date.today().isoformat()
        cursor.execute('''
            INSERT INTO daily_stats (date, emails_sent) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET emails_sent = emails_sent + 1
        ''', (today,))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email already exists (duplicate prevention)
        return False

def is_email_sent(email: str) -> bool:
    """Check if email was already sent to this recipient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM sent_emails WHERE email = ?', (email,))
    return cursor.fetchone() is not None

def get_today_count() -> int:
    """Get number of emails sent today."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    # Query sent_emails directly instead of daily_stats
    cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE sent_date LIKE ?", (f"{today}%",))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_total_count() -> int:
    """Get total emails sent all-time."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sent_emails')
    return cursor.fetchone()[0]

def get_remaining_today(daily_limit: int = 500) -> int:
    """Get remaining emails that can be sent today."""
    return max(0, daily_limit - get_today_count())

def get_all_sent_emails() -> List[str]:
    """Get list of all sent email addresses."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM sent_emails')
    return [row[0] for row in cursor.fetchall()]

def migrate_from_legacy_dbs():
    """
    Migrate data from all legacy databases to unified tracking.
    Call this once to consolidate all existing data.
    """
    print("🔄 MIGRATING LEGACY DATABASES TO UNIFIED TRACKING...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    migrated = 0
    skipped = 0
    
    # Legacy DB 1: email_tracking.db (root)
    if os.path.exists('email_tracking.db'):
        print("  📁 Migrating from email_tracking.db...")
        legacy = sqlite3.connect('email_tracking.db')
        lcur = legacy.cursor()
        try:
            lcur.execute('SELECT email, name, subject, date FROM sent_emails')
            for row in lcur.fetchall():
                try:
                    cursor.execute('''
                        INSERT INTO sent_emails (email, recipient_name, subject, sent_date, source)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (row[0], row[1], row[2], row[3], 'turbo_sender'))
                    migrated += 1
                except sqlite3.IntegrityError:
                    skipped += 1
        except Exception as e:
            print(f"    Error: {e}")
        legacy.close()
    
    # Legacy DB 2: campaign_results/email_tracking.db
    if os.path.exists('campaign_results/email_tracking.db'):
        print("  📁 Migrating from campaign_results/email_tracking.db...")
        legacy = sqlite3.connect('campaign_results/email_tracking.db')
        lcur = legacy.cursor()
        try:
            lcur.execute('SELECT email, recipient_name, subject, sent_date FROM sent_emails')
            for row in lcur.fetchall():
                try:
                    cursor.execute('''
                        INSERT INTO sent_emails (email, recipient_name, subject, sent_date, source)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (row[0], row[1], row[2], row[3], 'system.py'))
                    migrated += 1
                except sqlite3.IntegrityError:
                    skipped += 1
        except Exception as e:
            print(f"    Error: {e}")
        legacy.close()
    
    # Legacy DB 3: campaign_results/advanced_tracking.db
    if os.path.exists('campaign_results/advanced_tracking.db'):
        print("  📁 Migrating from campaign_results/advanced_tracking.db...")
        legacy = sqlite3.connect('campaign_results/advanced_tracking.db')
        lcur = legacy.cursor()
        try:
            # Get column names first
            lcur.execute("PRAGMA table_info(email_tracking)")
            cols = [c[1] for c in lcur.fetchall()]
            
            email_col = next((c for c in cols if 'email' in c.lower()), None)
            name_col = next((c for c in cols if 'name' in c.lower()), None)
            date_col = next((c for c in cols if 'date' in c.lower() or 'time' in c.lower()), None)
            
            if email_col:
                query = f"SELECT {email_col}"
                if name_col:
                    query += f", {name_col}"
                if date_col:
                    query += f", {date_col}"
                query += " FROM email_tracking"
                
                lcur.execute(query)
                for row in lcur.fetchall():
                    try:
                        cursor.execute('''
                            INSERT INTO sent_emails (email, recipient_name, sent_date, source)
                            VALUES (?, ?, ?, ?)
                        ''', (row[0], row[1] if len(row) > 1 else '', 
                              row[2] if len(row) > 2 else datetime.now().isoformat(), 
                              'advanced'))
                        migrated += 1
                    except sqlite3.IntegrityError:
                        skipped += 1
        except Exception as e:
            print(f"    Error: {e}")
        legacy.close()
    
    conn.commit()
    
    print(f"\n✅ MIGRATION COMPLETE")
    print(f"   Migrated: {migrated} emails")
    print(f"   Skipped (duplicates): {skipped}")
    print(f"   Total in unified DB: {get_total_count()}")
    
    return migrated, skipped

def print_status():
    """Print current tracking status."""
    print("\n" + "=" * 50)
    print("📊 UNIFIED EMAIL TRACKING STATUS")
    print("=" * 50)
    print(f"   Database: {UNIFIED_DB_PATH}")
    print(f"   Total sent (all-time): {get_total_count()}")
    print(f"   Sent today: {get_today_count()}")
    print(f"   Remaining today: {get_remaining_today()}")
    print("=" * 50)


# CLI interface
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'migrate':
            migrate_from_legacy_dbs()
        elif sys.argv[1] == 'status':
            print_status()
    else:
        print("Usage:")
        print("  python unified_tracker.py migrate  - Migrate from legacy DBs")
        print("  python unified_tracker.py status   - Show current status")
