#!/usr/bin/env python3
"""
Professor Email Template Test
Generate and send actual professor email template for approval
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add paths
sys.path.append('InternMailer/src')
sys.path.append('InternMailer/scheduler')

from gmail_sender import GmailSender
from email_generator import EmailGenerator
from resume_parser import ResumeParser

def generate_professor_test_email():
    """Generate actual professor email template for testing"""
    load_dotenv()
    
    print("🎯 Generating Professor Email Template...")
    
    # Load a sample professor for testing
    try:
        df = pd.read_csv('data/proffesor.csv', on_bad_lines='skip', encoding='utf-8', 
                       names=['University', 'Name', 'Email', 'Homepage', 'Research Area'], 
                       header=None, skiprows=1)
        
        # Clean the data
        df = df.dropna(subset=['Email'])
        df = df[df['Email'].str.contains('@', na=False)]
        df = df[df['University'] != 'University']
        df = df[df['Email'] != 'Email']
        df = df.dropna(how='all')
        
        # Get first professor as sample
        sample_prof = df.iloc[0].to_dict()
        print(f"📋 Sample Professor: {sample_prof['Name']} at {sample_prof['University']}")
        print(f"🔬 Research Area: {sample_prof['Research Area']}")
        
    except Exception as e:
        print(f"❌ Error loading professor data: {e}")
        # Fallback sample professor
        sample_prof = {
            'Name': 'Dr. John Smith',
            'University': 'Stanford University',
            'Email': 'john.smith@stanford.edu',
            'Research Area': 'Machine Learning',
            'Homepage': 'https://stanford.edu/~jsmith'
        }
        print(f"📋 Using fallback professor: {sample_prof['Name']}")
    
    # Parse resume if available
    resume_files = []
    if os.path.exists('resumes'):
        resume_files = [f for f in os.listdir('resumes') if f.endswith('.pdf')]
    
    if resume_files:
        resume_path = os.path.join('resumes', resume_files[0])
        print(f"📄 Using resume: {resume_files[0]}")
        
        try:
            # Parse resume
            parser = ResumeParser(resume_path)
            student_info = parser.parse()
            student_info['name'] = "Anamay Tripathy"
            student_info['email'] = "tripathy.anamay23@gmail.com"
            student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
            student_info['season'] = "Summer"
            student_info['funding'] = "Any"
            
            print(f"✅ Resume parsed successfully")
            print(f"📊 Skills found: {len(student_info.get('skills', []))} skills")
            print(f"📚 Projects found: {len(student_info.get('projects', []))} projects")
            
        except Exception as e:
            print(f"⚠️ Error parsing resume: {e}")
            # Fallback student info
            student_info = {
                'name': 'Anamay Tripathy',
                'email': 'tripathy.anamay23@gmail.com',
                'skills': ['Python', 'Machine Learning', 'Data Analysis', 'Deep Learning'],
                'projects': ['AI Research Project', 'Data Science Application'],
                'courses': ['Computer Science', 'Mathematics', 'Statistics'],
                'summary': 'Data Science Engineering student with strong technical skills'
            }
            resume_path = None
    else:
        print("⚠️ No resume found, using default student info")
        student_info = {
            'name': 'Anamay Tripathy',
            'email': 'tripathy.anamay23@gmail.com',
            'skills': ['Python', 'Machine Learning', 'Data Analysis'],
            'projects': ['Web Application', 'Data Analysis Project'],
            'courses': ['Computer Science', 'Mathematics'],
            'summary': 'Computer Science student seeking research opportunities'
        }
        resume_path = None
    
    # Generate email using AI/template
    try:
        email_gen = EmailGenerator(student_info, use_ollama=True, ollama_model='gemma3:latest')
        
        # Generate subject
        subject = email_gen.generate_subject(sample_prof)
        print(f"📧 Generated Subject: {subject}")
        
        # Generate body with custom prompt
        research_area = sample_prof.get('Research Area', '')
        professor_name = sample_prof.get('Name', '')
        university = sample_prof.get('University', '')
        
        custom_prompt = f"""
