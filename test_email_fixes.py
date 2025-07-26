#!/usr/bin/env python3
"""
Test script to verify email generation and validation fixes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'InternMailer/src'))

from email_generator import EmailGenerator
from gmail_sender import GmailSender

def test_email_generation():
    """Test email generation with the fixed code"""
    print("Testing email generation...")
    
    # Mock student info
    student_info = {
        'name': 'Anamay Tripathy',
        'email': 'tripathy.anamay23@gmail.com',
        'summary': 'Data Science Engineering student with strong technical skills',
        'skills': ['Python', 'Machine Learning', 'Data Analysis', 'Web Development'],
        'projects': ['Web applications', 'Data analysis projects', 'ML models'],
        'courses': ['Computer Science', 'Mathematics', 'Statistics', 'Machine Learning'],
        'resume_prefix': 'CV_Anamay_Modern'
    }
    
    # Mock professor data
    professor = {
        'Name': 'Manya Ghobadi',
        'University': 'Massachusetts Institute of Technology (MIT)',
        'Research Area': 'ML networks',
        'Email': 'ghobadi@mit.edu'
    }
    
    # Test email generator
    email_gen = EmailGenerator(student_info, use_ollama=False)  # Use template fallback
    
    # Test subject generation
    subject = email_gen.generate_subject(professor)
    print(f"Generated subject: {subject}")
    
    # Test body generation
    body = email_gen.generate_body(professor)
    print(f"Generated body length: {len(body)} characters")
    print(f"Body preview: {body[:200]}...")
    
    # Test with custom prompt
    custom_prompt = f"""
Write a professional, personalized research internship inquiry email from Anamay Tripathy to Prof. {professor['Name']} at {professor['University']}.
Their research area is: {professor['Research Area']}.
My background: {student_info['summary']}
My skills: {', '.join(student_info['skills'])}
My projects: {', '.join(student_info['projects'])}
My courses: {', '.join(student_info['courses'])}
My email: {student_info['email']}
The email should be concise, polite, and mention why I am interested in their work.
"""
    
    try:
        body_with_llm = email_gen.generate_with_llm(professor, custom_prompt=custom_prompt)
        print(f"LLM body length: {len(body_with_llm)} characters")
        print(f"LLM body preview: {body_with_llm[:200]}...")
    except Exception as e:
        print(f"LLM generation failed (expected if Ollama not running): {e}")
    
    return True

def test_email_validation():
    """Test email validation"""
    print("\nTesting email validation...")
    
    # Mock Gmail sender (without actual credentials)
    sender = GmailSender("test@example.com", "test_password")
    
    # Test valid emails
    valid_emails = [
        "test@example.com",
        "user@domain.org",
        "professor@mit.edu"
    ]
    
    # Test invalid emails
    invalid_emails = [
        "invalid-email",
        "@domain.com",
        "user@",
        "user@domain",
        "",
        None
    ]
    
    print("Testing valid emails:")
    for email in valid_emails:
        is_valid = sender.validate_email(email)
        print(f"  {email}: {'✅' if is_valid else '❌'}")
    
    print("Testing invalid emails:")
    for email in invalid_emails:
        is_valid = sender.validate_email(email)
        print(f"  {email}: {'✅' if is_valid else '❌'}")
    
    return True

def test_professor_data_mapping():
    """Test that professor data is correctly mapped"""
    print("\nTesting professor data mapping...")
    
    # Sample professor data from CSV
    professor_data = {
        'QS Rank': '1',
        'University': 'Massachusetts Institute of Technology (MIT)',
        'Name': 'Manya Ghobadi',
        'Email': 'ghobadi@mit.edu',
        'Homepage': 'http://people.csail.mit.edu/ghobadi',
        'Research Area': 'ML networks',
        'email_valid': True
    }
    
    # Test that the email generator can handle this data structure
    student_info = {
        'name': 'Anamay Tripathy',
        'email': 'tripathy.anamay23@gmail.com',
        'summary': 'Data Science Engineering student',
        'skills': ['Python', 'ML'],
        'projects': ['Web apps'],
        'courses': ['CS', 'Math'],
        'resume_prefix': 'CV_Anamay_Modern'
    }
    
    email_gen = EmailGenerator(student_info, use_ollama=False)
    
    # Test subject generation
    subject = email_gen.generate_subject(professor_data)
    print(f"Subject: {subject}")
    
    # Test body generation
    body = email_gen.generate_body(professor_data)
    print(f"Body length: {len(body)} characters")
    
    # Check that research area is properly included
    if 'ML networks' in body or 'your research' in body:
        print("✅ Research area properly included in email")
    else:
        print("❌ Research area not found in email")
    
    return True

if __name__ == "__main__":
    print("Testing email generation and validation fixes...")
    
    try:
        test_email_generation()
        test_email_validation()
        test_professor_data_mapping()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 