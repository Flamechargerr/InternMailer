#!/usr/bin/env python3
"""
Test Email Sender - Sends both HR and Academic Professor templates
"""

import pandas as pd
import random
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_random_professor():
    """Get a random professor from the database"""
    try:
        # Try the main database first
        df = pd.read_csv('data/scraped_professors_final.csv')
        if len(df) > 0:
            professor = df.iloc[random.randint(0, len(df)-1)]
            return {
                'name': professor['name'],
                'university': professor['affiliation'],
                'email': professor['email'],
                'research_area': 'Computer Science'  # Default research area
            }
    except:
        pass
    
    # Fallback to archive
    try:
        df = pd.read_csv('data/archive/professors_final.csv', on_bad_lines='skip')
        if len(df) > 0:
            professor = df.iloc[random.randint(0, len(df)-1)]
            return {
                'name': professor['Name'],
                'university': professor['University'],
                'email': professor['Email'],
                'research_area': professor['Research Area']
            }
    except:
        pass
    
    # Default fallback
    return {
        'name': 'Dr. Alan Turing',
        'university': 'University of Cambridge',
        'email': 'turing@cambridge.edu',
        'research_area': 'Computer Science'
    }

def create_hr_template_email(professor_data):
    """Create HR template email"""
    subject = f"Internship Opportunity - {professor_data['university']}"
    
    body = f"""
Dear Hiring Manager,

I hope this email finds you well. I am writing to express my interest in internship opportunities at {professor_data['university']}.

I am a passionate student with a strong background in computer science and a keen interest in {professor_data['research_area']}. I believe my skills and enthusiasm would make me a valuable addition to your team.

**Key Skills:**
- Programming: Python, Java, C++
- Machine Learning & AI
- Data Analysis
- Web Development
- Problem Solving

**Relevant Experience:**
- Academic projects in {professor_data['research_area']}
- Internship experience in software development
- Strong academic performance

I would welcome the opportunity to discuss how I can contribute to your organization. Please find my resume attached for your review.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
[Your Name]
Computer Science Student
[Your University]
[Your Email]
[Your Phone]
    """
    
    return subject, body

def create_academic_professor_email(professor_data):
    """Create academic professor research email"""
    subject = f"Research Collaboration Interest - {professor_data['research_area']}"
    
    body = f"""
Dear {professor_data['name']},

I hope this email finds you well. I am writing to express my interest in your research work in {professor_data['research_area']} at {professor_data['university']}.

I have been following your research contributions in {professor_data['research_area']} and am particularly interested in your work on [specific research topic]. Your recent publications on [specific area] have been particularly inspiring to my own academic pursuits.

**My Background:**
I am a [year] student at [Your University] studying Computer Science with a focus on {professor_data['research_area']}. My current research interests include:
- [Specific research area 1]
- [Specific research area 2]
- [Specific research area 3]

**Relevant Experience:**
- Research project on [related topic]
- Coursework in [relevant subjects]
- Programming skills: Python, Java, C++
- Experience with [relevant tools/frameworks]

I would be very interested in discussing potential research collaboration opportunities or internship positions in your lab. I am particularly drawn to your work on [specific aspect of their research] and believe I could contribute meaningfully to ongoing projects.

Would you be available for a brief discussion about potential opportunities? I would be happy to share more details about my background and research interests.

Thank you for considering my inquiry. I look forward to hearing from you.

Best regards,
[Your Name]
Computer Science Student
[Your University]
[Your Email]
[Your Phone]

---
*This email was generated as a test of the InternMailing system*
    """
    
    return subject, body

def send_email(recipient_email, subject, body, email_type):
    """Send email using Gmail SMTP"""
    try:
        # Get Gmail credentials from environment
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            print(f"❌ Gmail credentials not configured. Cannot send {email_type} email.")
            print("Please set GMAIL_USER and GMAIL_APP_PASSWORD environment variables.")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, recipient_email, text)
        server.quit()
        
        print(f"✅ {email_type} email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send {email_type} email: {str(e)}")
        return False

def main():
    """Main function to send test emails"""
    print("🚀 Starting Test Email Sender...")
    print("=" * 50)
    
    # Get random professor data
    professor_data = get_random_professor()
    print(f"📧 Using professor data: {professor_data['name']} from {professor_data['university']}")
    
    # Target email
    target_email = "tripathy.anamay23@gmail.com"
    
    # Send HR template email
    print("\n📋 Sending HR Template Email...")
    hr_subject, hr_body = create_hr_template_email(professor_data)
    hr_success = send_email(target_email, hr_subject, hr_body, "HR Template")
    
    # Send Academic Professor email
    print("\n🎓 Sending Academic Professor Email...")
    academic_subject, academic_body = create_academic_professor_email(professor_data)
    academic_success = send_email(target_email, academic_subject, academic_body, "Academic Professor")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print(f"HR Template Email: {'✅ SENT' if hr_success else '❌ FAILED'}")
    print(f"Academic Professor Email: {'✅ SENT' if academic_success else '❌ FAILED'}")
    
    if hr_success and academic_success:
        print("\n🎉 Both test emails sent successfully!")
    else:
        print("\n⚠️ Some emails failed. Check Gmail credentials.")
    
    # Email statistics
    print("\n📈 EMAIL DATABASE STATISTICS:")
    try:
        df = pd.read_csv('data/scraped_professors_final.csv')
        print(f"Total Professors Scraped: {len(df)}")
        print(f"Professors with Emails: {len(df[df['email'].notna() & (df['email'] != '')])}")
    except:
        print("Could not read professor database")
    
    try:
        df_archive = pd.read_csv('data/archive/professors_final.csv', on_bad_lines='skip')
        print(f"Archive Professors: {len(df_archive)}")
    except:
        print("Could not read archive database")

if __name__ == "__main__":
    main() 