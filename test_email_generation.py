#!/usr/bin/env python3
"""
Test script to verify email generation is working properly after the fix.
"""

import sys
import os
sys.path.append('src')

from email_generator import EmailGenerator
from azure_ai_client import generate_with_azure_ai

# Test data
student_info = {
    'name': 'Anamay Tripathy',
    'email': 'tripathy.anamay23@gmail.com',
    'skills': ['Python', 'JavaScript', 'React', 'Machine Learning', 'TensorFlow'],
    'projects': ['CrimeConnect', 'VARtificial Intelligence'],
    'courses': ['Data Structures', 'Machine Learning', 'Web Development'],
    'experience': ['Technical Head at YaanBarpe', 'Data Analyst Intern at Intellect Design Arena'],
    'summary': 'B.Tech Data Science student with strong technical skills'
}

professor = {
    'Name': 'Adam Belay',
    'Email': 'abelay@mit.edu',
    'University': 'MIT',
    'Research Area': 'Systems for ML'
}

print("🔧 Testing Email Generation System...")
print("=" * 50)

# Test 1: Direct Azure AI call
print("\n1. Testing Azure AI client directly:")
test_prompt = f"""Write a professional internship email from Anamay Tripathy to Prof. Adam Belay.
Research: Systems for ML
Background: B.Tech Data Science, MIT India
Skills: Python, Machine Learning, JavaScript
Request: Research internship opportunity
Keep it under 150 words and professional."""

result = generate_with_azure_ai(test_prompt)
print(f"Result length: {len(result)} characters")
print("Generated content:")
print("-" * 30)
print(result)
print("-" * 30)

# Test 2: Email Generator with LLM
print("\n2. Testing EmailGenerator with LLM:")
email_gen = EmailGenerator(student_info, use_azure_ai=True)
subject = email_gen.generate_subject(professor)
body = email_gen.generate_with_llm(professor, custom_prompt=test_prompt)

print(f"Subject: {subject}")
print(f"Body length: {len(body)} characters")
print("Generated body:")
print("-" * 30)
print(body)
print("-" * 30)

# Test 3: Check if it's JSON or proper email
print("\n3. Validation checks:")
is_json = body.strip().startswith('{') and body.strip().endswith('}')
has_dear = 'Dear' in body or 'dear' in body
has_regards = 'regards' in body.lower() or 'sincerely' in body.lower()

print(f"❌ Contains JSON format: {is_json}")
print(f"✅ Contains greeting (Dear): {has_dear}")
print(f"✅ Contains closing (regards/sincerely): {has_regards}")

if is_json:
    print("🚨 ERROR: Still generating JSON format!")
elif has_dear and has_regards:
    print("✅ SUCCESS: Proper email format generated!")
else:
    print("⚠️  WARNING: Email format may need improvement")

print("\n" + "=" * 50)
print("Test completed!")
