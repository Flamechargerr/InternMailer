#!/usr/bin/env python3
"""
RANDOM PROFESSOR TESTING - Research Assistant Email System
=========================================================

This script randomly selects 3 professors from the 40k list and tests:
1. Research Assistant publication discovery
2. Enhanced email generation with real data
3. CV attachment functionality
4. Follow-up system integration
5. Complete email system verification

All emails sent to: tripathy.anamay23@gmail.com for verification
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

def load_professor_database():
    """Load the large professor database"""
    try:
        with open('data/discovered_professors_batch1.json', 'r', encoding='utf-8') as f:
            professors = json.load(f)
        return professors
    except Exception as e:
        print(f"❌ Error loading professor database: {e}")
        return []

def select_random_professors(professors, count=3):
    """Randomly select professors from the database"""
    if len(professors) < count:
        return professors
    
    # Filter for professors with valid emails and names
    valid_professors = []
    for prof in professors:
        if (prof.get('name') and prof.get('affiliation') and 
            prof.get('email') and '@' in prof.get('email', '')):
            valid_professors.append(prof)
    
    if len(valid_professors) < count:
        return valid_professors[:count]
    
    return random.sample(valid_professors, count)

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
        os.makedirs('test_results', exist_ok=True)
        
        # Save publications JSON
        prof_name_clean = professor['name'].replace(' ', '_').replace('.', '')
        json_filename = f"test_results/test_publications_{timestamp}_{prof_name_clean}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(publications, f, indent=2, ensure_ascii=False)
        
        # Save email HTML
        html_filename = f"test_results/test_email_{timestamp}_{prof_name_clean}.html"
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
        
        result_filename = f"test_results/test_result_{timestamp}_{prof_name_clean}.json"
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Publications saved: {json_filename}")
        print(f"   ✅ Email saved: {html_filename}")
        print(f"   ✅ Test result saved: {result_filename}")
        
        return True, publications, research_area
    else:
        print(f"   ❌ Failed to send email")
        return False, publications, research_area

def test_followup_integration():
    """Test follow-up system integration"""
    print(f"\n🔄 FOLLOW-UP SYSTEM INTEGRATION TEST")
    print("-" * 60)
    
    # Check if follow-up files exist
    followup_files = [
        'data/followups.json',
        'data/emailed_professors.json',
        'followup_log.csv',
        'email_log.csv'
    ]
    
    for file_path in followup_files:
        if os.path.exists(file_path):
            print(f"   ✅ Found: {file_path}")
        else:
            print(f"   ⚠️ Missing: {file_path}")
    
    # Check if follow-up scripts exist
    followup_scripts = [
        'send_followup_emails.py',
        'auto_followup.py'
    ]
    
    for script in followup_scripts:
        if os.path.exists(script):
            print(f"   ✅ Found: {script}")
        else:
            print(f"   ⚠️ Missing: {script}")

def main():
    """Main testing function"""
    
    print("🧪 RANDOM PROFESSOR TESTING - Research Assistant Email System")
    print("=" * 80)
    print("🎯 Testing with 3 random professors from the 40k database")
    print("📧 All emails sent to: tripathy.anamay23@gmail.com")
    print("🔬 Testing complete Research Assistant integration")
    print("=" * 80)
    
    # Load professor database
    print("\n📊 Loading Professor Database")
    professors = load_professor_database()
    
    if not professors:
        print("❌ No professors loaded from database!")
        return
    
    print(f"✅ Loaded {len(professors)} professors from database")
    
    # Select random professors
    print(f"\n🎲 Selecting 3 Random Professors")
    test_professors = select_random_professors(professors, 3)
    
    if not test_professors:
        print("❌ No valid professors found for testing!")
        return
    
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
    
    # Test follow-up integration
    test_followup_integration()
    
    # Final Results Summary
    print(f"\n" + "=" * 80)
    print("🎉 RANDOM PROFESSOR TESTING - RESULTS SUMMARY")
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
        
        print(f"\n💾 Test data saved in 'test_results/' directory")
        print(f"   • Publication JSON files")
        print(f"   • Email HTML files")
        print(f"   • Test result summaries")
    
    print("=" * 80)
    
    if successful_tests == len(test_professors):
        print("🎯 SYSTEM STATUS: ✅ FULLY OPERATIONAL - READY FOR BULK MAILING!")
    elif successful_tests > 0:
        print("⚠️ SYSTEM STATUS: PARTIALLY FUNCTIONAL - SOME ISSUES DETECTED")
    else:
        print("❌ SYSTEM STATUS: NEEDS DEBUGGING - NO SUCCESSFUL EMAILS")
    
    print("=" * 80)
    
    return successful_tests == len(test_professors)

if __name__ == "__main__":
    main()
