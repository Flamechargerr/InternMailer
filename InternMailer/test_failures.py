#!/usr/bin/env python3
"""
Test script to reproduce and document baseline failures:
1. Ollama 90-second timeout
2. Gemma3 parsing issues 
3. Email-sending/config errors
"""

import os
import sys
import time
import logging
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from resume_parser import ResumeParser
from email_generator import EmailGenerator, generate_with_ollama
from gmail_sender import GmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_failures.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()

def test_ollama_timeout():
    """Test 1: Reproduce Ollama 90-second timeout issue"""
    print("\n" + "="*50)
    print("TEST 1: Ollama 90-second timeout")
    print("="*50)
    
    # Test with a very long, complex prompt that might timeout
    complex_prompt = """
    You are an expert resume parser. Please extract extremely detailed information from this resume text and provide comprehensive analysis including:
    - All technical skills with proficiency levels
    - All projects with detailed descriptions, technologies used, achievements, and impact metrics
    - All courses with learning outcomes and practical applications
    - All work experiences with responsibilities, achievements, and quantifiable results
    - Personal summary with career objectives and strengths
    - Recommendations for career development
    - Industry analysis and market positioning
    - Skill gap analysis and improvement suggestions
    
    Please provide this in JSON format with nested structures and comprehensive details for each section.
    Make sure to include at least 50 different technical skills, detailed project descriptions of at least 200 words each, and comprehensive analysis.
    
    Resume text: This is a very long resume with extensive details about multiple projects, numerous technical skills including Python, JavaScript, React, Node.js, MongoDB, MySQL, PostgreSQL, Docker, Kubernetes, AWS, GCP, Azure, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy, Machine Learning, Deep Learning, Natural Language Processing, Computer Vision, Data Analysis, Data Visualization, Web Development, Full Stack Development, Backend Development, Frontend Development, API Development, Database Design, System Architecture, DevOps, CI/CD, Git, GitHub, Linux, Windows, macOS, Agile, Scrum, and many more technologies spanning across multiple domains including artificial intelligence, machine learning, web development, mobile development, cloud computing, cybersecurity, data science, software engineering, and system administration.
    """
    
    start_time = time.time()
    try:
        response = generate_with_ollama(complex_prompt, 'gemma3:latest')
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Ollama response received in {duration:.2f} seconds")
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")
        
        if duration > 90:
            print(f"⚠️  WARNING: Response took {duration:.2f}s (>90s timeout threshold)")
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Ollama failed after {duration:.2f} seconds")
        print(f"Error: {e}")
        logging.error(f"Ollama timeout test failed: {e}")

def test_gemma3_parsing():
    """Test 2: Reproduce Gemma3 parsing issues"""
    print("\n" + "="*50)
    print("TEST 2: Gemma3 parsing issues")
    print("="*50)
    
    resume_path = "resumes/CV_Anamay_Modern.pdf"
    if not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        return
    
    # Test resume parsing with LLM
    print("Testing resume parsing with Gemma3...")
    parser = ResumeParser(resume_path, ollama_model='gemma3:latest')
    
    # Extract text first
    text = parser.extract_text()
    print(f"Extracted text length: {len(text)} characters")
    
    # Test LLM parsing
    try:
        start_time = time.time()
        llm_result = parser.parse_with_llm()
        end_time = time.time()
        
        print(f"✅ LLM parsing completed in {end_time - start_time:.2f} seconds")
        print(f"LLM result keys: {list(llm_result.keys()) if llm_result else 'None'}")
        
        if llm_result:
            print("LLM parsing successful:")
            for key, value in llm_result.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items - {value[:3]}...")
                else:
                    print(f"  {key}: {str(value)[:100]}...")
        else:
            print("❌ LLM parsing returned empty result")
            
    except Exception as e:
        print(f"❌ LLM parsing failed: {e}")
        logging.error(f"Gemma3 parsing failed: {e}")
    
    # Test rule-based parsing as fallback
    print("\nTesting rule-based parsing fallback...")
    try:
        rule_result = parser.parse_with_rules()
        print(f"✅ Rule-based parsing completed")
        print(f"Rule-based result keys: {list(rule_result.keys())}")
        
        for key, value in rule_result.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items - {value[:3]}...")
            else:
                print(f"  {key}: {str(value)[:100]}...")
                
    except Exception as e:
        print(f"❌ Rule-based parsing failed: {e}")
        logging.error(f"Rule-based parsing failed: {e}")

