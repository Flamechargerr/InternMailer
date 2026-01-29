"""
InternMailer - Auto-Action Engine
Takes automated actions based on reply classifications
"""

import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

class AutoActionEngine:
    """
    Automatically performs actions based on reply classifications
    - Send calendar links to interested parties
    - Archive rejections
    - Schedule follow-ups for OOO
    - Flag questions for manual review
    """
    
    def __init__(self, inbox_db='campaign_results/inbox_monitor.db'):
        self.inbox_db = inbox_db
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
    
    def get_pending_actions(self) -> List[Dict]:
        """Get all replies that need actions"""
        conn = sqlite3.connect(self.inbox_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_id, from_email, subject, category, confidence, cc_list, to_list
            FROM processed_replies
            WHERE action_taken = 'pending'
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'message_id': row[0],
                'email': row[1],
                'subject': row[2],
                'category': row[3],
                'confidence': row[4],
                'cc_list': row[5] if len(row) > 5 else '',
                'to_list': row[6] if len(row) > 6 else ''
            })
        
        conn.close()
        return results
    
    def process_interested_reply(self, reply: Dict) -> bool:
        """
        Handle INTERESTED reply:
        1. Add to priority contacts
        2. Send calendar link
        """
        try:
            # Add to priority contacts
            conn = sqlite3.connect(self.inbox_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO priority_contacts
                (email, name, replied_date, interest_level, message_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                reply['email'],
                reply['email'].split('@')[0],  # Extract name from email
                datetime.now().isoformat(),
                'high',
                reply['message_id']
            ))
            
            conn.commit()
            conn.close()
            
            # Send calendar link
            self._send_calendar_email(reply['email'], reply['subject'])
            
            print(f"   ✅ INTERESTED: Added {reply['email']} to priority list + sent calendar")
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing interested reply: {e}")
            return False
    
    def process_not_interested_reply(self, reply: Dict) -> bool:
        """
        Handle NOT_INTERESTED reply:
        1. Add to unsubscribe list
        2. Mark as closed
        """
        try:
            # Add to unsubscribe/blacklist
            conn = sqlite3.connect('email_tracking.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unsubscribed (
                    email TEXT PRIMARY KEY,
                    reason TEXT,
                    date TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO unsubscribed (email, reason, date)
                VALUES (?, ?, ?)
            ''', (reply['email'], 'not_interested', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            print(f"   📭 NOT INTERESTED: Unsubscribed {reply['email']}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing not interested: {e}")
            return False
    
    def process_question_reply(self, reply: Dict) -> bool:
        """
        Handle QUESTION reply:
        1. Flag for manual review
        2. Log to review queue
        """
        try:
            conn = sqlite3.connect(self.inbox_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    subject TEXT,
                    category TEXT,
                    added_date TEXT,
                    reviewed BOOLEAN DEFAULT 0,
                    message_id TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT INTO review_queue (email, subject, category, added_date, message_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (reply['email'], reply['subject'], 'question', datetime.now().isoformat(), reply['message_id']))
            
            conn.commit()
            conn.close()
            
            print(f"   ❓ QUESTION: Flagged {reply['email']} for manual review")
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing question: {e}")
            return False
    
    def process_out_of_office_reply(self, reply: Dict) -> bool:
        """
        Handle OUT_OF_OFFICE reply:
        1. Schedule follow-up in 14 days
        """
        try:
            conn = sqlite3.connect(self.inbox_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS followup_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    original_subject TEXT,
                    scheduled_date TEXT,
                    sent BOOLEAN DEFAULT 0,
                    message_id TEXT
                )
            ''')
            
            followup_date = (datetime.now() + timedelta(days=14)).isoformat()
            
            cursor.execute('''
                INSERT INTO followup_queue (email, original_subject, scheduled_date, message_id)
                VALUES (?, ?, ?, ?)
            ''', (reply['email'], reply['subject'], followup_date, reply['message_id']))
            
            conn.commit()
            conn.close()
            
            print(f"   ⏰ OUT OF OFFICE: Follow-up scheduled for {reply['email']} in 14 days")
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing out of office: {e}")
            return False
    
    def process_referral_reply(self, reply: Dict) -> bool:
        """
        Handle REFERRAL reply:
        1. Reply to All (Sender + CC + Others in To)
        2. Introduce self to new contact
        """
        try:
            # Send Reply All
            self._reply_to_all(
                reply['email'], 
                reply.get('to_list', ''), 
                reply.get('cc_list', ''), 
                reply['subject']
            )
            
            print(f"   🔄 REFERRAL: Replied to all (Subject: {reply['subject']})")
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing referral: {e}")
            return False

    def _reply_to_all(self, from_email: str, to_list_str: str, cc_list_str: str, original_subject: str):
        """Send Reply All email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Re: {original_subject}" if not original_subject.lower().startswith('re:') else original_subject
            msg['From'] = self.email_address
            
            # Construct To list: Sender + (Original To - Me)
            to_emails = [from_email]
            if to_list_str:
                others = [e.strip() for e in to_list_str.split(',') if e.strip()]
                for email in others:
                    if email.lower() != self.email_address.lower() and email.lower() != from_email.lower():
                        to_emails.append(email)
            
            msg['To'] = ", ".join(to_emails)
            
            # Construct CC list
            cc_emails = []
            if cc_list_str:
                cc_emails = [e.strip() for e in cc_list_str.split(',') if e.strip()]
                msg['Cc'] = ", ".join(cc_emails)
            
            recipients = to_emails + cc_emails
            
            body = f"""Dear All,

