#!/usr/bin/env python3
"""
Simple test campaign script for InternMailing system.
This script tests the email campaign functionality with mock data.
"""

import os
import sys
import json
from typing import Dict, List
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def load_mock_professors() -> List[Dict]:
    """Load mock professor data for testing."""
    mock_professors = [
        {
            "name": "Dr. John Smith",
            "email": "john.smith@university.edu",
            "university": "MIT",
            "research_area": "Machine Learning",
            "homepage": "https://example.com/john-smith"
        },
        {
            "name": "Dr. Jane Doe", 
            "email": "jane.doe@stanford.edu",
            "university": "Stanford University",
            "research_area": "Computer Vision",
            "homepage": "https://example.com/jane-doe"
        },
        {
            "name": "Dr. Alice Johnson",
            "email": "alice.johnson@berkeley.edu", 
            "university": "UC Berkeley",
            "research_area": "Natural Language Processing",
            "homepage": "https://example.com/alice-johnson"
        }
    ]
    return mock_professors

def generate_mock_email(professor: Dict) -> str:
    """Generate a mock email for testing."""
    template = f"""
Subject: Research Internship Inquiry - {professor['research_area']}

Dear {professor['name']},

I hope this email finds you well. I am a Data Science Engineering student at Manipal Institute of Technology, graduating in 2027. I am writing to express my interest in your research work in {professor['research_area']}.

I have been following your research publications and am particularly interested in contributing to ongoing projects in your lab at {professor['university']}.

Would you be available for a brief discussion about potential research opportunities?

Best regards,
[Your Name]
Data Science Engineering Student
Manipal Institute of Technology
"""
    return template.strip()

def run_test_campaign(num_emails: int = 3) -> Dict:
    """Run a test campaign with mock data."""
    print(f"🚀 Starting test campaign with {num_emails} emails...")
    
    # Load mock data
    professors = load_mock_professors()[:num_emails]
    
    results = {
        "campaign_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "mode": "dry_run",
        "total_candidates": len(professors),
        "emails_generated": 0,
        "emails_sent": 0,
        "success_rate": 0.0,
        "duration_seconds": 0.0,
        "email_previews": []
    }
    
    start_time = datetime.now()
    
    # Generate emails
    for professor in professors:
        email_content = generate_mock_email(professor)
        
        results["email_previews"].append({
            "to": professor["email"],
            "subject": f"Research Internship Inquiry - {professor['research_area']}",
            "body": email_content,
            "recipient": professor["name"],
            "university": professor["university"]
        })
        
        results["emails_generated"] += 1
        print(f"✅ Generated email for {professor['name']} at {professor['university']}")
    
    # In test mode, we don't actually send emails
    results["emails_sent"] = 0  # Would be same as emails_generated in real mode
    results["success_rate"] = 100.0 if results["emails_generated"] > 0 else 0.0
    results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
    
    print(f"📧 Campaign completed: {results['emails_generated']} emails generated")
    print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")
    print(f"📊 Success rate: {results['success_rate']:.1f}%")
    
    return results

def save_test_results(results: Dict):
    """Save test results to a file."""
    os.makedirs("data", exist_ok=True)
    output_file = f"data/test_campaign_{results['campaign_id']}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"💾 Results saved to {output_file}")

def main():
    """Main function to run the test campaign."""
    print("=" * 60)
    print("🎯 InternMailing Test Campaign")
    print("=" * 60)
    
    # Check environment
    print("🔧 Checking environment...")
    test_mode = os.getenv('TEST_MODE', 'true').lower()
    print(f"   Test Mode: {test_mode}")
    
    if len(sys.argv) > 1:
        try:
            num_emails = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid number of emails. Using default (3).")
            num_emails = 3
    else:
        num_emails = 3
    
    # Run campaign
    try:
        results = run_test_campaign(num_emails)
        save_test_results(results)
        
        print("\n📋 Campaign Summary:")
        print(f"   Campaign ID: {results['campaign_id']}")
        print(f"   Mode: {results['mode']}")
        print(f"   Emails Generated: {results['emails_generated']}")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        
        print(f"\n📧 Email Previews:")
        for i, preview in enumerate(results['email_previews'], 1):
            print(f"   {i}. To: {preview['to']} ({preview['recipient']})")
            print(f"      Subject: {preview['subject']}")
            print()
        
        print("✅ Test campaign completed successfully!")
        
    except Exception as e:
        print(f"❌ Test campaign failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
