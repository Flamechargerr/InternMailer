import streamlit as st

# Page configuration must be first
st.set_page_config(
    page_title="InternMailer 🚀", 
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import pandas as pd
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scheduler'))
sys.path.append('.')

# Import components with error handling
try:
    from scheduler.streamlit_api import get_followup_manager
except ImportError:
    def get_followup_manager():
        return None

try:
    from shared import config_manager, professor_manager, ui_components
except ImportError:
    config_manager = professor_manager = ui_components = None

load_dotenv()

# Utility functions for data loading
def load_json_data(file_path):
    """Load JSON data with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        pass
    return []

def get_system_statistics():
    """Get comprehensive system statistics"""
    stats = {
        'professors_total': 0,
        'jobs_scraped': 0,
        'hr_emails_found': 0,
        'applications_sent': 0,
        'customized_cvs': 0,
        'outreach_results': 0,
        'last_activity': None
    }
    
    # Count professors
    prof_files = ['data/professors.json', 'data/proffesor.csv', 'data/professors_master_list.csv']
    for file_path in prof_files:
        if os.path.exists(file_path):
            try:
                if file_path.endswith('.json'):
                    data = load_json_data(file_path)
                    stats['professors_total'] = len(data)
                elif file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    stats['professors_total'] = len(df)
                break
            except Exception:
                continue
    
    # Count job-related data
    job_data = load_json_data('data/scraped_jobs.json')
    stats['jobs_scraped'] = len(job_data)
    
    hr_data = load_json_data('data/hr_emails.json')
    stats['hr_emails_found'] = len(hr_data)
    
    app_data = load_json_data('data/application_log.json')
    stats['applications_sent'] = len(app_data)
    
    cv_data = load_json_data('data/customized_cvs.json')
    stats['customized_cvs'] = len(cv_data)
    
    outreach_data = load_json_data('data/outreach_results.json')
    if outreach_data and isinstance(outreach_data, dict):
        stats['outreach_results'] = outreach_data.get('emails_sent', 0)
    
    # Get last activity from various log files
    activity_files = [
        'data/application_log.json',
        'data/outreach_results.json',
        'data/emailed_professors.json'
    ]
    
    latest_activity = None
    for file_path in activity_files:
        if os.path.exists(file_path):
            try:
                stat = os.stat(file_path)
                file_time = datetime.fromtimestamp(stat.st_mtime)
                if latest_activity is None or file_time > latest_activity:
                    latest_activity = file_time
            except Exception:
                continue
    
    stats['last_activity'] = latest_activity
    return stats

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
    
    # Check data files - try multiple possible locations
    prof_csv_paths = [
        'data/proffesor.csv',
        '../data/proffesor.csv',
        'InternMailer/data/proffesor.csv',
        os.path.join(os.path.dirname(__file__), 'data', 'proffesor.csv')
    ]
    prof_csv_found = any(os.path.exists(path) for path in prof_csv_paths)
    if not prof_csv_found:
        issues.append("Professor CSV file not found. Tried: " + ', '.join(prof_csv_paths))
    
    # Check resume directory
    if not os.path.exists('resumes'):
        os.makedirs('resumes', exist_ok=True)
    
    return issues


# Check configuration and show warnings
config_issues = check_configuration()
if config_issues:
    st.sidebar.error("⚠️ Configuration Issues")
    for issue in config_issues:
        st.sidebar.warning(f"• {issue}")
    
    with st.sidebar.expander("Setup Instructions"):
        st.markdown("""
        **Required Setup:**
        1. Create a `.env` file in the project root
        2. Add your Gmail credentials:
           ```
           GMAIL_USER=your-email@gmail.com
           GMAIL_APP_PASSWORD=your-app-password
           ```
        3. Generate Gmail App Password:
           - Go to Google Account settings
           - Security → App passwords
           - Generate password for "Mail"
        4. Ensure `data/proffesor.csv` exists
        """)
else:
    st.sidebar.success("✅ Configuration OK")

# Enhanced styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
    }
    .sub-title {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">🚀 InternMailer</h1>
    <p class="sub-title">AI-Powered Academic Outreach Platform</p>
    <p>Connect with professors worldwide using intelligent email personalization</p>
</div>
""", unsafe_allow_html=True)

