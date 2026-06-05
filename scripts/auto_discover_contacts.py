#!/usr/bin/env python3
"""
Auto-Discover Contacts for Imported Jobs
========================================
Runs EnhancedLeadDiscovery for the newly imported jobs.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock TCC blocked modules
import types
fake_certifi = types.ModuleType("certifi")
fake_certifi.where = lambda: "/etc/ssl/cert.pem"
sys.modules["certifi"] = fake_certifi

fake_psutil = types.ModuleType("psutil")
fake_psutil.cpu_percent = lambda interval=None: 5.0
fake_psutil.cpu_count = lambda: 8
fake_psutil.virtual_memory = lambda: types.SimpleNamespace(total=16*1024**3, available=8*1024**3, used=8*1024**3, percent=50.0)
fake_psutil.disk_usage = lambda path: types.SimpleNamespace(total=500*1024**3, used=250*1024**3, free=250*1024**3, percent=50.0)
sys.modules["psutil"] = fake_psutil

os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'

from core.lead_discovery import EnhancedLeadDiscovery
from core.database_manager import get_job_discovery_db

def main():
    print("🔍 Starting Auto-Discovery for Imported Jobs...")
    
    # 1. Get imported jobs
    db = get_job_discovery_db()
    jobs = db.fetch_all("SELECT company, url, apply_url FROM jobs WHERE source='manual_import_tier_list'")
    
    if not jobs:
        print("No imported jobs found to process.")
        return

    print(f"Found {len(jobs)} imported jobs. Extracting domains...")
    
    # 2. Extract domains
    eld = EnhancedLeadDiscovery()
    domains = set()
    for job in jobs:
        # Try apply_url first
        d = eld._extract_domain(job['apply_url'])
        if d: domains.add(d)
        
        # Try url
        d = eld._extract_domain(job['url'])
        if d: domains.add(d)

    domain_list = list(domains)
    print(f"Extracted {len(domain_list)} unique domains.")
    
    # 3. Run Discovery
    # We set a cap of 50 or so to avoid hitting rate limits too hard if scraping
    result = eld.discover(domains=domain_list, daily_cap=100)
    
    print("\n✅ Discovery Finished!")
    print(f"Contacts Found: {result.get('contacts_found', 0)}")
    print(f"Contacts Saved: {result.get('contacts_saved', 0)}")

if __name__ == "__main__":
    main()
