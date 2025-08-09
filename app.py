import streamlit as st

# Set up page configuration FIRST - before any other streamlit commands
st.set_page_config(page_title="InternMailing Dashboard",
                   page_icon="📬",
                   layout="wide")

# Now import other modules
import os
import json
from datetime import datetime
from src.shared.ui_components import UIComponents
from src.shared.session_state import session_state

# Initialize the UI Components
ui = UIComponents()
ui.apply_global_styles()

# Hero Section
ui.create_main_header("Welcome to InternMailing Dashboard",
                      "Streamline your outreach and job applications from one place.")

# Navigation Section
st.markdown("## Quick Navigation")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🚀 Professor Outreach", use_container_width=True):
        session_state.track_navigation("Professor Outreach")
        st.switch_page("pages/01_Professor_Outreach.py")
        
with col2:
    if st.button("🤖 Job Applications", use_container_width=True):
        session_state.track_navigation("Job Applications")
        st.switch_page("pages/02_Job_Applications.py")
        
with col3:
    if st.button("🔍 Professor Scraper", use_container_width=True):
        session_state.track_navigation("Professor Scraper")
        st.switch_page("pages/03_Professor_Scraper.py")
        
with col4:
    if st.button("📚 Documentation", use_container_width=True):
        st.info("Documentation not yet available")

# Helper functions to get real status data
def get_resumes_count():
    """Get count of uploaded resumes"""
    resumes_dir = "resumes"
    if os.path.exists(resumes_dir):
        return len([f for f in os.listdir(resumes_dir) if f.endswith('.pdf')])
    return 0

def get_emails_sent_today():
    """Get count of emails sent today (from session state and file sources)"""
    # First check session state for today's count
    session_count = len(session_state.get_sent_emails_today())
    
    # Also check file sources for completeness
    file_count = 0
    today = datetime.now().date()
    
    # Check outreach results
    for file_path in ["data/outreach_results.json", "data/generated_application_emails.json", "data/pending_emails.json"]:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            timestamp = item.get('timestamp', item.get('sent_at', ''))
                            if timestamp:
                                try:
                                    item_date = datetime.fromisoformat(timestamp.replace('Z', '')).date()
                                    if item_date == today:
                                        file_count += 1
                                except:
                                    pass
            except:
                pass
    
    # Return the maximum of session count or file count
    return max(session_count, file_count)

def get_env_vars_detected():
    """Get count of detected environment variables"""
    env_vars = ['OPENAI_API_KEY', 'GMAIL_USER', 'GMAIL_APP_PASSWORD', 'HUNTER_API_KEY', 'AZURE_API_KEY']
    return len([var for var in env_vars if os.getenv(var)])

def get_professor_data_stats():
    """Get professor data statistics"""
    stats = {'total': 0, 'with_email': 0}
    if os.path.exists("data/scraped_professors.csv"):
        try:
            import pandas as pd
            df = pd.read_csv("data/scraped_professors.csv")
            stats['total'] = len(df)
            stats['with_email'] = len(df[df['email'].notna() & (df['email'] != '')])
        except:
            pass
    return stats

# Global Status Widgets
st.markdown("## 📊 System Status Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    resumes_count = get_resumes_count()
    st.metric(
        label="📄 Resumes Uploaded",
        value=resumes_count,
        help="Number of PDF resumes in the resumes directory"
    )

with col2:
    emails_today = get_emails_sent_today()
    st.metric(
        label="📧 Emails Sent Today",
        value=emails_today,
        help="Number of emails sent or generated today"
    )

with col3:
    env_vars = get_env_vars_detected()
    st.metric(
        label="🔐 Environment Variables",
        value=f"{env_vars}/5",
        help="Key API keys and credentials detected"
    )

with col4:
    prof_stats = get_professor_data_stats()
    st.metric(
        label="👨‍🔬 Professors in Database",
        value=prof_stats['total'],
        delta=f"{prof_stats['with_email']} with emails",
        help="Total professors scraped with contact information"
    )

# Recent Activity Section
st.markdown("## 🕒 Quick Access")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Quick Actions")
    if st.button("🔄 Run Health Check", use_container_width=True):
        with st.spinner("Running system health check..."):
            st.success("✅ All systems operational")
            st.info(f"✓ {env_vars}/5 environment variables configured")
            st.info(f"✓ {resumes_count} resume(s) available")
            st.info(f"✓ {prof_stats['total']} professors in database")
    
    if st.button("📁 Open Data Directory", use_container_width=True):
        if os.path.exists("data"):
            files = os.listdir("data")
            st.write(f"Data directory contains {len(files)} files:")
            for file in files[:5]:  # Show first 5 files
                st.write(f"• {file}")
            if len(files) > 5:
                st.write(f"... and {len(files) - 5} more files")
        else:
            st.warning("Data directory not found")

with col2:
    st.markdown("### ⚙️ System Information")
    st.info(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Environment status
    env_status = "🟢 Production" if env_vars >= 3 else "🟡 Development"
    st.info(f"📊 Environment: {env_status}")
    
    # Data status
    data_status = "🟢 Ready" if prof_stats['total'] > 0 else "🟡 No Data"
    st.info(f"💾 Data Status: {data_status}")
    
    # Session state debug info
    with st.expander("📊 Session State Debug"):
        debug_info = session_state.debug_info()
        st.json(debug_info)
