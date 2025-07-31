import os
import csv
import json
import pandas as pd
from src.enhanced_professor_scraper import EnhancedProfessorScraper as ProfessorScraper
import time
from datetime import datetime
from generate_email import generate_personalized_email
from send_mass_email import send_mass_email

def run_scraper_in_batches(data_dir, batch_size=100, total_professors=1000, max_workers=50):
    """Run the professor scraper in batches with enhanced multiprocessing."""
    if not os.path.exists(data_dir):
        print(f"Data directory '{data_dir}' not found!")
        return

    try:
        # Initialize scraper with increased worker count
        scraper = ProfessorScraper(data_dir, max_workers=max_workers)
        
        print("📚 Parsing all CSV files...")
        all_professors = scraper.parse_csvs()
        print(f"Found {len(all_professors)} total professors in CSV files")
        
        if not all_professors:
            print("No professors to scrape.")
            return
        
        # Check existing cache to see how many are already scraped
        cache_summary = scraper.get_scraped_summary()
        print(f"📋 Cache status: {cache_summary['total_professors_scraped']} professors already scraped, {cache_summary['total_emails_found']} emails found")
        
        # Get only unscraped professors
        unscraped_professors = scraper.get_unscraped_professors(all_professors)
        print(f"🆕 Found {len(unscraped_professors)} unscraped professors")
        
        if not unscraped_professors:
            print("🎉 All professors have already been scraped! Loading existing results...")
            scraper.professors = all_professors
            scraper._load_cached_emails()
            final_professors = scraper.deduplicate_and_filter()
            print(f"📊 Final dataset: {len(final_professors)} unique professors with emails")
            return
        
        # Limit to the requested total from unscraped
        professors_to_scrape = unscraped_professors[:total_professors]
        print(f"🎯 Will scrape {len(professors_to_scrape)} new professors in batches of {batch_size} using {max_workers} workers")
        
        num_batches = (len(professors_to_scrape) + batch_size - 1) // batch_size
        all_enriched_professors = []
        total_scraped = 0
        total_emails_found = 0
        
        print(f"\n🚀 Starting batch processing at {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        for i in range(num_batches):
            batch_start_time = time.time()
            batch = professors_to_scrape[i*batch_size:(i+1)*batch_size]

            print(f"\n📦 Processing batch {i+1}/{num_batches} ({len(batch)} professors)")
            print(f"⚡ Using {max_workers} parallel workers...")

            # Set batch and run parallel scraping
            scraper.professors = batch
            enriched_batch = scraper.enrich_with_emails_parallel()
            all_enriched_professors.extend(enriched_batch)
            
            # Count results for this batch
            batch_emails = sum(1 for prof in enriched_batch if prof.get('email', '').strip())
            total_scraped += len(batch)
            total_emails_found += batch_emails
            
            batch_end_time = time.time()
            batch_duration = batch_end_time - batch_start_time
            
            print(f"✅ Batch {i+1} completed in {batch_duration:.2f}s")
            print(f"📧 Found {batch_emails}/{len(batch)} emails ({batch_emails/len(batch)*100:.1f}% success)")
            print(f"📈 Total progress: {total_scraped}/{len(professors_to_scrape)} professors, {total_emails_found} emails found")
            
            # Add delay between batches to be respectful (reduced for efficiency)
            if i < num_batches - 1:
                print("⏳ Waiting 2 seconds before next batch...")
                time.sleep(2)

        print("\n" + "=" * 60)
        print("🎯 All batches processed!")

        # Combine with previously scraped professors
        print("🔄 Loading all professors (including previously scraped)...")
        scraper.professors = all_professors  # Load all professors
        scraper._load_cached_emails()  # Load cached emails for all
        
        # Deduplicate and filter final results
        print("🧹 Deduplicating and filtering final results...")
        final_professors = scraper.deduplicate_and_filter()
        print(f"📊 Final dataset: {len(final_professors)} unique professors with emails")
        
        # Save to CSV with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(data_dir, f"scraped_professors_batch_{timestamp}.csv")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if final_professors:
                fieldnames = final_professors[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(final_professors)
                
        print(f"\n✅ Scraping completed! Results saved to {output_file}")
        
        # Enhanced statistics
        overall_cache_summary = scraper.get_scraped_summary()
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   🎯 Target: {total_professors} new professors")
        print(f"   ✅ Actually scraped: {total_scraped} professors")
        print(f"   📧 New emails found: {total_emails_found}")
        print(f"   📈 New batch success rate: {total_emails_found/total_scraped*100:.1f}%")
        print(f"   🏆 Total in cache: {overall_cache_summary['total_professors_scraped']} professors")
        print(f"   📬 Total emails in cache: {overall_cache_summary['total_emails_found']}")
        print(f"   📊 Overall success rate: {overall_cache_summary['success_rate']}%")
        print(f"   💾 Unique professors with emails in final file: {len(final_professors)}")
        
        # Update the main final file as well
        main_output_file = os.path.join(data_dir, "scraped_professors_final.csv")
        with open(main_output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if final_professors:
                fieldnames = final_professors[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(final_professors)
        print(f"   📄 Updated main file: {main_output_file}")
        
        # Load previously emailed professors and send new emails
        duplication_check = set()
        emailed_professors_file = os.path.join(data_dir, "emailed_professors.json")
        
        # Read existing emailed professors
        try:
            with open(emailed_professors_file, 'r', encoding='utf-8') as f:
                existing_emailed_professors = json.load(f)["professors"]
                duplication_check.update(p["email"] for p in existing_emailed_professors)
        except FileNotFoundError:
            existing_emailed_professors = []
        
        # Generate and send personalized emails
        new_emailed_entries = []
        emails_sent = 0
        for professor in final_professors:
            if professor['email'] not in duplication_check:
                professor_name = professor['name']
                recipient_email = professor['email']
                homepage = professor.get('homepage', '')
                subject = f"Research Internship Inquiry – Anamay Tripathy re: {professor.get('Research Area', 'Computer Science')}"
                print(f"📧 Generating email for {professor_name}")
                try:
                    email_content = generate_personalized_email(professor_name, professor.get('Research Area', 'Computer Science'))
                    print(f"📨 Sending email to {recipient_email}")
                    send_mass_email(subject, email_content, [recipient_email], attachment_path='Anamay_Tripathy_CV.txt')
                    emails_sent += 1
                    
                    new_emailed_entries.append({
                        "email": recipient_email,
                        "name": professor_name,
                        "university": professor.get('affiliation', ''),
                        "first_emailed": datetime.now().isoformat(),
                        "last_emailed": datetime.now().isoformat(),
                        "last_subject": subject,
                        "status": "sent",
                        "email_count": 1,
                        "notes": "Automated send - batch scraper"
                    })
                except Exception as e:
                    print(f"❌ Failed to send email to {professor_name}: {e}")
            else:
                print(f"⏭️ Skipping {professor['name']} - already emailed")
        
        # Update emailed professors file
        existing_emailed_professors.extend(new_emailed_entries)
        with open(emailed_professors_file, 'w', encoding='utf-8') as f:
            json.dump({"professors": existing_emailed_professors}, f, indent=2)
        
        print(f"\n📧 EMAIL STATISTICS:")
        print(f"   📨 New emails sent: {emails_sent}")
        print(f"   ⏭️ Emails skipped (duplicates): {len(final_professors) - emails_sent}")
        print(f"   📬 Total tracked emails: {len(existing_emailed_professors)}")
        
    except Exception as e:
        print(f"❌ Scraping failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # This part is for running from the command line, not from Streamlit
    import sys
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
        run_scraper_in_batches(data_directory)
    else:
        print("Please provide the data directory as an argument.")

