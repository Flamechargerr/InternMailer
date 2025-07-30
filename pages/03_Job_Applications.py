
import streamlit as st
import os
import json
import pandas as pd
from job_application_orchestrator import JobApplicationOrchestrator
from application_tracker import ApplicationTracker
from hr_email_generator import HREmailGenerator
from ui_utils import apply_theme_styles, show_config_status

# --- App Configuration ---
st.set_page_config(
    page_title="Job Application Automator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme_styles()

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
        
        st.header("Actions")
        if st.button("Run Job Application Pipeline"):
            run_orchestrator(job_board_url)
        
        st.header("Application Status")
        tracker = ApplicationTracker()
        status_counts = tracker._load_log()
        if status_counts:
            df = pd.DataFrame(status_counts)
            if 'status' in df.columns:
                st.bar_chart(df['status'].value_counts())

    # --- Main Content Area ---
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Parsed Jobs", "Customized CVs", "Generated Emails"])
    
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
        display_generated_emails("data/generated_application_emails.json")

def run_orchestrator(job_board_url):
    base_cv_path = "data/base_cv.json"
    
    # Ensure base_cv.json exists
    if not os.path.exists(base_cv_path):
        st.error("base_cv.json not found! Please create it first.")
        return

    orchestrator = JobApplicationOrchestrator(
        base_cv_path=base_cv_path,
        job_board_url=job_board_url
    )
    
    with st.spinner("Running the job application pipeline..."):
        orchestrator.run_pipeline()
    
    st.success("Pipeline completed successfully!")

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
                ["pending", "applied", "interview", "rejected", "offer"],
                index=["pending", "applied", "interview", "rejected", "offer"].index(app['status']),
                key=f"status_{i}"
            )
            if st.button("Update", key=f"update_{i}"):
                tracker.update_status(i, new_status)
                st.experimental_rerun()

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


