#!/usr/bin/env python3
"""
Extreme-performance batch professor email scraper with maximum parallel processing.
Processes 1000 professors at a time with 400 concurrent workers for ultimate efficiency and accuracy.
Includes advanced duplicate prevention, intelligent caching, and optimized connection handling.
"""

import sys
import os
import csv
import logging
from datetime import datetime

# Add src to path
sys.path.append('.')
from src.enhanced_professor_scraper import EnhancedProfessorScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_professors_from_csvs(data_dir):
    """Load professors from all available CSV files, avoiding duplicates."""
    csv_files = [
        'scraped_professors_1000.csv',
        'scraped_professors_final.csv', 
        'scraped_professors_merged.csv',
        'discovered_professors.csv'
    ]
    
    # Also load from csrankings files
    for fname in os.listdir(data_dir):
        if fname.startswith('csrankings-') and fname.endswith('.csv'):
            csv_files.append(fname)
    
    professors = []
    seen_profs = set()
    
    for filename in csv_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('name', '').strip()
                        affiliation = row.get('affiliation', '').strip()
                        if name and affiliation:
                            prof_key = f"{name}|{affiliation}"
                            if prof_key not in seen_profs:
                                seen_profs.add(prof_key)
                                professors.append(row)
                logging.info(f"Loaded {len(professors)} professors from {filename}")
            except Exception as e:
                logging.warning(f"Could not load {filename}: {e}")
    
    return professors

def main():
    data_dir = './data'
    
    # Load all professors
    all_professors = load_professors_from_csvs(data_dir)
    logging.info(f"Total professors loaded: {len(all_professors)}")
    
    # Initialize scraper with ULTRA-HIGH performance settings - 1000 workers for MAXIMUM efficiency
    scraper = EnhancedProfessorScraper(data_dir, max_workers=1000)
    
    # Get unscraped professors only
    unscraped = scraper.get_unscraped_professors(all_professors)
    logging.info(f"Unscraped professors: {len(unscraped)}")
    
    if not unscraped:
        logging.info("All professors have been scraped already!")
        return
    
    # Process 3000 professors for ULTRA-HIGH throughput and efficiency
    target_count = 3000
    if len(unscraped) < target_count:
        logging.warning(f"Only {len(unscraped)} unscraped professors available, processing all of them")
        batch = unscraped
    else:
        batch = unscraped[:target_count]
    
    logging.info(f"🚀💥 Processing batch of {len(batch)} professors with 1000 concurrent workers for ULTRA-HIGH performance")
    
    # Set professors and enrich with emails
    scraper.professors = batch
    enriched = scraper.enrich_with_emails_parallel()
    filtered = scraper.deduplicate_and_filter()
    
    logging.info(f"Successfully enriched {len(filtered)} professors with valid emails")
    
    # Save results
    if filtered:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(data_dir, f'enriched_professors_batch_{timestamp}.csv')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(filtered[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered)
        
        logging.info(f"✅ Saved enriched data to {output_file}")
        logging.info(f"Fields saved: {fieldnames}")
        
        # Print summary stats
        with_emails = sum(1 for prof in filtered if prof.get('email', '').strip())
        success_rate = (with_emails / len(filtered)) * 100 if filtered else 0
        
        print(f"\n📊 Batch Processing Summary:")
        print(f"   - Total processed: {len(batch)}")
        print(f"   - Valid emails found: {with_emails}")
        print(f"   - Success rate: {success_rate:.1f}%")
        print(f"   - Output file: {output_file}")
    
    # Print scraper summary
    summary = scraper.get_scraped_summary()
    print(f"\n🔍 Overall Scraper Summary:")
    print(f"   - Total scraped: {summary['total_professors_scraped']}")
    print(f"   - Total emails found: {summary['total_emails_found']}")
    print(f"   - Overall success rate: {summary['success_rate']}%")

if __name__ == "__main__":
    main()
