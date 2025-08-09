#!/usr/bin/env python3
"""
Mass Mailing Batch 5 - InternMailing System
Send 5 emails (mix of HR and professors) for initial mass mailing test
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
import json
from jinja2 import Template
import time
from datetime import datetime

load_dotenv()

def load_html_template(template_path):
    """Load HTML template from file"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_professors_batch(count=3):
    """Get a batch of professors from the database"""
    try:
        df = pd.read_csv('data/scraped_professors_final.csv')
        # Get professors that haven't been emailed yet
        if os.path.exists('data/emailed_professors.json'):
            with open('data/emailed_professors.json', 'r') as f:
                emailed_professors = json.load(f)
                emailed_emails = [p.get('email', '') for p in emailed_professors]
        else:
            emailed_emails = []
        
        # Filter out already emailed professors
        available_professors = df[~df['email'].isin(emailed_emails)]
        
        if len(available_professors) < count:
            print(f"⚠️ Only {len(available_professors)} professors available, using all")
            count = len(available_professors)
        
        professors = available_professors.sample(n=count)
        
        return [{
            'first_name': row.get('first_name', 'John'),
            'last_name': row.get('last_name', 'Doe'),
            'university': row.get('university', 'University of Technology'),
            'research_area': row.get('research_area', 'Computer Science'),
            'email': row.get('email', 'professor@university.edu')
        } for _, row in professors.iterrows()]
        
    except Exception as e:
        print(f"Error getting professors: {e}")
        return [{
            'first_name': 'John',
            'last_name': 'Doe',
            'university': 'University of Technology',
            'research_area': 'Computer Science',
            'email': 'professor@university.edu'
        } for _ in range(count)]

def get_hr_contacts_batch(count=2):
    """Get a batch of HR contacts from the database"""
    try:
        with open('data/enhanced_hr_contacts.json', 'r') as f:
            hr_data = json.load(f)
            
        # Get HR contacts that haven't been contacted yet
        if os.path.exists('data/contacted_hr.json'):
            with open('data/contacted_hr.json', 'r') as f:
                contacted_hr = json.load(f)
                contacted_emails = [h.get('email', '') for h in contacted_hr]
        else:
            contacted_emails = []
        
        # Filter out already contacted HR
        available_hr = [h for h in hr_data if h.get('email') not in contacted_emails]
        
        if len(available_hr) < count:
            print(f"⚠️ Only {len(available_hr)} HR contacts available, using all")
            count = len(available_hr)
        
        selected_hr = random.sample(available_hr, count)
        
        return [{
            'name': contact.get('name', 'Hiring Manager'),
            'email': contact.get('email', 'hr@company.com'),
            'company': contact.get('company', 'Tech Company'),
            'position': contact.get('position', 'HR Manager')
        } for contact in selected_hr]
        
    except Exception as e:
        print(f"Error getting HR contacts: {e}")
        return [{
            'name': 'Hiring Manager',
            'email': 'hr@techcompany.com',
            'company': 'Tech Company',
            'position': 'HR Manager'
        } for _ in range(count)]

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

def send_html_email_with_cv(recipient_email, subject, html_content, email_type, recipient_name):
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
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient_email, msg.as_string())
        server.quit()
        print(f"✅ {email_type} email sent successfully to {recipient_name} ({recipient_email})")
        return True
    except Exception as e:
        print(f"❌ Failed to send {email_type} email to {recipient_name}: {e}")
        return False

