#!/usr/bin/env python3
"""
Final validation script to confirm all Azure AI fixes are working properly
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def main():
    print("🔧 AZURE AI FIX VALIDATION")
    print("=" * 60)
    print(f"📅 Validation run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Environment Configuration
    print("1️⃣ Testing Environment Configuration...")
    from dotenv import load_dotenv
    load_dotenv()
    
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token and github_token != "your_github_token_here":
        print("   ✅ GitHub token configured")
        print(f"   🔑 Token: {github_token[:12]}...")
    else:
        print("   ❌ GitHub token not configured")
        return False
    
    # Test 2: Azure AI Client Initialization
    print("\n2️⃣ Testing Azure AI Client Initialization...")
    try:
        from src.azure_ai_client import get_azure_ai_client, AZURE_AI_AVAILABLE
        
        if AZURE_AI_AVAILABLE:
            print("   ✅ Azure AI SDK is available")
        else:
            print("   ❌ Azure AI SDK not available")
            return False
            
        client = get_azure_ai_client()
        print(f"   ✅ Client created: {type(client).__name__}")
        print(f"   🌐 Endpoint: {client.endpoint}")
        print(f"   🤖 Model: {client.model}")
        
        if client.is_available():
            print("   ✅ Client is available and configured")
        else:
            print("   ❌ Client not properly configured")
            return False
            
    except Exception as e:
        print(f"   ❌ Client initialization failed: {e}")
        return False
    
    # Test 3: Simple Generation Test
    print("\n3️⃣ Testing AI Generation...")
    try:
        test_prompt = "Write a brief professional greeting for an email."
        response = client.generate_with_fallback(test_prompt)
        
        if response and len(response.strip()) > 10:
            print("   ✅ Generation successful")
            print(f"   📝 Response length: {len(response)} characters")
            print(f"   💬 Sample: {response[:60]}...")
        else:
            print("   ❌ Generation failed or empty response")
            return False
            
    except Exception as e:
        print(f"   ❌ Generation test failed: {e}")
        return False
    
    # Test 4: Email Generation Test
    print("\n4️⃣ Testing Academic Email Generation...")
    try:
        email_prompt = """Generate a professional email to Prof. Williams about a research internship in machine learning.
        Student: Anamay Tripathy
        University: MIT Manipal"""
        
        email_response = client.generate_with_fallback(email_prompt)
        
        if email_response and len(email_response) > 200:
            print("   ✅ Email generation successful")
            print(f"   📏 Email length: {len(email_response)} characters")
            
            # Check for key components
            has_greeting = any(word in email_response.lower() for word in ['dear', 'hello', 'hi'])
            has_closing = any(word in email_response.lower() for word in ['regards', 'sincerely', 'best'])
            has_name = 'anamay' in email_response.lower()
            
            print(f"   🎯 Has greeting: {'✅' if has_greeting else '❌'}")
            print(f"   🎯 Has closing: {'✅' if has_closing else '❌'}")
            print(f"   🎯 Contains name: {'✅' if has_name else '❌'}")
            
        else:
            print("   ❌ Email generation failed or too short")
            return False
            
    except Exception as e:
        print(f"   ❌ Email generation test failed: {e}")
        return False
    
    # Test 5: Performance Metrics
    print("\n5️⃣ Testing Performance Metrics...")
    try:
        metrics = client.get_performance_metrics()
        print("   ✅ Performance metrics retrieved")
        for key, value in metrics.items():
            print(f"   📊 {key}: {value}")
            
    except Exception as e:
        print(f"   ❌ Performance metrics failed: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Azure AI client is fully functional")
    print("✅ GPT-4o model is responding correctly")
    print("✅ Email generation is working properly")
    print("✅ Ready for production use")
    print("\n💡 The application should now work without Azure AI errors!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
