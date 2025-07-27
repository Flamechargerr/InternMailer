"""
Email sending module with Gmail API integration and rate limiting
"""
import os
import time
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict
import schedule
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

class EmailSender:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/gmail.send',
                      'https://www.googleapis.com/auth/gmail.compose']
        self.service = None
        self.rate_limit_delay = 180  # 20 emails per hour = 180 seconds between emails
        self.max_retries = 3
        self.circuit_breaker_threshold = 5
        self.error_count = 0
        self.last_reset_time = time.time()
        
        # Initialize Gmail service
        self._authenticate_gmail()
        
        # Setup logging
        self.log_file = 'send_log.csv'
        self._setup_logging()
    
    def _authenticate_gmail(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Check if we have stored credentials
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                # For production, you would set up OAuth flow properly
                print("Gmail authentication required. Please set up OAuth credentials.")
                print("For demo purposes, using mock authentication.")
                return
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print("Gmail API authenticated successfully")
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            self.service = None
    
    def _setup_logging(self):
        """Setup CSV logging for sent emails"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'to', 'name', 'subject', 'status', 'match_score', 'error'])
    
    def _log_email(self, email_info: Dict, status: str, error: str = ""):
        """Log email sending attempt"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                email_info.get('to', ''),
                email_info.get('name', ''),
                email_info.get('subject', ''),
                status,
                email_info.get('match_score', 0),
                error
            ])
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should trip"""
        current_time = time.time()
        
        # Reset error count every hour
        if current_time - self.last_reset_time > 3600:
            self.error_count = 0
            self.last_reset_time = current_time
        
        return self.error_count < self.circuit_breaker_threshold
    
    def _send_single_email(self, draft_info: Dict) -> Dict:
        """Send a single email with retry logic"""
        if not self._check_circuit_breaker():
            error_msg = "Circuit breaker tripped - too many errors"
            self._log_email(draft_info, 'failed', error_msg)
            return {'status': 'failed', 'error': error_msg}
        
        for attempt in range(self.max_retries):
            try:
                if not self.service:
                    # Mock sending for demo purposes
                    print(f"MOCK: Sending email to {draft_info.get('to')}")
                    print(f"Subject: {draft_info.get('subject')}")
                    self._log_email(draft_info, 'sent (mock)')
                    return {'status': 'sent', 'method': 'mock'}
                
                # Send the actual email using Gmail API
                draft_payload = draft_info.get('draft_payload', {})
                
                message = self.service.users().messages().send(
                    userId='me',
                    body=draft_payload
                ).execute()
                
                print(f"✓ Email sent to {draft_info.get('name')} ({draft_info.get('to')})")
                self._log_email(draft_info, 'sent')
                
                return {
                    'status': 'sent',
                    'message_id': message.get('id'),
                    'to': draft_info.get('to'),
                    'name': draft_info.get('name'),
                    'match_score': draft_info.get('match_score')
                }
                
            except HttpError as e:
                error_msg = f"Gmail API error: {e}"
                print(f"Attempt {attempt + 1} failed for {draft_info.get('to')}: {error_msg}")
                
                if attempt == self.max_retries - 1:
                    self.error_count += 1
                    self._log_email(draft_info, 'failed', error_msg)
                    return {'status': 'failed', 'error': error_msg}
                
                # Exponential backoff
                time.sleep(2 ** attempt)
                
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                print(f"Attempt {attempt + 1} failed for {draft_info.get('to')}: {error_msg}")
                
                if attempt == self.max_retries - 1:
                    self.error_count += 1
                    self._log_email(draft_info, 'failed', error_msg)
                    return {'status': 'failed', 'error': error_msg}
                
                time.sleep(2 ** attempt)
        
        return {'status': 'failed', 'error': 'Max retries exceeded'}
    
    def _schedule_follow_ups(self, email_info: Dict):
        """Schedule follow-up emails"""
        try:
            # Schedule follow-up at +7 days
            follow_up_1_date = datetime.now() + timedelta(days=7)
            follow_up_2_date = datetime.now() + timedelta(days=14)
            
            # For demo purposes, just log the scheduled follow-ups
            print(f"Follow-up 1 scheduled for {follow_up_1_date.strftime('%Y-%m-%d')} to {email_info.get('name')}")
            print(f"Follow-up 2 scheduled for {follow_up_2_date.strftime('%Y-%m-%d')} to {email_info.get('name')}")
            
            # In production, you would integrate with a task scheduler like Celery
            # or use Google Calendar API to set reminders
            
        except Exception as e:
            print(f"Error scheduling follow-ups for {email_info.get('name')}: {e}")

def send_emails(drafts: List[Dict]) -> List[Dict]:
    """
    Send emails with rate limiting and error handling
    Returns list of send results
    """
    sender = EmailSender()
    results = []
    
    print(f"Sending {len(drafts)} emails with rate limiting...")
    
    for i, draft in enumerate(drafts):
        try:
            print(f"\nSending email {i+1}/{len(drafts)} to {draft.get('name', 'Unknown')}")
            
            # Send the email
            result = sender._send_single_email(draft)
            results.append(result)
            
            # Schedule follow-ups if email was sent successfully
            if result.get('status') == 'sent':
                sender._schedule_follow_ups(draft)
            
            # Rate limiting - wait between emails (except for the last one)
            if i < len(drafts) - 1:
                print(f"Rate limiting: waiting {sender.rate_limit_delay} seconds...")
                time.sleep(sender.rate_limit_delay)
            
        except Exception as e:
            error_msg = f"Error sending email to {draft.get('name', 'Unknown')}: {e}"
            print(error_msg)
            
            result = {'status': 'failed', 'error': error_msg}
            results.append(result)
            sender._log_email(draft, 'failed', error_msg)
    
    # Summary
    sent_count = sum(1 for r in results if r.get('status') == 'sent')
    failed_count = len(results) - sent_count
    
    print(f"\n📧 Email Campaign Summary:")
    print(f"✓ Sent: {sent_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"📊 Success rate: {(sent_count/len(results)*100):.1f}%")
    print(f"📝 Detailed logs saved to: {sender.log_file}")
    
    return results

def get_send_log() -> List[Dict]:
    """Read and return the send log as a list of dictionaries"""
    try:
        with open('send_log.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        return []

# For testing
if __name__ == "__main__":
    # Test with sample draft data
    sample_drafts = [
        {
            'to': 'test1@university.edu',
            'name': 'Dr. Test Professor 1',
            'subject': 'Research Internship Opportunity',
            'body': 'Sample email body...',
            'match_score': 0.75,
            'draft_payload': {'message': {'raw': 'base64_encoded_message'}}
        },
        {
            'to': 'test2@university.edu',
            'name': 'Dr. Test Professor 2',
            'subject': 'Winter Internship Application',
            'body': 'Another sample email body...',
            'match_score': 0.65,
            'draft_payload': {'message': {'raw': 'base64_encoded_message'}}
        }
    ]
    
    results = send_emails(sample_drafts)
    print(f"Test completed. Results: {len(results)} emails processed")
