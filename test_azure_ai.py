#!/usr/bin/env python3
"""
Comprehensive test of Azure AI client to ensure it's working properly.
"""

import sys
import os
sys.path.append('src')

from azure_ai_client import get_azure_ai_client, generate_with_azure_ai

print("🔧 Testing Azure AI Client Configuration...")
print("=" * 50)

# Test 1: Check environment variables
print("\n1. Environment Configuration:")
github_token = os.getenv('GITHUB_TOKEN')
if github_token:
    print(f"✅ GITHUB_TOKEN: {github_token[:10]}...")
else:
    print("❌ GITHUB_TOKEN: Not found")

# Test 2: Initialize client
print("\n2. Client Initialization:")
try:
    client = get_azure_ai_client()
    print(f"✅ Client created: {type(client).__name__}")
    print(f"✅ Client available: {client.is_available()}")
    
    metrics = client.get_performance_metrics()
    print(f"✅ Endpoint: {metrics['endpoint']}")
    print(f"✅ Model: {metrics['model']}")
    print(f"✅ Available: {metrics['available']}")
except Exception as e:
    print(f"❌ Client initialization failed: {e}")

# Test 3: Simple generation test
print("\n3. Simple Generation Test:")
try:
    simple_prompt = "Write a one-sentence professional greeting."
    result = generate_with_azure_ai(simple_prompt)
    print(f"✅ Result length: {len(result)} characters")
    print(f"✅ Generated: {result}")
    
    # Check if it's proper text (not JSON)
    is_json = result.strip().startswith('{') and result.strip().endswith('}')
    print(f"✅ Is proper text (not JSON): {not is_json}")
    
except Exception as e:
    print(f"❌ Generation failed: {e}")

# Test 4: Email generation test
print("\n4. Email Generation Test:")
try:
    email_prompt = """Write a professional research internship email from Anamay Tripathy to Prof. John Smith.
Research: Machine Learning
Background: B.Tech Data Science student
Skills: Python, Machine Learning
Request: Research internship opportunity
Keep it under 150 words and professional."""
    
    result = generate_with_azure_ai(email_prompt)
    print(f"✅ Email length: {len(result)} characters")
    
    # Validation checks
    has_dear = 'Dear' in result or 'dear' in result
    has_regards = 'regards' in result.lower() or 'sincerely' in result.lower()
    is_json = result.strip().startswith('{') and result.strip().endswith('}')
    
    print(f"✅ Contains greeting: {has_dear}")
    print(f"✅ Contains closing: {has_regards}")
    print(f"✅ Not JSON format: {not is_json}")
    
    if has_dear and has_regards and not is_json:
        print("🎉 EMAIL GENERATION: SUCCESS")
    else:
        print("🚨 EMAIL GENERATION: NEEDS ATTENTION")
        
    print("\nGenerated email:")
    print("-" * 30)
    print(result)
    print("-" * 30)
    
except Exception as e:
    print(f"❌ Email generation failed: {e}")

print("\n" + "=" * 50)
print("Azure AI Test Completed!")
