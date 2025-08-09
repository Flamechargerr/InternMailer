#!/usr/bin/env python3
"""
Live Email Campaign - Send to 3 TRULY FRESH Professors 
InternMailing System with Enhanced Academic Templates
"""

import os
import smtplib
import json
import pandas as pd
import random
import glob
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from jinja2 import Template
import time

load_dotenv()

def get_all_contacted_emails():
    """Get all emails that have been contacted from all sources"""
    contacted_emails = set()
    
    # Check emailed_professors.json
    try:
        with open('data/emailed_professors.json', 'r') as f:
            emailed = json.load(f)
            for prof in emailed:
                email = prof.get('recipient_email', '').strip()
                if email:
                    contacted_emails.add(email)
                    print(f"🔍 Found contacted: {email}")
    except FileNotFoundError:
        print("📋 No emailed_professors.json found")
    
    # Check campaign_results folder
    campaign_files = glob.glob('campaign_results/email_*.txt')
    for file_path in campaign_files:
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline()
                if 'TO:' in first_line:
                    # Extract email from "TO: Name <email>" format
                    if '<' in first_line and '>' in first_line:
                        email = first_line.split('<')[1].split('>')[0].strip()
                        contacted_emails.add(email)
                        print(f"🔍 Found campaign email: {email}")
        except:
            continue
    
    # Check personalized_emails folder  
    personalized_files = glob.glob('personalized_emails/email_*.txt')
    for file_path in personalized_files:
        # Extract name from filename and try to match with professor data
        filename = os.path.basename(file_path)
        if 'email_' in filename:
            # Extract professor name from filename
            name_part = filename.split('_', 3)[-1].replace('.txt', '').replace('_', ' ')
            print(f"🔍 Found personalized email for: {name_part}")
            # We'll match this by name later
    
    # Check fixed_campaign_results folder
    fixed_campaign_files = glob.glob('fixed_campaign_results/email_*.txt')
    for file_path in fixed_campaign_files:
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline()
                if 'TO:' in first_line:
                    if '<' in first_line and '>' in first_line:
                        email = first_line.split('<')[1].split('>')[0].strip()
                        contacted_emails.add(email)
                        print(f"🔍 Found fixed campaign email: {email}")
        except:
            continue
    
    print(f"📊 Total contacted emails found: {len(contacted_emails)}")
    return contacted_emails

def get_contacted_names():
    """Get names of professors who have been contacted"""
    contacted_names = set()
    
    # From personalized_emails folder
    personalized_files = glob.glob('personalized_emails/email_*.txt')
    for file_path in personalized_files:
        filename = os.path.basename(file_path)
        if 'email_' in filename:
            name_part = filename.split('_', 3)[-1].replace('.txt', '').replace('_', ' ')
            contacted_names.add(name_part.lower().strip())
    
    return contacted_names

