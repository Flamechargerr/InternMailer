import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scheduler'))
from scheduler.streamlit_api import get_followup_manager
import requests

# Import shared components
from shared import config_manager, professor_manager, ui_components

# Page configuration
st.set_page_config(
    page_title="InternMailer 🚀", 
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        <h3>📧 Email with CV</h3>
        <p>Send personalized emails with automatic CV attachment. Perfect for individual outreach to specific professors.</p>
        <ul>
            <li>AI-powered personalization</li>
            <li>Automatic CV attachment</li>
            <li>Real-time email preview</li>
            <li>Test mode available</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📧 Send Email with CV", key="email_cv_btn", type="primary"):
        st.info("💡 Navigate to the **Email With CV** page using the sidebar to send personalized emails.")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🚀 Start Outreach</h3>
        <p>Launch personalized email campaigns to professors worldwide. Upload your resume, 
        select preferences, and let AI generate tailored emails.</p>
        <ul>
            <li>AI-powered email generation</li>
            <li>Resume parsing & analysis</li>
            <li>Duplicate detection</li>
            <li>Dry run & live modes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Go to Outreach", key="outreach_btn", type="primary"):
        st.info("💡 Navigate to the **Outreach** page using the sidebar to start your campaign.")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>📅 Manage Follow-ups</h3>
        <p>Track and manage your follow-up emails with advanced scheduling and analytics.</p>
        <ul>
            <li>Automated follow-up scheduling</li>
            <li>Campaign management</li>
            <li>Response tracking</li>
            <li>Analytics & insights</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📅 Go to Follow-ups", key="followups_btn", type="primary"):
        st.info("💡 Navigate to the **Follow-ups** page using the sidebar to manage your campaigns.")

# Quick Stats Dashboard
st.header("📈 Quick Statistics")

if not config_issues:
    try:
        # Initialize session state for home page stats
        if 'home_stats' not in st.session_state:
            st.session_state.home_stats = {
                'total_campaigns': 0,
                'emails_sent': 0,
                'follow_ups_scheduled': 0,
                'response_rate': 0.0
            }
        
        followup_manager = get_followup_manager()
        analytics = followup_manager.get_analytics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Campaigns", len(analytics.get('campaigns', [])))
        
        with col2:
            st.metric("Follow-ups Sent", analytics.get('sent_followups', 0))
        
        with col3:
            st.metric("Scheduled", analytics.get('scheduled_followups', 0))
        
        with col4:
            overdue = analytics.get('overdue_followups', 0)
            if overdue > 0:
                st.metric("Overdue", overdue, delta_color="inverse")
            else:
                st.metric("Overdue", 0)
        
        # Show recent activity if available
        if analytics.get('campaigns'):
            st.subheader("📋 Recent Campaigns")
            for campaign in analytics['campaigns'][:3]:  # Show last 3 campaigns
                st.write(f"• **{campaign['name']}** - {campaign.get('followup_count', 0)} follow-ups")
        
    except Exception as e:
        st.warning(f"⚠️ Unable to load statistics: {str(e)}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Campaigns", "—")
        with col2:
            st.metric("Follow-ups Sent", "—")
        with col3:
            st.metric("Scheduled", "—")
        with col4:
            st.metric("Overdue", "—")
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
    
    ### 4. **Monitor & Manage**
    - Use the **Follow-ups** page to track responses
    - Schedule additional follow-ups
    - Analyze campaign performance
    - Adjust settings as needed
    
    ### 5. **Best Practices**
    - Always test with Dry Run first
    - Review generated emails before sending
    - Monitor response rates and adjust approach
    - Use follow-ups strategically (don't spam)
    """)

# Footer
st.markdown("---")
st.caption("InternMailer © 2024 | Built by Anamay Tripathy")
st.caption("💡 **Tip:** Use the sidebar to navigate between Outreach and Follow-ups pages.")
