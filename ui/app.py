"""
InternMailer: AI-Powered Academic Outreach Platform
Winter '25-'26 Customized MVP
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

from scraper.csrankings_scraper import fetch_and_parse, available_countries, parse_csv_professors
from mailer.generate_emails import generate_emails
from mailer.send_emails import send_emails, get_send_log

def main():
    st.set_page_config(
        page_title="InternMailer - AI Academic Outreach",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # --- UI Styling ---
    st.markdown("""
    <style>
    /* Reset Streamlit's default styles */
    .stApp {
        color: #2c3e50 !important;
    }
    
    /* Force text color for all elements */
    * {
        color: #2c3e50 !important;
    }
    
    /* Main containers */
    .stContainer > div {
        background-color: white !important;
    }
    
    /* Cards */
    .stMarkdown > div {
        background-color: white !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
    }
    
    /* Metric cards */
    .metric-card {
        background: #f8f9fa !important;
        padding: 1.5rem !important;
        border-radius: 8px !important;
        border-left: 4px solid #667eea !important;
        margin: 1rem 0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .metric-card h4 {
        color: #2c3e50 !important;
        margin: 0 0 0.5rem 0 !important;
    }
    
    .metric-card h2 {
        color: #2c3e50 !important;
        margin: 0.5rem 0 !important;
    }
    
    .metric-card p {
        color: #6c757d !important;
        margin: 0.25rem 0 0 0 !important;
    }
    
    /* Status indicators */
    .status-good {
        color: #28a745 !important;
        font-weight: bold !important;
    }
    
    .status-bad {
        color: #dc3545 !important;
        font-weight: bold !important;
    }
    
    /* Campaign card */
    .campaign-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
        padding: 2rem !important;
        border-radius: 15px !important;
        text-align: center !important;
        margin: 2rem 0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    
    .campaign-card h2 {
        color: white !important;
        margin: 0 0 1rem 0 !important;
    }
    
    .campaign-card p {
        color: white !important;
        margin: 0 !important;
        font-size: 1.1rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    
    /* Alerts */
    [role="alert"] {
        background-color: #f8f9fa !important;
        border-left: 4px solid #dc3545 !important;
        padding: 1rem !important;
        border-radius: 4px !important;
    }
    
    [role="alert"] p {
        color: #dc3545 !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    
    /* Sidebar */
    .st-emotion-cache-1cyp6kb {
        background-color: #f8f9fa !important;
    }
    
    .st-emotion-cache-1cyp6kb * {
        color: #2c3e50 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # --- Header ---
    st.markdown("""
    <div class="main-header">
        <h1>🚀 InternMailer</h1>
        <h3>AI-Powered Academic Outreach Platform</h3>
        <p>Winter '25–'26 Internship Campaign • Powered by HuggingFace AI & Gmail API</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Sidebar configuration ---
    st.sidebar.title("🎯 Campaign Control")
    st.sidebar.markdown("*Configure your outreach strategy*")
    st.sidebar.header("🔧 Configuration")

    # --- Helper: Reset Form ---
    def reset_form():
        st.session_state["country"] = None
        st.session_state["top_n"] = 20
        st.session_state["domains"] = ""
        st.session_state["cv_file"] = None

    # --- Country selection ---
    countries = available_countries("asia")
    country = st.sidebar.selectbox(
        "Select Country",
        countries,
        index=1 if "India" in countries else 0,
        key="country",
        help="Choose the country for professor discovery"
    )
    
    # --- Number of professors ---
    top_n = st.sidebar.slider(
        "Top N Professors",
        min_value=1,
        max_value=50,
        value=20,
        help="Number of top-ranked professors to contact",
        key="top_n"
    )
    
    # --- Research domains ---
    domains = st.sidebar.text_area(
        "Your Research Domains",
        placeholder="machine learning, data science, computer vision",
        help="Enter your research interests separated by commas",
        key="domains"
    )
    
    # --- CV upload ---
    cv_file = st.sidebar.file_uploader(
        "Upload your CV",
        type=["pdf", "docx"],
        help="Upload your CV in PDF or DOCX format",
        key="cv_file"
    )
    
    # --- Reset Button ---
    st.sidebar.button("🔄 Reset Form", on_click=reset_form, help="Clear all fields and start over")

    # --- Input Validation ---
    def validate_inputs(domains, cv_file):
        errors = []
        if not domains or not any(d.strip() for d in domains.split(",")):
            errors.append("Please enter at least one research domain.")
        if not cv_file:
            errors.append("Please upload your CV (PDF or DOCX).")
        elif not (cv_file.name.lower().endswith('.pdf') or cv_file.name.lower().endswith('.docx')):
            errors.append("CV must be a PDF or DOCX file.")
        return errors

    # --- Environment check ---
    env_status = check_environment()
    all_env_ready = all(env_status.values())

    # --- Main dashboard ---
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        with st.container():
            st.markdown("### 🎆 Features")
            st.markdown("""
            - 🔍 Smart Professor Discovery via CSRankings
            - 🤖 AI-Powered Email Generation
            - 📊 Skill Matching & Scoring
            - 📧 Automated Gmail Integration
            - 📅 Follow-up Scheduling
            """)
            st.markdown("""
            <style>
            [data-testid="stMarkdown"] ul {
                padding-left: 1.5rem !important;
                margin: 0.5rem 0 !important;
            }
            [data-testid="stMarkdown"] li {
                margin: 0.5rem 0 !important;
                color: #2c3e50 !important;
            }
            </style>
            """, unsafe_allow_html=True)
    with col2:
        with st.container():
            st.markdown("### ✅ System Status")
            if all_env_ready:
                st.markdown("<p style='color: #28a745; font-weight: bold;'>All systems operational!</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #dc3545; font-weight: bold;'>Configuration needed</p>", unsafe_allow_html=True)
    with col3:
        with st.container():
            ready_count = sum(env_status.values())
            total_count = len(env_status)
            st.markdown("### 📈 Ready")
            st.markdown(f"## {ready_count}/{total_count}")
            st.caption("Components")

    # --- Environment details in sidebar ---
    st.sidebar.header("🔧 Environment Setup")
    for var, status in env_status.items():
        icon = "✅" if status else "❌"
        st.sidebar.write(f"{icon} {var.replace('_', ' ').title()}")

    # --- Campaign Launch Section ---
    if all_env_ready:
        st.markdown("""
        <style>
        .campaign-container {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            color: white !important;
        }
        .campaign-container h2, .campaign-container p {
            color: white !important;
        }
        </style>
        <div class="campaign-container">
            <h2 style="margin: 0 0 1rem 0;">🚀 Ready to Launch Campaign!</h2>
            <p style="margin: 0; font-size: 1.1rem;">All systems are configured and ready for your Winter '25-'26 internship outreach</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin: 2rem 0;">
            <h2>⚙️ Configuration Required</h2>
            <p>Please complete your environment setup to launch campaigns</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Campaign Configuration Section ---
    st.header("🎯 Campaign Configuration")
    col1, col2 = st.columns([3, 2])
    with col1:
        # Campaign preview with better styling
        if domains and cv_file:
            domains_list = [d.strip() for d in domains.split(',') if d.strip()]
            st.markdown("""
            <div class="metric-card">
                <h4>📊 Campaign Preview</h4>
            </div>
            """, unsafe_allow_html=True)
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            with metric_col1:
                st.metric("🌍 Country", country)
            with metric_col2:
                st.metric("👨‍🏫 Professors", top_n)
            with metric_col3:
                st.metric("🔬 Domains", len(domains_list))
            with metric_col4:
                st.metric("📄 CV", "✅ Ready" if cv_file else "❌ Missing")
            st.success(f"🎯 Targeting professors in {country} with research in: {', '.join(domains_list[:3])}{'...' if len(domains_list) > 3 else ''}")
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🚀 Campaign Actions</h4>
        </div>
        """, unsafe_allow_html=True)
        campaign_ready = domains and cv_file and all_env_ready
        errors = validate_inputs(domains, cv_file)
        if campaign_ready and not errors:
            if st.button(
                "🚀 Launch Winter Campaign",
                type="primary",
                use_container_width=True,
                help="Start your personalized email campaign now!"
            ):
                run_campaign(country, top_n, domains, cv_file)
        else:
            if errors:
                for err in errors:
                    st.error(err)
            st.button(
                "🚀 Launch Winter Campaign",
                disabled=True,
                use_container_width=True,
                help="Complete configuration first: Upload CV, set domains, and configure environment"
            )
        st.markdown("---")
        col_test, col_logs = st.columns(2)
        with col_test:
            if st.button("🧪 Test", use_container_width=True):
                test_configuration(country, domains, cv_file)
        with col_logs:
            if st.button("📊 Logs", use_container_width=True):
                show_send_logs()
    # --- Configuration Summary ---
    st.markdown("""
    <div class="metric-card">
        <h4>📝 Configuration Summary</h4>
        <ul>
            <li><b>Country:</b> {}</li>
            <li><b>Top N Professors:</b> {}</li>
            <li><b>Domains:</b> {}</li>
            <li><b>CV Uploaded:</b> {}</li>
        </ul>
    </div>
    """.format(country, top_n, domains if domains else 'None', 'Yes' if cv_file else 'No'), unsafe_allow_html=True)
    # --- Recent activity section ---
    st.header("📈 Recent Activity")
    show_recent_activity()

def check_environment():
    """Check if environment variables are set"""
    required_vars = [
        'GMAIL_CLIENT_ID',
        'GMAIL_CLIENT_SECRET', 
        'HUGGINGFACE_API_KEY',
        'YOUR_UNIVERSITY',
        'YOUR_DISCIPLINE'
    ]
    
    status = {}
    for var in required_vars:
        value = os.getenv(var)
        status[var] = bool(value and value.strip())
    
    return status

def run_campaign(country, top_n, domains, cv_file):
    """Run the email campaign with enhanced progress tracking (CSV-based) and professor preview/filtering."""
    progress_container = st.container()
    with progress_container:
        st.markdown("""
        <div class="campaign-card">
            <h3>🚀 Campaign Launch in Progress</h3>
            <p>Sit back and relax while we handle your outreach!</p>
        </div>
        """, unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        # Step 1: Fetch professors (CSV-based)
        status_text.text("🔍 Step 1/5: Discovering professors...")
        progress_bar.progress(10)
        
        # First check if we have professors data
        try:
            contacts = parse_csv_professors(country, top_n * 2)  # Overcollect for filtering
            if not contacts:
                st.error("❌ No professors found. Please try a different country or check your CSV files.")
                return
            st.success(f"✅ Discovered {len(contacts)} professors from top universities")
        except Exception as e:
            st.error(f"❌ Error loading professor data: {str(e)}")
            st.info("ℹ️ Make sure you have the required CSV files in the data/ directory.")
            return
            
        # Step 2: Preview and filter professors
        status_text.text("👀 Step 2/5: Preview and filter professors...")
        progress_bar.progress(25)
        
        # Convert to DataFrame and handle missing data
        df = pd.DataFrame(contacts)
        
        # Ensure required columns exist
        for col in ['name', 'affiliation', 'email', 'profile_url']:
            if col not in df.columns:
                df[col] = ''
        
        # Add filtering widgets in a container
        with st.container():
            st.markdown("### 👨‍🏫 Professor Preview & Filtering")
            
            # Create two columns for filters
            col1, col2 = st.columns(2)
            
            with col1:
                min_score = st.slider(
                    "Minimum Match Score", 
                    min_value=0.0, 
                    max_value=1.0, 
                    value=0.2, 
                    step=0.05,
                    help="Filter professors by minimum match score"
                )
                
            with col2:
                require_email = st.checkbox(
                    "Only show professors with email", 
                    value=True,
                    help="Only show professors with valid email addresses"
                )
            
            affiliation_search = st.text_input(
                "Search by Affiliation (optional)", 
                value="",
                help="Filter by university or institution name"
            )
            
            # Compute match scores for preview
            from utils.prof_profile_parser import parse_profile
            from utils.skill_matcher import match_skills
            
            domains_list = [d.strip() for d in domains.split(',') if d.strip()]
            match_scores = []
            
            # Show progress for match score calculation
            progress_text = st.empty()
            progress_bar_2 = st.progress(0)
            
            for i, prof in enumerate(contacts):
                progress_text.text(f"🔍 Analyzing professor {i+1}/{len(contacts)}...")
                progress_bar_2.progress((i + 1) / len(contacts))
                try:
                    prof_profile = parse_profile(prof.get('profile_url', ''))
                    score = match_skills(domains_list, prof_profile.get('keywords', []))
                    match_scores.append(score)
                except Exception as e:
                    match_scores.append(0.0)  # Default score if parsing fails
            
            progress_text.empty()
            progress_bar_2.empty()
            
            # Add scores to dataframe
            df['match_score'] = match_scores
            
            # Debug: Show all professors before filtering
            with st.expander("🔍 Debug: All Professors (Before Filtering)", expanded=False):
                st.write("Raw professor data before filtering:")
                st.dataframe(df[['name', 'affiliation', 'email', 'match_score']])
            
            # Apply filters with debug info
            filtered_df = df.copy()
            
            # Debug: Show filter stats
            st.sidebar.write("### 🔍 Filter Stats")
            st.sidebar.write(f"Total professors: {len(df)}")
            
            # Apply match score filter
            if min_score > 0:
                filtered_df = filtered_df[filtered_df['match_score'] >= min_score]
                st.sidebar.write(f"After match score filter (≥{min_score}): {len(filtered_df)}")
            
            # Apply email filter
            if require_email:
                email_filter = filtered_df['email'].notna() & (filtered_df['email'] != '') & filtered_df['email'].str.contains('@', na=False)
                st.sidebar.write(f"Professors with valid emails: {email_filter.sum()}")
                filtered_df = filtered_df[email_filter]
            
            # Apply affiliation search
            if affiliation_search:
                affil_filter = filtered_df['affiliation'].str.contains(affiliation_search, case=False, na=False)
                st.sidebar.write(f"Professors matching affiliation: {affil_filter.sum()}")
                filtered_df = filtered_df[affil_filter]
            
            # Display filtered results with more context
            if len(filtered_df) == 0:
                st.warning("""
                ⚠️ No professors match your current filters. Try:
                - Lowering the minimum match score
                - Removing the email requirement
                - Broadening your affiliation search
                - Checking the debug section below for raw data
                """)
                
                # Show why professors might be filtered out
                if len(df) > 0:
                    st.error("""
                    Possible reasons for no matches:
                    1. No professors have a match score ≥ {}
                    2. Email requirement is filtering out all professors
                    3. Affiliation search is too specific
                    
                    Check the debug section above to see the raw professor data.
                    """.format(min_score))
                return
                
            # Show summary of filtered results
            st.success(f"✅ Found {len(filtered_df)} professors matching your criteria")
            
            # Display professors in an expandable table
            with st.expander("👥 View Matching Professors", expanded=True):
                st.dataframe(
                    filtered_df[['name', 'affiliation', 'email', 'match_score']].sort_values(
                        'match_score', ascending=False
                    ),
                    use_container_width=True,
                    column_config={
                        "name": "Name",
                        "affiliation": "Institution",
                        "email": "Email",
                        "match_score": st.column_config.NumberColumn(
                            "Match Score",
                            format="%.2f",
                            help="How well the professor's research matches your interests"
                        )
                    },
                    hide_index=True
                )
            
            # Let user select professors
            st.markdown("### 🎯 Select Professors for Outreach")
            
            # Create checkboxes for each professor
            selected_indices = []
            for idx, row in filtered_df.iterrows():
                col1, col2, col3 = st.columns([1, 3, 2])
                with col1:
                    selected = st.checkbox(
                        "", 
                        value=True,  # Default to selected
                        key=f"prof_{idx}",
                        label_visibility="collapsed"
                    )
                with col2:
                    st.markdown(f"**{row['name']}**  \n*{row['affiliation']}*")
                with col3:
                    st.markdown(f"📧 {row['email']}  \n🔍 Match: {row['match_score']:.2f}")
                
                if selected:
                    selected_indices.append(idx)
            
            if not selected_indices:
                st.warning("⚠️ Please select at least one professor to continue.")
                st.stop()
                
            selected_contacts = filtered_df.loc[selected_indices].to_dict(orient='records')
            st.success(f"✅ {len(selected_contacts)} professors selected for outreach.")
            
            # Add a confirmation step
            if not st.button("🚀 Confirm and Continue", type="primary"):
                st.stop()
        st.success(f"✅ {len(selected_contacts)} professors selected for outreach.")
        # Step 3: Generate emails
        status_text.text("🤖 Step 3/5: AI generating personalized emails...")
        progress_bar.progress(50)
        cv_bytes = cv_file.read()
        cv_filename = cv_file.name
        drafts = generate_emails(selected_contacts, domains, cv_bytes, cv_filename)
        if not drafts:
            st.warning("⚠️ No emails generated. This might be due to low match scores or API issues.")
            return
        st.success(f"✅ Generated {len(drafts)} personalized emails with skill matching")
        # Step 4: Send emails
        status_text.text("📧 Step 4/5: Sending emails via Gmail...")
        progress_bar.progress(75)
        results = send_emails(drafts)
        # Step 5: Complete
        status_text.text("🎉 Step 5/5: Campaign complete!")
        progress_bar.progress(100)
        sent_count = sum(1 for r in results if r.get('status') == 'sent')
        failed_count = len(results) - sent_count
        if sent_count > 0:
            st.balloons()
            st.success(f"🎉 Campaign Complete! Successfully sent {sent_count} emails!")
            if failed_count > 0:
                st.warning(f"⚠️ {failed_count} emails failed to send - check logs for details")
        else:
            st.error("❌ No emails were sent. Check the logs for details.")
        st.subheader("📊 Campaign Results")
        results_data = []
        for i, (draft, result) in enumerate(zip(drafts, results)):
            results_data.append({
                "Professor": draft.get('name', 'Unknown'),
                "Email": draft.get('to', ''),
                "Match Score": f"{draft.get('match_score', 0):.2f}",
                "Status": result.get('status', 'unknown'),
                "Error": result.get('error', '')[:50] + '...' if result.get('error') else ''
            })
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True)
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name=f"internmailer_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"❌ Error running campaign: {str(e)}")

def test_configuration(country, domains, cv_file):
    """Test the configuration with a small sample (CSV-based)"""
    try:
        with st.spinner("🧪 Testing configuration..."):
            # Test with just 2 professors
            test_contacts = parse_csv_professors(country, 2)
            if not test_contacts:
                st.error("❌ Test failed: No professors found")
                return
            if cv_file:
                cv_bytes = cv_file.read()
                cv_filename = cv_file.name
                test_drafts = generate_emails(test_contacts, domains, cv_bytes, cv_filename)
                if test_drafts:
                    st.success(f"✅ Test successful! Generated {len(test_drafts)} test emails")
                    if test_drafts:
                        st.subheader("📧 Email Preview")
                        preview_draft = test_drafts[0]
                        st.write(f"**To:** {preview_draft.get('name')} ({preview_draft.get('to')})")
                        st.write(f"**Subject:** {preview_draft.get('subject')}")
                        st.write(f"**Match Score:** {preview_draft.get('match_score', 0):.2f}")
                        with st.expander("View Email Body"):
                            st.text(preview_draft.get('body', ''))
                else:
                    st.warning("⚠️ Test generated 0 emails. Check your domains or try different professors.")
            else:
                st.error("❌ Please upload a CV file for testing")
    except Exception as e:
        st.error(f"❌ Test failed: {str(e)}")

def show_send_logs():
    """Display send logs"""
    try:
        logs = get_send_log()
        
        if not logs:
            st.info("📝 No send logs found. Run a campaign first.")
            return
        
        st.subheader("📊 Email Send Logs")
        
        # Convert to DataFrame
        logs_df = pd.DataFrame(logs)
        
        # Format timestamp
        if 'timestamp' in logs_df.columns:
            logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sent = len(logs_df[logs_df['status'].str.contains('sent', na=False)])
            st.metric("📧 Total Sent", total_sent)
        
        with col2:
            total_failed = len(logs_df[logs_df['status'] == 'failed'])
            st.metric("❌ Failed", total_failed)
        
        with col3:
            if len(logs_df) > 0:
                avg_match_score = pd.to_numeric(logs_df['match_score'], errors='coerce').mean()
                st.metric("🎯 Avg Match Score", f"{avg_match_score:.2f}")
        
        with col4:
            unique_days = logs_df['timestamp'].str[:10].nunique() if 'timestamp' in logs_df.columns else 0
            st.metric("📅 Active Days", unique_days)
        
        # Display logs table
        st.dataframe(logs_df, use_container_width=True)
        
        # Download logs
        csv = logs_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Logs CSV",
            data=csv,
            file_name=f"send_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"❌ Error loading logs: {str(e)}")

def show_recent_activity():
    """Show recent activity summary"""
    try:
        logs = get_send_log()
        
        if not logs:
            st.info("📝 No recent activity. Run your first campaign to see activity here.")
            return
        
        # Get recent logs (last 7 days)
        logs_df = pd.DataFrame(logs)
        
        if 'timestamp' in logs_df.columns:
            logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
            recent_logs = logs_df[logs_df['timestamp'] > (datetime.now() - pd.Timedelta(days=7))]
            
            if len(recent_logs) > 0:
                st.write(f"📊 **Last 7 days:** {len(recent_logs)} emails sent")
                
                # Show recent emails
                recent_summary = recent_logs.groupby('status').size().to_dict()
                
                for status, count in recent_summary.items():
                    if 'sent' in status:
                        st.write(f"✅ {count} sent")
                    elif 'failed' in status:
                        st.write(f"❌ {count} failed")
            else:
                st.write("📊 No activity in the last 7 days")
        
    except Exception as e:
        st.write(f"❌ Error loading recent activity: {str(e)}")

if __name__ == "__main__":
    main()
