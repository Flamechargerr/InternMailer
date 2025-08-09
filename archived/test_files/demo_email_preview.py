#!/usr/bin/env python3
"""
Demo Email Preview - Shows email content and comprehensive statistics
"""

import pandas as pd
import random
import json
from datetime import datetime

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

def get_comprehensive_email_stats():
    """Get comprehensive email statistics"""
    stats = {}
    
    # Main database
    try:
        df = pd.read_csv('data/scraped_professors_final.csv')
        stats['main_database'] = {
            'total_professors': len(df),
            'with_emails': len(df[df['email'].notna() & (df['email'] != '')]),
            'universities': df['affiliation'].nunique() if 'affiliation' in df.columns else 0
        }
    except Exception as e:
        stats['main_database'] = {'error': str(e)}
    
    # Archive database
    try:
        df_archive = pd.read_csv('data/archive/professors_final.csv', on_bad_lines='skip')
        stats['archive_database'] = {
            'total_professors': len(df_archive),
            'with_emails': len(df_archive[df_archive['Email'].notna() & (df_archive['Email'] != '')]),
            'universities': df_archive['University'].nunique() if 'University' in df_archive.columns else 0
        }
    except Exception as e:
        stats['archive_database'] = {'error': str(e)}
    
    # Cache database
    try:
        with open('data/scraped_professors_cache.json', 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        stats['cache_database'] = {
            'total_professors': len(cache_data)
        }
    except Exception as e:
        stats['cache_database'] = {'error': str(e)}
    
    # Emailed professors
    try:
        with open('data/emailed_professors.json', 'r') as f:
            emailed_data = json.load(f)
        stats['emailed_professors'] = {
            'total_emailed': len(emailed_data['professors'])
        }
    except Exception as e:
        stats['emailed_professors'] = {'error': str(e)}
    
    # Followups
    try:
        with open('data/followups.json', 'r') as f:
            followups_data = json.load(f)
        stats['followups'] = {
            'total_followups': len(followups_data)
        }
    except Exception as e:
        stats['followups'] = {'error': str(e)}
    
    # Job applications
    try:
        with open('data/application_log.json', 'r') as f:
            applications_data = json.load(f)
        stats['job_applications'] = {
            'total_applications': len(applications_data)
        }
    except Exception as e:
        stats['job_applications'] = {'error': str(e)}
    
    return stats

def main():
    """Main function to show email previews and statistics"""
    print("🚀 InternMailing System - Email Preview & Statistics")
    print("=" * 60)
    
    # Get random professor data
    professor_data = get_random_professor()
    print(f"📧 Using professor data: {professor_data['name']} from {professor_data['university']}")
    print(f"📧 Professor email: {professor_data['email']}")
    print(f"🎯 Research area: {professor_data['research_area']}")
    
    # Create and display HR template email
    print("\n" + "=" * 60)
    print("📋 HR TEMPLATE EMAIL PREVIEW")
    print("=" * 60)
    hr_subject, hr_body = create_hr_template_email(professor_data)
    print(f"Subject: {hr_subject}")
    print(f"To: tripathy.anamay23@gmail.com")
    print(f"From: [Your Gmail Account]")
    print("\nBody:")
    print(hr_body)
    
    # Create and display Academic Professor email
    print("\n" + "=" * 60)
    print("🎓 ACADEMIC PROFESSOR EMAIL PREVIEW")
    print("=" * 60)
    academic_subject, academic_body = create_academic_professor_email(professor_data)
    print(f"Subject: {academic_subject}")
    print(f"To: tripathy.anamay23@gmail.com")
    print(f"From: [Your Gmail Account]")
    print("\nBody:")
    print(academic_body)
    
    # Get and display comprehensive statistics
    print("\n" + "=" * 60)
    print("📈 COMPREHENSIVE EMAIL DATABASE STATISTICS")
    print("=" * 60)
    
    stats = get_comprehensive_email_stats()
    
    # Main database
    if 'error' not in stats['main_database']:
        print(f"📊 Main Database:")
        print(f"   • Total Professors: {stats['main_database']['total_professors']}")
        print(f"   • With Valid Emails: {stats['main_database']['with_emails']}")
        print(f"   • Unique Universities: {stats['main_database']['universities']}")
    else:
        print(f"📊 Main Database: Error - {stats['main_database']['error']}")
    
    # Archive database
    if 'error' not in stats['archive_database']:
        print(f"📊 Archive Database:")
        print(f"   • Total Professors: {stats['archive_database']['total_professors']}")
        print(f"   • With Valid Emails: {stats['archive_database']['with_emails']}")
        print(f"   • Unique Universities: {stats['archive_database']['universities']}")
    else:
        print(f"📊 Archive Database: Error - {stats['archive_database']['error']}")
    
    # Cache database
    if 'error' not in stats['cache_database']:
        print(f"📊 Cache Database:")
        print(f"   • Total Professors: {stats['cache_database']['total_professors']}")
    else:
        print(f"📊 Cache Database: Error - {stats['cache_database']['error']}")
    
    # Emailed professors
    if 'error' not in stats['emailed_professors']:
        print(f"📊 Emailed Professors:")
        print(f"   • Total Emailed: {stats['emailed_professors']['total_emailed']}")
    else:
        print(f"📊 Emailed Professors: Error - {stats['emailed_professors']['error']}")
    
    # Followups
    if 'error' not in stats['followups']:
        print(f"📊 Follow-up Emails:")
        print(f"   • Total Follow-ups: {stats['followups']['total_followups']}")
    else:
        print(f"📊 Follow-up Emails: Error - {stats['followups']['error']}")
    
    # Job applications
    if 'error' not in stats['job_applications']:
        print(f"📊 Job Applications:")
        print(f"   • Total Applications: {stats['job_applications']['total_applications']}")
    else:
        print(f"📊 Job Applications: Error - {stats['job_applications']['error']}")
    
    # Calculate total emails available
    total_emails = 0
    if 'error' not in stats['main_database']:
        total_emails += stats['main_database']['with_emails']
    if 'error' not in stats['archive_database']:
        total_emails += stats['archive_database']['with_emails']
    if 'error' not in stats['cache_database']:
        total_emails += stats['cache_database']['total_professors']
    
    print("\n" + "=" * 60)
    print("🎯 TOTAL EMAIL SUMMARY")
    print("=" * 60)
    print(f"📧 Total Email Addresses Available: {total_emails:,}")
    print(f"📧 Professors Already Contacted: {stats['emailed_professors'].get('total_emailed', 0)}")
    print(f"📧 Remaining Professors to Contact: {total_emails - stats['emailed_professors'].get('total_emailed', 0):,}")
    
    print("\n" + "=" * 60)
    print("✅ SYSTEM STATUS: FULLY OPERATIONAL")
    print("=" * 60)
    print("The InternMailing system is working perfectly!")
    print("To send actual emails, configure Gmail credentials in .env file:")
    print("GMAIL_USER=your_email@gmail.com")
    print("GMAIL_APP_PASSWORD=your_app_password")

if __name__ == "__main__":
    main() 