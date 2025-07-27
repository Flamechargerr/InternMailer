"""
InternMailer: AI-Powered Academic Outreach Platform
Winter '25-'26 Customized MVP - Fixed Version
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def safe_import():
    """Safely import modules with error handling"""
    try:
        from scraper.csrankings_scraper import fetch_and_parse, available_countries, parse_csv_professors
        from mailer.generate_emails import generate_emails
        from mailer.send_emails import send_emails, get_send_log
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    # Configure Streamlit page
    st.set_page_config(
        page_title="InternMailer - AI Academic Outreach",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Test imports first
    imports_ok, import_error = safe_import()
    if not imports_ok:
        st.error(f"❌ Import Error: {import_error}")
        st.stop()
    
    # Import modules after successful test
    from scraper.csrankings_scraper import fetch_and_parse, available_countries, parse_csv_professors
    from mailer.generate_emails import generate_emails
    from mailer.send_emails import send_emails, get_send_log
    
    # --- Styling ---
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .status-good { color: #28a745; font-weight: bold; }
    .status-bad { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    # --- Header ---
    st.markdown("""
    <div class="main-header">
        <h1>🚀 InternMailer</h1>
        <h3>AI-Powered Academic Outreach Platform</h3>
        <p>Winter '25–'26 Internship Campaign • Powered by AI & Gmail API</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Sidebar Configuration ---
    st.sidebar.title("🎯 Campaign Control")
    st.sidebar.markdown("*Configure your outreach strategy*")
    
    # Campaign settings
    st.sidebar.subheader("📍 Target Region")
    country = st.sidebar.selectbox(
        "Select Country",
        options=["India", "China", "Japan", "South Korea", "Singapore", "Hong Kong"],
        index=0
    )
    
    top_n = st.sidebar.slider("Number of Professors", min_value=5, max_value=50, value=10)
    
    st.sidebar.subheader("🔬 Research Domains")
    domains = st.sidebar.text_area(
        "Enter your research interests (comma-separated)",
        value="machine learning, artificial intelligence, data science",
        height=100
    )
    
    st.sidebar.subheader("📄 CV Upload")
    cv_file = st.sidebar.file_uploader(
        "Upload your CV (PDF)",
        type=['pdf'],
        help="Upload your CV to personalize emails"
    )
    
    # --- Main Content ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Campaign Dashboard")
        
        # Environment status
        st.markdown("### 🔧 System Status")
        
        # Check environment variables
        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        gmail_id = os.getenv('GMAIL_CLIENT_ID')
        gmail_secret = os.getenv('GMAIL_CLIENT_SECRET')
        
        col_env1, col_env2, col_env3 = st.columns(3)
        
        with col_env1:
            status = "✅ Ready" if hf_key else "❌ Missing"
            st.markdown(f"**HuggingFace API:** {status}")
        
        with col_env2:
            status = "✅ Ready" if gmail_id else "❌ Missing"
            st.markdown(f"**Gmail Client ID:** {status}")
        
        with col_env3:
            status = "✅ Ready" if gmail_secret else "❌ Missing"
            st.markdown(f"**Gmail Secret:** {status}")
        
        # Campaign metrics
        st.markdown("### 📈 Campaign Metrics")
        
        try:
            logs = get_send_log()
            total_sent = len([log for log in logs if 'sent' in log.get('status', '')])
            total_failed = len([log for log in logs if 'failed' in log.get('status', '')])
            
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                st.metric("📧 Emails Sent", total_sent)
            
            with col_m2:
                st.metric("❌ Failed", total_failed)
            
            with col_m3:
                success_rate = (total_sent / max(len(logs), 1)) * 100
                st.metric("📊 Success Rate", f"{success_rate:.1f}%")
        
        except Exception as e:
            st.warning(f"Could not load metrics: {e}")
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        # Test Configuration Button
        if st.button("🧪 Test Configuration", type="secondary", use_container_width=True):
            with st.spinner("Testing configuration..."):
                try:
                    # Test with a small sample
                    if cv_file is None:
                        st.error("❌ Please upload a CV file for testing")
                    else:
                        # Test professor data fetching
                        test_professors = [
                            {"name": "Dr. Test Professor", "email": "test@university.edu", 
                             "affiliation": "Test University", "profile_url": "https://example.com"}
                        ]
                        
                        cv_bytes = cv_file.read()
                        cv_filename = cv_file.name
                        
                        # Test email generation
                        test_drafts = generate_emails(test_professors, domains, cv_bytes, cv_filename)
                        
                        if test_drafts:
                            st.success(f"✅ Test successful! Generated {len(test_drafts)} test emails")
                            
                            # Show preview
                            with st.expander("📧 Email Preview"):
                                draft = test_drafts[0]
                                st.write(f"**To:** {draft.get('name')} ({draft.get('to')})")
                                st.write(f"**Subject:** {draft.get('subject')}")
                                st.text_area("Email Body:", draft.get('body', ''), height=200)
                        else:
                            st.warning("⚠️ Test generated 0 emails")
                
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")
        
        # Launch Campaign Button
        if st.button("🚀 Launch Campaign", type="primary", use_container_width=True):
            if cv_file is None:
                st.error("❌ Please upload a CV file before launching")
            elif not domains.strip():
                st.error("❌ Please enter your research domains")
            else:
                with st.spinner("Launching campaign..."):
                    try:
                        # Fetch professors
                        st.info("📡 Fetching professor data...")
                        professors = parse_csv_professors(country, top_n)
                        
                        if not professors:
                            st.warning("⚠️ No professors found. Try different criteria.")
                        else:
                            st.success(f"✅ Found {len(professors)} professors")
                            
                            # Generate emails
                            st.info("✍️ Generating personalized emails...")
                            cv_bytes = cv_file.read()
                            cv_filename = cv_file.name
                            
                            drafts = generate_emails(professors, domains, cv_bytes, cv_filename)
                            
                            if drafts:
                                st.success(f"✅ Generated {len(drafts)} email drafts")
                                
                                # Send emails (in demo mode, just log them)
                                st.info("📤 Sending emails...")
                                results = send_emails(drafts)
                                
                                sent_count = sum(1 for r in results if r.get('status') == 'sent')
                                st.success(f"🎉 Campaign completed! {sent_count} emails sent")
                                st.balloons()
                            else:
                                st.warning("⚠️ No emails generated")
                    
                    except Exception as e:
                        st.error(f"❌ Campaign failed: {str(e)}")
    
    # --- Recent Activity ---
    st.markdown("---")
    st.subheader("📝 Recent Activity")
    
    try:
        logs = get_send_log()
        if logs:
            # Show last 5 logs
            recent_logs = logs[-5:] if len(logs) > 5 else logs
            
            df = pd.DataFrame(recent_logs)
            if not df.empty:
                # Format the dataframe
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("📝 No recent activity found")
        else:
            st.info("📝 No activity logs found. Run your first campaign!")
    
    except Exception as e:
        st.warning(f"Could not load recent activity: {e}")
    
    # --- Footer ---
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🚀 InternMailer v1.0 | Winter '25-'26 Campaign | Built with Streamlit & ❤️</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
