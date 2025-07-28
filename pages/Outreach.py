import streamlit as st
import os
import pandas as pd
import json
from dotenv import load_dotenv
import sys
from jinja2 import Template
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from resume_parser import ResumeParser
from email_generator import EmailGenerator
from gmail_sender import GmailSender
from professor_scraper import ProfessorScraper
from scheduler.streamlit_api import get_followup_manager
from professor_tracker import ProfessorTracker
import time
import requests
import logging
from datetime import datetime, timedelta
from ui_utils import apply_theme_styles, show_config_status, create_input_with_help, handle_network_call

# Initialize session state for persistence
if 'outreach_results' not in st.session_state:
    st.session_state.outreach_results = {}
if 'last_resume_path' not in st.session_state:
    st.session_state.last_resume_path = None
if 'campaign_settings' not in st.session_state:
    st.session_state.campaign_settings = {
        'season': 'Any',
        'funding': 'Any',
        'countries': []
    }

# Initialize widget keys to prevent KeyError
if 'season_selectbox' not in st.session_state:
    st.session_state.season_selectbox = 'Any'
if 'funding_selectbox' not in st.session_state:
    st.session_state.funding_selectbox = 'Any'
if 'countries_multiselect' not in st.session_state:
    st.session_state.countries_multiselect = []
if 'outreach_mode' not in st.session_state:
    st.session_state.outreach_mode = 'Dry Run'

load_dotenv()

# Configuration validation
def check_configuration():
    """Check if all required configuration is set up"""
    issues = []
    
    # Check environment variables
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user:
        issues.append("GMAIL_USER environment variable not set")
    if not gmail_password:
        issues.append("GMAIL_APP_PASSWORD environment variable not set")
    
    # Check data files
    if not os.path.exists('data/proffesor.csv'):
        issues.append("Professor CSV file not found at 'data/proffesor.csv'")
    
    # Check resume directory
    if not os.path.exists('resumes'):
        os.makedirs('resumes', exist_ok=True)
    
    return issues

# Check if Azure AI is available
def is_azure_ai_available():
    try:
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        # Add src to path if not already there
        import sys
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
        if src_path not in sys.path:
            sys.path.append(src_path)
        
        from azure_ai_client import get_azure_ai_client
        client = get_azure_ai_client()
        return client.is_available()
    except Exception as e:
        print(f"Azure AI availability check failed: {e}")
        return False

apply_theme_styles()
st.title("🚀 Academic Outreach")

# Configuration validation
config_issues = check_configuration()
show_config_status(config_issues)

azure_ai_available = handle_network_call(is_azure_ai_available, "check Azure AI status")

if azure_ai_available:
    st.success("✅ Azure AI (GPT-4.1) enabled! Using advanced AI for intelligent email generation.")
else:
    st.info("Using template-based email generation with fallback when Azure AI is unavailable.")

# Upload resume section - always visible
st.header("1. Upload Your Resume")
uploaded_file = create_input_with_help(st.file_uploader, "Upload your PDF resume", "Upload your latest PDF resume. Skills and projects will be extracted automatically.", type=["pdf"])

