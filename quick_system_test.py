#!/usr/bin/env python3
"""
Quick System Test
Tests all components without JSON serialization issues
"""

import pandas as pd
import os
from datetime import datetime

def test_system_integration():
    """Test all system components"""
    print("🔍 QUICK SYSTEM INTEGRATION TEST")
    print("="*60)
    
    results = []
    
    # Test 1: HR Contacts
    print("\n👥 TESTING HR CONTACTS...")
    if os.path.exists('hr_contacts_cleaned.csv'):
        df = pd.read_csv('hr_contacts_cleaned.csv')
        required_columns = ['Name', 'Job Title', 'Company Name', 'Company Niche', 'Location']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if not missing_columns:
            print(f"✅ HR Contacts: {len(df)} contacts from {df['Company Name'].nunique()} companies")
            results.append(("HR Contacts", "PASS", f"{len(df)} contacts"))
        else:
            print(f"❌ HR Contacts: Missing columns {missing_columns}")
            results.append(("HR Contacts", "FAIL", "Missing columns"))
    else:
        print("❌ HR Contacts: File not found")
        results.append(("HR Contacts", "FAIL", "File not found"))

    # Test 2: Professor Database
    print("\n🎓 TESTING PROFESSOR DATABASE...")
    professor_files = [
        ('targeted_professors_scraped.csv', 'Targeted Professors'),
        ('professors_unified_scraped.csv', 'Unified Professors'),
        ('mass_professors_scraped.csv', 'Mass Professors')
    ]
    
    for file, name in professor_files:
        if os.path.exists(file):
            df = pd.read_csv(file)
            emails_count = df['email'].notna().sum() if 'email' in df.columns else 0
            print(f"✅ {name}: {len(df)} professors, {emails_count} with emails")
            results.append((name, "PASS", f"{len(df)} professors, {emails_count} emails"))
        else:
            print(f"❌ {name}: File not found")
            results.append((name, "FAIL", "File not found"))

    # Test 3: Email Templates
    print("\n📧 TESTING EMAIL TEMPLATES...")
    templates = [
        'templates/enhanced_email_template.html',
        'templates/academic_research_template.html',
        'templates/enhanced_hr_template.html'
    ]
    
    for template in templates:
        if os.path.exists(template):
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
                if '{{' in content and '}}' in content:
                    print(f"✅ {template}: Valid template")
                    results.append((os.path.basename(template), "PASS", "Valid template"))
                else:
                    print(f"⚠️ {template}: No placeholders")
                    results.append((os.path.basename(template), "WARN", "No placeholders"))
        else:
            print(f"❌ {template}: Not found")
            results.append((os.path.basename(template), "FAIL", "Not found"))

    # Test 4: Scraping Integration
    print("\n🔍 TESTING SCRAPING INTEGRATION...")
    if os.path.exists('data'):
        csv_files = [f for f in os.listdir('data') if f.endswith('.csv')]
        csrankings_files = [f for f in csv_files if 'csrankings' in f.lower()]
        print(f"✅ Data directory: {len(csv_files)} CSV files")
        print(f"✅ CSRankings files: {len(csrankings_files)} files")
        results.append(("Scraping Integration", "PASS", f"{len(csv_files)} files"))
    else:
        print("❌ Data directory not found")
        results.append(("Scraping Integration", "FAIL", "No data directory"))

    # Test 5: Template Rendering
    print("\n🎨 TESTING TEMPLATE RENDERING...")
    
    # Test HR template
    if os.path.exists('templates/enhanced_hr_template.html'):
        with open('templates/enhanced_hr_template.html', 'r', encoding='utf-8') as f:
            hr_template = f.read()
        
        test_hr_email = hr_template.replace('{{ name }}', 'John Smith').replace('{{ company_name }}', 'TechCorp')
        if 'John Smith' in test_hr_email and 'TechCorp' in test_hr_email:
            print("✅ HR template rendering: SUCCESS")
            results.append(("HR Template Rendering", "PASS", "Success"))
        else:
            print("❌ HR template rendering: FAILED")
            results.append(("HR Template Rendering", "FAIL", "Failed"))
    
    # Test Academic template
    if os.path.exists('templates/academic_research_template.html'):
        with open('templates/academic_research_template.html', 'r', encoding='utf-8') as f:
            academic_template = f.read()
        
        test_academic_email = academic_template.replace('{{ professor.last_name }}', 'Johnson').replace('{{ professor.research_area }}', 'Machine Learning')
        if 'Johnson' in test_academic_email and 'Machine Learning' in test_academic_email:
            print("✅ Academic template rendering: SUCCESS")
            results.append(("Academic Template Rendering", "PASS", "Success"))
        else:
            print("❌ Academic template rendering: FAILED")
            results.append(("Academic Template Rendering", "FAIL", "Failed"))

    # Generate Summary
    print("\n📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, status, details in results:
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
    
    # Save simple report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"quick_test_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(f"Quick System Test Report - {timestamp}\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total Tests: {total}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {total - passed}\n")
        f.write(f"Success Rate: {(passed/total)*100:.1f}%\n\n")
        f.write("Detailed Results:\n")
        for test_name, status, details in results:
            f.write(f"{status} - {test_name}: {details}\n")
    
    print(f"\n✅ Report saved to: {report_file}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is fully integrated and ready.")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check the detailed report.")
        return False

def main():
    """Main function"""
    success = test_system_integration()
    
    if success:
        print("\n✅ SYSTEM INTEGRATION: SUCCESS")
        print("All components are working properly!")
    else:
        print("\n❌ SYSTEM INTEGRATION: ISSUES DETECTED")
        print("Please check the test report for details.")

if __name__ == "__main__":
    main() 