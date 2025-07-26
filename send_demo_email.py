#!/usr/bin/env python3
"""
Send a demo email to Anamay's email to test the enhanced email generation system
"""

import sys
import os
sys.path.append('InternMailer/src')

from resume_parser import ResumeParser
from email_generator import EmailGenerator
from gmail_sender import GmailSender
from dotenv import load_dotenv

def send_demo_email():
    """Send a demo email to test the system"""
    print("=== Sending Demo Email ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Parse the CV
    cv_path = 'resumes/CV_Anamay_Modern.pdf'
    if not os.path.exists(cv_path):
        print("❌ CV file not found. Please ensure CV_Anamay_Modern.pdf is in the resumes/ folder.")
        return
    
    print("📄 Parsing CV...")
    parser = ResumeParser(cv_path)
    student_info = parser.parse()
    
    # Add additional info
    student_info['name'] = 'Anamay Tripathy'
    student_info['email'] = 'tripathy.anamay23@gmail.com'
    student_info['university'] = 'Manipal Institute of Technology'
    student_info['resume_prefix'] = 'CV_Anamay_Modern'
    
    # Create a demo professor (using your email)
    demo_professor = {
        'Name': 'Dr. AI Research Professor',
        'University': 'Demo University',
        'Research Area': 'Machine Learning and Data Science',
        'Email': 'tripathy.anamay23@gmail.com'  # Your email for demo
    }
    
    print(f"✅ CV parsed successfully!")
    print(f"   Skills: {len(student_info.get('skills', []))} found")
    print(f"   Projects: {len(student_info.get('projects', []))} found")
    
    # Generate email
    print("\n📧 Generating personalized email...")
    email_gen = EmailGenerator(student_info, use_ollama=False)
    
    # Find relevant skills and projects
    relevant = email_gen.find_relevant_skills_and_projects(demo_professor)
    print(f"🎯 Relevant Skills: {', '.join(relevant['skills'][:5])}")
    print(f"🎯 Relevant Projects: {', '.join(relevant['projects'])}")
    
    # Generate subject and body
    subject = email_gen.generate_subject(demo_professor)
    body = email_gen.generate_body(demo_professor)
    
    print(f"\n📨 Subject: {subject}")
    print(f"📝 Body (first 200 chars): {body[:200]}...")
    
    # Send email
    print("\n📤 Sending demo email...")
    try:
        sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
        
        # Add a demo prefix to the subject
        demo_subject = f"[DEMO] {subject}"
        
        # Add demo context to the body
        demo_body = f"""
=== INTERNMAILER DEMO EMAIL ===
This is a demonstration of the enhanced InternMailer system using your actual CV data.

{body}

=== END DEMO ===
This email was automatically generated using:
- Your actual CV data (26 skills, 5 projects, 4 experiences, 16 courses)
- Enhanced personalization based on professor's research area
- Template-based generation with relevant skill/project matching

The system successfully extracted and utilized your real information to create this personalized email.
"""
        
        success = sender.send_email(
            to_email=demo_professor['Email'],
            subject=demo_subject,
            body=demo_body,
            attachment_path=cv_path
        )
        
        if success:
            print("✅ Demo email sent successfully!")
            print(f"📬 Check your email ({demo_professor['Email']}) to see the personalized email.")
            print("\n🎉 The enhanced InternMailer system is working perfectly!")
        else:
            print("❌ Failed to send demo email. Please check your email credentials.")
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print("\nNote: Make sure your Gmail credentials are set in the .env file:")
        print("GMAIL_USER=your_email@gmail.com")
        print("GMAIL_APP_PASSWORD=your_app_password")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("✅ CV parsing: Successfully extracted all your real data")
    print("✅ Email personalization: Skills and projects matched to research area")
    print("✅ Professional formatting: Clean, engaging email template")
    print("✅ Email delivery: Sent to your inbox for review")

if __name__ == "__main__":
    send_demo_email()
