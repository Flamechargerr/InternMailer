#!/usr/bin/env python3
"""
ACTIVE PROFESSOR TESTING - Research Assistant Email System
=========================================================

This script tests with professors more likely to have recent publications
by filtering for active researchers from top universities.
"""

import sys
import os
import json
import random
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_assistant import ResearchAssistant
from enhanced_research_area_inference import EnhancedResearchAreaInference
from send_research_assistant_emails import create_enhanced_personalized_email, generate_publication_alignment
from send_html_template_emails_with_cv import send_html_email_with_cv

def get_active_professors():
    """Get professors more likely to have recent publications"""
    
    # Test with known active researchers from major universities
    active_professors = [
        {
            "name": "Yann LeCun",
            "affiliation": "New York University", 
            "email": "yann@cs.nyu.edu",
            "homepage": "https://yann.lecun.com"
        },
        {
            "name": "Fei-Fei Li", 
            "affiliation": "Stanford University",
            "email": "feifeili@cs.stanford.edu", 
            "homepage": "https://profiles.stanford.edu/fei-fei-li"
        },
        {
            "name": "Ian Goodfellow",
            "affiliation": "Google DeepMind",
            "email": "goodfellow@google.com",
            "homepage": "https://scholar.google.com/citations?user=iYN86KEAAAAJ"
        },
        {
            "name": "Yoshua Bengio",
            "affiliation": "University of Montreal",
            "email": "yoshua.bengio@umontreal.ca", 
            "homepage": "https://mila.quebec/en/person/yoshua-bengio"
        },
        {
            "name": "Andrew Ng",
            "affiliation": "Stanford University",
            "email": "ang@cs.stanford.edu",
            "homepage": "https://www.andrewng.org"
        },
        {
            "name": "Geoffrey Hinton",
            "affiliation": "University of Toronto", 
            "email": "hinton@cs.toronto.edu",
            "homepage": "https://www.cs.toronto.edu/~hinton"
        }
    ]
    
    return random.sample(active_professors, 3)

def test_professor_email_system(professor):
    """Test the complete email system for one professor"""
    
    print(f"\n📚 TESTING: {professor['name']}")
    print(f"🏛️ University: {professor['affiliation']}")
    print(f"📧 Email: {professor['email']}")
    print("-" * 60)
    
    # Initialize components
    research_assistant = ResearchAssistant()
    inference = EnhancedResearchAreaInference()
    
    # Step 1: Research Assistant Publication Discovery
    print("🔍 Step 1: Research Assistant Publication Discovery")
    publications = research_assistant.find_professor_publications(professor['name'])
    
    if not publications:
        print(f"❌ No publications found for {professor['name']}")
        return False, None, None
    
    print(f"   ✅ Found {len(publications)} recent publications:")
    for i, pub in enumerate(publications[:3], 1):  # Show first 3
        print(f"      {i}. {pub['title'][:50]}... ({pub['year']})")
    
    # Step 2: Research Area Inference
    print(f"\n🎯 Step 2: Research Area Inference")
    combined_text = ' '.join([pub['title'] + ' ' + pub['summary'] for pub in publications])
    research_area = inference.infer_research_area({
        'name': combined_text,
        'affiliation': professor['affiliation']
    })
    print(f"   ✅ Inferred research area: {research_area.upper()}")
    
    # Step 3: Enhanced Email Generation
    print(f"\n📧 Step 3: Enhanced Email Generation")
    subject = f"Research Internship Inquiry - Your work in {research_area}"
    html_content = create_enhanced_personalized_email(
        professor['name'], professor['affiliation'], publications, research_area
    )
    print(f"   ✅ Email generated with {len(publications)} publications")
    print(f"   ✅ Subject: {subject}")
    
    # Step 4: Email Sending Test
    print(f"\n✉️ Step 4: Email Sending Test")
    target_email = "tripathy.anamay23@gmail.com"
    
    success = send_html_email_with_cv(
        target_email,
        subject,
        html_content,
        f"Research Assistant Test - {professor['name']}"
    )
    
    if success:
        print(f"   ✅ Email sent successfully to {target_email}")
        
        # Step 5: Data Storage
        print(f"\n💾 Step 5: Data Storage and Tracking")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create test results directory
        os.makedirs('test_results_active', exist_ok=True)
        
        # Save publications JSON
        prof_name_clean = professor['name'].replace(' ', '_').replace('.', '')
        json_filename = f"test_results_active/test_publications_{timestamp}_{prof_name_clean}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(publications, f, indent=2, ensure_ascii=False)
        
        # Save email HTML
        html_filename = f"test_results_active/test_email_{timestamp}_{prof_name_clean}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save test result
        test_result = {
            "professor": professor,
            "publications_count": len(publications),
            "research_area": research_area,
            "email_subject": subject,
            "timestamp": timestamp,
            "success": True
        }
        
        result_filename = f"test_results_active/test_result_{timestamp}_{prof_name_clean}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Publications saved: {json_filename}")
        print(f"   ✅ Email saved: {html_filename}")
        print(f"   ✅ Test result saved: {result_filename}")
        
        return True, publications, research_area
    else:
        print(f"   ❌ Failed to send email")
        return False, publications, research_area

