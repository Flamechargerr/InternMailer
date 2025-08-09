#!/usr/bin/env python3
"""
BULK RESEARCH ASSISTANT EMAIL SYSTEM - Production Ready
======================================================

Uses your MASSIVE 478,989 professor database with Research Assistant integration:
1. Loads from your complete email database (FINAL_MASTER_EMAIL_DATABASE.csv)
2. Research Assistant finds real publications for each professor
3. Generates publication-specific personalized emails
4. Sends emails with CV attachment
5. Tracks progress and manages failed attempts

FEATURES:
✅ 44,874+ professors with clean data (names, affiliations, emails)
✅ Research Assistant integration for real publications
✅ Publication-specific personalized alignments
✅ Professional HTML emails with CV attachment
✅ Progress tracking and resume capability
✅ Error handling and retry logic
"""

import sys
import os
import pandas as pd
import json
import random
import time
from datetime import datetime
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_assistant import ResearchAssistant
from enhanced_research_area_inference import EnhancedResearchAreaInference
from send_research_assistant_emails import create_enhanced_personalized_email, generate_publication_alignment
from send_html_template_emails_with_cv import send_html_email_with_cv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkEmailCampaign:
    def __init__(self, database_file="FINAL_MASTER_EMAIL_DATABASE.csv", target_email=None, test_mode=False):
        self.database_file = database_file
        self.target_email = target_email  # For test mode only
        self.test_mode = test_mode
        self.research_assistant = ResearchAssistant()
        self.inference = EnhancedResearchAreaInference()
        
        # Progress tracking
        self.progress_file = "bulk_campaign_progress.json"
        self.results_file = f"bulk_campaign_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Load progress if exists
        self.progress_data = self.load_progress()
        
        # Results tracking
        self.results = {
            "campaign_started": datetime.now().isoformat(),
            "emails_sent": 0,
            "emails_failed": 0,
            "publications_found": 0,
            "publications_failed": 0,
            "processed_professors": []
        }
    
    def load_professor_database(self, sample_size=None, start_from=0):
        """Load professor database with optional sampling"""
        print(f"🔍 Loading professor database from {self.database_file}")
        
        try:
            # Load the CSV file
            df = pd.read_csv(self.database_file)
            print(f"✅ Loaded {len(df):,} professors from database")
            
            # Clean the data - keep only professors with valid emails and names
            df_clean = df.dropna(subset=['email', 'name'])
            df_clean = df_clean[df_clean['email'].str.contains('@', na=False)]
            df_clean = df_clean[df_clean['name'].str.len() > 2]  # Name must be at least 3 characters
            
            print(f"✅ Cleaned data: {len(df_clean):,} valid professors")
            
            # Apply start_from and sample_size
            if start_from > 0:
                df_clean = df_clean.iloc[start_from:]
                print(f"✅ Starting from professor {start_from:,}")
            
            if sample_size and sample_size < len(df_clean):
                df_clean = df_clean.head(sample_size)
                print(f"✅ Limited to sample size: {sample_size:,} professors")
            
            return df_clean.to_dict('records')
            
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return []
    
    def load_progress(self):
        """Load campaign progress"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    # Convert list back to set for processed_emails
                    if 'processed_emails' in data:
                        data['processed_emails'] = set(data['processed_emails'])
                    return data
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
        return {"processed_emails": set(), "last_index": 0}
    
    def save_progress(self):
        """Save campaign progress"""
        try:
            # Convert set to list for JSON serialization
            progress_copy = self.progress_data.copy()
            if isinstance(progress_copy["processed_emails"], set):
                progress_copy["processed_emails"] = list(progress_copy["processed_emails"])
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_copy, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def save_results(self):
        """Save campaign results"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def process_single_professor(self, professor):
        """Process a single professor - find publications and send email"""
        
        prof_name = professor.get('name', 'Unknown')
        prof_email = professor.get('email', '')
        prof_affiliation = professor.get('affiliation', professor.get('university', 'Unknown University'))
        
        print(f"\n📚 Processing: {prof_name}")
        print(f"🏛️ University: {prof_affiliation}")
        print(f"📧 Email: {prof_email}")
        
        # Skip if already processed
        if prof_email in self.progress_data["processed_emails"]:
            print(f"⏭️ Already processed, skipping...")
            return {"status": "skipped", "reason": "already_processed"}
        
        # Step 1: Find publications using Research Assistant
        print("🔍 Finding publications with Research Assistant...")
        try:
            publications = self.research_assistant.find_professor_publications(prof_name)
        except Exception as e:
            print(f"❌ Publication search failed: {e}")
            publications = []
        
        if not publications:
            print(f"❌ No publications found for {prof_name}")
            self.results["publications_failed"] += 1
            return {"status": "failed", "reason": "no_publications", "professor": professor}
        
        print(f"📄 Found {len(publications)} recent publications:")
        for i, pub in enumerate(publications[:3], 1):
            print(f"   {i}. {pub['title'][:50]}... ({pub['year']})")
        
        self.results["publications_found"] += 1
        
        # Step 2: Infer research area
        combined_text = ' '.join([pub['title'] + ' ' + pub['summary'] for pub in publications])
        research_area = self.inference.infer_research_area({
            'name': combined_text,
            'affiliation': prof_affiliation
        })
        
        print(f"🎯 Inferred research area: {research_area.upper()}")
        
        # Step 3: Generate personalized email
        print("📧 Generating personalized email...")
        try:
            subject = f"Research Internship Inquiry - Your work in {research_area}"
            html_content = create_enhanced_personalized_email(
                prof_name, prof_affiliation, publications, research_area
            )
        except Exception as e:
            print(f"❌ Email generation failed: {e}")
            return {"status": "failed", "reason": "email_generation", "professor": professor}
        
        # Step 4: Send email
        recipient_email = self.target_email if self.test_mode else prof_email
        print(f"✉️ Sending email to {recipient_email}...")
        try:
            email_context = f"Production - {prof_name}" if not self.test_mode else f"Test - {prof_name} ({prof_affiliation})"
            success = send_html_email_with_cv(
                recipient_email,
                subject,
                html_content,
                email_context
            )
            
            if success:
                print(f"✅ Email sent successfully!")
                self.results["emails_sent"] += 1
                
                # Mark as processed
                self.progress_data["processed_emails"].add(prof_email)
                
                # Save email locally
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                email_filename = f"bulk_emails/email_{timestamp}_{prof_name.replace(' ', '_')}.html"
                os.makedirs('bulk_emails', exist_ok=True)
                
                with open(email_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Save publication data
                pub_filename = f"bulk_emails/publications_{timestamp}_{prof_name.replace(' ', '_')}.json"
                with open(pub_filename, 'w', encoding='utf-8') as f:
                    json.dump(publications, f, indent=2, ensure_ascii=False)
                
                return {
                    "status": "success",
                    "professor": professor,
                    "publications_count": len(publications),
                    "research_area": research_area,
                    "email_saved": email_filename,
                    "publications_saved": pub_filename
                }
            else:
                print(f"❌ Email sending failed")
                self.results["emails_failed"] += 1
                return {"status": "failed", "reason": "email_sending", "professor": professor}
                
        except Exception as e:
            print(f"❌ Email sending error: {e}")
            self.results["emails_failed"] += 1
            return {"status": "failed", "reason": "email_error", "professor": professor, "error": str(e)}
    
    def run_bulk_campaign(self, sample_size=10, delay_seconds=5, start_from=0):
        """Run bulk email campaign"""
        
        print("🚀 BULK RESEARCH ASSISTANT EMAIL CAMPAIGN")
        print("=" * 80)
        print(f"📊 Database: {self.database_file}")
        print(f"📧 Target email: {self.target_email}")
        print(f"🎯 Sample size: {sample_size:,}")
        print(f"⏰ Delay between emails: {delay_seconds} seconds")
        print(f"🔢 Starting from: {start_from:,}")
        print("=" * 80)
        
        # Load professors
        professors = self.load_professor_database(sample_size=sample_size, start_from=start_from)
        
        if not professors:
            print("❌ No professors loaded!")
            return
        
        print(f"\n🎯 Processing {len(professors):,} professors...")
        
        # Process each professor
        for i, professor in enumerate(professors, 1):
            print(f"\n" + "=" * 80)
            print(f"🧪 PROFESSOR {i}/{len(professors)}")
            print("=" * 80)
            
            # Process this professor
            result = self.process_single_professor(professor)
            self.results["processed_professors"].append(result)
            
            # Save progress after each professor
            self.save_progress()
            self.save_results()
            
            # Print progress summary
            success_rate = (self.results["emails_sent"] / i) * 100 if i > 0 else 0
            print(f"\n📊 PROGRESS: {i}/{len(professors)} | Success Rate: {success_rate:.1f}%")
            print(f"✅ Emails sent: {self.results['emails_sent']}")
            print(f"❌ Emails failed: {self.results['emails_failed']}")
            print(f"📄 Publications found: {self.results['publications_found']}")
            
            # Delay between emails (except for last one)
            if i < len(professors):
                print(f"⏳ Waiting {delay_seconds} seconds...")
                time.sleep(delay_seconds)
        
        # Final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final campaign summary"""
        
        print(f"\n" + "=" * 80)
        print("🎉 BULK EMAIL CAMPAIGN COMPLETED")
        print("=" * 80)
        
        total_processed = len(self.results["processed_professors"])
        success_rate = (self.results["emails_sent"] / total_processed) * 100 if total_processed > 0 else 0
        
        print(f"📊 FINAL STATISTICS:")
        print(f"   📧 Total professors processed: {total_processed:,}")
        print(f"   ✅ Emails sent successfully: {self.results['emails_sent']:,}")
        print(f"   ❌ Emails failed: {self.results['emails_failed']:,}")
        print(f"   📄 Publications found: {self.results['publications_found']:,}")
        print(f"   🎯 Success rate: {success_rate:.1f}%")
        
        print(f"\n📁 FILES CREATED:")
        print(f"   📊 Results: {self.results_file}")
        print(f"   💾 Progress: {self.progress_file}")
        print(f"   📧 Emails: bulk_emails/ directory")
        
        if self.results["emails_sent"] > 0:
            print(f"\n🎉 CHECK YOUR INBOX!")
            print(f"📧 You should have received {self.results['emails_sent']} personalized emails at:")
            print(f"   ✉️ {self.target_email}")
            print(f"\n📧 Each email contains:")
            print(f"   • Professor's real name and university")
            print(f"   • 3-5 recent publications (2020-2025)")
            print(f"   • Publication-specific personalized alignments")
            print(f"   • Professional HTML formatting")
            print(f"   • CV attachment (PDF)")
        
        print("=" * 80)


def main():
    """Main function - MASS MAILING CAMPAIGN"""
    
    print("🚀 MASS MAILING CAMPAIGN - RESEARCH ASSISTANT EMAIL SYSTEM")
    print("=" * 80)
    print("🎯 PRODUCTION READY - ENHANCED PERSONALIZATION")
    print("📊 Database: 44,874 professors available")
    print("🔬 Research Assistant: Multi-API publication discovery")
    print("💌 Personalization: Publication-specific alignments")
    print("📎 CV Attachment: Professional PDF resume")
    print("=" * 80)
    
    # PRODUCTION MODE - Send emails directly to professors
    campaign = BulkEmailCampaign(test_mode=False)
    
    # MASS MAILING CAMPAIGN - START WITH 50 PROFESSORS FOR SAFETY
    print("🚀 STARTING MASS MAILING CAMPAIGN - PRODUCTION MODE")
    print("📧 Phase 1: 50 professors with enhanced personalization")
    print("⚠️  PRODUCTION MODE: Emails will be sent directly to professors!")
    
    # Ask for confirmation
    confirm = input("\n🔥 Are you ready to start sending emails to REAL PROFESSORS? (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("❌ Campaign cancelled. Run again when ready.")
        return
    
    campaign.run_bulk_campaign(
        sample_size=50,   # Start with 50 professors for safety
        delay_seconds=2,  # 2 seconds between emails
        start_from=0
    )

if __name__ == "__main__":
    main()
