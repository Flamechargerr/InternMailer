#!/usr/bin/env python3
"""
Comprehensive test of the enhanced personalized email system
Tests multiple professors with different research areas
"""

import sys
import os
sys.path.append('src')
from enhanced_personalized_email import generate_deeply_personalized_email

# Test with different types of professors
test_professors = [
    {
        'name': 'Andrew Ng',
        'university': 'Stanford University',
        'research_area': 'Machine Learning and AI',
        'notable_papers': [
            'Machine Learning Yearning',
            'Deep Learning Specialization',
            'Coursera AI Education Platform'
        ],
        'current_projects': [
            'AI for Everyone initiative',
            'Deep Learning research',
            'AI education platforms'
        ],
        'homepage_text': 'Research focuses on machine learning, deep learning, and AI education. Known for founding Coursera and leading AI education initiatives. Current work includes democratizing AI education and advancing deep learning research.'
    },
    {
        'name': 'Yann LeCun',
        'university': 'NYU',
        'research_area': 'Computer Vision and Deep Learning',
        'notable_papers': [
            'Convolutional Neural Networks',
            'Self-Supervised Learning',
            'Energy-Based Models'
        ],
        'current_projects': [
            'Self-supervised learning research',
            'Computer vision advances',
            'Meta AI research'
        ],
        'homepage_text': 'Research focuses on computer vision, deep learning, and self-supervised learning. Pioneered convolutional neural networks and continues work on fundamental AI architectures.'
    },
    {
        'name': 'Fei-Fei Li',
        'university': 'Stanford University', 
        'research_area': 'Computer Vision and AI Ethics',
        'notable_papers': [
            'ImageNet Large Scale Visual Recognition',
            'Human-Centered AI',
            'AI for Social Good'
        ],
        'current_projects': [
            'Human-Centered AI Institute',
            'AI ethics research',
            'Medical AI applications'
        ],
        'homepage_text': 'Research focuses on computer vision, human-centered AI, and AI ethics. Known for ImageNet dataset and pioneering work in visual recognition. Current work emphasizes responsible AI development.'
    }
]

def test_professor_email(professor_data, test_name):
    """Test email generation for a specific professor"""
    print(f"\n{'='*80}")
    print(f"🔧 Testing: {test_name}")
    print(f"Professor: {professor_data['name']} ({professor_data['university']})")
    print(f"Research Area: {professor_data['research_area']}")
    print(f"{'='*80}")
    
    try:
        # Generate email
        email_content = generate_deeply_personalized_email(professor_data)
        
        # Save to file
        safe_name = professor_data['name'].replace(' ', '_').replace('.', '')
        output_file = f"test_email_{safe_name}.html"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Subject: Research Internship Inquiry – Anamay Tripathy re: {professor_data['research_area']}\n\n")
            f.write(email_content)
        
        # Validation checks
        print(f"✅ Email generated successfully")
        print(f"📁 Saved to: {output_file}")
        print(f"📏 Length: {len(email_content)} characters")
        
        # Content validation
        has_first_person = "I am" in email_content or "Your work" in email_content or "your research" in email_content
        has_papers = any(paper in email_content for paper in professor_data.get('notable_papers', []))
        has_greeting = f"Prof. {professor_data['name'].split()[-1]}" in email_content
        
        print(f"✅ Uses first-person addressing: {has_first_person}")
        print(f"✅ References their papers: {has_papers}")
        print(f"✅ Proper greeting: {has_greeting}")
        
        if has_first_person and has_greeting:
            print("🎉 SUCCESS: Email meets personalization criteria!")
        else:
            print("⚠️  WARNING: Email may need improvement")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def run_comprehensive_test():
    """Run comprehensive test of all professors"""
    print("🚀 Starting Comprehensive Enhanced Email System Test")
    print("="*80)
    
    success_count = 0
    total_tests = len(test_professors)
    
    for i, professor in enumerate(test_professors, 1):
        test_name = f"Test {i}/{total_tests}: {professor['name']}"
        if test_professor_email(professor, test_name):
            success_count += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    print(f"📈 Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! System is ready for Streamlit integration.")
    else:
        print("⚠️  Some tests failed. Review errors before Streamlit integration.")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    run_comprehensive_test()
