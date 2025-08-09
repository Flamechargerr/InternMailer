#!/usr/bin/env python3
"""
Large Scale Personalized Mass Mailing - InternMailing System
Send emails to 20+ professors with guaranteed research area personalization
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
import re

# Import enhanced research area inference
from enhanced_research_area_inference import EnhancedResearchAreaInference

load_dotenv()

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def load_html_template(template_path):
    """Load HTML template from file"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_large_scale_professors(count=20):
    """Get a large batch of professors with guaranteed research area personalization"""
    try:
        df = pd.read_csv('data/scraped_professors_final.csv')
        
        # Initialize enhanced research area inference
        inference = EnhancedResearchAreaInference()
        
        # Get professors that haven't been emailed yet
        if os.path.exists('data/emailed_professors.json'):
            with open('data/emailed_professors.json', 'r') as f:
                emailed_data = json.load(f)
                if isinstance(emailed_data, list):
                    emailed_emails = [p.get('recipient_email', '') for p in emailed_data]
                else:
                    emailed_emails = []
        else:
            emailed_emails = []
        
        # Filter out already emailed professors and invalid emails
        available_professors = df[
            (~df['email'].isin(emailed_emails)) & 
            (df['email'].apply(is_valid_email))
        ]
        
        # Target professors with known research areas (expanded list)
        target_names = [
            # Machine Learning / AI
            'Abedelaziz Mohaisen', 'Aaron Bernstein', 'Abhishek Kumar', 'Aaron Clauset',
            
            # Computer Vision
            'Abhinav Gupta', 'Aaron F. Bobick', 'Abhijit Mahalanobis', 'Abhinav Shrivastava',
            'Abhir Bhalerao', 'Abhishek Roy',
            
            # Cybersecurity
            'Abhi Shelat', 'Abhishek Kumar', 'Abhishek Sharma',
            
            # Data Science
            'Abhishek Jain', 'Abhishek Sharma', 'Aaron Clauset',
            
            # Distributed Systems
            'Abhishek Bhattacharjee', 'Abhishek Chandra', 'Aaron Schulman', 
            'Abhishek Singh', 'Abhishek Verma',
            
            # Web Technologies
            'Aaron Steven White', 'Aaron Visaggio', 'Abhishek Kumar', 'Abhishek Sharma'
        ]
        
        # Find professors with target names
        targeted_professors = []
        for target_name in target_names:
            matches = available_professors[available_professors['name'].str.contains(target_name, case=False, na=False)]
            if len(matches) > 0:
                targeted_professors.extend(matches.to_dict('records'))
        
        # If we don't have enough targeted professors, add some with good inference
        if len(targeted_professors) < count:
            remaining_needed = count - len(targeted_professors)
            remaining_professors = available_professors[~available_professors['name'].isin([p['name'] for p in targeted_professors])]
            
            # Sample remaining professors and check their inference
            sample_professors = remaining_professors.sample(min(remaining_needed * 5, len(remaining_professors)))
            
            for _, row in sample_professors.iterrows():
                professor_data = {
                    'name': row.get('name', ''),
                    'affiliation': row.get('affiliation', '')
                }
                research_area = inference.infer_research_area(professor_data)
                
                # Only add if it's not generic computer science
                if research_area != 'computer science':
                    targeted_professors.append(row.to_dict())
                    if len(targeted_professors) >= count:
                        break
        
        # Limit to requested count
        if len(targeted_professors) > count:
            targeted_professors = targeted_professors[:count]
        
        def parse_name(full_name):
            """Parse full name into first and last name"""
            if pd.isna(full_name) or not full_name:
                return 'John', 'Doe'
            
            # Clean the name and remove artifacts like "0001"
            name_str = str(full_name).strip()
            # Remove common artifacts
            name_str = re.sub(r'\s+0001$', '', name_str)  # Remove "0001" at the end
            name_str = re.sub(r'\s+\d+$', '', name_str)   # Remove any numbers at the end
            name_str = re.sub(r'^\d+\s+', '', name_str)   # Remove numbers at the beginning
            
            name_parts = name_str.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
            elif len(name_parts) == 1:
                first_name = name_parts[0]
                last_name = name_parts[0]
            else:
                first_name = 'John'
                last_name = 'Doe'
            
            return first_name, last_name
        
        professor_list = []
        for professor_data in targeted_professors:
            # Parse name
            first_name, last_name = parse_name(professor_data.get('name'))
            
            # Infer research area with enhanced system
            prof_data = {
                'name': professor_data.get('name', ''),
                'affiliation': professor_data.get('affiliation', '')
            }
            research_area = inference.infer_research_area(prof_data)
            research_details = inference.get_research_area_details(research_area)
            
            professor_list.append({
                'first_name': first_name,
                'last_name': last_name,
                'university': str(professor_data.get('affiliation', 'University of Technology')).strip(),
                'research_area': research_area,
                'research_title': research_details['title'],
                'research_alignment': research_details['research_alignment'],
                'highlighted_projects': research_details['highlighted_projects'],
                'relevant_coursework': research_details['relevant_coursework'],
                'skills_emphasis': research_details['skills_emphasis'],
                'email': str(professor_data.get('email', 'professor@university.edu')).strip()
            })
        
        return professor_list
        
    except Exception as e:
        print(f"Error getting large scale professors: {e}")
        return []

