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
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FollowUpScheduler:
    """
    Automatically sends follow-up emails to:
    - Contacts who haven't replied after 7 days
    - Out-of-office contacts after 14 days
    Maximum 1 follow-up per contact
    """
    
    def __init__(self):
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.tracking_db = 'email_tracking.db'
        self.inbox_db = 'campaign_results/inbox_monitor.db'
        self.followup_delay_days = 7
        self.max_followups = 1
    
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
            
            body = f"""Hi {contact['name']},

I wanted to follow up on my previous email about internship/research opportunities.

I'm very interested in your work and would love to discuss potential collaboration.

Would you have 10-15 minutes for a brief call this week?

Best regards,
Anamay Tripathy
"""
            
            if dry_run:
                logger.info("[DRY RUN] Would send follow-up to %s", contact['email'])
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
            
            logger.info("Follow-up sent to %s", contact['email'])
            return True
            
        except Exception as e:
            logger.exception("Failed to send follow-up to %s", contact.get('email', 'unknown'))
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
            
            logger.info("Processing %s scheduled follow-ups", len(due_followups))
            
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
            logger.exception("Error processing scheduled follow-ups")
            return 0
    
    def run_followup_cycle(self, dry_run: bool = False):
        """
        Complete follow-up cycle:
        1. Send follow-ups to no-reply contacts
        2. Send scheduled OOO follow-ups
        """
        logger.info("Starting follow-up cycle")
        
        if dry_run:
            logger.info("DRY RUN MODE - No emails will be sent")
        
        # Regular follow-ups (no reply after 7 days)
        contacts_needing_followup = self.get_emails_needing_followup()
        logger.info("Found %s contacts needing follow-up", len(contacts_needing_followup))
        
        sent_count = 0
        for contact in contacts_needing_followup:
            if self.send_followup(contact, dry_run=dry_run):
                sent_count += 1
        
        # Scheduled OOO follow-ups
        scheduled_count = self.process_scheduled_followups(dry_run=dry_run)
        
        logger.info("Follow-up cycle complete")
        logger.info("Regular follow-ups: %s", sent_count)
        logger.info("Scheduled follow-ups: %s", scheduled_count)
        logger.info("Total follow-ups: %s", sent_count + scheduled_count)

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