def load_all_professor_data():
    """Load professor data from multiple sources"""
    all_professors = []
    
    # Load from professors.json (main source)
    try:
        with open('data/professors.json', 'r') as f:
            professors_data = json.load(f)
            for prof in professors_data:
                all_professors.append({
                    'source': 'professors.json',
                    'name': prof.get('Name', ''),
                    'email': prof.get('Email', ''),
                    'university': prof.get('University', ''),
                    'research_area': prof.get('Research Area', 'Computer Science')
                })
        print(f"📁 Loaded {len(professors_data)} professors from professors.json")
    except FileNotFoundError:
        print("📋 professors.json not found")
    
    # Load from CSV files as backup
    csv_files = [
        'data/csrankings-a.csv', 'data/csrankings-b.csv', 'data/csrankings-c.csv',
        'data/csrankings-d.csv', 'data/csrankings-e.csv', 'data/csrankings-f.csv',
        'data/csrankings-g.csv', 'data/csrankings-h.csv', 'data/csrankings-i.csv',
        'data/csrankings-j.csv', 'data/csrankings-k.csv', 'data/csrankings-l.csv',
        'data/csrankings-m.csv', 'data/csrankings-n.csv', 'data/csrankings-o.csv',
        'data/csrankings-p.csv', 'data/csrankings-q.csv', 'data/csrankings-r.csv',
        'data/csrankings-s.csv', 'data/csrankings-t.csv', 'data/csrankings-u.csv',
        'data/csrankings-v.csv', 'data/csrankings-w.csv', 'data/csrankings-x.csv',
        'data/csrankings-y.csv', 'data/csrankings-z.csv'
    ]
    
    csv_count = 0
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                for _, row in df.iterrows():
                    name = row.get('name', '')
                    homepage = row.get('homepage', '')
                    affiliation = row.get('affiliation', '')
                    
                    # Try to extract email from homepage or construct it
                    email = ""
                    if pd.notna(homepage) and '@' in str(homepage):
                        # Sometimes email is in homepage field
                        email = str(homepage).strip()
                    elif pd.notna(name) and pd.notna(affiliation):
                        # Try to construct a basic email (this is speculative)
                        name_parts = str(name).lower().split()
                        if len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = name_parts[-1]
                            # Common academic email formats
                            if 'mit.edu' in str(affiliation).lower():
                                email = f"{first_name[0]}{last_name}@mit.edu"
                            elif 'stanford.edu' in str(affiliation).lower():
                                email = f"{first_name[0]}{last_name}@stanford.edu"
                            elif 'berkeley.edu' in str(affiliation).lower():
                                email = f"{first_name[0]}{last_name}@berkeley.edu"
                    
                    if email and '@' in email and name:
                        all_professors.append({
                            'source': csv_file,
                            'name': name,
                            'email': email,
                            'university': affiliation,
                            'research_area': 'Computer Science'
                        })
                        csv_count += 1
            except Exception as e:
                print(f"⚠️ Error reading {csv_file}: {e}")
    
    print(f"📁 Loaded {csv_count} professors from CSV files")
    print(f"📊 Total professors loaded: {len(all_professors)}")
    return all_professors

def save_emailed_professor(professor_data, success):
    """Save professor to emailed list"""
    try:
        with open('data/emailed_professors.json', 'r') as f:
            emailed_professors = json.load(f)
    except FileNotFoundError:
        emailed_professors = []
    
    emailed_professors.append({
        "timestamp": datetime.now().isoformat(),
        "email_type": "Professor",
        "recipient_email": professor_data['email'],
        "recipient_name": professor_data['first_name'],
        "company": "",
        "university": professor_data['university'],
        "research_area": professor_data['research_area'],
        "success": success
    })
    
    with open('data/emailed_professors.json', 'w') as f:
        json.dump(emailed_professors, f, indent=4)

def get_truly_fresh_professors(count=3):
    """Get professors who have NEVER been contacted"""
    print("🔍 Loading all professor data...")
    all_professors = load_all_professor_data()
    
    print("📧 Getting all contacted emails...")
    contacted_emails = get_all_contacted_emails()
    
    print("👥 Getting all contacted names...")
    contacted_names = get_contacted_names()
    
    # Filter out contacted professors
    fresh_professors = []
    for prof in all_professors:
        email = prof['email'].strip()
        name = prof['name'].strip()
        
        # Skip if no valid email
        if not email or '@' not in email:
            continue
        
        # Skip if email was contacted
        if email in contacted_emails:
            continue
            
        # Skip if name was contacted (fuzzy match)
        name_lower = name.lower().strip()
        if any(contacted_name in name_lower or name_lower in contacted_name 
               for contacted_name in contacted_names):
            continue
        
        # Skip common test emails or invalid ones
        if any(test_domain in email.lower() for test_domain in 
               ['example.com', 'test.com', 'noscholarpage', 'temp']):
            continue
        
        # This professor looks fresh!
        name_parts = name.split()
        fresh_professors.append({
            'first_name': name_parts[0] if name_parts else 'Professor',
            'last_name': name_parts[-1] if len(name_parts) > 1 else 'Professor',
            'email': email,
            'university': prof['university'],
            'research_area': determine_research_area(prof['research_area'])
        })
    
    print(f"🎯 Found {len(fresh_professors)} truly fresh professors")
    
    # Return random selection
    if len(fresh_professors) >= count:
        return random.sample(fresh_professors, count)
    else:
        print(f"⚠️ Only {len(fresh_professors)} fresh professors available")
        return fresh_professors[:count]

