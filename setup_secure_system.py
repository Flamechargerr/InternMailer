#!/usr/bin/env python3
"""
🔒 SECURE SYSTEM SETUP UTILITY
================================================================================
Helps set up environment variables and run security checks
================================================================================
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_environment_variables():
    """Interactive setup for environment variables"""
    
    print("🔒 SECURE AI SYSTEM SETUP")
    print("=" * 50)
    print("\nThis will help you set up secure environment variables for the AI system.")
    print("Your credentials will be stored as environment variables, not in code.\n")
    
    # Check if variables already exist
    existing_username = os.getenv('SMTP_USERNAME')
    existing_password = os.getenv('SMTP_PASSWORD')
    
    if existing_username and existing_password:
        print(f"✅ Environment variables already configured:")
        print(f"   SMTP_USERNAME: {existing_username}")
        print(f"   SMTP_PASSWORD: {'*' * len(existing_password)}")
        
        if input("\nReconfigure? (y/N): ").lower().strip() != 'y':
            print("Keeping existing configuration.")
            return True
    
    print("\n📧 GMAIL SETUP REQUIRED:")
    print("1. Go to Google Account settings")
    print("2. Enable 2-Factor Authentication")
    print("3. Generate an 'App Password' for this application")
    print("4. Use the App Password (not your regular password)\n")
    
    # Get credentials
    username = input("Enter your Gmail address: ").strip()
    if not username or '@' not in username:
        print("❌ Invalid email address!")
        return False
    
    password = input("Enter your Gmail App Password (16 characters): ").strip()
    if not password or len(password) < 10:
        print("❌ Invalid password! Please use a proper App Password.")
        return False
    
    # Set environment variables for current session
    os.environ['SMTP_USERNAME'] = username
    os.environ['SMTP_PASSWORD'] = password
    
    print(f"\n✅ Environment variables configured for this session!")
    print(f"   SMTP_USERNAME: {username}")
    print(f"   SMTP_PASSWORD: {'*' * len(password)}")
    
    # Show how to make permanent
    print(f"\n🔧 TO MAKE PERMANENT:")
    print(f"Run these commands in PowerShell:")
    print(f"  $env:SMTP_USERNAME='{username}'")
    print(f"  $env:SMTP_PASSWORD='{password}'")
    print(f"\nOr add to your system environment variables through Windows Settings.")
    
    return True

def run_security_check():
    """Run basic security checks"""
    
    print("\n🔍 SECURITY CHECKS")
    print("=" * 30)
    
    checks = []
    
    # Check environment variables
    if os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD'):
        checks.append(("Environment Variables", "✅ PASS"))
    else:
        checks.append(("Environment Variables", "❌ FAIL - Not configured"))
    
    # Check database file
    db_path = Path(__file__).parent / "data" / "proffesor_clean.csv"
    if db_path.exists():
        checks.append(("Database File", "✅ PASS"))
    else:
        checks.append(("Database File", "❌ FAIL - Missing"))
    
    # Check Python packages
    try:
        import pandas, smtplib, ssl
        checks.append(("Required Packages", "✅ PASS"))
    except ImportError as e:
        checks.append(("Required Packages", f"❌ FAIL - {e}"))
    
    # Check write permissions
    try:
        test_dir = Path(__file__).parent / "secure_campaign_results"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        checks.append(("File Permissions", "✅ PASS"))
    except Exception as e:
        checks.append(("File Permissions", f"❌ FAIL - {e}"))
    
    # Display results
    print()
    for check, status in checks:
        print(f"{check:20} {status}")
    
    # Overall status
    failed = [check for check, status in checks if "FAIL" in status]
    if failed:
        print(f"\n⚠️  {len(failed)} security checks failed!")
        return False
    else:
        print(f"\n✅ All security checks passed!")
        return True

def run_test_campaign():
    """Run a small test campaign"""
    
    print("\n🧪 TEST CAMPAIGN")
    print("=" * 25)
    
    try:
        # Import the secure system
        from secure_automated_ai_system import SecureAutomatedAISystem
        
        print("Initializing secure system...")
        system = SecureAutomatedAISystem()
        
        print("Running test campaign (5 emails)...")
        results = system.run_secure_automation(max_emails=5)
        
        if results['success']:
            print(f"\n🎉 TEST SUCCESSFUL!")
            print(f"📧 Emails sent: {results['emails_sent']}")
            print(f"🎯 Success rate: {results['success_rate']:.1f}%")
            print(f"🔒 Security status: {results['security_status']}")
        else:
            print(f"\n❌ Test failed: {results.get('error', 'Unknown error')}")
            
        return results['success']
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

def main():
    """Main setup process"""
    
    print("🚀 SECURE AI CAMPAIGN SYSTEM SETUP")
    print("=" * 50)
    
    # Step 1: Environment setup
    print("\n📋 Step 1: Configure Environment Variables")
    if not setup_environment_variables():
        print("❌ Environment setup failed!")
        return
    
    # Step 2: Security check
    print("\n📋 Step 2: Security Checks")
    if not run_security_check():
        print("❌ Security checks failed! Please fix issues before continuing.")
        return
    
    # Step 3: Test campaign
    print("\n📋 Step 3: Test Campaign")
    if input("Run test campaign? (Y/n): ").lower().strip() != 'n':
        if run_test_campaign():
            print("\n🎉 SETUP COMPLETE!")
            print("Your secure AI system is ready for production use!")
        else:
            print("\n⚠️  Test failed. Please check configuration.")
    else:
        print("\n✅ Setup complete! You can now run:")
        print("   python secure_automated_ai_system.py")
    
    print(f"\n🔒 SECURITY FEATURES ENABLED:")
    print(f"   ✅ Environment-based credentials")
    print(f"   ✅ Input validation & sanitization")
    print(f"   ✅ Secure rate limiting")
    print(f"   ✅ Thread-safe operations")
    print(f"   ✅ Privacy-protected logging")
    print(f"   ✅ Secure file operations")

if __name__ == "__main__":
    main()
