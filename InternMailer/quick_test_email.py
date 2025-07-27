#!/usr/bin/env python3
"""
Quick test email generation without AI parsing
"""

import os
import sys
from dotenv import load_dotenv
from jinja2 import Template

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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
    
    # Mock student info (based on your actual info)
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
    
    print("🎯 Generating test email for Barbara Liskov...")
    print(f"Professor: {barbara_liskov['Name']}")
    print(f"Research Area: {barbara_liskov['Research Area']}")
    print(f"Email: {barbara_liskov['Email']}")
    print()
    
    # Generate subject
    subject = f"Research Internship Inquiry – {student_info['name']} re: {barbara_liskov['Research Area']}"
    
    # Generate email body using template
    email_template = """Dear Prof. {{ professor.Name }},

I am {{ student.name }}, currently pursuing {{ student.degree }} at {{ student.university }} (CGPA: {{ student.cgpa }}). I am writing to express my strong interest in your research on {{ professor['Research Area'] }}.

I bring practical experience as {{ student.experience[0] if student.experience else 'a technical professional' }}, where I gained valuable hands-on experience in software development and data analysis, particularly in distributed systems and data management.

My technical expertise includes {{ student.skills[:8] | join(', ') }}, among other technologies. Notable projects from my portfolio include:

{% for project in student.projects[:3] %}
• **{{ project }}**{% if project == 'CrimeConnect' %}: Engineered an FBI-inspired case management dashboard using MERN stack and Supabase, reducing case processing time by 40%{% elif project == 'VARtificial Intelligence' %}: Developed a machine learning-based predictor using XGBoost, achieving 89% accuracy{% elif project == 'HackOps' %}: Built a gamified cybersecurity training platform with 25+ challenges, improving user cyber-awareness by 35%{% elif project == 'Flora Fight Frenzy' %}: Created a game achieving 90% UI fidelity and 4.8/5 rating{% endif %}
{% endfor %}

My coursework in {{ student.courses[:6] | join(', ') }} has provided me with a strong theoretical foundation in distributed systems, while my project work demonstrates practical application of these concepts.

I am eager to contribute to your research group and would welcome the opportunity to discuss how my background aligns with your current projects. I am particularly interested in {{ professor['Research Area'].lower() }} and believe I could add value through my experience with {{ student.skills[:3] | join(', ') }}.

I have attached my resume ({{ student.resume_prefix }}) for your review. Thank you for considering my application.

Sincerely,  
{{ student.name }}  
{{ student.email }}  
{{ student.degree }}  
{{ student.university }}"""
    
    template = Template(email_template)
    body = template.render(student=student_info, professor=barbara_liskov)
    
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
            print("GMAIL_USER=liskov@csail.mit.edu")
            print("GMAIL_APP_PASSWORD=your-actual-app-password")
            return
        
        print(f"📤 Sending test email to {test_recipient}...")
        
        # Find resume file
        resume_path = None
        if os.path.exists('resumes'):
            resume_files = [f for f in os.listdir('resumes') if f.endswith('.pdf')]
            if resume_files:
                resume_path = os.path.join('resumes', resume_files[0])
        
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
If you approve this email format, reply with "APPROVED" to proceed with bulk sending to UI/UX professors.
"""
        
        success = sender.send_email(test_recipient, test_subject, test_body, resume_path)
        
        if success:
            print("✅ Test email sent successfully!")
            print("📬 Please check your email and approve to proceed with bulk campaign")
            print()
            print("Next steps:")
            print("1. Check your email inbox")
            print("2. Review the email format")
            print("3. If approved, run: python bulk_email_campaign.py")
        else:
            print("❌ Failed to send test email")
            print("Check your Gmail credentials and internet connection")
    else:
        print("📝 Test email generation completed. No email sent.")
        print()
        print("Next steps:")
        print("1. Review the email content above")
        print("2. If satisfied, run this script again and choose 'y' to send test")
        print("3. After approval, run: python bulk_email_campaign.py")

if __name__ == "__main__":
    main()