def test_email_config_errors():
    """Test 3: Reproduce email-sending/config errors"""
    print("\n" + "="*50)
    print("TEST 3: Email-sending/config errors")
    print("="*50)
    
    # Test Gmail sender configuration
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    print(f"Gmail user from .env: {gmail_user}")
    print(f"Gmail password configured: {'Yes' if gmail_password else 'No'}")
    
    if not gmail_user or not gmail_password:
        print("❌ Gmail credentials not properly configured in .env")
        return
    
    # Test Gmail sender initialization
    try:
        sender = GmailSender(gmail_user, gmail_password)
        print("✅ GmailSender initialized successfully")
    except Exception as e:
        print(f"❌ GmailSender initialization failed: {e}")
        logging.error(f"GmailSender init failed: {e}")
        return
    
    # Test email validation
    test_emails = [
        "valid@example.com",
        "invalid.email",
        "",
        None,
        "no-at-sign.com",
        "@domain.com",
        "user@",
        "user@domain",
        "user@domain."
    ]
    
    print("\nTesting email validation:")
    for email in test_emails:
        is_valid = sender.validate_email(email)
        print(f"  {str(email):20} -> {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test email sending (dry run - will fail with fake credentials)
    test_email = {
        'to': 'test@example.com',
        'subject': 'Test Email - Failure Audit',
        'body': 'This is a test email to verify error handling.'
    }
    
    print(f"\nAttempting to send test email to {test_email['to']}...")
    try:
        result = sender.send_email(
            test_email['to'], 
            test_email['subject'], 
            test_email['body'], 
            'resumes/CV_Anamay_Modern.pdf'
        )
        if result:
            print("✅ Email sent successfully (unexpected with test credentials)")
        else:
            print("❌ Email sending failed as expected with test credentials")
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        logging.error(f"Email sending failed: {e}")

def test_end_to_end_pipeline():
    """Test 4: End-to-end pipeline with error collection"""
    print("\n" + "="*50)
    print("TEST 4: End-to-end pipeline")
    print("="*50)
    
    resume_path = "resumes/CV_Anamay_Modern.pdf"
    
    try:
        # Step 1: Parse resume
        print("Step 1: Parsing resume...")
        parser = ResumeParser(resume_path, ollama_model='gemma3:latest')
        student_info = parser.parse()
        student_info.update({
            'name': 'Anamay Tripathy',
            'email': 'tripathy.anamay23@gmail.com',
            'resume_prefix': 'CV_Anamay_Modern'
        })
        print(f"✅ Resume parsed: {len(student_info.get('skills', []))} skills, {len(student_info.get('projects', []))} projects")
        
        # Step 2: Generate email
        print("Step 2: Generating email...")
        mock_professor = {
            'Name': 'Dr. Test Professor',
            'Research Area': 'Machine Learning',
            'University': 'Test University',
            'Email': 'professor@test.edu'
        }
        
        email_gen = EmailGenerator(student_info, use_ollama=True, ollama_model='gemma3:latest')
        subject = email_gen.generate_subject(mock_professor)
        
        start_time = time.time()
        body = email_gen.generate_with_llm(mock_professor)
        end_time = time.time()
        
        print(f"✅ Email generated in {end_time - start_time:.2f} seconds")
        print(f"Subject: {subject}")
        print(f"Body length: {len(body)} characters")
        print(f"Body preview: {body[:200]}...")
        
        # Step 3: Test email sending (will fail with test credentials)
        print("Step 3: Testing email sending...")
        sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
        result = sender.send_email(mock_professor['Email'], subject, body, resume_path)
        
        if result:
            print("✅ Email sent successfully")
        else:
            print("❌ Email sending failed (expected with test credentials)")
            
    except Exception as e:
        print(f"❌ End-to-end pipeline failed: {e}")
        logging.error(f"End-to-end pipeline failed: {e}")

def main():
    """Run all failure reproduction tests"""
    print("InternMailer Failure Audit - Baseline Testing")
    print("=" * 60)
    
    # Test 1: Ollama timeout
    test_ollama_timeout()
    
    # Test 2: Gemma3 parsing issues
    test_gemma3_parsing()
    
    # Test 3: Email config errors
    test_email_config_errors()
    
    # Test 4: End-to-end pipeline
    test_end_to_end_pipeline()
    
    print("\n" + "="*60)
    print("Failure audit complete. Check test_failures.log for detailed logs.")
    print("="*60)

if __name__ == "__main__":
    main()
