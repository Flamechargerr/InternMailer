#!/usr/bin/env python3
"""
Extract HR Contacts from Enhanced Background Emails
"""

import pandas as pd
import json
import re

def extract_hr_contacts():
    """Extract HR contacts from enhanced background emails"""
    print("🔍 EXTRACTING HR CONTACTS FROM ENHANCED BACKGROUND EMAILS")
    print("=" * 60)
    
    # Load enhanced background emails
    try:
        df = pd.read_csv('data/enhanced_background_emails_20250804_204317.csv')
        print(f"📊 Loaded {len(df):,} emails from enhanced background database")
    except Exception as e:
        print(f"❌ Error loading enhanced background emails: {e}")
        return
    
    # HR-related keywords to identify HR contacts
    hr_keywords = [
        'hr', 'human.resources', 'recruitment', 'talent', 'hiring', 'recruiter',
        'careers', 'jobs', 'employment', 'staffing', 'personnel', 'talent.acquisition',
        'hr@', 'recruiting@', 'careers@', 'jobs@', 'talent@', 'hiring@',
        'hr-', 'recruitment-', 'talent-', 'hiring-', 'careers-', 'jobs-',
        'hr_', 'recruitment_', 'talent_', 'hiring_', 'careers_', 'jobs_'
    ]
    
    # Company-related keywords
    company_keywords = [
        'company', 'corp', 'inc', 'llc', 'ltd', 'enterprise', 'business',
        'tech', 'software', 'ai', 'ml', 'data', 'analytics', 'consulting',
        'startup', 'venture', 'capital', 'investment', 'finance', 'banking'
    ]
    
    hr_contacts = []
    
    # Filter for HR-related emails
    for idx, row in df.iterrows():
        email = str(row['email']).lower()
        name = str(row['name']) if pd.notna(row['name']) else ''
        affiliation = str(row['affiliation']) if pd.notna(row['affiliation']) else ''
        
        # Check if email contains HR keywords
        is_hr = any(keyword in email for keyword in hr_keywords)
        
        # Check if name or affiliation contains HR keywords
        is_hr_name = any(keyword in name.lower() for keyword in hr_keywords)
        is_hr_affiliation = any(keyword in affiliation.lower() for keyword in hr_keywords)
        
        # Check if it's a company email (not academic)
        is_company = any(keyword in email for keyword in company_keywords)
        is_academic = any(domain in email for domain in ['.edu', 'university', 'college', 'institute'])
        
        if (is_hr or is_hr_name or is_hr_affiliation) and is_company and not is_academic:
            # Clean the email
            clean_email = re.sub(r'[^\w@.-]', '', email)
            if '@' in clean_email and '.' in clean_email.split('@')[1]:
                hr_contacts.append({
                    'email': clean_email,
                    'name': name if name != 'nan' else '',
                    'affiliation': affiliation if affiliation != 'nan' else '',
                    'source': 'enhanced_background',
                    'extracted_at': row['extracted_at']
                })
    
    # Remove duplicates
    unique_hr_contacts = []
    seen_emails = set()
    for contact in hr_contacts:
        if contact['email'] not in seen_emails:
            unique_hr_contacts.append(contact)
            seen_emails.add(contact['email'])
    
    print(f"\n🎯 FOUND HR CONTACTS:")
    print(f"   • Total HR contacts found: {len(unique_hr_contacts):,}")
    
    # Save to file
    output_file = 'data/extracted_hr_contacts.json'
    with open(output_file, 'w') as f:
        json.dump(unique_hr_contacts, f, indent=2)
    
    print(f"   • Saved to: {output_file}")
    
    # Show sample
    print(f"\n📋 SAMPLE HR CONTACTS:")
    for i, contact in enumerate(unique_hr_contacts[:10]):
        print(f"   {i+1}. {contact['email']} - {contact['name']} - {contact['affiliation']}")
    
    return unique_hr_contacts

def update_hr_database():
    """Update the HR database with extracted contacts"""
    print("\n🔄 UPDATING HR DATABASE")
    print("=" * 60)
    
    # Load existing HR contacts
    existing_hr = []
    try:
        with open('data/enhanced_hr_contacts.json', 'r') as f:
            existing_hr = json.load(f)
        print(f"📊 Existing HR contacts: {len(existing_hr)}")
    except:
        print("📊 No existing HR contacts found")
    
    # Load extracted HR contacts
    try:
        with open('data/extracted_hr_contacts.json', 'r') as f:
            extracted_hr = json.load(f)
        print(f"📊 Extracted HR contacts: {len(extracted_hr)}")
    except:
        print("❌ No extracted HR contacts found")
        return
    
    # Combine and remove duplicates
    all_hr_contacts = existing_hr + extracted_hr
    unique_hr_contacts = []
    seen_emails = set()
    
    for contact in all_hr_contacts:
        email = contact.get('email', '')
        if email and email not in seen_emails:
            unique_hr_contacts.append(contact)
            seen_emails.add(email)
    
    # Save combined database
    with open('data/enhanced_hr_contacts.json', 'w') as f:
        json.dump(unique_hr_contacts, f, indent=2)
    
    print(f"✅ Updated HR database: {len(unique_hr_contacts)} total contacts")
    print(f"📈 Added {len(extracted_hr)} new HR contacts")

if __name__ == "__main__":
    extract_hr_contacts()
    update_hr_database() 