#!/usr/bin/env python3
"""
Email Test Script for InternMailer
Tests Gmail SMTP functionality before running the main application
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'InternMailer/src'))

def test_email_sending():
    """Test basic email sending functionality"""
    print("🧪 Testing InternMailer Email Functionality")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("❌ Gmail credentials not found in .env file")
        print("Please run setup.py first or create .env manually")
        return False
    
    print(f"📧 Gmail User: {gmail_user}")
    print(f"🔐 Password: {'*' * len(gmail_password) if gmail_password else 'NOT SET'}")
    
    try:
        # Import after path setup
        from gmail_sender import GmailSender
        
        # Create sender instance
        sender = GmailSender(gmail_user, gmail_password, 'test_email_log.csv')
        
        # Test email content
        test_subject = "🧪 InternMailer Test Email"
        test_body = """
Hello!

This is a test email from InternMailer to verify that your Gmail SMTP configuration is working correctly.

✅ If you receive this email, your setup is successful!

Key details:
- Sent from: InternMailer Test Script
- Gmail SMTP: Working
- Rate limiting: Enabled
- Logging: Functional

You can now use InternMailer to send personalized academic outreach emails.

Best regards,
InternMailer Team
"""
        
        # Send test email to yourself
        print(f"\n📤 Sending test email to {gmail_user}...")
        
        success = sender.send_email(
            to_email=gmail_user,
            subject=test_subject,
            body=test_body
        )
        
        if success:
            print("✅ Test email sent successfully!")
            print(f"📧 Check your inbox: {gmail_user}")
            print("📊 Email log created: test_email_log.csv")
            return True
        else:
            print("❌ Failed to send test email")
            print("📋 Check test_email_log.csv for error details")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_email_validation():
    """Test email validation functionality"""
    print("\n🔍 Testing Email Validation...")
    
    try:
        from gmail_sender import GmailSender
        sender = GmailSender("test@test.com", "test", 'test_log.csv')
        
        test_cases = [
            ("valid@example.com", True),
            ("user.name@domain.co.uk", True),
            ("invalid-email", False),
            ("@domain.com", False),
            ("user@", False),
            ("", False),
            (None, False),
        ]
        
        all_passed = True
        for email, expected in test_cases:
            result = sender.validate_email(email)
            status = "✅" if result == expected else "❌"
            if result != expected:
                all_passed = False
            print(f"{status} {email} -> {result} (expected {expected})")
        
        if all_passed:
            print("✅ All email validation tests passed!")
        else:
            print("❌ Some email validation tests failed")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Email validation test failed: {e}")
        return False

def test_resume_parsing():
    """Test resume parsing functionality"""
    print("\n📄 Testing Resume Parsing...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'InternMailer/src'))
        from resume_parser import ResumeParser
        
        # Look for existing resume files
        resume_dir = "resumes"
        if not os.path.exists(resume_dir):
            print("⚠️  Resume directory not found")
            return False
            
        resume_files = [f for f in os.listdir(resume_dir) if f.endswith('.pdf')]
        if not resume_files:
            print("⚠️  No PDF resume files found in resumes/ directory")
            return False
        
        resume_path = os.path.join(resume_dir, resume_files[0])
        print(f"📄 Testing with: {resume_files[0]}")
        
        parser = ResumeParser(resume_path)
        student_info = parser.parse()
        
        print("📊 Parsed Information:")
        print(f"   Skills: {len(student_info.get('skills', []))} found")
        print(f"   Projects: {len(student_info.get('projects', []))} found")
        print(f"   Experience: {len(student_info.get('experience', []))} found")
        
        if student_info.get('skills') or student_info.get('projects'):
            print("✅ Resume parsing working!")
            return True
        else:
            print("⚠️  Resume parsing returned minimal data")
            return False
            
    except Exception as e:
        print(f"❌ Resume parsing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 InternMailer System Test")
    print("=" * 50)
    
    tests = [
        ("Email Validation", test_email_validation),
        ("Resume Parsing", test_resume_parsing),
        ("Email Sending", test_email_sending),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! InternMailer is ready to use.")
        print("\nNext steps:")
        print("1. Run: cd InternMailer && streamlit run app.py")
        print("2. Upload your resume and configure preferences")
        print("3. Start your academic outreach campaign!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("Run setup.py again or check the troubleshooting guide.")
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)
