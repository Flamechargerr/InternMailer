
import streamlit as st
import os
import json
import pandas as pd
import sys
sys.path.append('.')
from hr_email_generator import HREmailGenerator
# from job_harvester import JobHarvester
from job_parser import JobParser
from cv_customizer import CVCustomizer
from application_tracker import ApplicationTracker
from hr_finder import HRFinder

# --- App Configuration ---
st.set_page_config(
    page_title="Job Application Automator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---
def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Main Application ---
def main():
    st.title("🤖 Job Application Automator")
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("Configuration")
        job_board_url = st.text_input(
            "Job Board URL", 
            "https://www.linkedin.com/jobs/search/?keywords=remote%20internship"
        )
        hunter_api_key = st.text_input("Hunter.io API Key", type="password")

        st.header("Actions")
        if st.button("Run Job Application Pipeline"):
            run_orchestrator(job_board_url)
        if st.button("Find HR Emails"):
            if hunter_api_key:
                find_hr_emails(hunter_api_key)
            else:
                st.warning("Please enter your Hunter.io API key.")

        st.header("Scraping Status")
        finder = HRFinder(api_key="dummy") # No real key needed for status check
        scraped_summary = finder.get_scraped_summary()
        st.metric("Companies Scraped", f"{scraped_summary['total_companies_scraped']}/{len(load_data('companies.json'))}")
        st.metric("Total Emails Found", scraped_summary['total_emails_found'])
        if st.button("Clear Cache"):
            if os.path.exists(finder.cache_file):
                os.remove(finder.cache_file)
                st.success("Scraping cache cleared!")

    # --- Main Content Area ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Parsed Jobs", "Customized CVs", "Generated Emails", "HR Emails"])
    
    with tab1:
        st.header("Application Dashboard")
        display_dashboard()
        
    with tab2:
        st.header("Parsed Job Postings")
        display_data("data/parsed_jobs.json")
        
    with tab3:
        st.header("Customized CVs")
        display_data("data/customized_cvs.json")
        
    with tab4:
        st.header("Generated Emails")
        # Try multiple possible email file locations
        email_files = [
            "data/generated_application_emails.json",
            "data/outreach_results.json",
            "data/pending_emails.json"
        ]
        emails_found = False
        for email_file in email_files:
            if os.path.exists(email_file):
                if "generated_application_emails" in email_file:
                    display_generated_emails(email_file)
                else:
                    st.subheader(f"Data from {os.path.basename(email_file)}")
                    display_data(email_file)
                emails_found = True
        
        if not emails_found:
            st.info("💡 No generated emails found yet. Run the Job Application Pipeline to generate personalized application emails.")
            st.markdown("""
            **To generate application emails:**
            1. Configure your Job Board URL in the sidebar
            2. Click "Run Job Application Pipeline"
            3. The system will:
               - Scrape job postings
               - Parse job requirements
               - Customize your CV for each role
               - Generate personalized application emails
            """)
        
    with tab5:
        st.header("Found HR Emails")
        # Try multiple possible HR email file locations
        hr_files = ["data/hr_emails.json", "data/enhanced_hr_contacts.json"]
        hr_data_found = False
        
        for hr_file in hr_files:
            if os.path.exists(hr_file):
                hr_data = load_data(hr_file)
                if hr_data:
                    st.success(f"✅ Found {len(hr_data)} HR contacts from {os.path.basename(hr_file)}")
                    
                    # Group by company for better display
                    companies = {}
                    for contact in hr_data:
                        company = contact.get('company', 'Unknown')
                        if company not in companies:
                            companies[company] = []
                        companies[company].append(contact)
                    
                    for company, contacts in companies.items():
                        with st.expander(f"🏢 {company} ({len(contacts)} contacts)"):
                            for contact in contacts:
                                col1, col2, col3 = st.columns([2, 2, 1])
                                with col1:
                                    st.write(f"📧 **{contact.get('email', 'N/A')}**")
                                with col2:
                                    contact_type = contact.get('type', 'general')
                                    if contact_type == 'generic_hr':
                                        st.write("🎯 HR Contact")
                                    else:
                                        st.write(f"📋 {contact_type.title()}")
                                with col3:
                                    source = contact.get('source', 'unknown')
                                    if source == 'generated':
                                        st.write("🤖 Generated")
                                    else:
                                        st.write("🔍 Scraped")
                    hr_data_found = True
                    break
        
        if not hr_data_found:
            st.info("💡 No HR email data found yet. Use the Hunter.io integration to discover HR contacts.")
            st.markdown("""
            **To find HR emails:**
            1. Add your Hunter.io API key in the sidebar
            2. Click "Find HR Emails"
            3. The system will discover HR contacts for companies in your job applications
            
            **Note:** You can get a free Hunter.io API key at [hunter.io](https://hunter.io)
            """)

def find_hr_emails(api_key):
    with st.spinner("Finding HR emails..."):
        try:
            finder = HRFinder(api_key=api_key)
            all_companies = load_data("companies.json")
            
            unscraped_companies = finder.get_unscraped_companies(all_companies)
            
            if not unscraped_companies:
                st.success("All companies have already been scraped.")
                st.json(finder.get_scraped_summary())
                return

            st.info(f"Found {len(unscraped_companies)} unscraped companies out of {len(all_companies)} total.")

            # --- Append to existing emails instead of overwriting ---
            if os.path.exists("data/hr_emails.json"):
                all_emails = load_data("data/hr_emails.json")
            else:
                all_emails = []

            progress_bar = st.progress(0)
            for i, company in enumerate(unscraped_companies):
                st.write(f"Searching for HR emails at {company}...")
                emails = finder.find_hr_emails(company)
                if emails:
                    for email in emails:
                        email['company'] = company  # Add company name to email data
                    all_emails.extend(emails)
                progress_bar.progress((i + 1) / len(unscraped_companies))
            
            os.makedirs("data", exist_ok=True)
            with open("data/hr_emails.json", "w") as f:
                json.dump(all_emails, f, indent=4)
            
            st.success(f"Scraping complete! Found {len(all_emails)} total HR emails.")
            st.json(finder.get_scraped_summary())

        except Exception as e:
            st.error(f"Failed to find HR emails: {e}")

def run_orchestrator(job_board_url):
    """Simplified job application pipeline"""
    try:
        with st.spinner("Scraping job postings..."):
            # Step 1: Harvest jobs (temporarily disabled)
            st.warning("Job harvesting temporarily disabled. Using mock data.")
            jobs = [
                {"title": "Data Science Intern", "company": "Tech Corp", "location": "Remote", "description": "Looking for data science intern with Python skills"},
                {"title": "Software Engineer Intern", "company": "StartupXYZ", "location": "New York", "description": "Backend development intern position"}
            ]
            st.success(f"Found {len(jobs)} job postings!")
            
        with st.spinner("Parsing job requirements..."):
            # Step 2: Parse jobs
            parser = JobParser()
            parsed_jobs = [parser.parse_job(job) for job in jobs]
            
            # Save parsed jobs
            os.makedirs("data", exist_ok=True)
            with open("data/parsed_jobs.json", "w") as f:
                json.dump(parsed_jobs, f, indent=4)
            st.success("Job parsing completed!")
            
        with st.spinner("Customizing CV for each role..."):
            # Step 3: Customize CV
            customizer = CVCustomizer("data/base_cv.json")
            customized_cvs = []
            
            for job in parsed_jobs:
                cv = customizer.customize_cv(job)
                customized_cvs.append({
                    "job_title": job.get("title", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "customized_cv": cv
                })
            
            # Save customized CVs
            with open("data/customized_cvs.json", "w") as f:
                json.dump(customized_cvs, f, indent=4)
            st.success("CV customization completed!")
            
        with st.spinner("Generating application emails..."):
            # Step 4: Generate emails
            email_gen = HREmailGenerator()
            emails = []
            
            for item in customized_cvs:
                job_posting = {
                    'title': item['job_title'],
                    'company': item['company'],
                    'skills': item['customized_cv'].get('skills', [])
                }
                
                email_content = email_gen.generate_email(job_posting, item['customized_cv'])
                emails.append({
                    'job_title': item['job_title'],
                    'company': item['company'],
                    'email_content': email_content
                })
            
            # Save emails
            with open("data/generated_application_emails.json", "w") as f:
                json.dump(emails, f, indent=4)
            st.success("Email generation completed!")
            
        st.success("🎉 Pipeline completed successfully!")
        
    except Exception as e:
        st.error(f"Pipeline failed: {str(e)}")

def display_dashboard():
    tracker = ApplicationTracker()
    applications = tracker._load_log()
    
    if not applications:
        st.info("No applications logged yet.")
        return
    
    st.subheader(f"Total Applications: {len(applications)}")
    
    for i, app in enumerate(applications):
        with st.expander(f"{app.get('job_title')} at {app.get('company')}"):
            st.json(app)
            new_status = st.selectbox(
                "Update Status", 
                ["ready_to_apply", "pending", "applied", "interview", "rejected", "offer"],
                index=["ready_to_apply", "pending", "applied", "interview", "rejected", "offer"].index(app['status']),
                key=f"status_{i}"
            )
            if st.button("Update", key=f"update_{i}"):
                tracker.update_status(i, new_status)
                st.rerun()

def display_data(file_path):
    data = load_data(file_path)
    if not data:
        st.warning(f"No data found in {file_path}")
        return
    st.json(data)

def display_generated_emails(file_path):
    emails = load_data(file_path)
    if not emails:
        st.warning("No emails generated yet.")
        return
    
    for i, email_data in enumerate(emails):
        with st.expander(f"Email for {email_data['job_title']} at {email_data['company']}"):
            st.code(email_data['email_content'], language='text')

if __name__ == "__main__":
    main()


