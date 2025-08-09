#!/usr/bin/env python3
"""
ENHANCED BULK EMAIL CAMPAIGN - TARGET 80%+ SUCCESS RATE
======================================================

Improvements:
1. Enhanced Research Assistant with multiple sources
2. Better professor filtering and validation
3. Smart retry mechanisms for failed searches
4. Improved research area inference
5. Better email personalization
6. Advanced progress tracking
7. Quality scoring and professor prioritization
8. Automatic campaign optimization

Usage:
    python enhanced_bulk_campaign.py --mode production --size 100 --delay 2
    python enhanced_bulk_campaign.py --mode test --size 5 --email your@email.com
"""

import sys
import os
import pandas as pd
import json
import random
import time
import argparse
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_research_assistant import EnhancedResearchAssistant
from enhanced_research_area_inference import EnhancedResearchAreaInference
from send_research_assistant_emails import create_enhanced_personalized_email, generate_publication_alignment
from send_html_template_emails_with_cv import send_html_email_with_cv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBulkCampaign:
    def __init__(self, database_file="FINAL_MASTER_EMAIL_DATABASE.csv", test_email=None):
        self.database_file = database_file
        self.test_email = test_email
        self.research_assistant = EnhancedResearchAssistant()
        self.inference = EnhancedResearchAreaInference()
        
        # Enhanced progress tracking
        self.progress_file = "enhanced_campaign_progress.json"
        self.results_file = f"enhanced_campaign_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Load progress
        self.progress_data = self.load_progress()
        
        # Enhanced metrics
        self.results = {
            "campaign_started": datetime.now().isoformat(),
            "emails_sent": 0,
            "emails_failed": 0,
            "publications_found": 0,
            "publications_failed": 0,
            "retry_attempts": 0,
            "retry_successes": 0,
            "high_quality_matches": 0,
            "processed_professors": [],
            "quality_metrics": {
                "total_citations": 0,
                "avg_publications_per_prof": 0,
                "top_venues_found": []
            }
        }
    
    def load_progress(self):
        """Load enhanced progress tracking"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    if 'processed_emails' in data:
                        data['processed_emails'] = set(data['processed_emails'])
                    if 'failed_names' not in data:
                        data['failed_names'] = set()
                    else:
                        data['failed_names'] = set(data['failed_names'])
                    return data
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
        
        return {
            "processed_emails": set(), 
            "failed_names": set(),
            "last_index": 0,
            "quality_threshold": 0.6
        }
    
    def save_progress(self):
        """Save enhanced progress tracking"""
        try:
            progress_copy = self.progress_data.copy()
            progress_copy["processed_emails"] = list(progress_copy["processed_emails"])
            progress_copy["failed_names"] = list(progress_copy["failed_names"])
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_copy, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def load_professor_database_enhanced(self, sample_size=None, start_from=0, quality_filter=True):
        """Enhanced professor database loading with quality filtering"""
        print(f"🔍 Loading enhanced professor database from {self.database_file}")
        
        try:
            df = pd.read_csv(self.database_file)
            print(f"✅ Loaded {len(df):,} professors from database")
            
            # Enhanced cleaning
            df_clean = df.dropna(subset=['email', 'name'])
            df_clean = df_clean[df_clean['email'].str.contains('@', na=False)]
            df_clean = df_clean[df_clean['name'].str.len() > 2]
            
            # Remove obviously bad email formats
            df_clean = df_clean[~df_clean['email'].str.contains(r'[0-9]{3,}', regex=True, na=False)]
            df_clean = df_clean[~df_clean['email'].str.contains(r'\.open$|\.eduphone$|items\.|assistant$', regex=True, na=False)]
            
            print(f"✅ After enhanced cleaning: {len(df_clean):,} valid professors")
            
            if quality_filter:
                # Quality scoring
                df_clean['quality_score'] = self.calculate_professor_quality_score(df_clean)
                df_clean = df_clean[df_clean['quality_score'] >= self.progress_data.get('quality_threshold', 0.6)]
                df_clean = df_clean.sort_values('quality_score', ascending=False)
                print(f"✅ After quality filtering: {len(df_clean):,} high-quality professors")
            
            # Apply pagination
            if start_from > 0:
                df_clean = df_clean.iloc[start_from:]
            
            if sample_size and sample_size < len(df_clean):
                df_clean = df_clean.head(sample_size)
            
            return df_clean.to_dict('records')
            
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return []
    
    def calculate_professor_quality_score(self, df):
        """Calculate quality scores for professors"""
        scores = []
        
        for _, row in df.iterrows():
            score = 0.5  # Base score
            
            # Name quality
            name = str(row.get('name', ''))
            if len(name.split()) >= 2:  # Has first and last name
                score += 0.2
            if not any(char.isdigit() for char in name):  # No numbers in name
                score += 0.1
            
            # Email quality
            email = str(row.get('email', ''))
            if email.endswith('.edu'):
                score += 0.2
            if not any(suspicious in email.lower() for suspicious in ['phone', 'fax', 'office', 'items']):
                score += 0.1
            
            # Affiliation quality
            affiliation = str(row.get('affiliation', '') or row.get('university', ''))
            if any(keyword in affiliation.lower() for keyword in ['university', 'college', 'institute']):
                score += 0.1
            
            scores.append(min(score, 1.0))  # Cap at 1.0
        
        return scores
    
    def process_professor_enhanced(self, professor):
        """Enhanced professor processing with retry logic"""
        prof_name = professor.get('name', 'Unknown')
        prof_email = professor.get('email', '')
        prof_affiliation = professor.get('affiliation', professor.get('university', 'Unknown University'))
        
        print(f"\n📚 Enhanced processing: {prof_name}")
        print(f"🏛️ University: {prof_affiliation}")
        print(f"📧 Email: {prof_email}")
        print(f"⭐ Quality Score: {professor.get('quality_score', 'N/A'):.2f}" if professor.get('quality_score') else "")
        
        # Skip if already processed
        if prof_email in self.progress_data["processed_emails"]:
            print(f"⏭️ Already processed, skipping...")
            return {"status": "skipped", "reason": "already_processed"}
        
        # Skip if previously failed (unless retry conditions met)
        if prof_name in self.progress_data.get("failed_names", set()):
            if not self.should_retry_professor(prof_name):
                print(f"⏭️ Previously failed, skipping...")
                return {"status": "skipped", "reason": "previously_failed"}
        
        # Enhanced publication search
        print("🔍 Enhanced publication search with multiple sources...")
        try:
            publications = self.research_assistant.find_professor_publications(prof_name, prof_affiliation)
        except Exception as e:
            print(f"❌ Publication search failed: {e}")
            publications = []
        
        if not publications:
            print(f"❌ No publications found for {prof_name}")
            self.progress_data["failed_names"].add(prof_name)
            self.results["publications_failed"] += 1
            return {"status": "failed", "reason": "no_publications", "professor": professor}
        
        # Quality assessment of publications
        quality_score = self.assess_publication_quality(publications)
        print(f"📄 Found {len(publications)} publications (Quality: {quality_score:.2f})")
        
        for i, pub in enumerate(publications[:3], 1):
            citations_info = f" ({pub['citations']} citations)" if pub.get('citations', 0) > 0 else ""
            print(f"   {i}. {pub['title'][:60]}... ({pub['year']}) - {pub['source']}{citations_info}")
        
        self.results["publications_found"] += 1
        if quality_score >= 0.8:
            self.results["high_quality_matches"] += 1
        
        # Enhanced research area inference
        combined_text = ' '.join([
            pub['title'] + ' ' + pub.get('summary', '') + ' ' + pub.get('venue', '')
            for pub in publications
        ])
        
        research_area = self.inference.infer_research_area({
            'name': combined_text,
            'affiliation': prof_affiliation
        })
        
        print(f"🎯 Inferred research area: {research_area.upper()}")
        
        # Enhanced email generation
        print("📧 Generating enhanced personalized email...")
        try:
            subject = f"Research Internship Inquiry - Your work in {research_area}"
            html_content = create_enhanced_personalized_email(
                prof_name, prof_affiliation, publications, research_area
            )
        except Exception as e:
            print(f"❌ Email generation failed: {e}")
            return {"status": "failed", "reason": "email_generation", "professor": professor}
        
        # Send email
        recipient_email = self.test_email if self.test_email else prof_email
        send_mode = "Test Mode" if self.test_email else "Production"
        print(f"✉️ Sending email to {recipient_email} ({send_mode})...")
        
        try:
            success = send_html_email_with_cv(
                recipient_email,
                subject,
                html_content,
                f"Enhanced Campaign - {prof_name}"
            )
            
            if success:
                print(f"✅ Email sent successfully!")
                self.results["emails_sent"] += 1
                
                # Update progress
                self.progress_data["processed_emails"].add(prof_email)
                if prof_name in self.progress_data.get("failed_names", set()):
                    self.progress_data["failed_names"].remove(prof_name)
                    self.results["retry_successes"] += 1
                
                # Update quality metrics
                total_citations = sum(pub.get('citations', 0) for pub in publications)
                self.results["quality_metrics"]["total_citations"] += total_citations
                
                # Save email and publications
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                email_filename = f"enhanced_emails/email_{timestamp}_{prof_name.replace(' ', '_')}.html"
                os.makedirs('enhanced_emails', exist_ok=True)
                
                with open(email_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                pub_filename = f"enhanced_emails/publications_{timestamp}_{prof_name.replace(' ', '_')}.json"
                with open(pub_filename, 'w', encoding='utf-8') as f:
                    pub_data = {
                        "professor": professor,
                        "publications": publications,
                        "research_area": research_area,
                        "quality_score": quality_score,
                        "total_citations": total_citations
                    }
                    json.dump(pub_data, f, indent=2, ensure_ascii=False)
                
                return {
                    "status": "success",
                    "professor": professor,
                    "publications_count": len(publications),
                    "research_area": research_area,
                    "quality_score": quality_score,
                    "total_citations": total_citations,
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
    
    def assess_publication_quality(self, publications):
        """Assess the quality of found publications"""
        if not publications:
            return 0.0
        
        total_score = 0
        for pub in publications:
            score = 0.3  # Base score for having a publication
            
            # Recent publications get higher scores
            year = pub.get('year')
            if year and str(year).isdigit():
                year_int = int(year)
                if year_int >= 2023:
                    score += 0.3
                elif year_int >= 2021:
                    score += 0.2
                elif year_int >= 2020:
                    score += 0.1
            
            # Citation count
            citations = pub.get('citations', 0)
            if citations > 100:
                score += 0.3
            elif citations > 20:
                score += 0.2
            elif citations > 5:
                score += 0.1
            
            # Venue quality
            venue = pub.get('venue', '').lower()
            if any(keyword in venue for keyword in ['nature', 'science', 'cell']):
                score += 0.2
            elif any(keyword in venue for keyword in ['ieee', 'acm', 'neurips', 'icml']):
                score += 0.15
            
            # Source reliability
            source_scores = {
                'Google Scholar': 0.1,
                'Semantic Scholar': 0.1,
                'CrossRef': 0.1,
                'arXiv': 0.05,
                'PubMed': 0.1
            }
            score += source_scores.get(pub.get('source'), 0.05)
            
            total_score += min(score, 1.0)
        
        return min(total_score / len(publications), 1.0)
    
    def should_retry_professor(self, prof_name):
        """Determine if we should retry a previously failed professor"""
        # Simple retry logic - could be enhanced
        retry_count = self.results.get("retry_attempts", 0)
        return retry_count < 3  # Allow up to 3 retries
    
    def run_enhanced_campaign(self, sample_size=50, delay_seconds=2, start_from=0, test_mode=False):
        """Run enhanced bulk campaign with improved success rates"""
        
        print("🚀 ENHANCED BULK EMAIL CAMPAIGN")
        print("="*80)
        print(f"🎯 TARGET: 80%+ success rate")
        print(f"📊 Database: {self.database_file}")
        print(f"📧 Mode: {'Test' if test_mode else 'Production'}")
        print(f"🎯 Sample size: {sample_size:,}")
        print(f"⏰ Delay: {delay_seconds}s")
        print(f"🔢 Starting from: {start_from:,}")
        print("="*80)
        
        # Load professors with enhanced filtering
        professors = self.load_professor_database_enhanced(
            sample_size=sample_size, 
            start_from=start_from,
            quality_filter=True
        )
        
        if not professors:
            print("❌ No professors loaded!")
            return
        
        print(f"\n🎯 Processing {len(professors):,} high-quality professors...")
        
        # Process each professor
        for i, professor in enumerate(professors, 1):
            print(f"\n" + "="*80)
            print(f"🧪 PROFESSOR {i}/{len(professors)} - ENHANCED PROCESSING")
            print("="*80)
            
            result = self.process_professor_enhanced(professor)
            self.results["processed_professors"].append(result)
            
            # Save progress
            self.save_progress()
            self.save_results()
            
            # Enhanced progress reporting
            success_rate = (self.results["emails_sent"] / i) * 100 if i > 0 else 0
            quality_rate = (self.results["high_quality_matches"] / self.results["publications_found"]) * 100 if self.results["publications_found"] > 0 else 0
            
            print(f"\n📊 ENHANCED PROGRESS: {i}/{len(professors)}")
            print(f"✅ Success Rate: {success_rate:.1f}% (Target: 80%+)")
            print(f"⭐ High Quality: {quality_rate:.1f}%")
            print(f"📧 Emails sent: {self.results['emails_sent']}")
            print(f"❌ Failed: {self.results['emails_failed']}")
            print(f"📄 Publications: {self.results['publications_found']}")
            print(f"🔄 Retries: {self.results['retry_successes']}")
            
            # Delay
            if i < len(professors):
                print(f"⏳ Waiting {delay_seconds} seconds...")
                time.sleep(delay_seconds)
        
        # Final enhanced summary
        self.print_enhanced_summary()
    
    def print_enhanced_summary(self):
        """Print enhanced campaign summary with detailed metrics"""
        print(f"\n" + "="*80)
        print("🎉 ENHANCED CAMPAIGN COMPLETED")
        print("="*80)
        
        total_processed = len(self.results["processed_professors"])
        success_rate = (self.results["emails_sent"] / total_processed) * 100 if total_processed > 0 else 0
        quality_rate = (self.results["high_quality_matches"] / self.results["publications_found"]) * 100 if self.results["publications_found"] > 0 else 0
        
        print(f"📊 FINAL ENHANCED STATISTICS:")
        print(f"   📧 Total processed: {total_processed:,}")
        print(f"   ✅ Emails sent: {self.results['emails_sent']:,}")
        print(f"   🎯 Success rate: {success_rate:.1f}% (Target: 80%+)")
        print(f"   ⭐ High quality matches: {self.results['high_quality_matches']:,} ({quality_rate:.1f}%)")
        print(f"   📄 Publications found: {self.results['publications_found']:,}")
        print(f"   🔄 Successful retries: {self.results['retry_successes']:,}")
        
        if self.results["quality_metrics"]["total_citations"] > 0:
            avg_citations = self.results["quality_metrics"]["total_citations"] / self.results["publications_found"]
            print(f"   📈 Avg citations per publication: {avg_citations:.1f}")
        
        print(f"\n📁 ENHANCED FILES:")
        print(f"   📊 Results: {self.results_file}")
        print(f"   💾 Progress: {self.progress_file}")
        print(f"   📧 Emails: enhanced_emails/ directory")
        
        # Success rate assessment
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT! Success rate target achieved!")
        elif success_rate >= 70:
            print(f"\n👍 GOOD! Close to target success rate")
        elif success_rate >= 60:
            print(f"\n⚠️  MODERATE: Success rate needs improvement")
        else:
            print(f"\n❌ LOW: Success rate significantly below target")
        
        print("="*80)
    
    def save_results(self):
        """Save enhanced results"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced Bulk Email Campaign')
    parser.add_argument('--mode', choices=['production', 'test'], default='test', help='Campaign mode')
    parser.add_argument('--size', type=int, default=20, help='Number of professors to process')
    parser.add_argument('--delay', type=int, default=2, help='Delay between emails in seconds')
    parser.add_argument('--start', type=int, default=0, help='Starting index')
    parser.add_argument('--email', type=str, help='Test email address (for test mode)')
    
    args = parser.parse_args()
    
    print("🚀 ENHANCED BULK EMAIL CAMPAIGN SYSTEM")
    print("="*80)
    print("🎯 TARGETING 80%+ SUCCESS RATES")
    print("🔬 Multi-source publication discovery")
    print("⭐ Quality-based professor filtering") 
    print("🧠 Enhanced research area inference")
    print("📧 Improved email personalization")
    print("="*80)
    
    # Initialize campaign
    test_email = None
    if args.mode == 'test':
        test_email = args.email or "tripathy.anamay23@gmail.com"
    
    campaign = EnhancedBulkCampaign(test_email=test_email)
    
    # Confirmation for production mode
    if args.mode == 'production':
        print(f"\n⚠️  PRODUCTION MODE: Emails will be sent to REAL professors!")
        confirm = input("🔥 Are you ready to start the enhanced campaign? (y/N): ")
        if confirm.lower() not in ['y', 'yes']:
            print("❌ Campaign cancelled.")
            return
    
    # Run campaign
    campaign.run_enhanced_campaign(
        sample_size=args.size,
        delay_seconds=args.delay,
        start_from=args.start,
        test_mode=(args.mode == 'test')
    )

if __name__ == "__main__":
    main()