def determine_research_area(area):
    """Determine research area category for personalization"""
    area_lower = area.lower()
    if any(keyword in area_lower for keyword in ['machine learning', 'ai', 'artificial intelligence', 'ml']):
        return 'Machine Learning'
    elif any(keyword in area_lower for keyword in ['computer vision', 'cv', 'image']):
        return 'Computer Vision'
    elif any(keyword in area_lower for keyword in ['security', 'cyber', 'crypto']):
        return 'Cybersecurity'
    elif any(keyword in area_lower for keyword in ['data science', 'analytics', 'data']):
        return 'Data Science'
    elif any(keyword in area_lower for keyword in ['distributed', 'systems', 'cloud']):
        return 'Distributed Systems'
    elif any(keyword in area_lower for keyword in ['web', 'frontend', 'backend']):
        return 'Web Technologies'
    else:
        return 'Computer Science'

def load_html_template(template_path):
    """Load HTML template from file"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_personalized_academic_email(professor_data):
    """Create highly personalized academic email using enhanced template"""
    template_content = load_html_template('templates/enhanced_academic_research_template.html')
    
    # Determine personalization based on research area
    research_area = professor_data['research_area']
    
    # Set personalized content based on research area
    if research_area == 'Machine Learning':
        highlighted_projects = ['VARtificial Intelligence - Machine Learning Sports Prediction System']
        relevant_coursework = ['Machine Learning', 'Deep Learning', 'Statistical Analysis', 'Python Programming', 'Neural Networks']
        skills_emphasis = ['TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost']
        research_alignment = f"My expertise in machine learning algorithms, deep learning frameworks, and AI applications directly aligns with your research in {research_area}. My projects demonstrate practical implementation of ML models achieving 89% prediction accuracy."
    elif research_area == 'Computer Vision':
        highlighted_projects = ['Computer Vision and Image Analysis Systems']
        relevant_coursework = ['Computer Vision', 'Image Processing', 'OpenCV', 'Digital Signal Processing']
        skills_emphasis = ['OpenCV', 'Computer Vision', 'Image Processing', 'Pattern Recognition']
        research_alignment = f"My experience with computer vision algorithms, image processing techniques, and pattern recognition systems directly relates to your research in {research_area}. I have hands-on experience with OpenCV and advanced image analysis."
    elif research_area == 'Cybersecurity':
        highlighted_projects = ['HackOps - Cybersecurity Simulation and Training Platform']
        relevant_coursework = ['Network Security', 'Cryptography', 'Ethical Hacking', 'Information Security']
        skills_emphasis = ['Security Frameworks', 'Penetration Testing', 'Network Security']
        research_alignment = f"My cybersecurity training platform with 25+ security challenges and penetration testing experience directly relates to your research in {research_area}. I've implemented comprehensive security frameworks improving user awareness by 35%."
    elif research_area == 'Data Science':
        highlighted_projects = ['CrimeConnect - FBI-Inspired Case Management Dashboard']
        relevant_coursework = ['Data Science', 'Statistical Analysis', 'Data Visualization', 'Predictive Modeling']
        skills_emphasis = ['Statistical Analysis', 'Data Visualization', 'Predictive Modeling']
        research_alignment = f"My background in statistical analysis, predictive modeling, and data visualization aligns perfectly with your research in {research_area}. I've achieved 22% improvement in user engagement through data-driven insights."
    elif research_area == 'Distributed Systems':
        highlighted_projects = ['Scalable System Architectures and Cloud Platforms']
        relevant_coursework = ['Distributed Systems', 'Cloud Computing', 'System Architecture', 'Performance Optimization']
        skills_emphasis = ['AWS', 'GCP', 'Docker', 'System Design']
        research_alignment = f"My experience with scalable system architectures, cloud computing, and distributed algorithm optimization directly complements your research in {research_area}. I have practical experience with AWS, GCP, and high-performance computing systems."
    else:  # Default for any other area
        highlighted_projects = ['VARtificial Intelligence', 'CrimeConnect', 'HackOps']
        relevant_coursework = ['Data Structures & Algorithms', 'Machine Learning', 'Database Management', 'Software Engineering']
        skills_emphasis = ['Python', 'Machine Learning', 'System Design', 'Full Stack Development']
        research_alignment = f"My diverse technical background and experience across multiple domains of computer science positions me well to contribute to your research in {research_area}."
    
    context = {
        'professor': {
            'last_name': professor_data['last_name'],
            'research_area': research_area,
            'research_title': research_area,
            'research_alignment': research_alignment,
            'highlighted_projects': highlighted_projects,
            'relevant_coursework': relevant_coursework,
            'skills_emphasis': skills_emphasis,
            'recent_publications_html': None
        }
    }
    
    html_content = Template(template_content).render(**context)
    subject = f"Research Internship Inquiry - {research_area}"
    
    return subject, html_content

def send_html_email_with_cv(recipient_email, subject, html_content, professor_name):
    """Send HTML email with CV attachment"""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("❌ Gmail credentials not found in environment variables")
        return False
    
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
        print(f"✅ Email sent successfully to {professor_name} ({recipient_email})")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {professor_name}: {e}")
        return False

def main():
    """Main function to send live emails to 3 truly fresh professors"""
    print("🚀 LIVE EMAIL CAMPAIGN - SENDING TO 3 TRULY FRESH PROFESSORS")
    print("=" * 80)
    print("📧 Using Enhanced Academic Research Template with Personalization")
    print("📎 CV attachments included automatically")
    print("🎯 Research area-specific content adaptation")
    print("🔍 Advanced filtering to exclude ALL previously contacted professors")
    print("=" * 80)
    print()
    
    # Get 3 truly fresh professors
    print("🔍 Finding professors who have NEVER been contacted...")
    fresh_professors = get_truly_fresh_professors(3)
    
    if not fresh_professors:
        print("❌ No truly fresh professors found!")
        print("💡 All professors in database may have been contacted already")
        return
    
    print(f"✅ Found {len(fresh_professors)} truly fresh professors to contact:")
    for i, prof in enumerate(fresh_professors, 1):
        print(f"   {i}. {prof['first_name']} {prof['last_name']} - {prof['university']}")
        print(f"      📧 {prof['email']} | 🎯 {prof['research_area']}")
    print()
    
    # Confirm before sending
    user_input = input("🤔 Ready to send live emails to these FRESH professors? (y/n): ")
    if user_input.lower() != 'y':
        print("❌ Email campaign cancelled by user.")
        return
    
    print()
    print("📤 STARTING LIVE EMAIL CAMPAIGN...")
    print("=" * 80)
    
    successful_sends = 0
    
    for i, professor in enumerate(fresh_professors, 1):
        print(f"\n📧 EMAIL {i}/{len(fresh_professors)}: {professor['first_name']} {professor['last_name']}")
        print(f"🏫 University: {professor['university']}")
        print(f"🎯 Research Area: {professor['research_area']}")
        print(f"📩 Email: {professor['email']}")
        
        # Create personalized email
        subject, html_content = create_personalized_academic_email(professor)
        print(f"📋 Subject: {subject}")
        
        # Send email
        success = send_html_email_with_cv(
            professor['email'], 
            subject, 
            html_content, 
            f"{professor['first_name']} {professor['last_name']}"
        )
        
        # Save to emailed list
        save_emailed_professor(professor, success)
        
        if success:
            successful_sends += 1
            print(f"✅ Email {i} sent successfully!")
        else:
            print(f"❌ Email {i} failed to send.")
        
        # Add delay between emails to avoid rate limiting
        if i < len(fresh_professors):
            print("⏳ Waiting 5 seconds before next email...")
            time.sleep(5)
    
    print("\n" + "=" * 80)
    print("📊 LIVE EMAIL CAMPAIGN RESULTS")
    print("=" * 80)
    print(f"📤 Total emails attempted: {len(fresh_professors)}")
    print(f"✅ Successfully sent: {successful_sends}")
    print(f"❌ Failed to send: {len(fresh_professors) - successful_sends}")
    print(f"📈 Success rate: {(successful_sends/len(fresh_professors)*100):.1f}%")
    
    if successful_sends > 0:
        print("\n🎉 CAMPAIGN FEATURES DEPLOYED:")
        print("✅ Enhanced Academic Research Template")
        print("✅ Research area-specific personalization")
        print("✅ CV attachments included")
        print("✅ Professional HTML styling")
        print("✅ Tailored project highlighting")
        print("✅ Customized research alignment")
        print("✅ Advanced duplicate detection")
        
        print("\n📧 Fresh professors contacted with personalized emails:")
        for prof in fresh_professors:
            print(f"   • {prof['first_name']} {prof['last_name']} ({prof['research_area']})")
    
    print("\n" + "=" * 80)
    print("🚀 LIVE EMAIL CAMPAIGN TO TRULY FRESH PROFESSORS COMPLETED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
