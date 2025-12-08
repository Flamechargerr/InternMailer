"""
Daily Automation Scheduler for InternMailer
Handles automated job discovery, matching, and application processing
"""

import schedule
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List
import threading
import os
from pathlib import Path

# Import InternMailer modules
from job_scraper import JobScraper
from ai_matcher import AIJobMatcher
from resume_tailor import ResumeTailor
from cover_letter_generator import CoverLetterGenerator
from contact_finder import ContactFinder
from prestige_scorer import PrestigeScorer
from application_tracker import ApplicationTracker, ApplicationStatus
from email_notifier import EmailNotifier
from database_manager import DatabaseManager

class InternMailerScheduler:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        
        # Initialize components
        self.job_scraper = JobScraper()
        self.ai_matcher = AIJobMatcher()
        self.resume_tailor = ResumeTailor()
        self.cover_letter_generator = CoverLetterGenerator()
        self.contact_finder = ContactFinder()
        self.prestige_scorer = PrestigeScorer()
        self.application_tracker = ApplicationTracker()
        self.email_notifier = EmailNotifier()
        self.db_manager = DatabaseManager()
        
        # Load configuration
        self.config = self._load_config()
        
        # Scheduler state
        self.is_running = False
        self.scheduler_thread = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scheduler.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'user_profile': {
                'degree': 'BTech',
                'branch': 'Data Science',
                'semester': 5,
                'level': 'Undergraduate',
                'target_term': 'Summer 2026'
            },
            'schedule': {
                'daily_run_time': '09:00',
                'max_applications_per_day': 10,
                'min_match_score': 0.65,
                'min_prestige_tier': 'Tier 3'
            },
            'email': {
                'recipient': 'tripathy.anamay23@gmail.com',
                'daily_report': True,
                'follow_up_reminders': True
            }
        }
    
    def daily_job_discovery(self) -> Dict:
        """Main daily job discovery and processing pipeline"""
        self.logger.info("Starting daily job discovery pipeline")
        
        try:
            # Step 1: Scrape new job opportunities
            self.logger.info("Step 1: Scraping job opportunities")
            raw_jobs = self.job_scraper.scrape_all_sources()
            self.logger.info(f"Found {len(raw_jobs)} raw job opportunities")
            
            # Step 2: Filter and validate jobs
            self.logger.info("Step 2: Filtering and validating jobs")
            filtered_jobs = self._filter_jobs(raw_jobs)
            self.logger.info(f"Filtered to {len(filtered_jobs)} valid opportunities")
            
            # Step 3: Add prestige scoring
            self.logger.info("Step 3: Adding prestige scores")
            scored_jobs = self.prestige_scorer.rank_opportunities(filtered_jobs)
            
            # Step 4: AI matching and scoring
            self.logger.info("Step 4: AI matching and scoring")
            matched_jobs = self.ai_matcher.score_opportunities(scored_jobs)
            
            # Step 5: Filter by match score and prestige
            self.logger.info("Step 5: Filtering by match score and prestige")
            qualified_jobs = self._filter_qualified_jobs(matched_jobs)
            self.logger.info(f"Found {len(qualified_jobs)} qualified opportunities")
            
            # Step 6: Find contact information
            self.logger.info("Step 6: Finding contact information")
            jobs_with_contacts = self._add_contact_info(qualified_jobs)
            
            # Step 7: Generate application materials
            self.logger.info("Step 7: Generating application materials")
            application_bundles = self._generate_application_materials(jobs_with_contacts)
            
            # Step 8: Save to database
            self.logger.info("Step 8: Saving to database")
            saved_applications = self._save_applications(application_bundles)
            
            # Step 9: Generate daily report
            self.logger.info("Step 9: Generating daily report")
            daily_report = self._generate_daily_report(saved_applications)
            
            # Step 10: Send email notification
            if self.config['email']['daily_report']:
                self.logger.info("Step 10: Sending email notification")
                self.email_notifier.send_daily_report(daily_report)
            
            self.logger.info("Daily job discovery pipeline completed successfully")
            return daily_report
            
        except Exception as e:
            self.logger.error(f"Error in daily job discovery pipeline: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _filter_jobs(self, raw_jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on criteria"""
        filtered = []
        
        for job in raw_jobs:
            # Check if it's an internship
            if not self._is_internship(job):
                continue
                
            # Check if it's for undergraduates
            if not self._is_undergraduate_eligible(job):
                continue
                
            # Check if it's in target domains
            if not self._is_target_domain(job):
                continue
                
            # Check if already applied
            if self._already_applied(job):
                continue
                
            filtered.append(job)
            
        return filtered
    
    def _is_internship(self, job: Dict) -> bool:
        """Check if job is an internship"""
        title = job.get('job_title', '').lower()
        job_type = job.get('job_type', '').lower()
        
        internship_keywords = ['intern', 'internship', 'summer program', 'co-op', 'trainee']
        return any(keyword in title or keyword in job_type for keyword in internship_keywords)
    
    def _is_undergraduate_eligible(self, job: Dict) -> bool:
        """Check if job is eligible for undergraduates"""
        eligibility = job.get('eligibility', '').lower()
        description = job.get('description', '').lower()
        
        # Exclude PhD/Masters only positions
        exclusions = ['phd only', 'masters only', 'graduate only', 'postgraduate']
        if any(exclusion in eligibility or exclusion in description for exclusion in exclusions):
            return False
            
        # Look for undergraduate indicators
        ug_indicators = ['undergraduate', 'bachelor', 'btech', 'be ', 'student']
        return any(indicator in eligibility or indicator in description for indicator in ug_indicators)
    
    def _is_target_domain(self, job: Dict) -> bool:
        """Check if job is in target domains"""
        title = job.get('job_title', '').lower()
        description = job.get('description', '').lower()
        
        target_keywords = [
            'machine learning', 'ml', 'artificial intelligence', 'ai',
            'data science', 'data scientist', 'data analyst',
            'software engineer', 'software developer', 'swe',
            'research', 'deep learning', 'nlp', 'computer vision'
        ]
        
        return any(keyword in title or keyword in description for keyword in target_keywords)
    
    def _already_applied(self, job: Dict) -> bool:
        """Check if already applied to this job"""
        company = job.get('company', '')
        title = job.get('job_title', '')
        
        return self.db_manager.application_exists(company, title)
    
    def _filter_qualified_jobs(self, matched_jobs: List[Dict]) -> List[Dict]:
        """Filter jobs by match score and prestige"""
        min_match_score = self.config['schedule']['min_match_score']
        min_tier = self.config['schedule']['min_prestige_tier']
        
        qualified = []
        for job in matched_jobs:
            match_score = job.get('match_score', 0.0)
            prestige_tier = job.get('prestige_tier', 'Unknown')
            
            if match_score >= min_match_score:
                if min_tier == 'Tier 3' or prestige_tier in ['Tier 1', 'Tier 2']:
                    qualified.append(job)
                elif min_tier == 'Tier 2' and prestige_tier in ['Tier 1', 'Tier 2']:
                    qualified.append(job)
                elif min_tier == 'Tier 1' and prestige_tier == 'Tier 1':
                    qualified.append(job)
        
        # Sort by prestige score then match score
        qualified.sort(key=lambda x: (x.get('prestige_score', 0), x.get('match_score', 0)), reverse=True)
        
        # Limit to max applications per day
        max_apps = self.config['schedule']['max_applications_per_day']
        return qualified[:max_apps]
    
    def _add_contact_info(self, jobs: List[Dict]) -> List[Dict]:
        """Add contact information to jobs"""
        jobs_with_contacts = []
        
        for job in jobs:
            try:
                contact_info = self.contact_finder.find_contacts(
                    job.get('company', ''),
                    job.get('job_title', ''),
                    job.get('description', '')
                )
                job['contact'] = contact_info
                jobs_with_contacts.append(job)
            except Exception as e:
                self.logger.warning(f"Could not find contact for {job.get('company')}: {e}")
                job['contact'] = {}
                jobs_with_contacts.append(job)
        
        return jobs_with_contacts
    
    def _generate_application_materials(self, jobs: List[Dict]) -> List[Dict]:
        """Generate tailored resumes and cover letters"""
        application_bundles = []
        
        for job in jobs:
            try:
                # Generate tailored resume
                tailored_resume = self.resume_tailor.tailor_resume(job)
                
                # Generate cover letter
                cover_letter = self.cover_letter_generator.generate_cover_letter(job)
                
                # Create application bundle
                bundle = {
                    'job_info': job,
                    'tailored_resume': tailored_resume,
                    'cover_letter': cover_letter,
                    'application_bundle': {
                        'job_title': job.get('job_title'),
                        'company': job.get('company'),
                        'contact_email': job.get('contact', {}).get('email', ''),
                        'apply_link': job.get('apply_link'),
                        'tailored_resume_text': tailored_resume.get('raw_text', ''),
                        'cover_letter_text': cover_letter.get('raw_text', ''),
                        'match_score': job.get('match_score'),
                        'prestige_tier': job.get('prestige_tier'),
                        'status': 'not_applied'
                    }
                }
                
                application_bundles.append(bundle)
                
            except Exception as e:
                self.logger.error(f"Error generating materials for {job.get('company')}: {e}")
        
        return application_bundles
    
    def _save_applications(self, application_bundles: List[Dict]) -> List[Dict]:
        """Save applications to database"""
        saved_applications = []
        
        for bundle in application_bundles:
            try:
                # Save application to database
                app_id = self.db_manager.save_application(bundle['job_info'])
                
                # Save application materials
                self.db_manager.save_application_materials(
                    app_id,
                    bundle['tailored_resume'],
                    bundle['cover_letter']
                )
                
                # Update application tracker
                self.application_tracker.update_application_status(
                    app_id,
                    ApplicationStatus.NOT_APPLIED,
                    "Application materials generated",
                    "automated"
                )
                
                bundle['application_id'] = app_id
                saved_applications.append(bundle)
                
            except Exception as e:
                self.logger.error(f"Error saving application: {e}")
        
        return saved_applications
    
    def _generate_daily_report(self, applications: List[Dict]) -> Dict:
        """Generate daily report in required JSON format"""
        today = datetime.now().date().isoformat()
        
        # Count by tiers
        tier_counts = {'Tier 1': 0, 'Tier 2': 0, 'Tier 3': 0}
        for app in applications:
            tier = app['job_info'].get('prestige_tier', 'Unknown')
            if tier in tier_counts:
                tier_counts[tier] += 1
        
        # Prepare opportunities list
        opportunities_ranked = []
        for app in applications:
            opportunities_ranked.append({
                'job_title': app['job_info'].get('job_title'),
                'company': app['job_info'].get('company'),
                'location': app['job_info'].get('location'),
                'apply_link': app['job_info'].get('apply_link'),
                'contact_email': app['job_info'].get('contact', {}).get('email'),
                'match_score': app['job_info'].get('match_score'),
                'prestige_tier': app['job_info'].get('prestige_tier'),
                'prestige_score': app['job_info'].get('prestige_score')
            })
        
        # Application logs
        application_logs = []
        for app in applications:
            application_logs.append({
                'application_id': app.get('application_id'),
                'timestamp': datetime.now().isoformat(),
                'action': 'materials_generated',
                'status': 'not_applied'
            })
        
        # Materials
        materials = []
        for app in applications:
            materials.append({
                'application_id': app.get('application_id'),
                'resume_content': app['tailored_resume'].get('raw_text'),
                'cover_letter_content': app['cover_letter'].get('raw_text')
            })
        
        return {
            'date': today,
            'summary': {
                'total_found': len(applications),
                'shortlisted': len(applications),
                'auto_applied': 0,  # No auto-application, only material generation
                'manual_required': len(applications),
                'tiers': tier_counts
            },
            'opportunities_ranked': opportunities_ranked,
            'application_logs': application_logs,
            'materials': materials
        }
    
    def process_follow_ups(self):
        """Process pending follow-up reminders"""
        try:
            pending_reminders = self.application_tracker.get_pending_follow_ups()
            
            if pending_reminders and self.config['email']['follow_up_reminders']:
                self.email_notifier.send_follow_up_reminders(pending_reminders)
                
                # Mark reminders as sent
                for reminder in pending_reminders:
                    self.application_tracker.mark_follow_up_completed(reminder['reminder_id'])
                    
            self.logger.info(f"Processed {len(pending_reminders)} follow-up reminders")
            
        except Exception as e:
            self.logger.error(f"Error processing follow-ups: {e}")
    
    def update_daily_metrics(self):
        """Update daily application metrics"""
        try:
            self.application_tracker.update_metrics_daily()
            self.logger.info("Daily metrics updated")
        except Exception as e:
            self.logger.error(f"Error updating daily metrics: {e}")
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        # Schedule daily job discovery
        daily_time = self.config['schedule']['daily_run_time']
        schedule.every().day.at(daily_time).do(self.daily_job_discovery)
        
        # Schedule follow-up processing (every 2 hours during business hours)
        for hour in [9, 11, 13, 15, 17]:
            schedule.every().day.at(f"{hour:02d}:00").do(self.process_follow_ups)
        
        # Schedule daily metrics update (end of day)
        schedule.every().day.at("23:30").do(self.update_daily_metrics)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"Scheduler started - Daily run at {daily_time}")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def stop_scheduler(self):
        """Stop the automated scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        self.logger.info("Scheduler stopped")
    
    def run_once(self) -> Dict:
        """Run the pipeline once manually"""
        self.logger.info("Running InternMailer pipeline manually")
        return self.daily_job_discovery()

if __name__ == "__main__":
    # Initialize and start scheduler
    scheduler = InternMailerScheduler()
    
    try:
        # Run once for testing
        result = scheduler.run_once()
        print(json.dumps(result, indent=2))
        
        # Start automated scheduler
        # scheduler.start_scheduler()
        # 
        # # Keep running
        # while True:
        #     time.sleep(60)
            
    except KeyboardInterrupt:
        scheduler.stop_scheduler()
        print("\nScheduler stopped by user")