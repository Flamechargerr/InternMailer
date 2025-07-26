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
        self.last_send_time = 0
        self.min_delay = 2  # Minimum delay between emails (seconds)
        load_dotenv()
        
        # Create log file with headers if it doesn't exist
        if not os.path.exists(log_path):
            with open(log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Email', 'Subject', 'Status', 'Timestamp', 'Error'])

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

    def _rate_limit(self):
        """Enforce rate limiting between emails"""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logging.info(f"Rate limiting: waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_send_time = time.time()

    def send_email(self, to_email: str, subject: str, body: str, attachment_path: str = None) -> bool:
        """Send email with rate limiting and better error handling"""
        # Validate credentials first
        if not self.user or not self.app_password:
            error_msg = "Gmail credentials not configured"
            logging.error(error_msg)
            self.log_status(to_email, subject, 'config_error', error_msg)
            return False
            
        # Validate email before sending
        if not self.validate_email(to_email):
            error_msg = f"Invalid email address: {to_email}"
            logging.error(error_msg)
            self.log_status(to_email, subject, 'invalid_email', error_msg)
            return False

        # Apply rate limiting
        self._rate_limit()
            
        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Handle attachment
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)
            except Exception as e:
                error_msg = f"Failed to attach file: {e}"
                logging.error(error_msg)
                self.log_status(to_email, subject, 'attachment_error', error_msg)
                return False
        
        # Send email with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=self.context, timeout=30) as server:
                    server.login(self.user, self.app_password)
                    server.send_message(msg)
                logging.info(f"Email sent to {to_email}")
                self.log_status(to_email, subject, 'sent')
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"Gmail authentication failed: {e}"
                logging.error(error_msg)
                self.log_status(to_email, subject, 'auth_error', error_msg)
                return False  # Don't retry auth errors
                
            except (smtplib.SMTPRecipientsRefused, smtplib.SMTPServerDisconnected) as e:
                error_msg = f"SMTP error (attempt {attempt + 1}/{max_retries}): {e}"
                logging.warning(error_msg)
                if attempt == max_retries - 1:
                    self.log_status(to_email, subject, 'smtp_error', error_msg)
                    return False
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                logging.error(error_msg)
                if attempt == max_retries - 1:
                    self.log_status(to_email, subject, 'failed', error_msg)
                    return False
                time.sleep(1)
        
        return False

    def log_status(self, to_email: str, subject: str, status: str, error: str = ''):
        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([to_email, subject, status, time.strftime('%Y-%m-%d %H:%M:%S'), error])

    def send_bulk(self, emails: List[Dict[str, Any]], attachment_path: str = None):
        for email in emails:
            sent = self.send_email(email['to'], email['subject'], email['body'], attachment_path)
            wait_time = random.randint(60, 120)
            if sent:
                logging.info(f"Waiting {wait_time}s before next email...")
                time.sleep(wait_time)

# TODO: Add unit tests for GmailSender 