# Handle resume upload and persistence
resume_path = None
if uploaded_file:
    resume_path = os.path.join("resumes", uploaded_file.name)
    with open(resume_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.last_resume_path = resume_path
    st.success(f"Uploaded {uploaded_file.name}")
elif st.session_state.last_resume_path and os.path.exists(st.session_state.last_resume_path):
    resume_path = st.session_state.last_resume_path
    st.info(f"Using previous resume: {os.path.basename(resume_path)}")
else:
    # Check for existing resume files
    resume_dir = "resumes"
    if os.path.exists(resume_dir):
        resume_files = [f for f in os.listdir(resume_dir) if f.endswith('.pdf')]
        if resume_files:
            resume_path = os.path.join(resume_dir, resume_files[0])
            st.session_state.last_resume_path = resume_path
            st.info(f"Using existing resume: {resume_files[0]}")

# Campaign preferences - always visible
st.header("2. Campaign Preferences")
col1, col2 = st.columns(2)
with col1:
    season_options = ["Any", "Winter", "Summer"]
    current_season = st.session_state.campaign_settings.get('season', 'Any')
    season_index = season_options.index(current_season) if current_season in season_options else 0
    
    season = create_input_with_help(st.selectbox, "Internship Season", "Select the preferred internship season.", 
                         options=season_options,
                         index=season_index,
                         key="season_selectbox")
    st.session_state.campaign_settings['season'] = season

with col2:
    funding_options = ["Any", "Paid", "Unpaid"]
    current_funding = st.session_state.campaign_settings.get('funding', 'Any')
    funding_index = funding_options.index(current_funding) if current_funding in funding_options else 0
    
    funding = create_input_with_help(st.selectbox, "Funding Preference", "Select if you prefer paid, unpaid, or any internship.", 
                          options=funding_options,
                          index=funding_index,
                          key="funding_selectbox")
    st.session_state.campaign_settings['funding'] = funding

# Select countries - always visible
st.header("3. Select Target Countries (Optional)")
st.caption("Choose countries to target for outreach. Leave blank for global search.")
countries = ["US", "UK", "Europe", "Singapore", "Canada", "Australia", "Other"]
selected_countries = create_input_with_help(st.multiselect, "Countries", "Choose countries to target for outreach. Leave blank for global search.", 
                                   options=countries, 
                                   default=st.session_state.campaign_settings.get('countries', []),
                                   key="countries_multiselect")
st.session_state.campaign_settings['countries'] = selected_countries

# Mode selection - always visible
st.header("4. Outreach Mode")
mode = create_input_with_help(st.radio, "Choose Mode:", "Dry Run: Preview emails without sending. Live Send: Actually send emails to professors.", 
                               options=["Dry Run", "Live Send"])

# Display selected mode
if mode == "Live Send":
    st.warning("📧 Emails will be sent!")
else:
    st.info("🔍 This is a dry run.")

# Test email section - always visible
st.header("4.5. Test Email Configuration")
st.caption("Send a test email to yourself to verify your Gmail configuration works correctly.")

test_email_col1, test_email_col2 = st.columns([2, 1])
with test_email_col1:
    test_email = st.text_input("Test Email Address", value=os.getenv('GMAIL_USER', ''), help="Enter your email to receive a test message", label_visibility="visible")
with test_email_col2:
    st.write("")
    if st.button("Send Test Email", disabled=not test_email, help="Send a test email to verify your configuration"):
        if test_email:
            try:
                gmail_user = os.getenv('GMAIL_USER')
                gmail_password = os.getenv('GMAIL_APP_PASSWORD')
                
                if gmail_user and gmail_password:
                    sender = GmailSender(gmail_user, gmail_password)
                    test_sent = sender.send_test_email(test_email)
                    
                    if test_sent:
                        st.success("✅ Test email sent successfully! Check your inbox.")
                    else:
                        st.error("❌ Failed to send test email. Check your Gmail credentials in .env file.")
                else:
                    st.error("❌ Gmail credentials not configured. Please check your .env file.")
            except Exception as e:
                st.error(f"❌ Error sending test email: {str(e)}")

# Progress bar and run button - always visible
st.header("5. Launch Outreach")

# Add approval workflow for live mode
if mode == "Live Send":
    st.warning("⚠️ **Live Send Mode**: Emails will be sent to real professors. Please review your settings carefully.")
    
    # Multiple confirmation checkboxes for safety
    st.subheader("Live Send Confirmation")
    
    confirmation_1 = st.checkbox(
        "✅ I have sent a test email and confirmed Gmail configuration works",
        help="Test email functionality before sending to professors"
    )
    
    confirmation_2 = st.checkbox(
        "✅ I have reviewed my resume and campaign settings",
        help="Ensure all information is current and accurate"
    )
    
    confirmation_3 = st.checkbox(
        "✅ I understand that real emails will be sent to professors",
        help="This is not a simulation - actual emails will be delivered"
    )
    
    approval_checkbox = confirmation_1 and confirmation_2 and confirmation_3
    
    with st.expander("Pre-send Checklist", expanded=not approval_checkbox):
        st.markdown("""
        Before sending emails to professors, please ensure:
        
        ✅ **Test email sent successfully** - Your Gmail configuration is working  
        ✅ **Resume uploaded** - Your latest resume is attached  
        ✅ **Campaign settings reviewed** - Season, funding, and countries are correct  
        ✅ **Rate limiting understood** - Emails will be sent with delays to avoid spam detection  
        ✅ **Follow-up system ready** - You can manage responses through the Follow-ups page  
        """)
    
    # Add batch size slider for live mode
    col1, col2 = st.columns([3, 1])
    with col1:
        batch_size = st.slider("Batch Size", min_value=1, max_value=100, value=10, step=1,
                             help="Select how many emails to send in this batch (1-100)")
    with col2:
        unlimited_batch = st.checkbox("Unlimited", help="Send to all matching professors")
    
    if unlimited_batch:
        batch_size = 'Unlimited'
        st.info("⚠️ All matching professors will be contacted in this batch.")
    
    run_button = st.button("🚀 Send Emails to Professors", 
                          disabled=not (resume_path and approval_checkbox), 
                          type="primary")
else:
    st.info("🔍 Dry Run Mode: No emails will be sent. This will generate and preview emails only.")
    
    # Add batch size slider for dry run mode too
    col1, col2 = st.columns([3, 1])
    with col1:
        batch_size = st.slider("Preview Batch Size", min_value=1, max_value=100, value=10, step=1,
                             help="Select how many emails to generate and preview (1-100)")
    with col2:
        unlimited_preview = st.checkbox("Preview All", help="Preview all matching professors")
    
    if unlimited_preview:
        batch_size = 'Unlimited'
        st.info("⚠️ All matching professors will be previewed.")
    
    run_button = st.button("🔍 Start Dry Run", disabled=not resume_path, type="primary")

# Progress tracking
progress_bar = st.progress(0)
log_placeholder = st.empty()

# Initialize analytics in session state
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'professors_matched': 0,
        'emails_sent': 0,
        'response_rate': 0.0,
        'followups_scheduled': 0
    }

