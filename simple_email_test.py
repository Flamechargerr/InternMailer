#!/usr/bin/env python3
"""
Simple Email Test - Direct Gmail SMTP Test
Tests Gmail SMTP functionality directly
"""

import os
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_gmail_connection():
    """Test Gmail SMTP connection and authentication"""
    print("🧪 Testing Gmail SMTP Connection")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("❌ Gmail credentials not found in .env file")
        print("Current .env variables:")
        print(f"   GMAIL_USER: {gmail_user}")
        print(f"   GMAIL_APP_PASSWORD: {'*' * len(gmail_password) if gmail_password else 'NOT SET'}")
        return False
    
    print(f"📧 Gmail User: {gmail_user}")
    print(f"🔐 Password: {'*' * len(gmail_password)}")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Test connection and authentication
        print("\n🔌 Connecting to Gmail SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=30) as server:
            print("✅ Connection established")
            
            print("🔐 Authenticating...")
            server.login(gmail_user, gmail_password)
            print("✅ Authentication successful!")
            
            # Create test email
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = gmail_user  # Send to self
            msg['Subject'] = "🧪 InternMailer Test Email - SMTP Working!"
            
            body = """
Hello!

This is a test email from InternMailer to verify that your Gmail SMTP configuration is working correctly.

✅ If you receive this email, your setup is successful!

Key details:
- Sent from: InternMailer Simple Test Script
- Gmail SMTP: Working
- Authentication: Successful

You can now use InternMailer to send personalized academic outreach emails.

Best regards,
InternMailer Team
"""
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"📤 Sending test email to {gmail_user}...")
            server.send_message(msg)
            print("✅ Test email sent successfully!")
            
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail authentication failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure you're using an App Password, not your regular Gmail password")
        print("2. Generate App Password: https://myaccount.google.com/apppasswords")
        print("3. Enable 2-factor authentication if not already enabled")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_gmail_connection()
    if success:
        print("\n🎉 Email functionality is working!")
        print("Next steps:")
        print("1. Run the main InternMailer app: cd InternMailer && streamlit run app.py")
        print("2. Upload your resume and start your outreach campaign")
    else:
        print("\n⚠️ Email setup needs attention. Please fix the issues above.")
    
    sys.exit(0 if success else 1)
