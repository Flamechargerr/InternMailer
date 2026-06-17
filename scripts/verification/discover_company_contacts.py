#!/usr/bin/env python3
"""
Discover company contacts for job applications

This script discovers recruiter/HR contacts for companies in your job database.
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

def discover_contacts_for_jobs():
    """Discover contacts for companies with jobs"""
    
    # Get companies from jobs database
    print("📊 Loading companies from job database...")
    conn = sqlite3.connect('/tmp/internmailer_db/job_discovery.db')
    cursor = conn.execute('''
        SELECT DISTINCT company, COUNT(*) as job_count 
        FROM jobs 
        WHERE company IS NOT NULL 
        GROUP BY company 
        ORDER BY job_count DESC
    ''')
    companies = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(companies)} companies with jobs:\n")
    for company, count in companies:
        print(f"  • {company}: {count} jobs")
    
    print(f"\n{'='*60}")
    print("CONTACT DISCOVERY OPTIONS")
    print(f"{'='*60}\n")
    
    print("Option 1: Use Hunter.io API (Automated)")
    print("  - Requires Hunter API credits (you have 23 remaining)")
    print("  - May not work for all companies")
    print()
    
    print("Option 2: Manual Entry (Recommended)")
    print("  - Find contacts on LinkedIn")
    print("  - Search: 'recruiter at [company]' or 'talent acquisition [company]'")
    print("  - Add to data/company_contacts.csv")
    print()
    
    print("Option 3: Reset Existing Contacts (Testing)")
    print("  - Re-send to 14 existing contacts")
    print("  - Run: python reset_sent_emails.py")
    print()
    
    choice = input("Choose option (1/2/3) or 'q' to quit: ").strip()
    
    if choice == '1':
        print("\n🔍 Attempting Hunter.io discovery...")
        try_hunter_discovery(companies)
    elif choice == '2':
        print("\n📝 Manual entry guide:")
        show_manual_entry_guide(companies)
    elif choice == '3':
        print("\n🔄 Run this command:")
        print("  python reset_sent_emails.py")
    else:
        print("Cancelled.")

def try_hunter_discovery(companies):
    """Try to discover contacts using Hunter.io"""
    from core.lead_discovery import EnhancedLeadDiscovery
    
    # Convert company names to domains
    domains = []
    for company, _ in companies:
        # Try common domain patterns
        domain = company.lower().replace(' ', '').replace(',', '') + '.com'
        domains.append(domain)
    
    print(f"\nSearching {len(domains)} domains...")
    print("This may take a few minutes...\n")
    
    try:
        eld = EnhancedLeadDiscovery()
        result = eld.discover(domains=domains, daily_cap=50)
        
        print(f"\n✅ Discovery complete!")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Contacts found: {result.get('contacts_found', 0)}")
        print(f"New contacts: {result.get('new_contacts', 0)}")
        
        if result.get('contacts_found', 0) > 0:
            print(f"\n✅ Contacts saved to: data/company_contacts.csv")
            print("You can now send emails!")
        else:
            print(f"\n⚠️  No contacts found via Hunter.io")
            print("Try Option 2 (Manual Entry) instead")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nHunter.io discovery failed. Try manual entry instead.")

def show_manual_entry_guide(companies):
    """Show guide for manual contact entry"""
    print("\n" + "="*60)
    print("MANUAL CONTACT ENTRY GUIDE")
    print("="*60 + "\n")
    
    print("1. Find contacts on LinkedIn:")
    print("   Search: 'recruiter at [company]' or 'talent acquisition [company]'\n")
    
    print("2. Add to data/company_contacts.csv in this format:")
    print("   name,email,company,role,domain,source,discovered_at\n")
    
    print("3. Example entries for your companies:\n")
    
    # Show template for first 5 companies
    for company, _ in companies[:5]:
        domain = company.lower().replace(' ', '') + '.com'
        timestamp = datetime.now().isoformat()
        print(f"   John Doe,john.doe@{domain},{domain},Technical Recruiter,{domain},manual,{timestamp}")
    
    print("\n4. After adding contacts, refresh browser and click 'Send Emails'")
    
    print(f"\n{'='*60}")
    print("QUICK LINKEDIN SEARCH LINKS")
    print(f"{'='*60}\n")
    
    for company, _ in companies[:5]:
        search_query = f"recruiter at {company}".replace(' ', '%20')
        print(f"  • {company}:")
        print(f"    https://www.linkedin.com/search/results/people/?keywords={search_query}")
        print()

if __name__ == '__main__':
    print("="*60)
    print("🎯 COMPANY CONTACT DISCOVERY")
    print("="*60 + "\n")
    
    discover_contacts_for_jobs()
