import os
import logging
from dotenv import load_dotenv
from resume_parser import ResumeParser
from professor_scraper import ProfessorScraper
from semantic_matcher import SemanticMatcher
from email_generator import EmailGenerator
from gmail_sender import GmailSender
from followup_scheduler import FollowupScheduler

logging.basicConfig(level=logging.INFO)

load_dotenv()

# TODO: Replace with Streamlit UI integration

def main():
    try:
        # 1. Parse resume
        resume_path = os.getenv('RESUME_PATH', '../resumes/CV_Anamay_Modern.pdf')
        parser = ResumeParser(resume_path)
        student_info = parser.parse()
        logging.info(f"Extracted student info: {student_info}")

        # 2. Scrape professors
        scraper = ProfessorScraper('../data')
        professors = scraper.parse_csvs()
        professors = scraper.deduplicate_and_filter()
        for prof in professors:
            if prof.get('homepage'):
                prof['homepage_text'] = scraper.scrape_homepage(prof['homepage'])

        # 3. Semantic matching
        matcher = SemanticMatcher()
        matches = matcher.match(student_info['summary'], professors)
        logging.info(f"Matched {len(matches)} professors.")

        # 4. Generate emails
        email_gen = EmailGenerator(student_info, os.getenv('OPENAI_API_KEY'))
        emails = []
        for prof in matches:
            subject = email_gen.generate_subject(prof)
            body = email_gen.generate_body(prof)
            emails.append({'to': prof['email'], 'subject': subject, 'body': body})

        # 5. Send emails
        sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
        sender.send_bulk(emails, resume_path)

        # 6. Schedule follow-ups
        scheduler = FollowupScheduler()
        for email in emails:
            scheduler.log_first_send(email['to'])
        scheduler.schedule_followups()

    except Exception as e:
        logging.error(f"Error in main workflow: {e}")

if __name__ == '__main__':
    main()

# TODO: Add CLI/Streamlit integration
# TODO: Add unit/integration tests for main workflow 