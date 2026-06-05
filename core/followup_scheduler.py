"""
InternMailer - Follow-Up Scheduler
Automatically sends follow-ups to contacts who haven't replied
"""

import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from utils.config import config
from utils.profile import get_profile

class FollowUpScheduler:
    """
    Automatically sends follow-up emails to:
    - Contacts who haven't replied after 7 days
    - Out-of-office contacts after 14 days
    Maximum 1 follow-up per contact
    """
    
    def __init__(self):
        self.email_address = config.EMAIL_ADDRESS
        self.password = config.EMAIL_PASSWORD
        self.tracking_db = config.DATABASE_PATH
        self.inbox_db = config.INBOX_DB_PATH
        self.followup_delay_days = config.FOLLOWUP_DELAY_DAYS
        self.max_followups = 1
        self.profile = get_profile()
        self._ensure_tracking_schema()

    def _ensure_tracking_schema(self):
        """Ensure tracking tables/columns exist for follow-ups."""
        with sqlite3.connect(self.tracking_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    name TEXT,
                    company TEXT,
                    position TEXT,
                    subject TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    provider_used TEXT,
                    ai_confidence REAL,
                    status TEXT DEFAULT 'sent',
                    followup_sent BOOLEAN DEFAULT 0,
                    replied BOOLEAN DEFAULT 0
                )
            ''')
            existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(sent_emails)")]
            if 'subject' not in existing_cols:
                conn.execute("ALTER TABLE sent_emails ADD COLUMN subject TEXT")
            conn.commit()
    
    def get_emails_needing_followup(self) -> list:
        """
        Find sent emails that haven't received a reply after 7 days
        and haven't been followed up yet
        """
        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()
        
        # Create follow-up tracking table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS followups_sent (
                email TEXT PRIMARY KEY,
                original_sent_date TEXT,
                followup_sent_date TEXT,
                attempts INTEGER DEFAULT 1
            )
        ''')
        
        # Find sent emails without replies
        since_date = (datetime.now() - timedelta(days=self.followup_delay_days)).isoformat()
        
        cursor.execute('''
            SELECT DISTINCT s.email, s.sent_at, s.subject, s.name
            FROM sent_emails s
            LEFT JOIN followups_sent f ON s.email = f.email
            WHERE s.sent_at < ?
            AND (f.email IS NULL OR f.attempts < ?)
            LIMIT 50
        ''', (since_date, self.max_followups))
        
        results = []
        for row in cursor.fetchall():
            email = row[0]
            
            # Check if they replied (in processed_replies)
            if self._has_replied(email):
                continue
            
            results.append({
                'email': email,
                'sent_date': row[1],
                'subject': row[2],
                'name': row[3] or email.split('@')[0]
            })
        
        conn.close()
        return results
    
    def _has_replied(self, email: str) -> bool:
        """Check if contact has replied"""
        try:
            conn = sqlite3.connect(self.inbox_db)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_replies WHERE from_email = ? LIMIT 1", (email,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except:
            return False
    
    def send_followup(self, contact: dict, dry_run: bool = False) -> bool:
        """Send follow-up email to contact"""
        try:
            subject = f"Re: {contact['subject']}"
            
            signature = self.profile.signature_text()
            body = f"""Hi {contact['name']},

I wanted to follow up on my previous email about potential opportunities.

I'm very interested in your work and would love to discuss how I might contribute.

Would you have 10-15 minutes for a brief call this week?

Best regards,
{signature}
"""
            
            if dry_run:
                print(f"   [DRY RUN] Would send follow-up to {contact['email']}")
                return True
            
            # Create email
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = contact['email']
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_address, self.password)
                server.send_message(msg)
            
            # Track follow-up
            self._track_followup(contact['email'], contact['sent_date'])
            
            print(f"   ✅ Follow-up sent to {contact['email']}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to send follow-up to {contact['email']}: {e}")
            return False
    
    def _track_followup(self, email: str, original_date: str):
        """Track that follow-up was sent"""
        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO followups_sent (email, original_sent_date, followup_sent_date, attempts)
            VALUES (?, ?, ?, COALESCE((SELECT attempts FROM followups_sent WHERE email = ?), 0) + 1)
        ''', (email, original_date, datetime.now().isoformat(), email))
        
        conn.commit()
        conn.close()
    
    def process_scheduled_followups(self, dry_run: bool = False) -> int:
        """
        Process out-of-office follow-ups that are scheduled
        (from follow-up queue in inbox_monitor.db)
        """
        try:
            conn = sqlite3.connect(self.inbox_db)
            cursor = conn.cursor()
            
            # Get due follow-ups
            cursor.execute('''
                SELECT id, email, original_subject, scheduled_date, message_id
                FROM followup_queue
                WHERE sent = 0 AND datetime(scheduled_date) <= datetime('now')
            ''')
            
            due_followups = cursor.fetchall()
            conn.close()
            
            if not due_followups:
                return 0
            
            print(f"\n⏰ Processing {len(due_followups)} scheduled follow-ups...")
            
            sent_count = 0
            for row in due_followups:
                followup_id, email, subject, _, message_id = row
                
                contact = {
                    'email': email,
                    'subject': subject,
                    'name': email.split('@')[0],
                    'sent_date': datetime.now().isoformat()
                }
                
                if self.send_followup(contact, dry_run=dry_run):
                    sent_count += 1
                    
                    if not dry_run:
                        # Mark as sent
                        conn = sqlite3.connect(self.inbox_db)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE followup_queue SET sent = 1 WHERE id = ?', (followup_id,))
                        conn.commit()
                        conn.close()
            
            return sent_count
            
        except Exception as e:
            print(f"❌ Error processing scheduled follow-ups: {e}")
            return 0
    
    def run_followup_cycle(self, dry_run: bool = False):
        """
        Complete follow-up cycle:
        1. Send follow-ups to no-reply contacts
        2. Send scheduled OOO follow-ups
        """
        print("📤 Starting follow-up cycle...\n")
        
        if dry_run:
            print("🧪 DRY RUN MODE - No emails will be sent\n")
        
        # Regular follow-ups (no reply after 7 days)
        contacts_needing_followup = self.get_emails_needing_followup()
        print(f"📋 Found {len(contacts_needing_followup)} contacts needing follow-up")
        
        sent_count = 0
        for contact in contacts_needing_followup:
            if self.send_followup(contact, dry_run=dry_run):
                sent_count += 1
        
        # Scheduled OOO follow-ups
        scheduled_count = self.process_scheduled_followups(dry_run=dry_run)
        
        print(f"\n✅ Follow-up cycle complete!")
        print(f"   Regular follow-ups: {sent_count}")
        print(f"   Scheduled follow-ups: {scheduled_count}")
        print(f"   Total: {sent_count + scheduled_count}")

# Singleton
_scheduler_instance = None

def get_followup_scheduler():
    """Get singleton follow-up scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = FollowUpScheduler()
    return _scheduler_instance

# CLI
if __name__ == '__main__':
    import sys
    
    scheduler = get_followup_scheduler()
    
    dry_run = '--dry-run' in sys.argv or '--test' in sys.argv
    scheduler.run_followup_cycle(dry_run=dry_run)
