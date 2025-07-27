"""
Simplified Gmail authentication helper
"""
import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GmailAuthHelper:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        self.creds = None
        self.service = None
    
    def create_credentials_file(self, client_id, client_secret):
        """Create credentials.json file for OAuth"""
        credentials = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080"]
            }
        }
        
        with open('credentials.json', 'w') as f:
            json.dump(credentials, f)
        
        return 'credentials.json'
    
    def authenticate_desktop_flow(self, client_id, client_secret):
        """Authenticate using desktop application flow"""
        try:
            # Create credentials file
            creds_file = self.create_credentials_file(client_id, client_secret)
            
            # Check if token.json exists
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=8080)
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def create_message_with_attachment(self, to, subject, body, attachment_data, attachment_filename):
        """Create email message with attachment"""
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        # Add body
        message.attach(MIMEText(body, 'plain'))
        
        # Add attachment
        if attachment_data:
            attachment = MIMEApplication(attachment_data)
            attachment.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
            message.attach(attachment)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_message}
    
    def send_email(self, to, subject, body, attachment_data=None, attachment_filename=None):
        """Send email"""
        try:
            message = self.create_message_with_attachment(to, subject, body, attachment_data, attachment_filename)
            
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            return {'status': 'sent', 'message_id': result['id']}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

def authenticate_gmail():
    """Standalone function for Gmail authentication - for backward compatibility"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("Missing Gmail credentials in environment variables")
            return None
        
        auth = GmailAuthHelper()
        if auth.authenticate_desktop_flow(client_id, client_secret):
            return auth.service
        else:
            return None
            
    except Exception as e:
        print(f"Gmail authentication error: {e}")
        return None

# Usage example
if __name__ == "__main__":
    auth = GmailAuthHelper()
    
    # Test authentication
    client_id = "your_client_id"
    client_secret = "your_client_secret"
    
    if auth.authenticate_desktop_flow(client_id, client_secret):
        print("✅ Authentication successful!")
        
        # Test sending email
        result = auth.send_email(
            to="test@example.com",
            subject="Test Email",
            body="This is a test email from InternMailer!"
        )
        print(f"Send result: {result}")
    else:
        print("❌ Authentication failed")
