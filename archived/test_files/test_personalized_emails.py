#!/usr/bin/env python3
"""
Test Personalized Emails - InternMailing System
Send 2 test emails (1 HR + 1 Professor) using the new personalized templates
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import pandas as pd
import random
from jinja2 import Template

load_dotenv()

def load_html_template(template_path):
    """Load HTML template from file"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_random_professor():
    """Get a random professor from the database"""
    try:
        df = pd.read_csv('data/scraped_professors_final.csv')
        professor = df.sample(n=1).iloc[0]
        return {
            'first_name': professor.get('first_name', 'John'),
            'last_name': professor.get('last_name', 'Doe'),
            'university': professor.get('university', 'University of Technology'),
            'research_area': professor.get('research_area', 'Computer Science'),
            'email': professor.get('email', 'professor@university.edu')
        }
    except:
        return {
            'first_name': 'John',
            'last_name': 'Doe',
            'university': 'University of Technology',
            'research_area': 'Computer Science',
            'email': 'professor@university.edu'
        }

def get_random_hr_contact():
    """Get a random HR contact from the database"""
    try:
        with open('data/enhanced_hr_contacts.json', 'r') as f:
            import json
            hr_data = json.load(f)
            if hr_data:
                contact = random.choice(hr_data)
                return {
                    'name': contact.get('name', 'Hiring Manager'),
                    'email': contact.get('email', 'hr@company.com'),
                    'company': contact.get('company', 'Tech Company'),
                    'position': contact.get('position', 'HR Manager')
                }
    except:
        pass
    
    return {
        'name': 'Hiring Manager',
        'email': 'hr@techcompany.com',
        'company': 'Tech Company',
        'position': 'HR Manager'
    }

def create_hr_html_email(hr_data):
    """Create HR template email with company data"""
    template_content = load_html_template('templates/enhanced_hr_template.html')
    context = {
        'company_name': hr_data['company'], 
        'company_niche': 'Technology', 
        'name': hr_data['name']
    }
    html_content = Template(template_content).render(**context)
    return f"Internship Opportunity - {hr_data['company']}", html_content

def create_academic_html_email(professor_data):
    """Create personalized academic professor template email"""
    template_content = load_html_template('templates/enhanced_academic_research_template.html')
    context = {
        'professor': {
            'last_name': professor_data['last_name'], 
            'research_area': professor_data['research_area']
        }
    }
    html_content = Template(template_content).render(**context)
    return f"Research Internship Inquiry - {professor_data['research_area']}", html_content

def send_html_email_with_cv(recipient_email, subject, html_content, email_type):
    """Send HTML email with CV attachment"""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = gmail_user
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html'))
    
    # Attach CV
    cv_path = 'resumes/CV_Anamay_Modern.pdf'
    if os.path.exists(cv_path):
        with open(cv_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename=CV_Anamay_Tripathy.pdf'
        )
        msg.attach(part)
        print(f"📎 CV attached: {cv_path}")
    else:
        print(f"⚠️ CV not found at: {cv_path}")
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient_email, msg.as_string())
        server.quit()
        print(f"✅ {email_type} email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send {email_type} email: {e}")
        return False

def main():
    """Main function to send 2 test emails for confirmation"""
    print("🎯 TESTING PERSONALIZED EMAILS - CONFIRMATION")
    print("=" * 60)
    print("Sending 2 test emails (1 HR + 1 Professor) for confirmation")
    print("=" * 60)
    
    # Get random data
    professor_data = get_random_professor()
    hr_data = get_random_hr_contact()
    
    print(f"📧 Professor: {professor_data['first_name']} {professor_data['last_name']} from {professor_data['university']}")
    print(f"🎯 Research area: {professor_data['research_area']}")
    print(f"🏢 HR Contact: {hr_data['name']} from {hr_data['company']}")
    print()
    
    target_email = "tripathy.anamay23@gmail.com"
    
    # Send HR Template Email
    print("📋 Creating HR Template Email...")
    hr_subject, hr_html = create_hr_html_email(hr_data)
    hr_success = send_html_email_with_cv(target_email, hr_subject, hr_html, "HR Template")
    print()
    
    # Send Personalized Academic Professor Email
    print("🎓 Creating Personalized Academic Professor Email...")
    academic_subject, academic_html = create_academic_html_email(professor_data)
    academic_success = send_html_email_with_cv(target_email, academic_subject, academic_html, "Personalized Academic Professor")
    print()
    
    print("=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    print(f"HR Template Email: {'✅ SENT' if hr_success else '❌ FAILED'}")
    print(f"Academic Professor Email: {'✅ SENT' if academic_success else '❌ FAILED'}")
    print()
    
    if hr_success and academic_success:
        print("🎉 BOTH TEST EMAILS SENT SUCCESSFULLY!")
        print("📧 Check your email: tripathy.anamay23@gmail.com")
        print("📎 CV should be attached to both emails!")
        print()
        print("✅ CONFIRMATION: Templates are working perfectly!")
        print("🚀 Ready for mass bulk mailing!")
    else:
        print("❌ Some emails failed to send. Please check the errors above.")
        print("🔧 Fix any issues before proceeding with mass mailing.")
    
    print("=" * 60)
    print("📋 NEXT STEPS:")
    print("1. Check your email for both test emails")
    print("2. Confirm the templates look good")
    print("3. If satisfied, proceed with mass bulk mailing")
    print("4. If not satisfied, let me know what needs adjustment")
    print("=" * 60)

if __name__ == "__main__":
    main() 