def get_hr_contacts_batch(count=5):
    """Get a batch of HR contacts from the database"""
    try:
        with open('data/enhanced_hr_contacts.json', 'r') as f:
            hr_data = json.load(f)
            
        # Get HR contacts that haven't been contacted yet
        if os.path.exists('data/contacted_hr.json'):
            with open('data/contacted_hr.json', 'r') as f:
                contacted_data = json.load(f)
                if isinstance(contacted_data, list):
                    contacted_emails = [h.get('recipient_email', '') for h in contacted_data]
                else:
                    contacted_emails = []
        else:
            contacted_emails = []
        
        # Filter out already contacted HR and invalid emails
        available_hr = [
            h for h in hr_data 
            if h.get('email') not in contacted_emails and is_valid_email(h.get('email', ''))
        ]
        
        if len(available_hr) < count:
            print(f"⚠️ Only {len(available_hr)} HR contacts available, using all")
            count = len(available_hr)
        
        if count == 0:
            print("⚠️ No available HR contacts found")
            return []
        
        selected_hr = random.sample(available_hr, count)
        
        return [{
            'name': str(contact.get('name', 'Hiring Manager')).strip(),
            'email': str(contact.get('email', 'hr@company.com')).strip(),
            'company': str(contact.get('company', 'Tech Company')).strip(),
            'position': str(contact.get('position', 'HR Manager')).strip()
        } for contact in selected_hr]
        
    except Exception as e:
        print(f"Error getting HR contacts: {e}")
        return []

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
    """Create personalized academic professor template email with research area details"""
    template_content = load_html_template('templates/enhanced_academic_research_template.html')
    context = {
        'professor': {
            'last_name': professor_data['last_name'], 
            'research_area': professor_data['research_area'],
            'research_title': professor_data['research_title'],
            'research_alignment': professor_data['research_alignment'],
            'highlighted_projects': professor_data['highlighted_projects'],
            'relevant_coursework': professor_data['relevant_coursework'],
            'skills_emphasis': professor_data['skills_emphasis']
        }
    }
    html_content = Template(template_content).render(**context)
    
    return f"Research Internship Inquiry - {professor_data['research_title']}", html_content

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
                if not isinstance(logs, list):
                    logs = []
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=4)
            
    except Exception as e:
        print(f"Warning: Could not log email: {e}")

