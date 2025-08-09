#!/usr/bin/env python3
"""
Enhanced Internship Outreach System Test Runner
===============================================

This script demonstrates the improved system with:
1. Scholar ID prioritization for ultra-accurate research data
2. Advanced research area classification with hierarchical scoring  
3. Personalized research alignment for every professor and publication
4. Multi-source academic data discovery with robust fallbacks

This will generate and send 2 test emails to your address for review.
"""

import sys
import os
import pandas as pd
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from internship_outreach_system import InternshipOutreachSystem
from ultra_accurate_research_finder import UltraAccurateResearchFinder

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_system_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_sample_professor_data():
    """Create sample professor data for testing with Scholar IDs"""
    sample_data = [
        {
            'Name': 'Yann LeCun',
            'Email': 'yann@fb.com', 
            'University': 'Meta AI',
            'ScholarID': 'WLN3QrAAAAAJ'  # Real Scholar ID
        },
        {
            'Name': 'Geoffrey Hinton',
            'Email': 'hinton@cs.toronto.edu',
            'University': 'University of Toronto', 
            'ScholarID': 'JicYPdAAAAAJ'  # Real Scholar ID
        },
        {
            'Name': 'Andrew Ng',
            'Email': 'ang@cs.stanford.edu',
            'University': 'Stanford University',
            'ScholarID': 'mG4imMEAAAAJ'  # Real Scholar ID  
        },
        {
            'Name': 'Fei-Fei Li',
            'Email': 'feifeili@cs.stanford.edu',
            'University': 'Stanford University',
            'ScholarID': 'rDfyQnIAAAAJ'  # Real Scholar ID
        },
        {
            'Name': 'Yoshua Bengio', 
            'Email': 'yoshua.bengio@umontreal.ca',
            'University': 'University of Montreal',
            'ScholarID': 'kukA0LcAAAAJ'  # Real Scholar ID
        }
    ]
    
    return pd.DataFrame(sample_data)


def run_enhanced_system_test():
    """Run the enhanced system test with improved research data discovery"""
    
    print("\n" + "="*80)
    print("🚀 ENHANCED INTERNSHIP OUTREACH SYSTEM v2.0")
    print("="*80)
    print("✨ NEW FEATURES:")
    print("   • Scholar ID prioritization for maximum research data accuracy")
    print("   • Advanced multi-source academic API integration") 
    print("   • Hierarchical keyword-based research area classification")
    print("   • Individual publication-specific research alignment")
    print("   • Intelligent fallback mechanisms and caching")
    print("="*80 + "\n")
    
    # Your profile
    my_profile = {
        'name': 'Anamay Tripathy',
        'background': 'a third-year B.Tech Data Science student at MIT Manipal, India',
        'email': 'tripathy.anamay23@gmail.com',
        'interests': ['machine learning', 'artificial intelligence', 'deep learning'],
        'skills': ['Python', 'TensorFlow', 'PyTorch', 'SQL', 'React.js', 'AWS'],
        'achievements': 'Led technical development at a government-incubated startup; Automated KPI dashboards at Intellect Design Arena, saving 12+ hours weekly; Achieved 89% prediction accuracy in a sports prediction project.',
        'portfolio': 'YOUR_PORTFOLIO_URL',
        'linkedin': 'YOUR_LINKEDIN_URL', 
        'github': 'YOUR_GITHUB_URL'
    }
    
    # Initialize the enhanced system
    system = InternshipOutreachSystem(my_profile, test_mode=True)
    
    # Create sample professor data (you can replace this with your actual data files)
    professor_df = create_sample_professor_data()
    
    print(f"📊 Sample professor database loaded: {len(professor_df)} professors")
    print("🎯 Professors selected for testing:")
    for i, prof in professor_df.iterrows():
        scholar_status = "✅ Has Scholar ID" if prof.get('ScholarID') else "⚠️  No Scholar ID"
        print(f"   {i+1}. {prof['Name']} ({prof['University']}) - {scholar_status}")
    
    print(f"\n📧 Test emails will be sent to: {my_profile['email']}")
    
    # Test with 2 professors
    successful_tests = 0
    target_tests = 2
    
    print(f"\n🧪 STARTING ENHANCED SYSTEM TESTS (Target: {target_tests} emails)")
    print("-" * 60)
    
    for i, (_, prof) in enumerate(professor_df.iterrows()):
        if successful_tests >= target_tests:
            break
            
        print(f"\n📍 Test {successful_tests + 1}: Processing {prof['Name']} from {prof['University']}")
        
        try:
            # Fetch research data using Scholar ID prioritization
            scholar_id = prof.get('ScholarID', None)
            
            if scholar_id and 'noscholar' not in str(scholar_id).lower():
                print(f"🔑 Using Scholar ID: {scholar_id}")
                profile = system.research_finder.create_author_profile(
                    name=prof['Name'],
                    affiliation=prof['University'], 
                    email=prof['Email'],
                    scholar_id=scholar_id
                )
            else:
                print("🔍 Using name-based search (no Scholar ID)")
                profile = system.research_finder.create_author_profile(
                    name=prof['Name'],
                    affiliation=prof['University'],
                    email=prof['Email']
                )
            
            if not profile or not profile.recent_publications:
                print(f"❌ No research data found for {prof['Name']}")
                continue
            
            print(f"✅ Found {len(profile.recent_publications)} publications")
            print(f"🧠 Research interests: {', '.join(profile.research_interests[:3])}")
            
            # Generate personalized email
            email_data = system.create_personalized_email(profile)
            if not email_data:
                print(f"❌ Failed to generate email for {prof['Name']}")
                continue
            
            print(f"📝 Generated personalized email with subject: '{email_data['subject'][:50]}...'")
            
            # Save locally and send test email
            system.save_email_to_file(email_data)
            success = system.send_email(email_data, to_override=my_profile['email'])
            
            if success:
                successful_tests += 1
                print(f"✅ Test email {successful_tests} sent successfully!")
                print(f"📧 Check your inbox at {my_profile['email']}")
            else:
                print(f"⚠️  Email saved locally but not sent (check SMTP config)")
            
        except Exception as e:
            logger.error(f"Error processing {prof['Name']}: {str(e)}")
            print(f"❌ Error processing {prof['Name']}: {str(e)}")
            continue
    
    # Summary
    print("\n" + "="*80)
    print("📊 ENHANCED SYSTEM TEST SUMMARY")
    print("="*80)
    print(f"✅ Successful tests: {successful_tests}/{target_tests}")
    print(f"📧 Test emails sent to: {my_profile['email']}")
    print(f"💾 Local copies saved in: test_emails/ folder")
    print(f"📋 Logs available in: enhanced_system_test.log")
    
    if successful_tests > 0:
        print(f"\n🎉 SUCCESS! Please check your inbox for {successful_tests} test emails.")
        print("🔍 Review the emails to verify:")
        print("   • Research publications are authentic and recent")
        print("   • Research area classification is accurate") 
        print("   • Personal alignment is specific and compelling")
        print("   • Publication-specific alignments are unique")
    else:
        print(f"\n❌ No test emails were sent. Check the logs for issues.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    run_enhanced_system_test()
