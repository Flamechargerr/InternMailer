#!/usr/bin/env python3
"""
Test script to debug Azure AI parsing issue
"""

import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_azure_ai_parsing():
    print("=== Testing Azure AI Resume Parsing ===")
    
    # Test environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    github_token = os.getenv('GITHUB_TOKEN')
    print(f"GITHUB_TOKEN present: {'ghp_' in str(github_token) if github_token else False}")
    
    # Test Azure AI client
    from azure_ai_client import get_azure_ai_client
    client = get_azure_ai_client()
    print(f"Azure AI client available: {client.is_available()}")
    print(f"Azure AI client has api_key: {client.api_key is not None}")
    
    # Test Azure AI parser
    from parsing.azure_ai_parser import AzureAIResumeParser
    parser = AzureAIResumeParser()
    print(f"Azure AI parser available: {parser.is_available()}")
    
    # Test resume parsing
    try:
        from resume_parser import ResumeParser
        resume_parser = ResumeParser('resumes/CV_Anamay_Modern.pdf')
        print(f"Resume parser providers: {[p.get_provider_name() for p in resume_parser.providers]}")
        
        result = resume_parser.parse()
        print(f"✅ Resume parsing SUCCESS!")
        print(f"Skills found: {len(result.get('skills', []))}")
        print(f"Projects found: {len(result.get('projects', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Resume parsing FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_azure_ai_parsing()
    exit(0 if success else 1)
