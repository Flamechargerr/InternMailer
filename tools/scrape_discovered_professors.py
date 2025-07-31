import os
import csv
from src.enhanced_professor_scraper import EnhancedProfessorScraper

def scrape_discovered_professors(data_dir, discovered_file="discovered_professors.csv", max_workers=8):
    """Scrape emails from newly discovered professors."""
    
    discovered_path = os.path.join(data_dir, discovered_file)
    if not os.path.exists(discovered_path):
        print(f"No {discovered_file} found in {data_dir}")
        return
    
    # Load discovered professors
    discovered_professors = []
    with open(discovered_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            discovered_professors.append(row)
    
    print(f"Found {len(discovered_professors)} newly discovered professors")
    
    # Initialize enhanced scraper
    scraper = EnhancedProfessorScraper(data_dir, max_workers=max_workers)
    
    # Convert discovered professors to format expected by scraper
    formatted_professors = []
    for prof in discovered_professors:
        formatted_prof = {
            'name': prof['name'],
            'affiliation': prof['affiliation'],
            'homepage': prof['homepage'],
            'scholarid': prof.get('scholarid', ''),
            'source': prof.get('source', 'discovered')
        }
        formatted_professors.append(formatted_prof)
    
    # Set professors and scrape
    scraper.professors = formatted_professors
    
    print(f"Starting to scrape emails for {len(formatted_professors)} discovered professors...")
    enriched_professors = scraper.enrich_with_emails_parallel()
    
    # Filter for those with emails
    with_emails = [prof for prof in enriched_professors if prof.get('email', '').strip()]
    
    print(f"✅ Successfully found emails for {len(with_emails)} out of {len(formatted_professors)} professors")
    print(f"   Success rate: {len(with_emails)/len(formatted_professors)*100:.1f}%")
    
    # Save results
    output_file = os.path.join(data_dir, "discovered_professors_enriched.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        if enriched_professors:
            fieldnames = ['name', 'affiliation', 'homepage', 'scholarid', 'email', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched_professors)
    
    print(f"💾 Saved enriched discovered professors to {output_file}")
    
    # Show some examples
    print(f"\n📧 Example discovered emails:")
    for i, prof in enumerate(with_emails[:10]):
        print(f"   {i+1}. {prof['name']} ({prof['affiliation']}) - {prof['email']}")
    
    return enriched_professors, with_emails

def merge_discovered_with_main(data_dir):
    """Merge discovered professors with main database."""
    discovered_enriched_file = os.path.join(data_dir, "discovered_professors_enriched.csv")
    main_file = os.path.join(data_dir, "scraped_professors_merged.csv")
    
    if not os.path.exists(discovered_enriched_file):
        print("No enriched discovered professors file found")
        return
    
    # Load discovered professors
    discovered_profs = []
    with open(discovered_enriched_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        discovered_profs = list(reader)
    
    # Load main database
    main_profs = []
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            main_profs = list(reader)
    
    # Merge avoiding duplicates by email
    existing_emails = {prof.get('email', '').strip() for prof in main_profs if prof.get('email', '').strip()}
    new_profs = [prof for prof in discovered_profs if prof.get('email', '').strip() and prof.get('email', '').strip() not in existing_emails]
    
    all_profs = main_profs + new_profs
    
    # Normalize fieldnames - ensure all professors have the same fields
    all_fieldnames = set()
    for prof in all_profs:
        all_fieldnames.update(prof.keys())
    
    # Fill missing fields with empty strings
    for prof in all_profs:
        for field in all_fieldnames:
            if field not in prof:
                prof[field] = ''
    
    # Save merged data
    output_file = os.path.join(data_dir, "scraped_professors_final.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        if all_profs:
            fieldnames = sorted(all_fieldnames)  # Sort for consistency
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_profs)
    
    total_with_emails = sum(1 for prof in all_profs if prof.get('email', '').strip())
    
    print(f"\n🔗 Merge Summary:")
    print(f"   - Previous professors: {len(main_profs)}")
    print(f"   - New discovered professors: {len(new_profs)}")
    print(f"   - Total professors: {len(all_profs)}")
    print(f"   - Total with emails: {total_with_emails}")
    print(f"   - Overall success rate: {total_with_emails/len(all_profs)*100:.1f}%")
    print(f"   - Saved to: {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
    else:
        data_directory = "data"
    
    # Scrape emails for discovered professors
    enriched, with_emails = scrape_discovered_professors(data_directory)
    
    # Merge with main database
    merge_discovered_with_main(data_directory)