def log_sent_email(recipient_data, email_type, success):
    """Log sent email for tracking"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'email_type': email_type,
        'recipient_email': recipient_data.get('email', ''),
        'recipient_name': recipient_data.get('name', recipient_data.get('first_name', 'Unknown')),
        'company': recipient_data.get('company', ''),
        'university': recipient_data.get('university', ''),
        'research_area': recipient_data.get('research_area', ''),
        'success': success
    }
    
    # Log to appropriate file
    if email_type == 'HR':
        log_file = 'data/contacted_hr.json'
    else:
        log_file = 'data/emailed_professors.json'
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=4)
            
    except Exception as e:
        print(f"Warning: Could not log email: {e}")

def main():
    """Main function to send batch of 5 emails"""
    print("🚀 MASS MAILING BATCH 5 - INTERNMAILING SYSTEM")
    print("=" * 60)
    print("Sending 5 emails (3 Professors + 2 HR) for mass mailing test")
    print("=" * 60)
    
    # Get recipients
    professors = get_professors_batch(3)
    hr_contacts = get_hr_contacts_batch(2)
    
    print(f"📧 Professors selected: {len(professors)}")
    for prof in professors:
        print(f"   • {prof['first_name']} {prof['last_name']} from {prof['university']} ({prof['research_area']})")
    
    print(f"🏢 HR Contacts selected: {len(hr_contacts)}")
    for hr in hr_contacts:
        print(f"   • {hr['name']} from {hr['company']}")
    
    print()
    
    # Track results
    results = {
        'total_sent': 0,
        'total_failed': 0,
        'professors_sent': 0,
        'hr_sent': 0,
        'professors_failed': 0,
        'hr_failed': 0
    }
    
    # Send professor emails
    print("🎓 SENDING PROFESSOR EMAILS...")
    print("-" * 40)
    for i, professor in enumerate(professors, 1):
        print(f"📧 Sending email {i}/3 to Professor {professor['first_name']} {professor['last_name']}...")
        
        subject, html_content = create_academic_html_email(professor)
        success = send_html_email_with_cv(
            professor['email'], 
            subject, 
            html_content, 
            "Academic Professor", 
            f"{professor['first_name']} {professor['last_name']}"
        )
        
        if success:
            results['professors_sent'] += 1
            results['total_sent'] += 1
        else:
            results['professors_failed'] += 1
            results['total_failed'] += 1
        
        log_sent_email(professor, 'Professor', success)
        
        # Small delay between emails
        time.sleep(2)
    
    print()
    
    # Send HR emails
    print("🏢 SENDING HR EMAILS...")
    print("-" * 40)
    for i, hr_contact in enumerate(hr_contacts, 1):
        print(f"📧 Sending email {i}/2 to {hr_contact['name']} from {hr_contact['company']}...")
        
        subject, html_content = create_hr_html_email(hr_contact)
        success = send_html_email_with_cv(
            hr_contact['email'], 
            subject, 
            html_content, 
            "HR Template", 
            hr_contact['name']
        )
        
        if success:
            results['hr_sent'] += 1
            results['total_sent'] += 1
        else:
            results['hr_failed'] += 1
            results['total_failed'] += 1
        
        log_sent_email(hr_contact, 'HR', success)
        
        # Small delay between emails
        time.sleep(2)
    
    print()
    print("=" * 60)
    print("📊 BATCH 5 MASS MAILING RESULTS:")
    print("=" * 60)
    print(f"Total Emails Sent: {results['total_sent']}/5")
    print(f"Total Emails Failed: {results['total_failed']}/5")
    print(f"Success Rate: {(results['total_sent']/5)*100:.1f}%")
    print()
    print(f"Professors: {results['professors_sent']}/3 sent, {results['professors_failed']}/3 failed")
    print(f"HR Contacts: {results['hr_sent']}/2 sent, {results['hr_failed']}/2 failed")
    print()
    
    if results['total_sent'] == 5:
        print("🎉 ALL 5 EMAILS SENT SUCCESSFULLY!")
        print("✅ Mass mailing system is working perfectly!")
        print("🚀 Ready to increase batch size for larger campaigns!")
    elif results['total_sent'] >= 3:
        print("✅ Most emails sent successfully!")
        print("⚠️ Some emails failed - check errors above")
        print("🔧 Fix any issues before increasing batch size")
    else:
        print("❌ Multiple emails failed")
        print("🔧 Please fix issues before proceeding with larger batches")
    
    print("=" * 60)
    print("📋 NEXT STEPS:")
    print("1. Check email delivery and responses")
    print("2. Monitor for any bounce-backs")
    print("3. If successful, increase batch size")
    print("4. Continue with larger mass mailing campaigns")
    print("=" * 60)

if __name__ == "__main__":
    main() 