#!/usr/bin/env python3
"""
Check email setup and show first few contacts before sending
"""

import csv
import os
from datetime import datetime

# Email configuration
EMAIL_ADDRESS = "tripathy.anamay23@gmail.com"
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your_app_specific_password')

# File paths
CSV_FILE = "hr_contacts_from_spreadsheet.csv"
TEMPLATE_FILE = "enhanced_personalized_template.html"
CV_FILE = "resumes/CV_Anamay_Modern.pdf"
CONTACTED_FILE = "contacted_companies.txt"

def check_files_exist():
    """Check if all required files exist"""
    files_to_check = [
        (CSV_FILE, "CSV contact file"),
        (TEMPLATE_FILE, "Email template"),
        (CV_FILE, "Resume/CV file")
    ]
    
    print("📁 File Check:")
    all_exist = True
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✓ {description}: {file_path}")
        else:
            print(f"  ✗ {description}: {file_path} (NOT FOUND)")
            all_exist = False
    
    return all_exist

def check_email_config():
    """Check email configuration"""
    print("\n📧 Email Configuration:")
    print(f"  Email Address: {EMAIL_ADDRESS}")
    
    if EMAIL_PASSWORD == 'your_app_specific_password':
        print("  ⚠️  Email Password: NOT SET (you need to set EMAIL_PASSWORD environment variable)")
        print("     To set it, run: $env:EMAIL_PASSWORD='your_gmail_app_password'")
        return False
    else:
        print("  ✓ Email Password: SET")
        return True

def preview_contacts():
    """Preview first few contacts from CSV"""
    print(f"\n👥 Contact Preview (first 5):")
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
            # Skip disclaimer row
            first_line = csvfile.readline()
            if 'disclaimer' in first_line.lower() or 'educational' in first_line.lower():
                reader = csv.DictReader(csvfile)
            else:
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
            
            contacts = list(reader)
            print(f"  Total contacts found: {len(contacts)}")
            
            print("\n  First 5 contacts:")
            for i, contact in enumerate(contacts[:5], 1):
                name = contact.get('Name', 'N/A')
                company = contact.get('Company Name', 'N/A')
                title = contact.get('Job Title', 'N/A')
                location = contact.get('Location', 'N/A')
                niche = contact.get('Company Niche', 'N/A')
                linkedin = contact.get('Linkedin URL', 'N/A')
                
                print(f"    {i}. {name}")
                print(f"       Company: {company}")
                print(f"       Title: {title}")
                print(f"       Location: {location}")
                print(f"       Niche: {niche}")
                print(f"       LinkedIn: {linkedin}")
                print()
                
            return len(contacts)
    except Exception as e:
        print(f"  ✗ Error reading CSV: {e}")
        return 0

def generate_test_email(contact):
    """Generate email address for testing"""
    linkedin_url = contact.get('Linkedin URL', '')
    company_name = contact.get('Company Name', '')
    
    if not linkedin_url or not company_name:
        return None
    
    try:
        if '/in/' in linkedin_url:
            username = linkedin_url.split('/in/')[-1].rstrip('/')
        else:
            return None
        
        # Clean company name for domain
        company_domain = company_name.lower().replace(' ', '').replace('&', '').replace(',', '')
        common_suffixes = ['pvtltd', 'ltd', 'llc', 'inc', 'corp', 'private', 'limited']
        for suffix in common_suffixes:
            company_domain = company_domain.replace(suffix, '')
        
        # Generate email
        email = f"{username}@{company_domain}.com"
        return email
    except Exception:
        return None

def main():
    """Main function to check setup"""
    print("🔍 Email Campaign Setup Check")
    print("=" * 50)
    
    # Check files
    files_ok = check_files_exist()
    
    # Check email config
    email_ok = check_email_config()
    
    # Preview contacts
    contact_count = preview_contacts()
    
    # Show generated emails for first few contacts
    if contact_count > 0:
        print("\n📨 Generated Email Addresses (first 5):")
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
                first_line = csvfile.readline()
                if 'disclaimer' in first_line.lower() or 'educational' in first_line.lower():
                    reader = csv.DictReader(csvfile)
                else:
                    csvfile.seek(0)
                    reader = csv.DictReader(csvfile)
                
                contacts = list(reader)
                for i, contact in enumerate(contacts[:5], 1):
                    name = contact.get('Name', 'N/A')
                    company = contact.get('Company Name', 'N/A')
                    email = generate_test_email(contact)
                    print(f"    {i}. {name} at {company}: {email if email else 'Could not generate'}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Final status
    print("\n🎯 Status Summary:")
    print("=" * 30)
    
    if files_ok and email_ok and contact_count > 0:
        print("✅ Ready to send emails!")
        print(f"📊 Will process {contact_count} contacts")
        print("\n🚀 To start sending emails, run:")
        print("   python send_all_remaining_emails.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        
        if not email_ok:
            print("\n📝 To set up Gmail app password:")
            print("1. Go to Google Account settings")
            print("2. Enable 2-Factor Authentication")
            print("3. Generate an App Password for 'Mail'")
            print("4. Set it as environment variable:")
            print("   $env:EMAIL_PASSWORD='your_16_digit_app_password'")

if __name__ == "__main__":
    main()
