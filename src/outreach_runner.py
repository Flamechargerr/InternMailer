import os
import sys
import pandas as pd
import time
from datetime import datetime
from resume_parser import ResumeParser
from email_generator import EmailGenerator
from gmail_sender import GmailSender
from professor_scraper import ProfessorScraper
# Import enhanced email generation system
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from enhanced_personalized_email import generate_deeply_personalized_email
# Fix import path for followup manager
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scheduler'))
from streamlit_api import get_followup_manager
from professor_tracker import ProfessorTracker
from email_validator import validate_email
from enhanced_campaign_system import EnhancedCampaignSystem, EmailCandidate, CampaignMode

class OutreachRunner:
    def __init__(self, resume_path: str, season: str, funding: str, selected_countries: list, mode: str, progress_callback, log_callback, batch_size: int = None):
        self.resume_path = resume_path
        self.season = season
        self.funding = funding
        self.selected_countries = selected_countries
        self.mode = mode
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.batch_size = batch_size

    def run(self):
        self.log_callback(":mag: **Initializing professor tracker...**")
        tracker = ProfessorTracker()

        already_emailed = [
            {'email': 'liskov@csail.mit.edu', 'name': 'Barbara H. Liskov', 'university': 'MIT'},
            {'email': 'asuman@mit.edu', 'name': 'Asuman E. Ozdaglar', 'university': 'MIT'},
            {'email': 'arvind@csail.mit.edu', 'name': 'Arvind', 'university': 'MIT'},
            {'email': 'asolar@csail.mit.edu', 'name': 'Armando Solar-Lezama', 'university': 'MIT'},
            {'email': 'torralba@csail.mit.edu', 'name': 'Antonio Torralba', 'university': 'MIT'},
            {'email': 'moitra@mit.edu', 'name': 'Ankur Moitra', 'university': 'MIT'},
            {'email': 'anant@csail.mit.edu', 'name': 'Anant Agarwal', 'university': 'MIT'},
            {'email': 'rakhlin@mit.edu', 'name': 'Alexander Rakhlin', 'university': 'MIT'},
            {'email': 'adamc@csail.mit.edu', 'name': 'Adam Chlipala', 'university': 'MIT'},
            {'email': 'abelay@mit.edu', 'name': 'Adam Belay', 'university': 'MIT'}
        ]

        # Add previously emailed professors to tracker
        for prof in already_emailed:
            tracker.add_emailed_professor(
                email=prof['email'],
                name=prof['name'],
                university=prof['university'],
                subject="Previously contacted",
                status="sent",
                notes="Pre-existing contact"
            )
        stats = tracker.get_stats()
        self.log_callback(f":mag: **Professor tracker initialized - {stats['total_emailed']} professors already contacted**")

        self.log_callback(":mag: **Parsing resume...**")
        try:
            # Add explicit environment loading and debugging
            from dotenv import load_dotenv
            load_dotenv()
            
            import os
            github_token = os.getenv('GITHUB_TOKEN')
            self.log_callback(f"🔑 GITHUB_TOKEN loaded: {'Yes' if github_token and 'ghp_' in github_token else 'No'}")
            
            parser = ResumeParser(self.resume_path)
            self.log_callback(f"📄 Parser initialized with providers: {[p.get_provider_name() for p in parser.providers]}")
            self.log_callback(f"🔍 Azure AI available: {parser.providers[0].is_available() if parser.providers else 'No providers'}")
            
            student_info = parser.parse()
            self.log_callback(f"✅ Resume parsed successfully with {len(student_info.get('skills', []))} skills")
        except Exception as e:
            self.log_callback(f"❌ Resume parsing failed: {str(e)}")
            import traceback
            self.log_callback(f"❌ Full traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Resume parsing failed: {str(e)}")
        
        student_info['name'] = "Anamay Tripathy"
        student_info['email'] = "tripathy.anamay23@gmail.com"
        student_info['resume_prefix'] = os.path.splitext(os.path.basename(self.resume_path))[0]
        student_info['season'] = self.season
        student_info['funding'] = self.funding
        self.progress_callback(10)

        self.log_callback(":mag: **Loading professors from CSV...**")
        professors = []

        try:
            # Read CSV with error handling for malformed lines
            df = pd.read_csv('professors_final.csv', on_bad_lines='skip', encoding='utf-8', 
                           names=['University', 'Name', 'Email', 'Homepage', 'Research Area'], 
                           header=None, skiprows=1)
            
            # Clean the data
            df = df.dropna(subset=['Email'])  # Remove rows with missing emails
            df = df[df['Email'].str.contains('@', na=False)]  # Only keep valid email formats
            df = df[df['University'] != 'University']  # Remove duplicate headers
            df = df[df['Email'] != 'Email']  # Remove duplicate headers
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            self.log_callback(f"Found {len(df)} professor records in CSV (after cleaning)")

            for _, row in df.iterrows():
                email = row.get('Email', '')

                if pd.isna(email) or not email or email.strip() == '':
                    continue

                # Use secure email validator
                is_valid_format = validate_email(email)

                if is_valid_format:
                    prof_data = {}
                    for k, v in row.items():
                        if pd.notna(v) and str(v).strip() != '':
                            prof_data[k.strip()] = str(v).strip()

                    if prof_data.get('Name') and prof_data.get('Email'):
                        professors.append(prof_data)
                else:
                    if len([p for p in professors]) < 5:
                        self.log_callback(f"Skipping invalid email: {email}")

        except FileNotFoundError:
            raise RuntimeError("Professor CSV file not found. Ensure 'data/proffesor.csv' exists.")
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file: {e}")

        self.log_callback(f"Number of professors with valid emails: {len(professors)}")
        if len(professors) > 0:
            self.log_callback(f"Sample professor record: {professors[0]}")

        if self.selected_countries:
            filtered = []
            for prof in professors:
                if 'country' in prof and prof['country'] in self.selected_countries:
                    filtered.append(prof)
            professors = filtered

        try:
            scraper = ProfessorScraper(data_dir='data')
            for i, prof in enumerate(professors):
                if prof.get('Homepage') and i < 10:
                    try:
                        prof['homepage_text'] = scraper.scrape_homepage(prof['Homepage'])
                    except Exception as e:
                        self.log_callback(f"Could not scrape homepage for {prof.get('Name', 'Unknown')}: {e}")
                if i % 10 == 0:
                    self.progress_callback(10 + int(20 * i / max(1, len(professors))))
        except Exception as e:
            self.log_callback(f"Scraper initialization failed: {e}")
            self.progress_callback(30)

        self.log_callback(f":mag: **Total professors after deduplication: {len(professors)}**")

        matches = professors

        # Apply batch size limit if specified
        if self.batch_size and self.batch_size > 0:
            matches = matches[:self.batch_size]
            self.log_callback(f":mag: **Limiting to batch size of {self.batch_size} professors**")
        professors_matched = len(matches)
        self.progress_callback(50)

        # Initialize enhanced campaign system
        self.log_callback(":rocket: **Initializing Enhanced Campaign System...**")
        enhanced_campaign = EnhancedCampaignSystem(
            data_dir='data',
            cooldown_days=30,
            pending_expires_hours=24,
            email_delay_seconds=30
        )
        
        # Convert professors to EmailCandidate objects
        self.log_callback(":email: **Preparing email candidates...**")
        candidates = []
        for prof in professors:
            candidate = EmailCandidate(
                email=prof['Email'],
                name=prof['Name'], 
                university=prof['University'],
                research_area=prof['Research Area'],
                homepage_text=prof.get('homepage_text', '')
            )
            candidates.append(candidate)
        
        self.log_callback(f"📋 Created {len(candidates)} email candidates")
        
        # Generate eligibility report
        self.log_callback(":mag: **Analyzing candidate eligibility...**")
        eligibility_report = enhanced_campaign.get_campaign_eligibility_report(candidates)
        analysis = eligibility_report['candidate_analysis']
        
        self.log_callback(f"📊 Smart Eligibility Analysis:")
        self.log_callback(f"   • Total candidates: {analysis['total_candidates']}")
        self.log_callback(f"   • Eligible: {analysis['eligible']['count']}")
        
        # Show prioritization breakdown
        if 'prioritization' in analysis:
            prioritization = analysis['prioritization']
            if prioritization['dry_run_upgrades'] > 0:
                self.log_callback(f"     🎆 Priority: {prioritization['dry_run_upgrades']} dry run upgrades")
            if prioritization['new_professors'] > 0:
                self.log_callback(f"     ✨ New: {prioritization['new_professors']} new professors")
            if prioritization['cooldown_expired'] > 0:
                self.log_callback(f"     ⏰ Expired: {prioritization['cooldown_expired']} cooldown expired")
        
        self.log_callback(f"   • Already contacted: {analysis['ineligible']['count']}")
        self.log_callback(f"   • In cooldown: {analysis['cooldown']['count']}")
        self.log_callback(f"   • Currently pending: {analysis['pending']['count']}")
        self.log_callback(f"   • Eligibility rate: {analysis['eligibility_rate']:.1f}%")
        
        if eligibility_report['recommendations']:
            self.log_callback(":bulb: **Recommendations:**")
            for rec in eligibility_report['recommendations']:
                self.log_callback(f"   - {rec}")
        
        self.progress_callback(60)
        
        # Determine campaign mode
        campaign_mode = CampaignMode.DRY_RUN if self.mode == "Dry Run" else CampaignMode.LIVE_SEND
        
        # Create campaign and schedule follow-ups 
        followup_manager = get_followup_manager()
        campaign_name = f"Outreach {datetime.now().strftime('%Y-%m-%d %H:%M')} ({self.mode})"
        followup_campaign_id = followup_manager.create_campaign(campaign_name, f"Academic outreach for {self.season} internships")
        
        # Prepare enhanced campaign
        self.log_callback(f":gear: **Preparing {campaign_mode.value} campaign...**")
        campaign_id, prep_results = enhanced_campaign.prepare_campaign(
            candidates=candidates,
            campaign_name=campaign_name,
            mode=campaign_mode,
            respect_cooldown=True
        )
        
        self.log_callback(f"✅ Campaign prepared: {prep_results['eligible_for_sending']} emails ready")
        
        # Define email generator function
        def email_generator(professor_data):
            """Generate personalized email using existing system."""
            try:
                # Convert back to expected format
                prof_data = {
                    'name': professor_data['name'],
                    'university': professor_data['university'],
                    'research_area': professor_data['research_area'],
                    'notable_papers': [
                        f"Research in {professor_data['research_area']}",
                        f"Advanced work in {professor_data['research_area']} at {professor_data['university']}",
                        f"Pioneering studies in {professor_data['research_area']}"
                    ],
                    'current_projects': [
                        f"{professor_data['research_area']} research",
                        f"Advanced {professor_data['research_area']} applications",
                        f"Collaborative {professor_data['research_area']} initiatives"
                    ],
                    'homepage_text': professor_data.get('homepage_text', '')
                }
                
                # Use existing enhanced email generation
                body = generate_deeply_personalized_email(prof_data)
                subject = f"Research Internship Inquiry – Anamay Tripathy re: {professor_data['research_area']}"
                
                return {
                    'subject': subject,
                    'body': body
                }
            except Exception as e:
                self.log_callback(f"❌ Error generating email: {e}")
                return None
        
        # Define email sender function for live mode
        def email_sender(email, subject, body):
            """Send email using existing Gmail sender."""
            try:
                sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
                success = sender.send_email(email, subject, body, self.resume_path)
                if success:
                    # Log to followup system
                    followup_manager.log_email_sent(followup_campaign_id, email, subject)
                return success
            except Exception as e:
                self.log_callback(f"❌ Error sending email to {email}: {e}")
                return False
        
        self.progress_callback(70)
        
        # Execute campaign
        self.log_callback(f":rocket: **Executing {campaign_mode.value} campaign...**")
        result = enhanced_campaign.execute_campaign(
            campaign_id=campaign_id,
            candidates=candidates,
            email_generator_func=email_generator,
            email_sender_func=email_sender if campaign_mode == CampaignMode.LIVE_SEND else None,
            mode=campaign_mode,
            max_emails=self.batch_size if self.batch_size else None
        )
        
        # Log results
        self.log_callback(f"✅ Campaign completed!")
        self.log_callback(f"   • Processed: {result.emails_prepared}")
        self.log_callback(f"   • {'Sent' if campaign_mode == CampaignMode.LIVE_SEND else 'Simulated'}: {result.emails_sent}")
        self.log_callback(f"   • Failed: {result.failed_count}")
        self.log_callback(f"   • Success rate: {result.success_rate:.1f}%")
        self.log_callback(f"   • Duration: {result.duration_seconds:.2f}s")
        
        if result.errors:
            self.log_callback(f"⚠️ Errors encountered:")
            for error in result.errors[:3]:  # Show first 3 errors
                self.log_callback(f"   - {error}")
        
        self.progress_callback(90)
        
        # Return results in expected format
        return {
            'success': True,
            'professors_matched': professors_matched,
            'emails_sent': result.emails_sent,
            'followups_scheduled': result.emails_sent,
            'email_previews': result.email_previews,
            'campaign_id': followup_campaign_id,
            'enhanced_campaign_id': campaign_id,
            'eligibility_analysis': analysis,
            'success_rate': result.success_rate,
            'duration_seconds': result.duration_seconds
        }
