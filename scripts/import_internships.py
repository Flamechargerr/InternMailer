#!/usr/bin/env python3
"""
Import Internships from Markdown List
=====================================
Reads 'internship_opportunities_2025_2026.md' and imports jobs into the database.
"""

import re
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
MARKDOWN_FILE = "/Users/anamay/Library/Containers/net.whatsapp.WhatsApp/Data/tmp/documents/E54CCCF6-AF17-45A0-AA6F-494575CBA097/internship_opportunities_2025_2026.md"
DB_PATH = "/tmp/internmailer_db/job_discovery.db"

def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find company blocks
    # Looking for: ### 1. Company Name
    company_pattern = re.compile(r'### \d+\.\s+(.*?)\n(.*?)(?=\n###|\n##|\Z)', re.DOTALL)
    
    matches = company_pattern.findall(content)
    jobs = []

    for company_name, block in matches:
        company_name = company_name.strip()
        
        # Extract Roles
        roles_match = re.search(r'\*\*Roles:\*\*\s+(.*?)\n', block)
        roles = roles_match.group(1).strip() if roles_match else "Software Engineer Intern"
        
        # Extract Apply URL or Careers Page
        apply_match = re.search(r'\*\*(?:Apply|Careers Page):\*\*\s+(.*?)\n', block)
        url = apply_match.group(1).strip() if apply_match else ""
        
        # Clean URL (sometimes it has text after it?)
        if url:
             # Basic cleanup, sometimes markdown links [text](url) or just raw url
             # For now assume raw url or simple text
             pass

        # Extract Tier (Need to look backwards or track current tier, but for now specific tier isn't critical, 
        # just importing is good. Optionally we could track it if we parsed line by line)
        
        # Split roles if possible, or just create one entry
        # If multiple roles are listed (e.g. "Software Engineer, Data Scientist"), 
        # we might want to create separate entries? 
        # But they share the same URL. 
        # Strategy: Create one entry for the company main internship page.
        
        if not url:
            print(f"Skipping {company_name}: No URL found")
            continue

        job = {
            "company": company_name,
            "title": roles, # Put all roles in title for visibility, or truncate
            "url": url,
            "description": block.strip(),
            "source": "manual_import_tier_list",
            "posted_at": datetime.now().isoformat()
        }
        jobs.append(job)

    return jobs

def import_jobs(jobs):
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure table exists (it should, but just in case)
    # Refers to JobDiscoveryDB schema
    
    count = 0
    updated = 0
    
    for job in jobs:
        # Generate a unique URL to avoid constraints if the bare URL is the same for multiple entries 
        # (though here we only have one entry per companyblock)
        # But wait, other jobs might exist with this URL.
        # We'll use INSERT OR IGNORE or UPDATE.
        
        # If the URL is just "Check company website", we can't really use it.
        if "check company website" in job['url'].lower():
             # heuristic: generate a fake url for our tracking
             safe_name = re.sub(r'[^a-z0-9]', '', job['company'].lower())
             job['url'] = f"https://manual-import.internal/{safe_name}"

        try:
            # Check if exists
            cursor.execute("SELECT id FROM jobs WHERE url = ?", (job['url'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update?
                # cursor.execute("UPDATE jobs SET ... WHERE id=?", ...)
                updated += 1
            else:
                cursor.execute('''
                    INSERT INTO jobs (
                        source, company, title, url, apply_url, description, 
                        status, created_at, updated_at, score, visa_sponsorship
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job['source'],
                    job['company'],
                    job['title'],
                    job['url'],  # Using as unique ID
                    job['url'],  # Also as apply URL
                    job['description'],
                    'new',
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    10.0, # High score for manual list
                    1 if 'visa' in job['description'].lower() or 'sponsor' in job['description'].lower() else 0
                ))
                count += 1
                
        except sqlite3.IntegrityError as e:
            print(f"Error importing {job['company']}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Import complete. Imported {count} new jobs. Skipped {updated} existing.")

if __name__ == "__main__":
    found_jobs = parse_markdown(MARKDOWN_FILE)
    print(f"Found {len(found_jobs)} jobs in markdown.")
    import_jobs(found_jobs)
