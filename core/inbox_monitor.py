"""
InternMailer - Inbox Monitor
Automatically checks Gmail inbox for replies and classifies them
"""

import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Tuple
from core.reply_classifier import get_reply_classifier
from utils.config import config

class InboxMonitor:
    """
    Monitors Gmail inbox for replies to sent emails
    Uses IMAP to connect and process emails
    """
    
    def __init__(self, db_path='/tmp/internmailer_db/inbox_monitor.db'):
        self.db_path = db_path
        self.email_address = config.EMAIL_ADDRESS
        self.password = config.EMAIL_PASSWORD  # Gmail app password
        self.imap_server = 'imap.gmail.com'
        self.imap_port = 993
        self.classifier = get_reply_classifier()
        self._setup_database()
    
    def _setup_database(self):
        """Create database for tracking processed replies"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Track processed replies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_replies (
                message_id TEXT PRIMARY KEY,
                from_email TEXT,
                to_list TEXT,
                cc_list TEXT,
                subject TEXT,
                category TEXT,
                confidence REAL,
                sentiment REAL,
                received_date TEXT,
                processed_date TEXT,
                action_taken TEXT
            )
        ''')
        
        # Migration: Check if to_list column exists, add if not
        try:
            cursor.execute("SELECT to_list FROM processed_replies LIMIT 1")
        except sqlite3.OperationalError:
            print("📦 Upgrading database schema (adding to_list column)...")
            try:
                cursor.execute("ALTER TABLE processed_replies ADD COLUMN to_list TEXT")
            except Exception as e:
                print(f"⚠️ Migration warning: {e}")

        # Migration: Check if cc_list column exists, add if not
        try:
            cursor.execute("SELECT cc_list FROM processed_replies LIMIT 1")
        except sqlite3.OperationalError:
            print("📦 Upgrading database schema (adding cc_list column)...")
            try:
                cursor.execute("ALTER TABLE processed_replies ADD COLUMN cc_list TEXT")
            except Exception as e:
                print(f"⚠️ Migration warning: {e}")
        
        # Priority contacts (interested replies)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS priority_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                name TEXT,
                replied_date TEXT,
                interest_level TEXT,
                calendar_sent BOOLEAN DEFAULT 0,
                notes TEXT,
                message_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail via IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.password)
            return mail
        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            print(f"   Make sure you've created a Gmail App Password!")
            raise
    
    def get_unprocessed_replies(self, mail: imaplib.IMAP4_SSL, days_back: int = 7) -> List[Dict]:
        """
        Get unprocessed email replies from inbox
        
        Args:
            mail: IMAP connection
            days_back: How many days back to check
        
        Returns:
            List of email dictionaries
        """
        mail.select('INBOX')
        
        # Search for recent emails (both read and unread) to ensure we don't miss anything
        # (Database check prevents duplicates)
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        
        print(f"   Searching emails since {cutoff_date}...")
        status, messages = mail.search(None, f'(SINCE "{cutoff_date}")')
        
        if status != 'OK':
            print("No messages found")
            return []
        
        email_ids = messages[0].split()
        emails = []
        
        for email_id in email_ids:
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract details
                message_id = msg.get('Message-ID', '')
                from_email = self._extract_email(msg.get('From', ''))
                to_header = msg.get('To', '')
                to_list = self._extract_email_list(to_header)
                cc_header = msg.get('Cc', '')
                cc_list = self._extract_email_list(cc_header)
                subject = self._decode_subject(msg.get('Subject', ''))
                date = msg.get('Date', '')
                
                # Check if already processed
                if self._is_processed(message_id):
                    continue
                
                # Extract body
                body = self._get_email_body(msg)
                
                emails.append({
                    'message_id': message_id,
                    'from': from_email,
                    'to': to_list,
                    'cc': cc_list,
                    'subject': subject,
                    'date': date,
                    'body': body,
                    'email_id': email_id.decode()
                })
                
            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
                continue
        
        return emails
    
    def _extract_email_list(self, header: str) -> str:
        """Extract comma-separated list of emails from header"""
        if not header:
            return ""
        
        emails = []
        # Split by comma (naive but works for most)
        parts = header.split(',')
        for part in parts:
            email_addr = self._extract_email(part.strip())
            if email_addr:
                emails.append(email_addr)
        
        return ",".join(emails)
        
        return emails
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        if '<' in from_header and '>' in from_header:
            return from_header.split('<')[1].split('>')[0]
        return from_header
    
    def _decode_subject(self, subject: str) -> str:
        """Decode email subject"""
        decoded_parts = decode_header(subject)
        decoded_subject = ''
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_subject += part.decode(encoding or 'utf-8')
            else:
                decoded_subject += part
        return decoded_subject
    
    def _get_email_body(self, msg) -> str:
        """Extract email body (plain text preferred)"""
        body = ''
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                body = str(msg.get_payload())
        
        return body
    
    def _is_processed(self, message_id: str) -> bool:
        """Check if email was already processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_replies WHERE message_id = ?", (message_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def classify_and_store(self, email_data: Dict) -> Dict:
        """
        Classify email reply and store result
        
        Returns:
            Classification result with action recommendation
        """
        # Classify the reply
        result = self.classifier.classify_reply(
            email_data['body'],
            email_data['subject']
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processed_replies
            (message_id, from_email, to_list, cc_list, subject, category, confidence, sentiment, received_date, processed_date, action_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email_data['message_id'],
            email_data['from'],
            email_data.get('to', ''),
            email_data.get('cc', ''),
            email_data['subject'],
            result['category'].value,
            result['confidence'],
            result['sentiment'],
            email_data['date'],
            datetime.now().isoformat(),
            'pending'
        ))
        
        conn.commit()
        conn.close()
        
        return {
            **email_data,
            'classification': result
        }
    
    def check_inbox(self, dry_run: bool = False) -> List[Dict]:
        """
        Main method - check inbox for new replies
        
        Args:
            dry_run: If True, don't mark emails as read
        
        Returns:
            List of classified emails with recommended actions
        """
        print("📬 Checking Gmail inbox...")
        
        try:
            mail = self.connect_imap()
            print(f"✅ Connected to {self.email_address}")
            
            # Get unprocessed replies
            emails = self.get_unprocessed_replies(mail)
            print(f"📧 Found {len(emails)} unread emails")
            
            if not emails:
                mail.logout()
                return []
            
            # Classify each email
            classified_emails = []
            for email_data in emails:
                print(f"\n📨 Processing: {email_data['subject'][:50]}...")
                print(f"   From: {email_data['from']}")
                
                result = self.classify_and_store(email_data)
                classified_emails.append(result)
                
                category = result['classification']['category'].value
                confidence = result['classification']['confidence']
                action = result['classification']['suggested_action']
                
                print(f"   ✅ Category: {category.upper()} (confidence: {confidence:.0%})")
                print(f"   📋 Action: {action}")
            
            mail.logout()
            return classified_emails
            
        except Exception as e:
            print(f"❌ Error checking inbox: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get statistics on processed replies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM processed_replies")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM processed_replies GROUP BY category")
        by_category = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM priority_contacts")
        priority_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_processed': total,
            'by_category': by_category,
            'priority_contacts': priority_count
        }

# Singleton instance
_monitor_instance = None

def get_inbox_monitor():
    """Get singleton inbox monitor"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = InboxMonitor(db_path=config.INBOX_DB_PATH)
    return _monitor_instance

# CLI
if __name__ == '__main__':
    import sys
    
    monitor = get_inbox_monitor()
    
    if '--dry-run' in sys.argv or '--test' in sys.argv:
        print("🧪 DRY RUN MODE - Will not take actions\n")
        results = monitor.check_inbox(dry_run=True)
    else:
        results = monitor.check_inbox()
    
    print(f"\n📊 Processing Complete!")
    stats = monitor.get_stats()
    print(f"   Total processed: {stats['total_processed']}")
    print(f"   Priority contacts: {stats['priority_contacts']}")
    print(f"   By category: {stats['by_category']}")
