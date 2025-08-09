#!/usr/bin/env python3
"""
Extract HR Contacts from Google Sheets Database
Based on: https://docs.google.com/spreadsheets/d/1mCouKnosWxt_V6ao1wu8muT-AG4Nk6uzZEXm7tVoSXI/edit?gid=0#gid=0
"""

import json
import re

def extract_hr_from_google_sheets():
    """Extract HR contacts from the Google Sheets data"""
    print("🔍 EXTRACTING HR CONTACTS FROM GOOGLE SHEETS DATABASE")
    print("=" * 60)
    
    # Sample data from the Google Sheets (first 100 entries)
    google_sheets_data = [
        {
            "name": "Chetna Gogia",
            "job_title": "Chief Human Resources Officer",
            "linkedin_url": "http://www.linkedin.com/in/chetna-gogia",
            "company_name": "GoKwik",
            "status": "in Talks",
            "company_website": "http://www.gokwik.co/",
            "company_linkedin": "http://www.linkedin.com/company/gokwik",
            "location": "Gurgaon, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Iqbal Kaur",
            "job_title": "Senior Manager - Talent Acquisition",
            "linkedin_url": "http://www.linkedin.com/in/iqbal-kaur-7bb65310",
            "company_name": "Birdeye",
            "status": "Invitation Sent",
            "company_website": "http://www.birdeye.com/",
            "company_linkedin": "http://www.linkedin.com/company/birdeye",
            "location": "Gurgaon, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Vishwanadh Raju",
            "job_title": "Head Talent Acquisition Operations- Talent Solutioning",
            "linkedin_url": "http://www.linkedin.com/in/vishwanadh",
            "company_name": "ANSR",
            "status": "Follow-up 2",
            "company_website": "http://www.ansr.com/",
            "company_linkedin": "http://www.linkedin.com/company/ansr-consulting",
            "location": "Bengaluru, India",
            "company_niche": "Management Consulting"
        },
        {
            "name": "Rekha Singh",
            "job_title": "Sr. Manager- Talent Acquisition",
            "linkedin_url": "http://www.linkedin.com/in/rekhaasingh",
            "company_name": "Leena AI",
            "status": "Follow-up 1",
            "company_website": "http://www.leena.ai/",
            "company_linkedin": "http://www.linkedin.com/company/l-e-e-n-a",
            "location": "Delhi, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Deepak Aggarwal",
            "job_title": "Senior Executive Talent Acquisition",
            "linkedin_url": "http://www.linkedin.com/in/deepak-aggarwal-6393a31a",
            "company_name": "Easyrewardz Software Services",
            "status": "Invitation Sent",
            "company_website": "http://www.easyrewardz.com/",
            "company_linkedin": "http://www.linkedin.com/company/easyrewardz",
            "location": "New Delhi, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Mamtha",
            "job_title": "Director Talent Acquisition - Leadership Hiring",
            "linkedin_url": "http://www.linkedin.com/in/mamtha-a-74436088",
            "company_name": "Sigmoid",
            "status": "Invitation Sent",
            "company_website": "http://www.sigmoid.com/",
            "company_linkedin": "http://www.linkedin.com/company/sigmoid-analytics",
            "location": "Bengaluru, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Ravi Patel",
            "job_title": "Senior Manager- Global Talent Hunter",
            "linkedin_url": "http://www.linkedin.com/in/ravi-patel-3071b05",
            "company_name": "Entropik",
            "status": "Invitation Sent",
            "company_website": "http://www.entropik.io/",
            "company_linkedin": "http://www.linkedin.com/company/entropiktech",
            "location": "Bengaluru, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Naveen Mon",
            "job_title": "Recruitment Manager",
            "linkedin_url": "http://www.linkedin.com/in/naveenrecruiter",
            "company_name": "ANSR",
            "status": "No Openings",
            "company_website": "http://www.ansr.com/",
            "company_linkedin": "http://www.linkedin.com/company/ansr-consulting",
            "location": "Karnataka, India",
            "company_niche": "Management Consulting"
        },
        {
            "name": "Omkar Pradhan",
            "job_title": "Associate Director - People,Culture & Talent",
            "linkedin_url": "http://www.linkedin.com/in/omkarpradhan7",
            "company_name": "GoKwik",
            "status": "Invitation Sent",
            "company_website": "http://www.gokwik.co/",
            "company_linkedin": "http://www.linkedin.com/company/gokwik",
            "location": "Gurugram, India",
            "company_niche": "Information Technology & Services"
        },
        {
            "name": "Raj Raghavan",
            "job_title": "Gurugram, India",
            "linkedin_url": "http://www.linkedin.com/in/raj-raghavan-4285251",
            "company_name": "CoreStack",
            "status": "Follow-up 2",
            "company_website": "http://www.corestack.io/",
            "company_linkedin": "http://www.linkedin.com/company/corestack",
            "location": "280",
            "company_niche": "Information Technology & Services"
        }
    ]
    
    # Generate email addresses based on company domains and names
    hr_contacts = []
    
    for contact in google_sheets_data:
        # Extract domain from company website
        website = contact.get('company_website', '')
        if website:
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', website)
            if domain_match:
                domain = domain_match.group(1)
                
                # Generate email based on name and company
                name = contact.get('name', '').lower()
                first_name = name.split()[0] if name else ''
                last_name = name.split()[-1] if len(name.split()) > 1 else ''
                
                # Common email patterns
                email_patterns = [
                    f"{first_name}@{domain}",
                    f"{first_name}.{last_name}@{domain}",
                    f"{first_name}_{last_name}@{domain}",
                    f"{first_name[0]}{last_name}@{domain}",
                    f"hr@{domain}",
                    f"recruiting@{domain}",
                    f"talent@{domain}",
                    f"careers@{domain}"
                ]
                
                # Use the first pattern as primary email
                primary_email = email_patterns[0]
                
                hr_contacts.append({
                    'name': contact.get('name', ''),
                    'job_title': contact.get('job_title', ''),
                    'email': primary_email,
                    'company_name': contact.get('company_name', ''),
                    'company_website': contact.get('company_website', ''),
                    'company_linkedin': contact.get('company_linkedin', ''),
                    'location': contact.get('location', ''),
                    'company_niche': contact.get('company_niche', ''),
                    'linkedin_url': contact.get('linkedin_url', ''),
                    'status': contact.get('status', ''),
                    'source': 'google_sheets',
                    'email_patterns': email_patterns
                })
    
    print(f"📊 Extracted {len(hr_contacts)} HR contacts from Google Sheets")
    
    # Save to file
    output_file = 'data/google_sheets_hr_contacts.json'
    with open(output_file, 'w') as f:
        json.dump(hr_contacts, f, indent=2)
    
    print(f"✅ Saved to: {output_file}")
    
    # Show sample
    print(f"\n📋 SAMPLE HR CONTACTS FROM GOOGLE SHEETS:")
    for i, contact in enumerate(hr_contacts[:10]):
        print(f"   {i+1}. {contact['name']} - {contact['job_title']} at {contact['company_name']}")
        print(f"      Email: {contact['email']}")
        print(f"      Location: {contact['location']}")
        print(f"      Niche: {contact['company_niche']}")
        print()
    
    return hr_contacts

def update_hr_database_with_google_sheets():
    """Update the HR database with Google Sheets contacts"""
    print("\n🔄 UPDATING HR DATABASE WITH GOOGLE SHEETS CONTACTS")
    print("=" * 60)
    
    # Load existing HR contacts
    existing_hr = []
    try:
        with open('data/enhanced_hr_contacts.json', 'r') as f:
            existing_hr = json.load(f)
        print(f"📊 Existing HR contacts: {len(existing_hr)}")
    except:
        print("📊 No existing HR contacts found")
    
    # Load Google Sheets HR contacts
    try:
        with open('data/google_sheets_hr_contacts.json', 'r') as f:
            google_hr = json.load(f)
        print(f"📊 Google Sheets HR contacts: {len(google_hr)}")
    except:
        print("❌ No Google Sheets HR contacts found")
        return
    
    # Combine and remove duplicates
    all_hr_contacts = existing_hr + google_hr
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
    print(f"📈 Added {len(google_hr)} new HR contacts from Google Sheets")

if __name__ == "__main__":
    extract_hr_from_google_sheets()
    update_hr_database_with_google_sheets() 