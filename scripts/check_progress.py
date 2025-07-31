import os
import json
import csv
from collections import defaultdict

def check_scraping_progress(data_dir):
    """Check the current progress of professor scraping."""
    
    # Check cache file
    cache_file = os.path.join(data_dir, "scraped_professors_cache.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        total_cached = len(cache_data)
        with_emails = sum(1 for prof_data in cache_data.values() if prof_data.get('email_found', '').strip())
        
        print(f"📊 Cache Progress:")
        print(f"   - Total professors processed: {total_cached}")
        print(f"   - Professors with emails found: {with_emails}")
        print(f"   - Success rate: {with_emails/total_cached*100:.1f}%")
        
        # Count by affiliation
        affiliations = defaultdict(int)
        for prof_data in cache_data.values():
            affiliation = prof_data.get('affiliation', 'Unknown')
            affiliations[affiliation] += 1
        
        print(f"\n🏫 Top 10 Affiliations:")
        for affiliation, count in sorted(affiliations.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   - {affiliation}: {count}")
    else:
        print("No cache file found.")
    
    # Check CSV files
    csv_files = [
        "scraped_professors_1000.csv",
        "scraped_professors_enhanced.csv", 
        "scraped_professors_merged.csv"
    ]
    
    print(f"\n📁 CSV Files Status:")
    for filename in csv_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                with_emails = sum(1 for row in rows if row.get('email', '').strip())
                print(f"   - {filename}: {len(rows)} professors, {with_emails} with emails")
        else:
            print(f"   - {filename}: Not found")

def get_recent_finds(data_dir, limit=20):
    """Get recent email finds from the cache."""
    cache_file = os.path.join(data_dir, "scraped_professors_cache.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Get professors with emails, sorted by scraped_at time
        with_emails = []
        for prof_key, prof_data in cache_data.items():
            if prof_data.get('email_found', '').strip():
                with_emails.append((prof_data.get('scraped_at', ''), prof_data))
        
        with_emails.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\n✅ Recent Email Discoveries (last {limit}):")
        for i, (scraped_at, prof_data) in enumerate(with_emails[:limit]):
            name = prof_data.get('name', 'Unknown')
            affiliation = prof_data.get('affiliation', 'Unknown')
            email = prof_data.get('email_found', '')
            print(f"   {i+1}. {name} ({affiliation}) - {email}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "data"
    
    check_scraping_progress(data_dir)
    get_recent_finds(data_dir, 15)
