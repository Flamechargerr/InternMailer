import streamlit as st
import os
import pandas as pd
import sys
from datetime import datetime
import json
from jinja2 import Template

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from outreach_runner import OutreachRunner
from shared.ui_components import UIComponents
from shared.session_state import session_state
from email_generator import EmailGenerator
from send_email_with_cv import send_email_with_cv

# --- UI Components ---
ui = UIComponents()
ui.apply_global_styles()

def load_html_template(template_path):
    """Load HTML template from file"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_personalized_academic_email(professor_data):
    """Create personalized academic professor template email"""
    template_content = load_html_template('templates/enhanced_academic_research_template.html')
    context = {
        'professor': {
            'last_name': professor_data.get('last_name', 'Doe'), 
            'research_area': professor_data.get('research_area', 'Computer Science')
        }
    }
    html_content = Template(template_content).render(**context)
    return f"Research Internship Inquiry - {professor_data.get('research_area', 'Computer Science')}", html_content

# --- Main Application ---
def main():
    """Main function to run the Streamlit page."""
    
    # Track navigation
    session_state.track_navigation("Professor Outreach Page")

    # Header and mode selection
    st.title("🚀 Unified Professor Outreach")
    option = st.selectbox("Select Mode", ["Individual", "Bulk"])
    
    if option == "Bulk":
        ui.create_main_header("Bulk Professor Outreach", "Launch large-scale, personalized campaigns.")
        handle_bulk_outreach()
    else:
        st.header("Individual Professor Outreach")
        handle_individual_outreach()

def handle_bulk_outreach():
    """Handle bulk outreach logic"""
    # Resume Upload
    st.subheader("1. Upload Your Resume")
    uploaded_file = st.file_uploader(
        "Upload your CV/Resume (PDF only)",
        type=["pdf"],
        help="Your resume will be parsed to extract skills, projects, and experience for email personalization."
    )

    # Campaign Settings
    st.subheader("2. Campaign Settings")
    settings = ui.create_campaign_settings()

    # Start Button
    st.subheader("3. Launch Campaign")
    start_button = st.button("Start Outreach", type="primary")

    if start_button and uploaded_file:
        with st.spinner("Saving uploaded resume..."):
            resumes_dir = os.path.join(os.path.dirname(__file__), '..', 'resumes')
            os.makedirs(resumes_dir, exist_ok=True)
            resume_path = os.path.join(resumes_dir, uploaded_file.name)
            with open(resume_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            session_state.set_resume_path(resume_path)

        run_bulk_campaign(settings)
    elif start_button:
        st.error("Please upload your resume before starting the campaign.")

    # Display results if they exist
    if session_state.has_key("campaign_results"):
        display_results(session_state.get_campaign_results())

def handle_individual_outreach():
    """Handle individual outreach logic"""
    with st.sidebar:
        st.header("Configuration")
        professor_name = st.text_input("Professor Name", "Dr. Alan Turing")
        university = st.text_input("University", "University of Cambridge")
        research_area = st.text_input("Research Area", "Computer Science")
        recipient_email = st.text_input("Recipient Email", "test@example.com")

        st.header("Actions")
        if st.button("Send Individual Email"):
            professor_data = {
                "name": professor_name,
                "university": university,
                "research_area": research_area,
                "last_name": professor_name.split()[-1] if professor_name else "Doe"
            }
            send_individual_email(professor_data, recipient_email)

    st.subheader("Email Preview")
    professor_data = {
        "name": professor_name,
        "university": university,
        "research_area": research_area,
        "last_name": professor_name.split()[-1] if professor_name else "Doe"
    }
    
    # Use new personalized template
    subject, html_content = create_personalized_academic_email(professor_data)
    
    st.write(f"**Subject:** {subject}")
    st.markdown("**Preview:**")
    st.components.v1.html(html_content, height=600, scrolling=True)

def send_individual_email(professor_data, recipient_email):
    """Send individual email using new personalized template"""
    try:
        subject, html_content = create_personalized_academic_email(professor_data)
        
        # Use the existing send_email_with_cv function
        success = send_email_with_cv(professor_data, recipient_email)
        
        if success:
            st.success(f"✅ Email sent successfully to {recipient_email}")
            st.info(f"Subject: {subject}")
        else:
            st.error(f"❌ Failed to send email to {recipient_email}")
            
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")

def run_bulk_campaign(settings):
    """Execute bulk outreach campaign"""
    st.header("Campaign Progress")

    log_area = st.empty()
    progress_bar = st.empty()

    logs = []
    def log_callback(message):
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        log_area.info("\n".join(logs))

    def progress_callback(percent):
        progress_bar.progress(percent)

    try:
        runner = OutreachRunner(
            resume_path=session_state.get_resume_path(),
            season=settings.get('season'),
            funding=settings.get('funding'),
            selected_countries=settings.get('countries'),
            mode=settings.get('mode'),
            progress_callback=progress_callback,
            log_callback=log_callback,
            batch_size=settings.get('batch_size')
        )

        with st.spinner("Running campaign... This may take a few minutes."):
            results = runner.run()

        session_state.set_campaign_results(results)
        st.rerun() # Rerun to display results cleanly

    except Exception as e:
        st.error(f"An error occurred during the campaign: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def display_results(results):
    """Display campaign results"""
    st.header("Campaign Complete!")

    st.success(
        f"Campaign executed successfully in {results.get('duration_seconds', 0):.2f} seconds."
    )

    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Professors Matched", results.get('professors_matched', 0))
    with col2:
        st.metric("Emails Sent/Simulated", results.get('emails_sent', 0))
    with col3:
        st.metric("Success Rate", f"{results.get('success_rate', 0):.1f}%")
    with col4:
        st.metric("Follow-ups Scheduled", results.get('followups_scheduled', 0))

    # Previews and Logs
    preview_tab, analysis_tab = st.tabs(["Email Previews", "Eligibility Analysis"])

    with preview_tab:
        st.subheader("Email Previews")
        if results.get("email_previews"):
            for i, preview in enumerate(results["email_previews"][:5]): # Show top 5
                recipient = preview.get('to', preview.get('recipient', 'Unknown'))
                subject = preview.get('subject', 'No Subject')
                body = preview.get('body', preview.get('content', 'No content available'))
                with st.expander(f"To: {recipient} | Subject: {subject}", expanded=i==0):
                    st.markdown(body, unsafe_allow_html=True)
        else:
            st.info("No email previews available.")

    with analysis_tab:
        st.subheader("Eligibility Analysis")
        analysis = results.get('eligibility_analysis', {})
        if analysis:
            st.json(analysis)
        else:
            st.info("No eligibility analysis was performed.")

if __name__ == "__main__":
    main()
