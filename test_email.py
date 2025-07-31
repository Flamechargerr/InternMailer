#!/usr/bin/env python3
"""
Test script to send a professional test email to verify the InternMailer system.
This sends a realistic professor-style email to test the system functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_sender import GmailSender

def send_test_email():
    """Send a professional test email that mimics what would be sent to professors."""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("Error: Gmail credentials not found in .env file")
        return False
    
    # Initialize Gmail sender
    sender = GmailSender(gmail_user, gmail_password)
    
    # Test email details - professional format similar to professor outreach
    to_email = "tripathy.anamay23@gmail.com"
    subject = "[TEST] InternMailer System Verification - Research Internship Inquiry"
    
    # Professional email body that mimics what would be sent to professors
    body = """
    <html>
    <body>
        <p>Dear System Administrator,</p>
        
        <p>This is a <strong>test message</strong> from the InternMailer system to verify that email functionality is working correctly.</p>
        
        <p>This test email simulates the format and content that would typically be sent to professors for research internship inquiries. The system includes:</p>
        
        <ul>
            <li>✅ SMTP connection to Gmail</li>
            <li>✅ HTML email formatting</li>
            <li>✅ Professional email structure</li>
            <li>✅ Rate limiting functionality</li>
            <li>✅ Error handling and logging</li>
        </ul>
        
        <p>If you receive this email, the InternMailer system is functioning properly and ready to send actual outreach emails to professors.</p>
        
        <p><strong>Test Details:</strong></p>
        <ul>
            <li>Sender: {sender_email}</li>
            <li>System: InternMailer v1.0</li>
            <li>Timestamp: Auto-generated</li>
            <li>Purpose: System functionality verification</li>
        </ul>
        
        <p>Best regards,<br>
        <strong>InternMailer System</strong><br>
        Automated Email Testing Service</p>
        
        <hr>
        <p><small><em>This is an automated test message. The actual emails sent to professors will contain personalized content based on research interests and background matching.</em></small></p>
    </body>
    </html>
    """.format(sender_email=gmail_user)
    
    print("🚀 Sending test email to verify InternMailer system...")
    print(f"📧 To: {to_email}")
    print(f"📝 Subject: {subject}")
    print("⏳ Please wait...")
    
    # Send the test email
    success = sender.send_email(to_email, subject, body, is_html=True)
    
    if success:
        print("✅ SUCCESS: Test email sent successfully!")
        print("📨 Please check your inbox at tripathy.anamay23@gmail.com")
        print("🔍 The email should appear in your inbox shortly.")
        print("\n📋 If you received the email, your InternMailer system is ready to:")
        print("   • Send personalized emails to professors")
        print("   • Handle attachments (resumes/CVs)")
        print("   • Log email status and responses")
        print("   • Apply rate limiting for bulk sending")
    else:
        print("❌ FAILED: Could not send test email.")
        print("🔧 Please check:")
        print("   • Gmail credentials in .env file")
        print("   • App password is correct")
        print("   • Internet connection")
        print("   • Gmail account settings allow app passwords")
    
    return success

if __name__ == "__main__":
    print("🧪 InternMailer System Test")
    print("=" * 50)
    send_test_email()
