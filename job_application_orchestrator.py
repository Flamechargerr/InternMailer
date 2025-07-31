
from enhanced_job_scraper import EnhancedJobScraper
from job_parser import process_job_postings
from cv_customizer import CVCustomizer, load_json, save_customized_cvs
from application_tracker import ApplicationTracker
from hr_finder import HRFinder
from send_email_with_cv import send_email_with_cv
import os

class JobApplicationOrchestrator:
    def __init__(self, base_cv_path: str, job_board_url: str):
        self.base_cv_path = base_cv_path
        self.job_board_url = job_board_url
        self.tracker = ApplicationTracker()

    def run_pipeline(self):
        self.hr_finder = HRFinder(api_key=os.getenv('HUNTER_API_KEY'))
        """
        Executes the full job application pipeline:
        1. Scrapes job postings
        2. Parses the scraped data
        3. Customizes the CV for each job
        4. Logs the applications
        """
        # Step 1: Scrape job postings
        print("--- Step 1: Scraping Jobs ---")
        scraper = EnhancedJobScraper()
        scraped_jobs = scraper.scrape_all_jobs(max_jobs_per_board=10)
        if not scraped_jobs:
            print("No jobs were scraped. Exiting pipeline.")
            return
        scraper.save_jobs_to_json(scraped_jobs, "job_postings.json")
        print(f"Successfully scraped {len(scraped_jobs)} jobs.")

        # Step 2: Parse job postings
        print("\n--- Step 2: Parsing Jobs ---")
        process_job_postings("data/job_postings.json", "data/parsed_jobs.json")

        # Step 3: Customize CVs
        print("\n--- Step 3: Customizing CVs ---")
        parsed_jobs = load_json("data/parsed_jobs.json")
        base_cv = load_json(self.base_cv_path)
        
        if not parsed_jobs or not base_cv:
            print("Parsed jobs or base CV not found. Exiting.")
            return

        customizer = CVCustomizer(base_cv_file=self.base_cv_path)
        customized_resumes = []

        for job in parsed_jobs:
            customized_cv = customizer.customize_for_job(job)
            customized_resumes.append({
                'job_title': job.get('title'),
                'company': job.get('company'),
                'customized_cv': customized_cv
            })
        
        save_customized_cvs(customized_resumes, "data/customized_cvs.json")
        print(f"Successfully generated {len(customized_resumes)} customized CVs.")

        # Step 4: Log Applications
        print("\n--- Step 4: Logging Applications ---")
        for job in parsed_jobs:
            self.tracker.log_application(job, status="ready_to_apply")
        
        self.tracker.display_summary()
        
        # Step 5: Find HR emails and send emails
        print("\n--- Step 5: Sending Emails ---")
        for job in parsed_jobs:
            company = job.get('company')
            if company:
                hr_emails = self.hr_finder.find_hr_emails(company)
                for email in hr_emails:
                    email_address = email.get('value')
                    if email_address:
                        print(f"Sending email to {email_address} for {company}...")
                        send_email_with_cv(job)
                        print(f"Email sent to {email_address}.")

if __name__ == "__main__":
    # Configuration
    # Replace with the actual URL of the job board you want to scrape
    JOB_BOARD_URL = "https://www.linkedin.com/jobs/search/?keywords=remote%20internship"
    
    # Create a JSON representation of your CV and save it to 'data/base_cv.json'
    # This is a one-time setup step.
    base_cv_data = {
        "name": "Anamay Tripathy",
        "email": "tripathy.anamay23@gmail.com",
        "skills": ["Python", "Data Analysis", "Machine Learning", "AWS"],
        "experience": [
            {"title": "Technical Head", "company": "YaanBarpe", "description": "Led AI-driven system architecture."},
            {"title": "Data Analyst Intern", "company": "Intellect Design Arena", "description": "Built ML pipelines."}
        ],
        "projects": [
            {"name": "VARtificial Intelligence", "description": "ML prediction system with 89% accuracy."},
            {"name": "CrimeConnect", "description": "Data-driven case management platform."}
        ]
    }
    
    import json
    import os
    if not os.path.exists('data'):
        os.makedirs('data')
    with open("data/base_cv.json", 'w') as f:
        json.dump([base_cv_data], f, indent=4) # Save as a list

    # Initialize and run the orchestrator
    orchestrator = JobApplicationOrchestrator(
        base_cv_path="data/base_cv.json",
        job_board_url=JOB_BOARD_URL
    )
    orchestrator.run_pipeline()

