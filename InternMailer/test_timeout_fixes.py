#!/usr/bin/env python3
"""
Test script to verify Ollama timeout fixes and improvements:
1. Enhanced HTTP client with streaming and retries
2. Prompt chunking for long resumes
3. Exponential backoff and fallback strategies
4. JSON parsing reliability improvements
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
from email_generator import EmailGenerator, get_ollama_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_timeout_fixes.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()

def test_enhanced_ollama_client():
    """Test 1: Enhanced Ollama client with streaming and chunking"""
    print("\n" + "="*60)
    print("TEST 1: Enhanced Ollama Client with Streaming & Chunking")
    print("="*60)
    
    client = get_ollama_client()
    
    # Test with a complex prompt that would previously timeout
    complex_prompt = """
    You are an expert resume parser and email generator. Please analyze the following comprehensive information:
    
    1. Technical Skills Analysis:
    - Programming Languages: Python (advanced), JavaScript (intermediate), C++ (basic), SQL (intermediate)
    - Frameworks: React, Node.js, Express.js, TensorFlow, PyTorch, Scikit-learn, Django, Flask, Spring Boot
    - Databases: MongoDB, MySQL, PostgreSQL, Redis, Elasticsearch
    - Cloud Platforms: AWS (EC2, S3, Lambda), GCP (Compute Engine, BigQuery), Azure (App Service, Cosmos DB)
    - DevOps Tools: Docker, Kubernetes, Jenkins, Git, GitLab CI/CD, Ansible, Terraform
    - Data Science: Pandas, NumPy, Matplotlib, Seaborn, Jupyter, Apache Spark, Hadoop
    
    2. Project Portfolio:
    - CrimeConnect: Full-stack web application using MERN stack with real-time crime data visualization
    - VARtificial Intelligence: Machine learning model for sports prediction with 85% accuracy
    - HackOps: Cybersecurity education platform with gamified learning modules
    - Flora Fight Frenzy: Interactive web-based game with JavaScript and Canvas API
    - DataDash Analytics: Business intelligence dashboard with Python backend and React frontend
    
    3. Academic Background:
    - B.Tech in Data Science Engineering from Manipal Institute of Technology
    - Relevant coursework: Machine Learning, Deep Learning, Data Structures, Algorithms, Database Systems
    - CGPA: 7.6/10, Dean's List recognition, Academic excellence awards
    
    4. Professional Experience:
    - Data Analyst Intern at Intellect Design Arena: Worked on financial data analysis and reporting
    - Web Development Intern: Built responsive web applications using modern frameworks
    - Technical Lead positions in multiple student organizations
    
    Please provide a comprehensive analysis and generate a professional email template.
    """
    
    print(f"Testing with complex prompt ({len(complex_prompt)} characters)")
    
    # Test different strategies
    strategies = [
        ("Streaming with Chunking", lambda: client.generate_with_streaming(complex_prompt, 'gemma3:latest', use_chunking=True)),
        ("Streaming without Chunking", lambda: client.generate_with_streaming(complex_prompt, 'gemma3:latest', use_chunking=False)),
        ("Fallback Strategy", lambda: client.generate_with_fallback(complex_prompt, 'gemma3:latest'))
    ]
    
    for strategy_name, strategy_func in strategies:
        print(f"\n--- Testing: {strategy_name} ---")
        start_time = time.time()
        try:
            result = strategy_func()
            duration = time.time() - start_time
            
            if result and len(result.strip()) > 10:
                print(f"✅ {strategy_name} succeeded in {duration:.2f}s")
                print(f"Response length: {len(result)} characters")
                print(f"Response preview: {result[:150]}...")
                if "[Timeout" not in result and "[Error" not in result:
                    print(f"✅ No timeout/error markers found")
                    break  # Success, no need to test other strategies
                else:
                    print(f"⚠️  Found timeout/error markers in response")
            else:
                print(f"❌ {strategy_name} returned empty/short response")
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {strategy_name} failed after {duration:.2f}s: {e}")

def test_resume_parsing_with_fixes():
    """Test 2: Resume parsing with enhanced timeout handling"""
    print("\n" + "="*60)
    print("TEST 2: Resume Parsing with Enhanced Client")
    print("="*60)
    
    resume_path = "resumes/CV_Anamay_Modern.pdf"
    if not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        return
    
    print("Testing enhanced resume parsing...")
    parser = ResumeParser(resume_path, ollama_model='gemma3:latest')
    
    # Test text extraction
    text = parser.extract_text()
    print(f"Extracted text length: {len(text)} characters")
    
    # Test enhanced LLM parsing
    start_time = time.time()
    try:
        llm_result = parser.parse_with_llm()
        duration = time.time() - start_time
        
        if llm_result:
            print(f"✅ Enhanced LLM parsing succeeded in {duration:.2f}s")
            print(f"Extracted data keys: {list(llm_result.keys())}")
            
            for key, value in llm_result.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items - {value[:3]}...")
                else:
                    print(f"  {key}: {str(value)[:100]}...")
        else:
            print(f"❌ Enhanced LLM parsing returned empty result after {duration:.2f}s")
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Enhanced LLM parsing failed after {duration:.2f}s: {e}")
    
    # Test complete parsing with fallback
    print("\nTesting complete parsing with fallback...")
    start_time = time.time()
    try:
        complete_result = parser.parse()
        duration = time.time() - start_time
        
        print(f"✅ Complete parsing completed in {duration:.2f}s")
        print(f"Final result keys: {list(complete_result.keys())}")
        
        skill_count = len(complete_result.get('skills', []))
        project_count = len(complete_result.get('projects', []))
        print(f"Skills extracted: {skill_count}, Projects extracted: {project_count}")
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Complete parsing failed after {duration:.2f}s: {e}")

def test_email_generation_with_fixes():
    """Test 3: Email generation with enhanced client"""
    print("\n" + "="*60)
    print("TEST 3: Email Generation with Enhanced Client")
    print("="*60)
    
    # Mock student info and professor data
    student_info = {
        'name': 'Anamay Tripathy',
        'email': 'tripathy.anamay23@gmail.com',
        'skills': ['Python', 'Machine Learning', 'TensorFlow', 'React', 'Node.js', 'Docker'],
        'projects': ['CrimeConnect', 'VARtificial Intelligence', 'HackOps'],
        'courses': ['Machine Learning', 'Deep Learning', 'Data Analytics'],
        'summary': 'Data Science Engineering student with strong technical skills'
    }
    
    mock_professor = {
        'Name': 'Dr. Test Professor',
        'Research Area': 'Machine Learning and Artificial Intelligence',
        'University': 'Test University',
        'Email': 'professor@test.edu'
    }
    
    email_gen = EmailGenerator(student_info, use_ollama=True, ollama_model='gemma3:latest')
    
    # Test subject generation (this is fast)
    subject = email_gen.generate_subject(mock_professor)
    print(f"Generated subject: {subject}")
    
    # Test enhanced email body generation
    print("Testing enhanced email body generation...")
    start_time = time.time()
    try:
        body = email_gen.generate_with_llm(mock_professor)
        duration = time.time() - start_time
        
        if body and len(body.strip()) > 10:
            print(f"✅ Enhanced email generation succeeded in {duration:.2f}s")
            print(f"Email body length: {len(body)} characters")
            print(f"Email body preview:\n{body[:300]}...")
        else:
            print(f"❌ Enhanced email generation returned empty/short result")
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Enhanced email generation failed after {duration:.2f}s: {e}")

def test_timeout_comparison():
    """Test 4: Compare old vs new timeout behavior"""
    print("\n" + "="*60)
    print("TEST 4: Timeout Behavior Comparison")
    print("="*60)
    
    # Simple test prompt that should work quickly
    simple_prompt = "Generate a brief professional email greeting. Keep it under 50 words."
    
    # Test with enhanced client
    print("Testing with enhanced client...")
    client = get_ollama_client()
    
    start_time = time.time()
    try:
        result = client.generate_with_fallback(simple_prompt, 'gemma3:latest')
        duration = time.time() - start_time
        
        if result:
            print(f"✅ Enhanced client succeeded in {duration:.2f}s")
            print(f"Result: {result}")
        else:
            print(f"❌ Enhanced client returned empty result")
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Enhanced client failed after {duration:.2f}s: {e}")
    
    # Test connection pooling benefits
    print("\nTesting connection reuse...")
    times = []
    for i in range(3):
        start_time = time.time()
        try:
            result = client.generate_with_fallback(f"Say hello #{i+1}", 'gemma3:latest')
            duration = time.time() - start_time
            times.append(duration)
            print(f"Request {i+1}: {duration:.2f}s")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"Average response time: {avg_time:.2f}s")
        print(f"Connection reuse {'✅ working' if times[-1] < times[0] else '⚠️  not significant'}")

def main():
    """Run all timeout fix verification tests"""
    print("Ollama Timeout Fixes - Verification Testing")
    print("=" * 70)
    
    # Test 1: Enhanced Ollama client
    test_enhanced_ollama_client()
    
    # Test 2: Resume parsing improvements
    test_resume_parsing_with_fixes()
    
    # Test 3: Email generation improvements
    test_email_generation_with_fixes()
    
    # Test 4: Timeout behavior comparison
    test_timeout_comparison()
    
    print("\n" + "="*70)
    print("Timeout fixes verification complete. Check test_timeout_fixes.log for detailed logs.")
    print("="*70)

if __name__ == "__main__":
    main()