Thank you for the response and the introduction.

I am excited to connect and would love to learn more about the team's work. The transition from research to real-world applications is exactly where my interest lies.

I have attached my details below. I would welcome the opportunity for a brief conversation to discuss how I might contribute.

Best regards,
Anamay Tripathy
B.Tech Data Science Engineering, MIT Manipal
https://anamay.vercel.app
"""
            
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Send via SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_address, self.password)
                server.send_message(msg)
            
        except Exception as e:
            print(f"   ❌ Failed to send reply-all email: {e}")
            raise e

    def _send_calendar_email(self, to_email: str, original_subject: str):
        """Send calendar link to interested party"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Re: {original_subject}"
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            body = f"""Hi,

Thank you for your interest! I'd love to discuss this opportunity further.

You can schedule a convenient time here: [Your Calendar Link]

Or let me know your availability and I'll send you a time.

Best regards,
Anamay Tripathy
"""
            
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Send via SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_address, self.password)
                server.send_message(msg)
            
        except Exception as e:
            print(f"   ❌ Failed to send calendar email: {e}")
    
    def mark_action_taken(self, message_id: str, action: str):
        """Mark reply as actioned"""
        conn = sqlite3.connect(self.inbox_db)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE processed_replies
            SET action_taken = ?
            WHERE message_id = ?
        ''', (action, message_id))
        conn.commit()
        conn.close()
    
    def process_all_pending(self, dry_run: bool = False) -> Dict:
        """
        Process all pending actions
        
        Returns:
            Statistics of actions taken
        """
        print("\n🤖 Processing pending actions...")
        
        pending = self.get_pending_actions()
        print(f"   Found {len(pending)} pending actions")
        
        if dry_run:
            print("   🧪 DRY RUN MODE - No actions will be taken\n")
        
        stats = {
            'interested': 0,
            'not_interested': 0,
            'question': 0,
            'out_of_office': 0,
            'referral': 0,
            'other': 0
        }
        
        for reply in pending:
            category = reply['category']
            
            if dry_run:
                print(f"   [DRY RUN] Would process {category} from {reply['email']}")
                continue
            
            success = False
            
            if category == 'interested':
                success = self.process_interested_reply(reply)
                stats['interested'] += 1
            elif category == 'not_interested':
                success = self.process_not_interested_reply(reply)
                stats['not_interested'] += 1
            elif category == 'question':
                success = self.process_question_reply(reply)
                stats['question'] += 1
            elif category == 'out_of_office':
                success = self.process_out_of_office_reply(reply)
                stats['out_of_office'] += 1
            elif category == 'referral':
                success = self.process_referral_reply(reply)
                stats['referral'] += 1
            else:
                stats['other'] += 1
            
            if success:
                self.mark_action_taken(reply['message_id'], category)
        
        return stats

# Singleton
_engine_instance = None

def get_auto_action_engine():
    """Get singleton auto-action engine"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AutoActionEngine()
    return _engine_instance

# CLI
if __name__ == '__main__':
    import sys
    
    engine = get_auto_action_engine()
    
    dry_run = '--dry-run' in sys.argv or '--test' in sys.argv
    
    if dry_run:
        print("🧪 DRY RUN MODE\n")
    
    stats = engine.process_all_pending(dry_run=dry_run)
    
    print("\n✅ Actions processed!")
    print(f"   Interested: {stats['interested']}")
    print(f"   Not interested: {stats['not_interested']}")
    print(f"   Questions: {stats['question']}")
    print(f"   Out of office: {stats['out_of_office']}")
    print(f"   Other: {stats['other']}")
