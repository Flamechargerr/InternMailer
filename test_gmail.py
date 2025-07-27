#!/usr/bin/env python3
"""
Quick Gmail Test Script
Test Gmail credentials before running the full app
"""

import os
import sys
from dotenv import load_dotenv
sys.path.append('InternMailer/src')
from gmail_sender import GmailSender

def test_gmail_connection():
    """Test Gmail connection and send a test email"""
    load_dotenv()
    
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    print("🧪 Testing Gmail Configuration...")
    print(f"📧 Gmail User: {gmail_user}")
    print(f"🔑 Gmail Password: {'*' * len(gmail_password) if gmail_password else 'NOT SET'}")
    
    if not gmail_user or not gmail_password:
        print("❌ Gmail credentials not configured in .env file")
        return False
    
    try:
        # Initialize Gmail sender
        sender = GmailSender(gmail_user, gmail_password)
        
        # Send test email to yourself
        print("📤 Sending test email...")
        success = sender.send_test_email(gmail_user)
        
        if success:
            print("✅ Test email sent successfully!")
            print(f"📬 Check your inbox at {gmail_user}")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gmail: {e}")
        return False

if __name__ == "__main__":
    print("🚀 InternMailer Gmail Test")
    print("=" * 40)
    
    success = test_gmail_connection()
    
    if success:
        print("\n🎉 Gmail configuration is working!")
        print("✅ Ready to proceed with bulk email sending")
        print("💡 Run 'python start_secure.py' to start the full app")
    else:
        print("\n⚠️ Gmail configuration needs to be fixed")
        print("📋 Steps to fix:")
        print("1. Go to https://myaccount.google.com/")
        print("2. Security → App passwords")
        print("3. Generate new app password for 'Mail'")
        print("4. Update GMAIL_APP_PASSWORD in .env file")
        print("5. Run this test script again")
