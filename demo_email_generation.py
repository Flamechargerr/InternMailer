#!/usr/bin/env python3
"""
Demo script to test enhanced email generation with Anamay's actual CV data
"""

import sys
import os
sys.path.append('InternMailer/src')

from resume_parser import ResumeParser
from email_generator import EmailGenerator
import json

def demo_email_generation():
    """Demo the enhanced email generation system"""
    print("=== InternMailer Enhanced Email Generation Demo ===\n")
    
    # Parse the actual CV
    cv_path = 'resumes/CV_Anamay_Modern.pdf'
    if not os.path.exists(cv_path):
        print("❌ CV file not found. Please ensure CV_Anamay_Modern.pdf is in the resumes/ folder.")
        return
    
    print("📄 Parsing CV...")
    parser = ResumeParser(cv_path)
    student_info = parser.parse()
    
    # Add additional info
    student_info['name'] = 'Anamay Tripathy'
    student_info['email'] = 'tripathy.anamay23@gmail.com'
    student_info['university'] = 'Manipal Institute of Technology'
    student_info['resume_prefix'] = 'CV_Anamay_Modern'
    
    print(f"✅ Parsed CV successfully!")
    print(f"   Skills: {len(student_info.get('skills', []))} found")
    print(f"   Projects: {len(student_info.get('projects', []))} found")
    print(f"   Courses: {len(student_info.get('courses', []))} found")
    print(f"   Experience: {len(student_info.get('experience', []))} found")
    
    # Create sample professors with different research areas
    sample_professors = [
        {
            'Name': 'Dr. Sarah Johnson',
            'University': 'Stanford University',
            'Research Area': 'Machine Learning and AI',
            'Email': 'tripathy.anamay23@gmail.com'  # Your email for demo
        },
        {
            'Name': 'Dr. Michael Chen',
            'University': 'MIT',
            'Research Area': 'Web Security and Cybersecurity',
            'Email': 'tripathy.anamay23@gmail.com'  # Your email for demo
        },
        {
            'Name': 'Dr. Emily Rodriguez',
            'University': 'UC Berkeley',
            'Research Area': 'Data Analytics and Visualization',
            'Email': 'tripathy.anamay23@gmail.com'  # Your email for demo
        }
    ]
    
    # Initialize email generator
    email_gen = EmailGenerator(student_info, use_ollama=False)  # Use template for now
    
    print("\n" + "="*60)
    print("GENERATING PERSONALIZED EMAILS")
    print("="*60)
    
    generated_emails = []
    
    for i, prof in enumerate(sample_professors, 1):
        print(f"\n📧 Email {i}: Prof. {prof['Name']} ({prof['Research Area']})")
        print("-" * 50)
        
        # Find relevant skills and projects for this professor
        relevant = email_gen.find_relevant_skills_and_projects(prof)
        print(f"🎯 Relevant Skills: {', '.join(relevant['skills'][:5])}")
        print(f"🎯 Relevant Projects: {', '.join(relevant['projects'])}")
        
        # Generate subject
        subject = email_gen.generate_subject(prof)
        print(f"📨 Subject: {subject}")
        
        # Generate body using enhanced prompt
        try:
            # Try LLM if available, otherwise use template
            body = email_gen.generate_with_llm(prof)
            if not body or body.strip() == "":
                body = email_gen.generate_body(prof)
            
            print(f"📝 Body Preview (first 300 chars):")
            print(f"   {body[:300]}...")
            
            generated_emails.append({
                'professor': prof,
                'subject': subject,
                'body': body,
                'relevant_skills': relevant['skills'],
                'relevant_projects': relevant['projects']
            })
            
        except Exception as e:
            print(f"❌ Error generating email: {e}")
    
    # Show summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    print(f"✅ Successfully generated {len(generated_emails)} personalized emails")
    print(f"📊 CV Data Extracted:")
    print(f"   • {len(student_info.get('skills', []))} technical skills")
    print(f"   • {len(student_info.get('projects', []))} projects")
    print(f"   • {len(student_info.get('experience', []))} work experiences")
    print(f"   • {len(student_info.get('courses', []))} relevant courses")
    
    # Save generated emails to file for review
    with open('demo_generated_emails.json', 'w', encoding='utf-8') as f:
        json.dump({
            'student_info': student_info,
            'generated_emails': generated_emails
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Demo results saved to 'demo_generated_emails.json'")
    print("\n🎉 Demo completed! The system now generates highly personalized emails based on your actual CV data.")
    
    return generated_emails

if __name__ == "__main__":
    demo_email_generation()
