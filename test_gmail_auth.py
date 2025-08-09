#!/usr/bin/env python3
"""
Gmail Authentication Test Script
===============================
This script helps you test your Gmail credentials before running the campaign.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_auth(email, password):
    """Test Gmail authentication."""
    print("🔐 Testing Gmail Authentication...")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {'*' * len(password)}")
    
    try:
        # Create SMTP connection
        context = ssl.create_default_context()
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print("📡 Connecting to Gmail SMTP server...")
            server.starttls(context=context)
            print("🔒 Starting TLS encryption...")
            
            print("🔐 Attempting login...")
            server.login(email, password)
            print("✅ Login successful!")
            
            # Try sending a test email to yourself
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email
            msg['Subject'] = "Gmail Authentication Test - SUCCESS"
            
            body = """
            Congratulations! Your Gmail authentication is working correctly.
            
            This test email confirms that:
            ✅ SMTP connection established
            ✅ TLS encryption working
            ✅ Authentication successful
            ✅ Email sending functional
            
            You can now run your email campaigns successfully!
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            print("📨 Sending test email to yourself...")
            text = msg.as_string()
            server.sendmail(email, email, text)
            print("✅ Test email sent successfully!")
            
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting steps:")
        print("1. Make sure 2-Factor Authentication is enabled on your Gmail account")
        print("2. Generate a NEW App Password:")
        print("   - Go to: https://myaccount.google.com/security")
        print("   - Click 'App passwords' (under 2-Step Verification)")
        print("   - Generate a new password for 'Mail' application")
        print("   - Use this 16-character password instead of your regular password")
        print("3. Make sure 'Less secure app access' is not needed (use App Password instead)")
        
        return False
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 Check your internet connection and try again.")
        return False

def main():
    print("🚀 Gmail Authentication Test")
    print("="*40)
    
    print("\n📋 Before testing, ensure:")
    print("1. You have 2-Factor Authentication enabled on Gmail")
    print("2. You have generated an App Password for this application")
    print("3. You're using the App Password, NOT your regular Gmail password")
    
    email = input("\n📧 Enter your Gmail address: ").strip()
    password = input("🔑 Enter your Gmail App Password: ").strip()
    
    if not email or not password:
        print("❌ Both email and password are required!")
        return
    
    if '@gmail.com' not in email:
        print("⚠️  Warning: This test is specifically for Gmail accounts")
    
    success = test_gmail_auth(email, password)
    
    if success:
        print("\n🎉 Success! Your credentials are working.")
        print("💡 You can now use these credentials in your email campaigns.")
        print(f"💾 Save these for your campaigns:")
        print(f"   EMAIL_ADDRESS={email}")
        print(f"   EMAIL_PASSWORD={password}")
    else:
        print("\n❌ Authentication failed. Please fix the issues above and try again.")

if __name__ == "__main__":
    main()
