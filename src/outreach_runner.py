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

        # Apply batch size limit if specified
        if self.batch_size and self.batch_size > 0:
            professors = professors[:self.batch_size]
            self.log_callback(f":mag: **Limiting to batch size of {self.batch_size} professors**")

        matches = professors
        professors_matched = len(matches)
        self.progress_callback(50)

        self.log_callback(":email: **Generating personalized emails...**")
        # Reuse already parsed student_info from above
        self.log_callback(f"📄 Using parsed resume data: {len(student_info.get('skills', []))} skills, {len(student_info.get('projects', []))} projects")
        
        # Integrate enhanced personalized email generation
        emails = []
        for prof in professors:
            professor_data = {
                'name': prof['Name'],
                'university': prof['University'],
                'research_area': prof['Research Area'],
                'notable_papers': [
                    f"Research in {prof['Research Area']}",
                    f"Advanced work in {prof['Research Area']} at {prof['University']}",
                    f"Pioneering studies in {prof['Research Area']}"
                ],
                'current_projects': [
                    f"{prof['Research Area']} research",
                    f"Advanced {prof['Research Area']} applications",
                    f"Collaborative {prof['Research Area']} initiatives"
                ],
                'homepage_text': prof.get('homepage_text', '')
            }
            
            try:
                # Use the enhanced email generation system
                body = generate_deeply_personalized_email(professor_data)
                subject = f"Research Internship Inquiry – Anamay Tripathy re: {prof['Research Area']}"
                self.log_callback("✅ Enhanced email generated successfully")
            except Exception as e:
                self.log_callback(f"Error generating email for {prof['Name']}: {e}")
                continue
            
            emails.append({'to': prof['Email'], 'subject': subject, 'body': body})

        self.progress_callback(60)

        # Create campaign and schedule follow-ups for both modes
        followup_manager = get_followup_manager()
        campaign_name = f"Outreach {datetime.now().strftime('%Y-%m-%d %H:%M')} ({'Dry Run' if self.mode == 'Dry Run' else 'Live Send'})"
        campaign_id = followup_manager.create_campaign(campaign_name, f"Academic outreach for {self.season} internships")

        if self.mode == "Dry Run":
            self.log_callback(":mag: **DRY RUN MODE - No emails will be sent**")
            message = "🔍 **DRY RUN MODE ACTIVE** - Emails are being generated and displayed but not sent."

            sent_count = 0
            skipped_count = 0
            for i, email in enumerate(emails):
                if tracker.is_professor_emailed(email['to']):
                    skipped_count += 1
                    self.log_callback(f"[DRY RUN] Skipping {email['to']} - Already contacted ⏭️")
                else:
                    time.sleep(0.1)
                    sent_count += 1
                    self.log_callback(f"[DRY RUN] Would send to {email['to']} - ✅ (Email prepared)")
                    # Log email as if it was sent to create follow-up tracking
                    followup_manager.log_email_sent(campaign_id, email['to'], email['subject'])

                self.progress_callback(60 + int(30 * (i+1) / max(1, len(emails))))

            self.progress_callback(90)
            return {
                'success': True,
                'professors_matched': professors_matched,
                'emails_sent': sent_count,
                'followups_scheduled': sent_count,  # Use sent_count since we only create follow-ups for non-skipped emails
                'email_previews': emails[:3],  # Only return first 3 for preview
                'campaign_id': campaign_id
            }

        else:  # Live Send mode
            sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
            sent_count = 0
            skipped_count = 0
            for i, email in enumerate(emails):
                if tracker.is_professor_emailed(email['to']):
                    skipped_count += 1
                    self.log_callback(f"[LIVE] Skipping {email['to']} - Already contacted ⏭️")
                else:
                    sent = sender.send_email(email['to'], email['subject'], email['body'], self.resume_path)
                    if sent:
                        sent_count += 1
                        # Log email to follow-up system only if actually sent
                        followup_manager.log_email_sent(campaign_id, email['to'], email['subject'])
                        # Add to tracker to prevent future duplicates
                        tracker.add_emailed_professor(
                            email=email['to'],
                            name=next((prof.get('Name', 'Unknown') for prof in professors if prof.get('Email') == email['to']), 'Unknown'),
                            university=next((prof.get('University', 'Unknown') for prof in professors if prof.get('Email') == email['to']), 'Unknown'),
                            subject=email['subject'],
                            status="sent",
                            notes=f"Live send - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                    self.log_callback(f"Sent to {email['to']} - {'✅' if sent else '❌'}")
                self.progress_callback(60 + int(30 * (i+1) / max(1, len(emails))))

            self.progress_callback(90)

            return {
                'success': True,
                'professors_matched': professors_matched,
                'emails_sent': sent_count,
                'followups_scheduled': sent_count,  # Only count actually sent emails
                'campaign_id': campaign_id
            }