Write a professional, personalized research internship inquiry email from Anamay Tripathy to Prof. {professor_name} at {university}.
Their research area is: {research_area}.
My background: {student_info.get('summary', 'Computer Science student with strong technical skills')}
My skills: {', '.join(student_info.get('skills', ['Python', 'Machine Learning', 'Data Analysis']))}
My projects: {', '.join(student_info.get('projects', ['Web applications', 'Data analysis projects']))}
My courses: {', '.join(student_info.get('courses', ['Computer Science', 'Mathematics', 'Statistics']))}
My email: {student_info['email']}
The email should be concise, polite, and mention why I am interested in their work.
"""
        
        try:
            # Try template generation first (more reliable)
            body = email_gen.generate_body(sample_prof)
            if body and body.strip():
                print("✅ Template-based email body created")
            else:
                print("🔄 Template failed, trying LLM generation")
                body = email_gen.generate_with_llm(sample_prof, custom_prompt=custom_prompt)
                if body and body.strip():
                    print("🤖 AI-generated email body created")
                else:
                    print("⚠️ Both template and LLM failed, using fallback")
                    body = email_gen.generate_fallback_body(sample_prof)
        except Exception as e:
            print(f"⚠️ Email generation failed: {e}")
            print("🔄 Using fallback template")
            body = email_gen.generate_fallback_body(sample_prof)
        
    except Exception as e:
        print(f"⚠️ EmailGenerator error: {e}")
        # Fallback manual template
        subject = f"Research Internship Inquiry - {research_area}"
        body = f"""Dear Professor {professor_name},

I hope this email finds you well. I am Anamay Tripathy, a Data Science Engineering student with a strong interest in {research_area}.

I have been following your research at {university} and am particularly interested in your work in {research_area}. Your contributions to this field align perfectly with my academic interests and career goals.

My technical background includes:
• Programming: {', '.join(student_info.get('skills', ['Python', 'Machine Learning']))}
• Projects: {', '.join(student_info.get('projects', ['Data analysis applications']))}
• Coursework: {', '.join(student_info.get('courses', ['Computer Science', 'Mathematics']))}

I would be honored to contribute to your research team and learn from your expertise. I am available for Summer internships and am flexible with funding arrangements.

I have attached my resume for your review and would welcome the opportunity to discuss potential research opportunities.

Thank you for your time and consideration.

Best regards,
Anamay Tripathy
Email: {student_info['email']}"""
    
    return subject, body, sample_prof, resume_path

def send_test_professor_email():
    """Send the actual professor email template to yourself for approval"""
    
    # Generate the email
    subject, body, sample_prof, resume_path = generate_professor_test_email()
    
    # Load Gmail credentials
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("❌ Gmail credentials not configured")
        return False
    
    # Initialize sender
    sender = GmailSender(gmail_user, gmail_password)
    
    # Create test email subject
    test_subject = f"[TEST EMAIL] {subject}"
    
    # Create test email body with context
    test_body = f"""🧪 THIS IS A TEST EMAIL FOR APPROVAL
==========================================

This is exactly how your email will appear to professors.
If you approve this template, reply with "APPROVED" and I'll proceed with bulk sending.

Target Professor (Sample): {sample_prof['Name']} at {sample_prof['University']}
Research Area: {sample_prof['Research Area']}

EMAIL CONTENT BELOW:
==========================================

Subject: {subject}

{body}

==========================================
END OF PROFESSOR EMAIL

📊 BULK SEND DETAILS:
• Total professors in database: ~900+
• Will skip already contacted professors
• Rate limited: 2-5 seconds between emails
• Resume attachment: {"Yes" if resume_path else "No"}

Reply "APPROVED" to proceed with bulk sending to all professors.
Reply "MODIFY" if you want to change the template.
"""
    
    print("📤 Sending test professor email template...")
    
    try:
        success = sender.send_email(
            to_email=gmail_user,
            subject=test_subject,
            body=test_body,
            attachment_path=resume_path
        )
        
        if success:
            print("✅ Test professor email sent successfully!")
            print(f"📬 Check your inbox at {gmail_user}")
            print("\n🎯 NEXT STEPS:")
            print("1. Check your email for the professor template")
            print("2. Review the email content and format")
            print("3. Reply 'APPROVED' if you want to proceed with bulk sending")
            print("4. Reply 'MODIFY' if you want to change anything")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False

if __name__ == "__main__":
    print("🎯 InternMailer Professor Email Template Test")
    print("=" * 60)
    
    success = send_test_professor_email()
    
    if success:
        print("\n🎉 Professor email template sent for your approval!")
        print("📧 Check your email and reply with your decision")
    else:
        print("\n❌ Failed to send test email")
        print("🔧 Please check your Gmail configuration")