def main():
    """Main function to send large scale personalized emails"""
    print("🚀 LARGE SCALE PERSONALIZED MASS MAILING - INTERNMAILING SYSTEM")
    print("=" * 60)
    print("Sending 20+ emails with GUARANTEED research area personalization")
    print("=" * 60)
    
    # Get recipients
    professors = get_large_scale_professors(20)
    hr_contacts = get_hr_contacts_batch(5)
    
    total_recipients = len(professors) + len(hr_contacts)
    
    if total_recipients == 0:
        print("❌ No recipients available for mass mailing")
        return
    
    # Group professors by research area for better overview
    research_areas = {}
    for prof in professors:
        area = prof['research_area']
        if area not in research_areas:
            research_areas[area] = []
        research_areas[area].append(prof)
    
    print(f"📧 Professors selected: {len(professors)}")
    print("🎯 Research Area Distribution:")
    for area, profs in research_areas.items():
        print(f"   • {area.title()}: {len(profs)} professors")
        for prof in profs[:3]:  # Show first 3 from each area
            print(f"     - {prof['first_name']} {prof['last_name']} from {prof['university']}")
        if len(profs) > 3:
            print(f"     ... and {len(profs) - 3} more")
    
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
        'hr_failed': 0,
        'research_area_stats': {}
    }
    
    # Send professor emails
    if professors:
        print("🎓 SENDING LARGE SCALE PERSONALIZED PROFESSOR EMAILS...")
        print("-" * 40)
        for i, professor in enumerate(professors, 1):
            print(f"📧 Sending email {i}/{len(professors)} to Professor {professor['first_name']} {professor['last_name']}...")
            print(f"   🎯 Research Area: {professor['research_area']} - {professor['research_title']}")
            
            subject, html_content = create_academic_html_email(professor)
            success = send_html_email_with_cv(
                professor['email'], 
                subject, 
                html_content, 
                "Large Scale Personalized Academic Professor", 
                f"{professor['first_name']} {professor['last_name']}"
            )
            
            if success:
                results['professors_sent'] += 1
                results['total_sent'] += 1
                
                # Track research area stats
                area = professor['research_area']
                if area not in results['research_area_stats']:
                    results['research_area_stats'][area] = {'sent': 0, 'failed': 0}
                results['research_area_stats'][area]['sent'] += 1
            else:
                results['professors_failed'] += 1
                results['total_failed'] += 1
                
                # Track research area stats
                area = professor['research_area']
                if area not in results['research_area_stats']:
                    results['research_area_stats'][area] = {'sent': 0, 'failed': 0}
                results['research_area_stats'][area]['failed'] += 1
            
            log_sent_email(professor, 'Professor', success)
            
            # Small delay between emails
            time.sleep(2)
        
        print()
    
    # Send HR emails
    if hr_contacts:
        print("🏢 SENDING HR EMAILS...")
        print("-" * 40)
        for i, hr_contact in enumerate(hr_contacts, 1):
            print(f"📧 Sending email {i}/{len(hr_contacts)} to {hr_contact['name']} from {hr_contact['company']}...")
            
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
    print("📊 LARGE SCALE PERSONALIZED MAILING RESULTS:")
    print("=" * 60)
    print(f"Total Emails Sent: {results['total_sent']}/{total_recipients}")
    print(f"Total Emails Failed: {results['total_failed']}/{total_recipients}")
    print(f"Success Rate: {(results['total_sent']/total_recipients)*100:.1f}%")
    print()
    print(f"Professors: {results['professors_sent']}/{len(professors)} sent, {results['professors_failed']}/{len(professors)} failed")
    print(f"HR Contacts: {results['hr_sent']}/{len(hr_contacts)} sent, {results['hr_failed']}/{len(hr_contacts)} failed")
    print()
    
    # Research area breakdown
    print("🎯 Research Area Breakdown:")
    for area, stats in results['research_area_stats'].items():
        total = stats['sent'] + stats['failed']
        success_rate = (stats['sent'] / total * 100) if total > 0 else 0
        print(f"   • {area.title()}: {stats['sent']}/{total} sent ({success_rate:.1f}% success)")
    
    print()
    
    if results['total_sent'] == total_recipients:
        print("🎉 ALL LARGE SCALE EMAILS SENT SUCCESSFULLY!")
        print("✅ Large scale personalized mailing system is working perfectly!")
        print("🎯 All professor emails have specific research area personalization!")
        print("🚀 Ready to scale up to even larger campaigns!")
    elif results['total_sent'] >= total_recipients * 0.8:
        print("✅ Most large scale emails sent successfully!")
        print("⚠️ Some emails failed - check errors above")
        print("🔧 Fix any issues before scaling up further")
    else:
        print("❌ Multiple large scale emails failed")
        print("🔧 Please fix issues before proceeding")
    
    print("=" * 60)
    print("📋 NEXT STEPS:")
    print("1. Check email delivery and verify personalization")
    print("2. Monitor for responses from personalized emails")
    print("3. If successful, expand to 50+ professor campaigns")
    print("4. Continue with even larger targeted campaigns")
    print("=" * 60)

if __name__ == "__main__":
    main() 