
"""
Follow-up Manager 3000 🚀
Handles automated follow-ups by checking for replies via IMAP.
"""
import imaplib
import email
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import datetime
import time
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GMAIL_USER = os.getenv('EMAIL_ADDRESS')
GMAIL_PASS = os.getenv('EMAIL_PASSWORD')
DB_PATH = 'email_tracking.db'
FOLLOWUP_STATE_FILE = 'followup_state.json'

class FollowUpManager:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.imap = None
        self.smtp = None
        self.sent_emails = []
        self.replies = set()
        self.followup_state = self._load_state()

    def _load_state(self):
        if os.path.exists(FOLLOWUP_STATE_FILE):
            try:
                with open(FOLLOWUP_STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {'followed_up': []}
        return {'followed_up': []}

    def _save_state(self):
        with open(FOLLOWUP_STATE_FILE, 'w') as f:
            json.dump(self.followup_state, f)

    def connect_imap(self):
        print("🔌 Connecting to IMAP...")
        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap.login(GMAIL_USER, GMAIL_PASS)
            print("✅ IMAP Connected")
            return True
        except Exception as e:
            print(f"❌ IMAP Connection Failed: {e}")
            return False

    def load_sent_history(self):
        """Load emails sent > 3 days ago from DB"""
        print("📖 Loading sent history...")
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                # Get emails sent more than 3 days ago
                three_days_ago = (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat()
                c.execute("SELECT email, name, subject, date FROM sent_emails WHERE date < ?", (three_days_ago,))
                rows = c.fetchall()
                self.sent_emails = rows
                print(f"📋 Found {len(rows)} potential follow-up candidates (sent > 3 days ago)")
        except Exception as e:
            # Create DB if not exists (for testing first time)
            print(f"⚠️ Could not read DB: {e}")
            self.sent_emails = []

    def scan_for_replies(self):
        """Scan Inbox for replies from candidates"""
        if not self.imap: return

        print("🔍 Scanning Inbox for replies...")
        self.imap.select("INBOX")
        
        # We search specifically for emails FROM the people we sent to
        # Optimization: Search for ALL emails in last 30 days, then filter in python
        # searching one by one via IMAP is slow.
        
        date_cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%d-%b-%Y")
        status, messages = self.imap.search(None, f'(SINCE "{date_cutoff}")')
        
        if status != "OK":
            print("⚠️ No messages found")
            return

        email_ids = messages[0].split()
        print(f"📨 Processing {len(email_ids)} recent incoming emails...")
        
        for e_id in email_ids[-200:]: # Look at last 200 emails
            try:
                res, msg = self.imap.fetch(e_id, "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        try:
                            msg = email.message_from_bytes(response[1])
                            from_header = decode_header(msg["From"])[0]
                            sender = from_header[0]
                            if isinstance(sender, bytes):
                                sender = sender.decode()
                            
                            # Extract standardized email info
                            if "<" in sender:
                                sender_email = sender.split("<")[1].split(">")[0]
                            else:
                                sender_email = sender
                                
                            self.replies.add(sender_email.lower().strip())
                        except:
                            pass
            except:
                pass
        
        print(f"✅ Identifed replies from {len(self.replies)} unique contacts.")

    def process_followups(self):
        """Check candidates and send follow-ups if no reply"""
        print("\n🚀 PROCESSING FOLLOW-UPS\n" + "="*30)
        
        count = 0
        for row in self.sent_emails:
            cand_email = row[0].lower().strip()
            name = row[1]
            original_subject = row[2]
            
            # 1. Check if already followed up
            if cand_email in self.followup_state['followed_up']:
                continue
                
            # 2. Check if replied
            if cand_email in self.replies:
                print(f"🎉 {name} ({cand_email}) REPLIED! No follow-up needed.")
                continue
            
            # 3. Send Follow-up
            print(f"⏳ No reply from {name} ({cand_email}). Sending follow-up...")
            
            if not self.dry_run:
                if self.send_followup(cand_email, name, original_subject):
                    self.followup_state['followed_up'].append(cand_email)
                    self._save_state()
                    count += 1
                    time.sleep(random.uniform(30, 60)) # Human delay
            else:
                print(f"   [DRY RUN] Would send follow-up to {cand_email}")
                count += 1
        
        print(f"\n✅ Processed {count} follow-ups.")

    def send_followup(self, to_email, name, original_subject):
        try:
            # Reconstruct subject with "Re:" if not present
            subject = f"Re: {original_subject}" if not original_subject.lower().startswith("re:") else original_subject
            
            body = f"""Dear Professor {name.split()[-1] if ' ' in name else name},

I hope you're having a great week.

I'm writing to gently follow up on my previous email regarding a potential research internship. I remain deeply interested in your work and would be grateful for any opportunity to contribute to your group.

Thank you for your time and consideration.

Best regards,
Anamay Tripathy
"""
            msg = MIMEMultipart()
            msg['From'] = GMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect SMTP if needed
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(GMAIL_USER, GMAIL_PASS)
                server.send_message(msg)
                
            print(f"   ✅ FOLLOW-UP SENT to {to_email}")
            return True
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Check replies but DO NOT send emails')
    args = parser.parse_args()
    
    manager = FollowUpManager(dry_run=args.dry_run)
    if manager.connect_imap():
        manager.load_sent_history()
        manager.scan_for_replies()
        manager.process_followups()
