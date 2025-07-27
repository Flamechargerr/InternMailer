#!/usr/bin/env python3
"""
Simple script to generate and send test email for Barbara Liskov
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from resume_parser import ResumeParser
from email_generator import EmailGenerator
from gmail_sender import GmailSender

load_dotenv()

def main():
    # Barbara Liskov's information
    barbara_liskov = {
        'Name': 'Barbara H. Liskov',
        'Email': 'liskov@csail.mit.edu',
        'University': 'Massachusetts Institute of Technology (MIT)',
        'Research Area': 'Distributed systems (AI)',
        'Homepage': 'https://www.csail.mit.edu/user/971'
    }
    
    print("🎯 Generating test email for Barbara Liskov...")
    print(f"Professor: {barbara_liskov['Name']}")
    print(f"Research Area: {barbara_liskov['Research Area']}")
    print(f"Email: {barbara_liskov['Email']}")
    print()
    
    # Check if resume exists
    resume_files = []
    if os.path.exists('resumes'):
        resume_files = [f for f in os.listdir('resumes') if f.endswith('.pdf')]
    
    if not resume_files:
        print("❌ No resume found in 'resumes/' directory")
        print("Please upload a PDF resume to the 'resumes/' folder")
        return
    
    resume_path = os.path.join('resumes', resume_files[0])
    print(f"📄 Using resume: {resume_files[0]}")
    
    try:
        # Parse resume
        print("📊 Parsing resume...")
        parser = ResumeParser(resume_path)
        student_info = parser.parse()
        student_info['name'] = "Anamay Tripathy"
        student_info['email'] = "tripathy.anamay23@gmail.com"
        student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
        
        print(f"✅ Extracted skills: {student_info.get('skills', [])[:5]}")
        print(f"✅ Extracted projects: {student_info.get('projects', [])[:3]}")
        print()
        
        # Generate email
        print("✍️ Generating personalized email...")
        email_gen = EmailGenerator(student_info, use_ollama=False)
        subject = email_gen.generate_subject(barbara_liskov, informal=False)
        body = email_gen.generate_body(barbara_liskov, informal=False)
        
        print("=" * 60)
        print("📧 GENERATED EMAIL:")
        print("=" * 60)
        print(f"To: {barbara_liskov['Email']}")
        print(f"Subject: {subject}")
        print()
        print("Body:")
        print(body)
        print("=" * 60)
        print()
        
        # Ask for approval to send test email
        send_test = input("Send this as a test email to your email address? (y/n): ").lower().strip()
        
        if send_test == 'y':
            test_recipient = input("Enter your email address: ").strip()
            if not test_recipient:
                print("❌ No email address provided")
                return
            
            # Check if credentials are configured
            gmail_user = os.getenv('GMAIL_USER')
            gmail_password = os.getenv('GMAIL_APP_PASSWORD')
            
            if not gmail_user or not gmail_password or gmail_password == 'your_app_password_here':
                print("❌ Gmail credentials not configured!")
                print("Please update .env file with:")
                print("GMAIL_USER=your-email@gmail.com")
                print("GMAIL_APP_PASSWORD=your-app-password")
                return
            
            print(f"📤 Sending test email to {test_recipient}...")
            
            # Send test email
            sender = GmailSender(gmail_user, gmail_password)
            test_subject = f"[TEST EMAIL FOR APPROVAL] {subject}"
            test_body = f"""This is a test email for your approval before bulk sending.

Original Recipient: {barbara_liskov['Email']} ({barbara_liskov['Name']})
Research Area: {barbara_liskov['Research Area']}

Subject: {subject}

Email Body:
{body}

---
If you approve this email format, reply with "APPROVED" to proceed with bulk sending.
"""
            
            success = sender.send_email(test_recipient, test_subject, test_body, resume_path)
            
            if success:
                print("✅ Test email sent successfully!")
                print("📬 Please check your email and approve to proceed with bulk campaign")
            else:
                print("❌ Failed to send test email")
                print("Check your Gmail credentials and internet connection")
        else:
            print("📝 Test email generation completed. No email sent.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