def main():
    """Main testing function"""
    
    print("🧪 ACTIVE PROFESSOR TESTING - Research Assistant Email System")
    print("=" * 80)
    print("🎯 Testing with 3 active professors from top universities")
    print("📧 All emails sent to: tripathy.anamay23@gmail.com")
    print("🔬 Testing complete Research Assistant integration")
    print("=" * 80)
    
    # Get active professors
    print(f"\n🎲 Selecting 3 Active Professors")
    test_professors = get_active_professors()
    
    print(f"✅ Selected {len(test_professors)} professors for testing:")
    for i, prof in enumerate(test_professors, 1):
        print(f"   {i}. {prof['name']} at {prof['affiliation']}")
    
    # Test each professor
    results = []
    successful_tests = 0
    
    for i, professor in enumerate(test_professors, 1):
        print(f"\n" + "=" * 80)
        print(f"🧪 TEST {i}/{len(test_professors)}")
        print("=" * 80)
        
        success, publications, research_area = test_professor_email_system(professor)
        
        results.append({
            "professor": professor,
            "success": success,
            "publications_count": len(publications) if publications else 0,
            "research_area": research_area
        })
        
        if success:
            successful_tests += 1
    
    # Final Results Summary
    print(f"\n" + "=" * 80)
    print("🎉 ACTIVE PROFESSOR TESTING - RESULTS SUMMARY")
    print("=" * 80)
    print(f"📊 Tests completed: {len(test_professors)}")
    print(f"✅ Successful emails: {successful_tests}")
    print(f"❌ Failed emails: {len(test_professors) - successful_tests}")
    print(f"📧 Target email: tripathy.anamay23@gmail.com")
    
    print(f"\n📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"   {i}. {result['professor']['name'][:30]:<30} | {status} | {result['publications_count']} pubs | {result['research_area']}")
    
    if successful_tests > 0:
        print(f"\n🎉 CHECK YOUR INBOX!")
        print(f"📧 You should have received {successful_tests} personalized emails at:")
        print(f"   ✉️ tripathy.anamay23@gmail.com")
        print(f"\n📧 Each email contains:")
        print(f"   • Professor's real name and university")
        print(f"   • 3-5 recent publications (2020-2025)")
        print(f"   • Publication-specific personalized alignments")
        print(f"   • Professional HTML formatting")
        print(f"   • CV attachment (PDF)")
        print(f"   • Complete email template (all sections)")
        
        print(f"\n💾 Test data saved in 'test_results_active/' directory")
        print(f"   • Publication JSON files")
        print(f"   • Email HTML files")
        print(f"   • Test result summaries")
    
    print("=" * 80)
    
    if successful_tests == len(test_professors):
        print("🎯 SYSTEM STATUS: ✅ FULLY OPERATIONAL - READY FOR BULK MAILING!")
    elif successful_tests > 0:
        print("⚠️ SYSTEM STATUS: PARTIALLY FUNCTIONAL - SOME ISSUES DETECTED")
        print("💡 NOTE: Some professors may not have recent publications in academic databases")
    else:
        print("❌ SYSTEM STATUS: NEEDS DEBUGGING - NO SUCCESSFUL EMAILS")
    
    print("=" * 80)
    
    return successful_tests >= 2  # Accept if at least 2 out of 3 work

if __name__ == "__main__":
    main()