# Main outreach execution
if run_button and resume_path:
    # Import outreach runner
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from outreach_runner import OutreachRunner
    
    # Create and run outreach
    runner = OutreachRunner(
        resume_path=resume_path,
        season=season,
        funding=funding,
        selected_countries=selected_countries,
        mode=mode,
        progress_callback=progress_bar.progress,
        log_callback=log_placeholder.write,
        batch_size=None if batch_size == 'Unlimited' else batch_size
    )
    
    try:
        results = handle_network_call(runner.run, "execute outreach campaign")
        
        if results:
            # Store results in session state
            st.session_state.outreach_results = results
            st.session_state.analytics.update({
                'professors_matched': results.get('professors_matched', 0),
                'emails_sent': results.get('emails_sent', 0),
                'followups_scheduled': results.get('followups_scheduled', 0)
            })
            
            # Display success state
            if results.get('success', False):
                from ui_utils import show_status_banner
                show_status_banner("Outreach completed successfully!", "success")
                
                # Show results summary
                with st.expander("📊 Campaign Results", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Professors Matched", results.get('professors_matched', 0), help="Number of professors found matching your criteria")
                    with col2:
                        st.metric("Emails Sent", results.get('emails_sent', 0), help="Number of emails successfully sent")
                    with col3:
                        st.metric("Follow-ups Scheduled", results.get('followups_scheduled', 0), help="Number of follow-up emails scheduled")
                
                # Store campaign ID for follow-ups
                if results.get('campaign_id'):
                    st.session_state.current_campaign_id = results['campaign_id']
            else:
                from ui_utils import show_status_banner
                show_status_banner("Outreach failed. Please check the logs above.", "error")
        else:
            from ui_utils import show_status_banner
            show_status_banner("Outreach operation was cancelled or failed.", "error")
            
    except Exception as e:
        from ui_utils import display_error_details
        display_error_details(e, "execute outreach campaign", show_details=True)
        log_placeholder.error(f"Error: {e}")
        progress_bar.progress(0)

# Analytics display - always visible
st.header("6. Campaign Analytics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Professors Matched", st.session_state.analytics.get('professors_matched', 0))
with col2:
    st.metric("Emails Sent", st.session_state.analytics.get('emails_sent', 0))
with col3:
    st.metric("Response Rate", f"{st.session_state.analytics.get('response_rate', 0.0):.1f}%")
with col4:
    st.metric("Follow-ups Scheduled", st.session_state.analytics.get('followups_scheduled', 0))

# Show recent results if available
if 'outreach_results' in st.session_state and st.session_state.outreach_results:
    results = st.session_state.outreach_results
    
    if results.get('email_previews'):
        st.header("7. Email Previews")
        with st.expander("📧 Generated Emails", expanded=False):
            for i, email in enumerate(results['email_previews'][:3]):  # Show first 3
                st.subheader(f"Email {i+1}: {email['to']}")
                st.text_area(f"Subject {i+1}", email['subject'], key=f"subject_{i}", label_visibility="visible")
                st.text_area(f"Body {i+1}", email['body'], height=200, key=f"body_{i}", label_visibility="visible")
                st.divider()

# Navigation hint
st.info("💡 **Tip:** Use the sidebar to navigate to the Follow-ups page to manage scheduled follow-ups.")
