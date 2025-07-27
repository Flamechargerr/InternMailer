#!/usr/bin/env python3
"""
Simple test email script to verify email functionality before bulk mailing
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_sender import GmailSender

def test_single_email():
    """Test sending a single email to the user"""
    load_dotenv()
    
    # Get credentials
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("❌ Missing email credentials in .env file")
        print("Please ensure GMAIL_USER and GMAIL_APP_PASSWORD are set")
        return False
    
    print(f"📧 Testing email functionality...")
    print(f"From: {gmail_user}")
    print(f"To: {gmail_user} (sending to self)")
    
    # Initialize sender
    try:
        sender = GmailSender(gmail_user, gmail_password)
        print("✅ Gmail sender initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Gmail sender: {e}")
        return False
    
    # Compose test email
    subject = "🚀 InternMailer Test Email"
    body = """
Dear Anamay,

This is a test email from InternMailer to verify the email sending functionality is working correctly.

If you receive this email, the system is ready for bulk mailing to professors.

Best regards,
InternMailer System

---
Test conducted on: 2025-07-27
System: InternMailer v1.0
"""
    
    # Send email
    try:
        print("📤 Sending test email...")
        success = sender.send_email(
            to_email=gmail_user,  # Send to self
            subject=subject,
            body=body,
            attachment_path=None  # No attachment for test
        )
        
        if success:
            print("✅ Test email sent successfully!")
            print("🔍 Please check your inbox/spam folder")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False

if __name__ == "__main__":
    print("🚀 InternMailer Email Test")
    print("=" * 40)
    
    success = test_single_email()
    
    if success:
        print("\n✅ Email test PASSED - Ready for bulk mailing!")
        print("💡 You can now run the main Streamlit app safely")
    else:
        print("\n❌ Email test FAILED - Please fix configuration before bulk mailing")
        print("💡 Check your .env file and Gmail App Password")
    
    print("=" * 40)
