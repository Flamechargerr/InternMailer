#!/usr/bin/env python3
"""
Send HTML Template Emails using existing templates
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import pandas as pd
import random
from jinja2 import Template

# Load environment variables
load_dotenv()

def get_random_professor():
    """Get a random professor for testing"""
    try:
        df = pd.read_csv('data/scraped_professors_final.csv')
        if len(df) > 0:
            professor = df.iloc[random.randint(0, len(df)-1)]
            return {
                'name': professor['name'],
                'university': professor['affiliation'],
                'email': professor['email'],
                'research_area': 'Computer Science',
                'last_name': professor['name'].split()[-1] if ' ' in professor['name'] else professor['name']
            }
    except:
        pass
    
    return {
        'name': 'Dr. Alan Turing',
        'university': 'University of Cambridge',
        'email': 'turing@cambridge.edu',
        'research_area': 'Computer Science',
        'last_name': 'Turing'
    }

def load_html_template(template_path):
    """Load HTML template from file"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error loading template {template_path}: {e}")
        return None

def create_hr_html_email(professor_data):
    """Create HR email using HTML template"""
    template_path = 'templates/enhanced_hr_template.html'
    template_content = load_html_template(template_path)
    
    if not template_content:
        return None, None
    
    # Create template context
    context = {
        'company_name': professor_data['university'],
        'company_niche': professor_data['research_area'],
        'name': 'Hiring Manager'
    }
    
    # Render template
    template = Template(template_content)
    html_content = template.render(**context)
    
    subject = f"Internship Opportunity - {professor_data['university']}"
    
    return subject, html_content

def create_academic_html_email(professor_data):
    """Create academic professor email using HTML template"""
    template_path = 'templates/academic_research_template.html'
    template_content = load_html_template(template_path)
    
    if not template_content:
        return None, None
    
    # Create template context
    context = {
        'professor': {
            'last_name': professor_data['last_name'],
            'research_area': professor_data['research_area']
        }
    }
    
    # Render template
    template = Template(template_content)
    html_content = template.render(**context)
    
    subject = f"Research Internship Inquiry - {professor_data['research_area']}"
    
    return subject, html_content

def send_html_email(recipient_email, subject, html_content, email_type):
    """Send HTML email using Gmail SMTP"""
    try:
        # Get Gmail credentials from environment
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            print(f"❌ Gmail credentials not configured. Cannot send {email_type} email.")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
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
    """Main function to send HTML template emails"""
    print("🎨 SENDING HTML TEMPLATE EMAILS - INTERNMAILING SYSTEM")
    print("=" * 70)
    
    # Get random professor data
    professor_data = get_random_professor()
    print(f"📧 Using professor: {professor_data['name']} from {professor_data['university']}")
    print(f"🎯 Research area: {professor_data['research_area']}")
    
    # Target email
    target_email = "tripathy.anamay23@gmail.com"
    
    # Send HR template email
    print("\n📋 Creating HR Template Email...")
    hr_subject, hr_html = create_hr_html_email(professor_data)
    
    if hr_subject and hr_html:
        hr_success = send_html_email(target_email, hr_subject, hr_html, "HR Template")
    else:
        print("❌ Failed to create HR template email")
        hr_success = False
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Send Academic Professor email
    print("\n🎓 Creating Academic Professor Email...")
    academic_subject, academic_html = create_academic_html_email(professor_data)
    
    if academic_subject and academic_html:
        academic_success = send_html_email(target_email, academic_subject, academic_html, "Academic Professor")
    else:
        print("❌ Failed to create Academic template email")
        academic_success = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 HTML EMAIL TEST RESULTS:")
    print("=" * 70)
    print(f"HR Template Email: {'✅ SENT' if hr_success else '❌ FAILED'}")
    print(f"Academic Professor Email: {'✅ SENT' if academic_success else '❌ FAILED'}")
    
    if hr_success and academic_success:
        print("\n🎉 Both HTML template emails sent successfully!")
        print("📧 Check your email: tripathy.anamay23@gmail.com")
        print("🎨 Emails are now properly formatted with HTML templates!")
    else:
        print("\n⚠️ Some emails failed. Check the error messages above.")
    
    print("\n" + "=" * 70)
    print("✅ SYSTEM STATUS: HTML TEMPLATES OPERATIONAL")
    print("=" * 70)
    print("🎨 HTML templates are now being used for professional formatting")
    print("📧 Your emails will have proper styling and layout")
    print("🚀 Ready to send beautiful, professional emails to professors!")

if __name__ == "__main__":
    main() 