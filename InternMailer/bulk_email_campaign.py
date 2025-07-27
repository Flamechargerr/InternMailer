#!/usr/bin/env python3
"""
Bulk email campaign for UI/UX professors
"""

import os
import sys
import pandas as pd
import time
from dotenv import load_dotenv
from jinja2 import Template

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_sender import GmailSender

load_dotenv()

def load_uiux_professors():
    """Load UI/UX related professors from CSV"""
    df = pd.read_csv('data/proffesor.csv', on_bad_lines='skip')
    
    # Filter for UI/UX related research areas
    uiux_keywords = ['ui', 'ux', 'user interface', 'user experience', 'human-computer', 'hci', 
                     'human-ai interaction', 'interaction', 'visualization', 'interface',
                     'human-ai', 'ai visualization', 'computational linguistics']
    
    uiux_profs = []
    for _, row in df.iterrows():
        research_area = str(row.get('Research Area', '')).lower()
        if any(keyword in research_area for keyword in uiux_keywords):
            prof = {
                'Name': row.get('Name', ''),
                'Email': row.get('Email', ''),
                'University': row.get('University', ''),
                'Research Area': row.get('Research Area', ''),
                'Homepage': row.get('Homepage', '')
            }
            
            # Validate email
            if prof['Email'] and '@' in prof['Email'] and '.' in prof['Email']:
                uiux_profs.append(prof)
    
    return uiux_profs

def generate_personalized_email(professor, student_info):
    """Generate personalized email for a professor"""
    
    # Generate subject
    subject = f"Research Internship Inquiry – {student_info['name']} re: {professor['Research Area']}"
    
    # Email template
    email_template = """Dear Prof. {{ professor.Name }},

I am {{ student.name }}, currently pursuing {{ student.degree }} at {{ student.university }} (CGPA: {{ student.cgpa }}). I am writing to express my strong interest in your research on {{ professor['Research Area'] }}.

{% if 'human' in professor['Research Area'].lower() or 'interaction' in professor['Research Area'].lower() %}
I bring practical experience as {{ student.experience[0] if student.experience else 'a technical professional' }}, where I gained valuable hands-on experience in user interface development and human-computer interaction, particularly through my work on interactive applications and user-centered design.
{% elif 'visualization' in professor['Research Area'].lower() %}
I bring practical experience as {{ student.experience[0] if student.experience else 'a technical professional' }}, where I gained valuable experience in data visualization and interactive dashboard development, particularly in creating intuitive user interfaces for complex data systems.
{% else %}
I bring practical experience as {{ student.experience[0] if student.experience else 'a technical professional' }}, where I gained valuable hands-on experience in software development and user interface design.
{% endif %}

My technical expertise includes {{ student.skills[:8] | join(', ') }}, among other technologies. Notable projects from my portfolio include:

{% for project in student.projects[:3] %}
• **{{ project }}**{% if project == 'CrimeConnect' %}: Engineered an FBI-inspired case management dashboard using MERN stack and Supabase, focusing on intuitive user experience and reducing case processing time by 40%{% elif project == 'VARtificial Intelligence' %}: Developed a machine learning-based predictor with an interactive web interface using XGBoost, achieving 89% accuracy{% elif project == 'HackOps' %}: Built a gamified cybersecurity training platform with engaging UI/UX design and 25+ interactive challenges, improving user cyber-awareness by 35%{% elif project == 'Flora Fight Frenzy' %}: Created a game with carefully crafted user interface achieving 90% UI fidelity and 4.8/5 user rating{% endif %}
{% endfor %}

My coursework in {{ student.courses[:6] | join(', ') }} has provided me with a strong theoretical foundation, while my project work demonstrates practical application of user-centered design principles and interface development.

I am eager to contribute to your research group and would welcome the opportunity to discuss how my background in interactive systems and user interface development aligns with your current projects. I am particularly interested in {{ professor['Research Area'].lower() }} and believe I could add value through my experience with {{ student.skills[:3] | join(', ') }}.

I have attached my resume ({{ student.resume_prefix }}) for your review. Thank you for considering my application.

Sincerely,  
{{ student.name }}  
{{ student.email }}  
{{ student.degree }}  
{{ student.university }}"""
    
    template = Template(email_template)
    body = template.render(student=student_info, professor=professor)
    
    return subject, body

