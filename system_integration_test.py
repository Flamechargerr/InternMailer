#!/usr/bin/env python3
"""
System Integration Test
Tests all components: HR contacts, professor database, scraping, and email templates
"""

import pandas as pd
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json
from datetime import datetime

class SystemIntegrationTest:
    def __init__(self):
        """Initialize the system integration test"""
        self.test_results = {}
        print("🔍 SYSTEM INTEGRATION TEST")
        print("="*60)

    def test_data_files(self):
        """Test all data files exist and are accessible"""
        print("\n📊 TESTING DATA FILES...")
        
        files_to_check = [
            'hr_contacts_cleaned.csv',
            'targeted_professors_scraped.csv',
            'professors_unified_scraped.csv',
            'mass_professors_scraped.csv'
        ]
        
        for file in files_to_check:
            if os.path.exists(file):
                df = pd.read_csv(file)
                self.test_results[f"{file}_exists"] = True
                self.test_results[f"{file}_rows"] = len(df)
                print(f"✅ {file}: {len(df)} rows")
            else:
                self.test_results[f"{file}_exists"] = False
                print(f"❌ {file}: NOT FOUND")

    def test_hr_contacts(self):
        """Test HR contacts data quality"""
        print("\n👥 TESTING HR CONTACTS...")
        
        if os.path.exists('hr_contacts_cleaned.csv'):
            df = pd.read_csv('hr_contacts_cleaned.csv')
            
            # Check required columns
            required_columns = ['Name', 'Job Title', 'Company Name', 'Company Niche', 'Location']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if not missing_columns:
                self.test_results['hr_contacts_columns'] = True
                print(f"✅ HR Contacts: {len(df)} contacts from {df['Company Name'].nunique()} companies")
                print(f"✅ Sample: {df['Name'].iloc[0]} at {df['Company Name'].iloc[0]}")
            else:
                self.test_results['hr_contacts_columns'] = False
                print(f"❌ Missing columns: {missing_columns}")

    def test_professor_database(self):
        """Test professor database quality"""
        print("\n🎓 TESTING PROFESSOR DATABASE...")
        
        files_to_check = [
            ('targeted_professors_scraped.csv', 'Targeted Professors'),
            ('professors_unified_scraped.csv', 'Unified Professors'),
            ('mass_professors_scraped.csv', 'Mass Professors')
        ]
        
        for file, name in files_to_check:
            if os.path.exists(file):
                df = pd.read_csv(file)
                emails_count = df['email'].notna().sum() if 'email' in df.columns else 0
                print(f"✅ {name}: {len(df)} professors, {emails_count} with emails")
                self.test_results[f"{name.lower().replace(' ', '_')}_count"] = len(df)
                self.test_results[f"{name.lower().replace(' ', '_')}_emails"] = emails_count

    def test_email_templates(self):
        """Test email templates exist and are valid"""
        print("\n📧 TESTING EMAIL TEMPLATES...")
        
        templates_to_check = [
            'templates/enhanced_email_template.html',
            'templates/academic_research_template.html',
            'templates/enhanced_hr_template.html'
        ]
        
        for template in templates_to_check:
            if os.path.exists(template):
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '{{' in content and '}}' in content:
                        self.test_results[f"{template}_valid"] = True
                        print(f"✅ {template}: Valid template with placeholders")
                    else:
                        self.test_results[f"{template}_valid"] = False
                        print(f"⚠️ {template}: No placeholders found")
            else:
                self.test_results[f"{template}_exists"] = False
                print(f"❌ {template}: NOT FOUND")

    def test_scraping_integration(self):
        """Test scraping integration with CSV files"""
        print("\n🔍 TESTING SCRAPING INTEGRATION...")
        
        # Check data directory
        if os.path.exists('data'):
            csv_files = [f for f in os.listdir('data') if f.endswith('.csv')]
            print(f"✅ Data directory: {len(csv_files)} CSV files")
            self.test_results['data_directory_files'] = len(csv_files)
            
            # Check for csrankings files
            csrankings_files = [f for f in csv_files if 'csrankings' in f.lower()]
            print(f"✅ CSRankings files: {len(csrankings_files)} files")
            self.test_results['csrankings_files'] = len(csrankings_files)
        else:
            print("❌ Data directory not found")
            self.test_results['data_directory_exists'] = False

    def test_email_sending_capability(self):
        """Test email sending capability (without actually sending)"""
        print("\n📤 TESTING EMAIL SENDING CAPABILITY...")
        
        try:
            # Test SMTP connection (will fail without credentials, but that's expected)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            print("✅ SMTP server connection test passed")
            self.test_results['smtp_connection'] = True
        except Exception as e:
            print(f"⚠️ SMTP connection test: {str(e)}")
            self.test_results['smtp_connection'] = False

    def test_template_rendering(self):
        """Test template rendering with sample data"""
        print("\n🎨 TESTING TEMPLATE RENDERING...")
        
        # Test HR template
        if os.path.exists('templates/enhanced_hr_template.html'):
            with open('templates/enhanced_hr_template.html', 'r', encoding='utf-8') as f:
                hr_template = f.read()
                
            # Sample HR data
            sample_hr_data = {
                'name': 'John Smith',
                'company_name': 'TechCorp',
                'company_niche': 'Artificial Intelligence'
            }
            
            # Test template replacement
            test_hr_email = hr_template
            for key, value in sample_hr_data.items():
                test_hr_email = test_hr_email.replace(f'{{{{ {key} }}}}', value)
            
            if 'John Smith' in test_hr_email and 'TechCorp' in test_hr_email:
                print("✅ HR template rendering: SUCCESS")
                self.test_results['hr_template_rendering'] = True
            else:
                print("❌ HR template rendering: FAILED")
                self.test_results['hr_template_rendering'] = False

        # Test Academic template
        if os.path.exists('templates/academic_research_template.html'):
            with open('templates/academic_research_template.html', 'r', encoding='utf-8') as f:
                academic_template = f.read()
                
            # Sample professor data
            sample_professor_data = {
                'professor.last_name': 'Johnson',
                'professor.research_area': 'Machine Learning'
            }
            
            # Test template replacement
            test_academic_email = academic_template
            for key, value in sample_professor_data.items():
                test_academic_email = test_academic_email.replace(f'{{{{ {key} }}}}', value)
            
            if 'Johnson' in test_academic_email and 'Machine Learning' in test_academic_email:
                print("✅ Academic template rendering: SUCCESS")
                self.test_results['academic_template_rendering'] = True
            else:
                print("❌ Academic template rendering: FAILED")
                self.test_results['academic_template_rendering'] = False

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 GENERATING TEST REPORT...")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        
        print(f"📊 TEST SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"system_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"✅ Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests

    def run_all_tests(self):
        """Run all system integration tests"""
        print("🚀 STARTING SYSTEM INTEGRATION TESTS...")
        
        self.test_data_files()
        self.test_hr_contacts()
        self.test_professor_database()
        self.test_email_templates()
        self.test_scraping_integration()
        self.test_email_sending_capability()
        self.test_template_rendering()
        
        success = self.generate_test_report()
        
        if success:
            print("\n🎉 ALL TESTS PASSED! System is fully integrated and ready.")
        else:
            print("\n⚠️ Some tests failed. Please check the detailed report.")
        
        return success

def main():
    """Main function"""
    tester = SystemIntegrationTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ SYSTEM INTEGRATION: SUCCESS")
        print("All components are working properly!")
    else:
        print("\n❌ SYSTEM INTEGRATION: ISSUES DETECTED")
        print("Please check the test report for details.")

if __name__ == "__main__":
    main() 