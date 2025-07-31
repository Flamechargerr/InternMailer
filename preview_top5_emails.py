import csv

# Load contacts
with open('hr_contacts_from_spreadsheet.csv', 'r', encoding='utf-8') as csvfile:
    lines = csvfile.readlines()
    # Skip the first disclaimer line and use the second line as headers
    csvfile.seek(0)
    next(csvfile)  # Skip disclaimer line
    reader = csv.DictReader(csvfile)
    company_data = list(reader)

role_mapping = {
    'Management Consulting': 'business analysis, process optimization, and strategic consulting',
    'Information Technology & Services': 'software development, data analysis, and technical solutions',
    'Data Science': 'machine learning, data engineering, and analytics',
    'Fintech': 'financial technology development and data analysis',
    'E-commerce': 'platform development, user experience optimization, and data analytics'
}

print("🎯 TOP 5 CONTACTS TO EMAIL:")
print("=" * 80)

for i, contact in enumerate(company_data[:5], 1):
    company_name = contact['Company Name']
    linkedin_url = contact['Linkedin URL']
    
    # Generate email from LinkedIn profile (simplified approach)
    if 'linkedin.com/in/' in linkedin_url:
        username = linkedin_url.split('/in/')[-1]
        email = f"{username}@{contact['Company Name'].lower().replace(' ', '').replace('.', '')}.com"
    else:
        email = f"hr@{contact['Company Name'].lower().replace(' ', '').replace('.', '')}.com"
    
    name = contact.get('Name', 'HR Team')
    title = contact.get('Job Title', 'HR Professional')
    location = contact.get('Location', 'Location')
    company_niche = contact.get('Company Niche', 'Technology')
    specific_role = role_mapping.get(company_niche, 'software development and data analysis')
    
    print(f"#{i} {name} ({title})")
    print(f"   Company: {company_name}")
    print(f"   Location: {location}")
    print(f"   Company Niche: {company_niche}")
    print(f"   Roles: {specific_role}")
    print(f"   Generated Email: {email}")
    print(f"   LinkedIn: {linkedin_url}")
    print()

print("⚠️  NOTE: These are generated email addresses based on LinkedIn profiles.")
print("   Actual email delivery may vary based on company email policies.")
print()
print("📋 PROCEED TO SEND EMAILS TO THESE 5 CONTACTS? (Y/N)")