def main():
    print("🚀 Starting UI/UX Professor Bulk Email Campaign")
    print("=" * 50)
    
    # Student info
    student_info = {
        'name': 'Anamay Tripathy',
        'email': 'tripathy.anamay23@gmail.com',
        'university': 'Manipal Institute of Technology',
        'degree': 'B.Tech Data Science Engineering',
        'cgpa': '7.6/10',
        'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Machine Learning', 
                  'Data Analytics', 'TensorFlow', 'MongoDB', 'Git', 'Docker', 'AWS'],
        'projects': ['CrimeConnect', 'VARtificial Intelligence', 'HackOps', 'Flora Fight Frenzy'],
        'experience': ['Data Analyst Intern at XYZ Company'],
        'courses': ['Data Science', 'Machine Learning', 'Database Management Systems', 
                   'Computer Networks', 'Web Technologies', 'Statistics'],
        'resume_prefix': 'CV_Anamay_Modern'
    }
    
    # Load professors
    print("📊 Loading UI/UX professors...")
    professors = load_uiux_professors()
    print(f"Found {len(professors)} UI/UX related professors")
    
    if not professors:
        print("❌ No UI/UX professors found!")
        return
    
    # Show preview
    print("\n📋 Professor List Preview:")
    for i, prof in enumerate(professors[:5]):
        print(f"{i+1}. {prof['Name']} ({prof['University']}) - {prof['Research Area']}")
    if len(professors) > 5:
        print(f"... and {len(professors) - 5} more")
    
    # Check credentials
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password or gmail_password == 'your_app_password_here':
        print("\n❌ Gmail credentials not configured!")
        print("Please update .env file with:")
        print("GMAIL_USER=liskov@csail.mit.edu")
        print("GMAIL_APP_PASSWORD=your-actual-app-password")
        return
    
    # Find resume
    resume_path = None
    if os.path.exists('resumes'):
        resume_files = [f for f in os.listdir('resumes') if f.endswith('.pdf')]
        if resume_files:
            resume_path = os.path.join('resumes', resume_files[0])
            print(f"📄 Using resume: {resume_files[0]}")
    
    # Confirm before sending
    print(f"\n⚠️  READY TO SEND {len(professors)} EMAILS")
    print(f"From: {gmail_user}")
    print(f"Resume: {resume_path if resume_path else 'None'}")
    
    confirm = input("\nProceed with bulk sending? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Campaign cancelled")
        return
    
    # Initialize sender
    sender = GmailSender(gmail_user, gmail_password)
    
    # Send emails
    print(f"\n📧 Starting to send {len(professors)} emails...")
    sent_count = 0
    failed_count = 0
    
    for i, professor in enumerate(professors, 1):
        print(f"\nProcessing {i}/{len(professors)}: {professor['Name']}")
        
        try:
            # Generate email
            subject, body = generate_personalized_email(professor, student_info)
            
            # Send email
            success = sender.send_email(professor['Email'], subject, body, resume_path)
            
            if success:
                sent_count += 1
                print(f"✅ Sent to {professor['Name']} ({professor['Email']})")
            else:
                failed_count += 1
                print(f"❌ Failed to send to {professor['Name']} ({professor['Email']})")
            
            # Rate limiting - wait between emails
            if i < len(professors):  # Don't wait after the last email
                wait_time = 5  # 5 seconds between emails
                print(f"⏱️  Waiting {wait_time}s before next email...")
                time.sleep(wait_time)
                
        except Exception as e:
            failed_count += 1
            print(f"❌ Error with {professor['Name']}: {e}")
    
    # Final report
    print(f"\n🎉 Campaign Complete!")
    print(f"✅ Successfully sent: {sent_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Success rate: {(sent_count/len(professors)*100):.1f}%")
    
    if os.path.exists('email_log.csv'):
        print(f"📋 Check email_log.csv for detailed results")

if __name__ == "__main__":
    main()
