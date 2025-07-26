import os
import logging
import time
import random
import smtplib
import ssl
import csv
from typing import List, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

class GmailSender:
    """
    Sends personalized emails with attachments using Gmail API or SMTP.
    """
    def __init__(self, user: str, app_password: str, log_path: str = 'email_log.csv'):
        self.user = user
        self.app_password = app_password
        self.log_path = log_path
        self.context = ssl.create_default_context()
        load_dotenv()

    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email or not isinstance(email, str):
            return False
        if '@' not in email:
            return False
        parts = email.split('@')
        if len(parts) != 2:
            return False
        local, domain = parts
        if not local or not domain:
            return False
        if '.' not in domain:
            return False
        return True

    def send_email(self, to_email: str, subject: str, body: str, attachment_path: str = None) -> bool:
        # Validate email before sending
        if not self.validate_email(to_email):
            logging.error(f"Invalid email address: {to_email}")
            self.log_status(to_email, subject, 'invalid_email')
            return False
            
        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        if attachment_path:
            try:
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)
            except Exception as e:
                logging.error(f"Failed to attach file: {e}")
                return False
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=self.context) as server:
                server.login(self.user, self.app_password)
                server.send_message(msg)
            logging.info(f"Email sent to {to_email}")
            self.log_status(to_email, subject, 'sent')
            return True
        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {e}")
            self.log_status(to_email, subject, 'failed')
            return False

    def log_status(self, to_email: str, subject: str, status: str):
        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([to_email, subject, status, time.strftime('%Y-%m-%d %H:%M:%S')])

    def send_bulk(self, emails: List[Dict[str, Any]], attachment_path: str = None):
        for email in emails:
            sent = self.send_email(email['to'], email['subject'], email['body'], attachment_path)
            wait_time = random.randint(60, 120)
            if sent:
                logging.info(f"Waiting {wait_time}s before next email...")
                time.sleep(wait_time)

# TODO: Add unit tests for GmailSender 