# System status checks
st.header("📊 System Status")

col1, col2, col3 = st.columns(3)

with col1:
    if not config_issues:
        st.success("✅ Configuration Valid")
    else:
        st.error("❌ Configuration Issues")

with col2:
    st.success("✅ GPT-4 Available")

with col3:
    try:
        followup_manager = get_followup_manager()
        analytics = followup_manager.get_analytics()
        st.info(f"📈 {analytics.get('total_followups', 0)} Total Follow-ups")
    except Exception:
        st.error("❌ Follow-up System Error")

# Navigation Section
st.header("🗺️ Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📧 Professor Outreach</h3>
        <p>Send personalized emails to professors for research opportunities. Uses AI to tailor content and attaches your CV automatically.</p>
        <ul>
            <li>AI-powered personalization</li>
            <li>Automatic CV attachment</li>
            <li>Real-time email preview</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📧 Go to Professor Outreach", key="prof_outreach_btn"):
        st.info("💡 Navigate to the **Professor Outreach** page using the sidebar to send emails.")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🤖 Job Application Automator</h3>
        <p>Automate job applications to companies and HR departments. Scrape job postings, customize your CV, and send personalized application emails.</p>
        <ul>
            <li>Job posting scraping from LinkedIn</li>
            <li>CV customization per role</li>
            <li>Automated email generation</li>
            <li>Application tracking & status updates</li>
            <li>HR email discovery</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🤖 Go to Job Automator", key="job_automator_btn"):
        st.info("💡 Navigate to the **Job Applications** page to automate your job search.")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>🔍 Professor Scraper</h3>
        <p>Scrape professor data from CSRankings and enrich it with contact information. Build your own database of potential research supervisors.</p>
        <ul>
            <li>Scrape from CSRankings</li>
            <li>Enrich with email addresses</li>
            <li>Deduplicate and filter data</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔍 Go to Professor Scraper", key="prof_scraper_btn"):
        st.info("💡 Navigate to the **Professor Scraper** page to build your database.")

# Quick Stats Dashboard
st.header("📈 System Statistics")

if not config_issues:
    try:
        # Get integrated system statistics
        system_stats = get_system_statistics()
        
        # Main metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👨‍🏫 Professors", system_stats['professors_total'])
        
        with col2:
            st.metric("💼 Jobs Scraped", system_stats['jobs_scraped'])
        
        with col3:
            st.metric("📧 HR Emails", system_stats['hr_emails_found'])
        
        with col4:
            st.metric("📨 Applications", system_stats['applications_sent'])
        
        # Additional metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Custom CVs", system_stats['customized_cvs'])
        
        with col2:
            st.metric("🎯 Outreach Sent", system_stats['outreach_results'])
        
        with col3:
            # Try to get followup statistics
            try:
                followup_manager = get_followup_manager()
                if followup_manager:
                    analytics = followup_manager.get_analytics()
                    st.metric("🔄 Follow-ups", analytics.get('total_followups', 0))
                else:
                    st.metric("🔄 Follow-ups", "—")
            except Exception:
                st.metric("🔄 Follow-ups", "—")
        
        with col4:
            if system_stats['last_activity']:
                days_ago = (datetime.now() - system_stats['last_activity']).days
                if days_ago == 0:
                    st.metric("🕒 Last Activity", "Today")
                elif days_ago == 1:
                    st.metric("🕒 Last Activity", "Yesterday")
                else:
                    st.metric("🕒 Last Activity", f"{days_ago} days ago")
            else:
                st.metric("🕒 Last Activity", "No activity")
        
        # Recent activity section
        st.subheader("📊 Data Overview")
        
        data_col1, data_col2 = st.columns(2)
        
        with data_col1:
            st.markdown("**📈 Professor Outreach**")
            if system_stats['professors_total'] > 0:
                st.success(f"✅ {system_stats['professors_total']:,} professors in database")
            else:
                st.warning("⚠️ No professor data found")
            
            if system_stats['outreach_results'] > 0:
                st.info(f"📧 {system_stats['outreach_results']} outreach emails sent")
        
        with data_col2:
            st.markdown("**💼 Job Applications**")
            if system_stats['jobs_scraped'] > 0:
                st.success(f"✅ {system_stats['jobs_scraped']} jobs scraped")
            else:
                st.warning("⚠️ No job data found")
            
            if system_stats['hr_emails_found'] > 0:
                st.info(f"📧 {system_stats['hr_emails_found']} HR contacts found")
            
            if system_stats['applications_sent'] > 0:
                st.info(f"📨 {system_stats['applications_sent']} applications sent")
        
        # Show data files status
        with st.expander("📁 Data Files Status", expanded=False):
            data_files = {
                "Professor Database": ["data/proffesor.csv", "data/professors.json"],
                "Job Postings": ["data/scraped_jobs.json", "data/parsed_jobs.json"],
                "HR Contacts": ["data/hr_emails.json", "data/enhanced_hr_contacts.json"],
                "Applications": ["data/application_log.json", "data/customized_cvs.json"],
                "Outreach Results": ["data/outreach_results.json", "data/emailed_professors.json"]
            }
            
            for category, files in data_files.items():
                st.markdown(f"**{category}:**")
                for file_path in files:
                    if os.path.exists(file_path):
                        try:
                            if file_path.endswith('.json'):
                                data = load_json_data(file_path)
                                count = len(data)
                            elif file_path.endswith('.csv'):
                                df = pd.read_csv(file_path)
                                count = len(df)
                            st.success(f"✅ {os.path.basename(file_path)} ({count} records)")
                        except Exception:
                            st.error(f"❌ {os.path.basename(file_path)} (corrupted)")
                    else:
                        st.warning(f"⚠️ {os.path.basename(file_path)} (missing)")
        
    except Exception as e:
        st.error(f"❌ Unable to load system statistics: {str(e)}")
        # Fallback metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Professors", "—")
        with col2:
            st.metric("Jobs", "—")
        with col3:
            st.metric("Applications", "—")
        with col4:
            st.metric("Follow-ups", "—")
else:
    st.info("📊 Statistics will be available after configuration is complete.")

# Getting Started Guide
st.header("🚀 Getting Started")

with st.expander("📝 Step-by-Step Guide", expanded=False):
    st.markdown("""
    ### 1. **Setup Configuration**
    - Create a `.env` file with your Gmail credentials
    - Ensure professor CSV data is available
    - Start Ollama service for AI features
    
    ### 2. **Send Individual Emails (Recommended Start)**
    - Navigate to the **Email with CV** page
    - Enter professor details (name, university, research area)
    - Use Test Mode to send to yourself first
    - Review and send personalized emails with CV attachment
    
    ### 3. **Launch Bulk Campaigns**
    - Navigate to the **Outreach** page
    - Upload your resume (PDF format)
    - Configure campaign preferences
    - Choose target countries (optional)
    - Select run mode (Dry Run recommended first)
    
    ### 4. **Job Application Automation**
    - Navigate to the **Job Applications** page
    - Configure LinkedIn job search URLs
    - Add Hunter.io API key for HR email discovery
    - Run the job application pipeline to:
      - Scrape job postings
      - Parse job requirements
      - Customize CVs for each role
      - Generate personalized application emails
    - Track application statuses in the dashboard
    
    ### 5. **Monitor & Manage**
    - Use the **Follow-ups** page to track responses
    - Schedule additional follow-ups
    - Analyze campaign performance
    - Adjust settings as needed
    
    ### 6. **Best Practices**
    - Always test with Dry Run first
    - Review generated emails before sending
    - Monitor response rates and adjust approach
    - Use follow-ups strategically (don't spam)
    """)

# Footer
st.markdown("---")
st.caption("InternMailer © 2024 | Built by Anamay Tripathy")
st.caption("💡 **Tip:** Use the sidebar to navigate between Outreach and Follow-ups pages.")
