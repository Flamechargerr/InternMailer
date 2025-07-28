import streamlit as st
import os
import pandas as pd
import sys
from datetime import datetime
import time
import json
from dotenv import load_dotenv

# Add src to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scheduler'))

from email_generator import EmailGenerator
from gmail_sender import GmailSender
from resume_parser import ResumeParser
from streamlit_api import get_followup_manager

load_dotenv()

# Initialize session state
if 'selected_professors' not in st.session_state:
    st.session_state.selected_professors = []
if 'generated_emails' not in st.session_state:
    st.session_state.generated_emails = {}
if 'sending_status' not in st.session_state:
    st.session_state.sending_status = {}

# Enhanced styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .professor-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        transition: all 0.2s ease;
    }
    .professor-card:hover {
        background: #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📧 Message Professor</h1>
    <p>Compose and send personalized emails to selected professors</p>
</div>
""", unsafe_allow_html=True)

# Configuration validation
def check_gmail_config():
    """Check if Gmail configuration is set up"""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    return gmail_user and gmail_password

# Load professor data
@st.cache_data
def load_professors_df():
    """Load professor data with caching and error handling"""
    try:
        # Read CSV with error handling for malformed lines
        df = pd.read_csv('data/proffesor.csv', on_bad_lines='skip', encoding='utf-8', 
                       names=['University', 'Name', 'Email', 'Homepage', 'Research Area'], 
                       header=None, skiprows=1)
        
        # Clean the data
        df = df.dropna(subset=['Email'])  # Remove rows with missing emails
        df = df[df['Email'].str.contains('@', na=False)]  # Only keep valid email formats
        df = df[df['University'] != 'University']  # Remove duplicate headers
        df = df[df['Email'] != 'Email']  # Remove duplicate headers
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip()
        
        st.success(f"✅ Loaded {len(df)} professors from database")
        return df
        
    except FileNotFoundError:
        st.error("❌ Professor database not found at 'data/proffesor.csv'")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading professor database: {e}")
        return pd.DataFrame()

# Load data
professors_df = load_professors_df()

if professors_df.empty:
    st.stop()

# 1. Search/Filter Section
st.header("🔍 1. Search & Filter Professors")

col1, col2 = st.columns(2)

with col1:
    # Text search
    search_query = st.text_input(
        "🔍 Search by name, university, or research area",
        placeholder="e.g., machine learning, Stanford, John Smith",
        help="Enter keywords to filter professors by name, university, or research area",
        label_visibility="visible"
    )
    
    # University filter
    universities = ['All'] + sorted(professors_df['University'].dropna().unique().tolist())
    selected_university = st.selectbox("🏛️ Filter by University", universities)

with col2:
    # Research area filter
    research_areas = ['All'] + sorted(professors_df['Research Area'].dropna().unique().tolist())
    selected_research_area = st.selectbox("🔬 Filter by Research Area", research_areas)
    
    # Country filter (if available)
    if 'Country' in professors_df.columns:
        countries = ['All'] + sorted(professors_df['Country'].dropna().unique().tolist())
        selected_country = st.selectbox("🌍 Filter by Country", countries)
    else:
        selected_country = 'All'

# Apply filters
filtered_df = professors_df.copy()

# Apply text search
if search_query:
    search_mask = (
        filtered_df['Name'].str.contains(search_query, case=False, na=False) |
        filtered_df['University'].str.contains(search_query, case=False, na=False) |
        filtered_df['Research Area'].str.contains(search_query, case=False, na=False)
    )
    filtered_df = filtered_df[search_mask]

# Apply university filter
if selected_university != 'All':
    filtered_df = filtered_df[filtered_df['University'] == selected_university]

# Apply research area filter
if selected_research_area != 'All':
    filtered_df = filtered_df[filtered_df['Research Area'] == selected_research_area]

# Apply country filter
if selected_country != 'All' and 'Country' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Country'] == selected_country]

st.info(f"📊 Found {len(filtered_df)} professors matching your criteria")

# 2. Professor Selection Section
st.header("👥 2. Select Recipients")

if len(filtered_df) == 0:
    st.warning("⚠️ No professors found with the current filters. Please adjust your search criteria.")
    st.stop()

# Bulk selection options
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("✅ Select All"):
        st.session_state.selected_professors = filtered_df.index.tolist()
        st.rerun()

with col2:
    if st.button("❌ Deselect All"):
        st.session_state.selected_professors = []
        st.rerun()

with col3:
    max_select = st.number_input("Max to select", min_value=1, max_value=len(filtered_df), value=min(10, len(filtered_df)))
    if st.button(f"🎯 Select First {max_select}"):
        st.session_state.selected_professors = filtered_df.head(max_select).index.tolist()
        st.rerun()

# Display professors with checkboxes
st.subheader(f"Select from {len(filtered_df)} professors:")

# Pagination for large datasets
items_per_page = 20
if len(filtered_df) > items_per_page:
    page_num = st.selectbox("📄 Page", range(1, (len(filtered_df) // items_per_page) + 2))
    start_idx = (page_num - 1) * items_per_page
    end_idx = start_idx + items_per_page
    display_df = filtered_df.iloc[start_idx:end_idx]
else:
    display_df = filtered_df

# Create selection checkboxes
for idx, row in display_df.iterrows():
    col1, col2 = st.columns([0.1, 0.9])
    
    with col1:
        is_selected = st.checkbox("Select", key=f"select_{idx}", value=idx in st.session_state.selected_professors, label_visibility="visible")
        
        if is_selected and idx not in st.session_state.selected_professors:
            st.session_state.selected_professors.append(idx)
        elif not is_selected and idx in st.session_state.selected_professors:
            st.session_state.selected_professors.remove(idx)
    
    with col2:
        with st.container():
            st.markdown(f"""
            **{row['Name']}** | {row['University']}
            
            📧 {row.get('Email', 'No email')} | 🔬 {row['Research Area']}
            """)

selected_count = len(st.session_state.selected_professors)
if selected_count > 0:
    st.success(f"✅ {selected_count} professor(s) selected")
else:
    st.info("ℹ️ No professors selected yet")

# 3. Email Composition Section
st.header("✍️ 3. Compose Email")

if selected_count == 0:
    st.warning("⚠️ Please select at least one professor to compose emails")
    st.stop()

# Resume selection for email generation
st.subheader("📄 Resume for Personalization")
resume_files = []
if os.path.exists('resumes'):
    resume_files = [f for f in os.listdir('resumes') if f.endswith('.pdf')]

if resume_files:
    selected_resume = st.selectbox("Select resume for personalization", resume_files)
    resume_path = os.path.join('resumes', selected_resume)
    st.success(f"✅ Using resume: {selected_resume}")
else:
    st.warning("⚠️ No resumes found in 'resumes' folder. Upload a resume in the Outreach page first.")
    resume_path = None

# Email template selection
email_style = st.radio(
    "📝 Email Style",
    ["Professional (Formal)", "Engaging (Semi-formal)", "Custom"],
    help="Choose the tone and style for your emails"
)

# Generate prefilled content using EmailGenerator
if resume_path and selected_count > 0:
    if st.button("🎯 Generate Personalized Content"):
        with st.spinner("Generating personalized emails..."):
            try:
                # Parse resume
                parser = ResumeParser(resume_path)
                student_info = parser.parse()
                student_info['name'] = "Anamay Tripathy"
                student_info['email'] = "tripathy.anamay23@gmail.com"
                student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
                
                # Initialize EmailGenerator
                email_gen = EmailGenerator(
                    student_info, 
                    use_azure_ai=True,  # Use Azure AI for better results
                    azure_ai_model='openai/gpt-4.1'
                )
                
                # Generate emails for each selected professor
                st.session_state.generated_emails = {}
                selected_profs = professors_df.loc[st.session_state.selected_professors]
                
                progress_bar = st.progress(0)
                for i, (idx, prof) in enumerate(selected_profs.iterrows()):
                    prof_dict = prof.to_dict()
                    
                    # Generate subject and body
                    informal = email_style == "Engaging (Semi-formal)"
                    subject = email_gen.generate_subject(prof_dict, informal=informal)
                    
                    try:
                        # Try LLM generation first, fallback to template
                        body = email_gen.generate_with_llm(prof_dict, informal=informal)
                        if not body or body.strip() == "":
                            body = email_gen.generate_body(prof_dict, informal=informal)
                    except:
                        body = email_gen.generate_body(prof_dict, informal=informal)
                    
                    st.session_state.generated_emails[idx] = {
                        'subject': subject,
                        'body': body,
                        'professor': prof_dict
                    }
                    
                    progress_bar.progress((i + 1) / len(selected_profs))
                
                st.success(f"✅ Generated {len(st.session_state.generated_emails)} personalized emails!")
                
            except Exception as e:
                st.error(f"❌ Error generating emails: {e}")

# Email subject and body inputs
st.subheader("📝 Email Content")

# Common subject (can be overridden per professor)
if st.session_state.generated_emails:
    # Use first generated subject as default
    first_email = list(st.session_state.generated_emails.values())[0]
    default_subject = first_email['subject']
    default_body = first_email['body']
else:
    default_subject = f"Research Internship Inquiry - {selected_research_area if selected_research_area != 'All' else 'Your Research'}"
    default_body = """Dear Professor [Name],

I hope this email finds you well. I am writing to express my interest in your research in [Research Area].

[Your personalized message here]

I have attached my resume for your review and would welcome the opportunity to discuss potential research opportunities.

Thank you for your time and consideration.

Best regards,
Anamay Tripathy"""

common_subject = st.text_input(
    "📧 Email Subject (will be used for all selected professors)",
    value=default_subject,
    help="This subject will be used for all emails unless customized individually",
    label_visibility="visible"
)

common_body = st.text_area(
    "📝 Email Body Template",
    value=default_body,
    height=300,
    help="Use [Name], [University], [Research Area] as placeholders that will be replaced for each professor",
    label_visibility="visible"
)

# Resume attachment option
attach_resume = st.checkbox("📎 Attach Resume", value=True, help="Attach your resume to the emails", label_visibility="visible")

# 4. Send Section
st.header("🚀 4. Send Emails")

# Gmail configuration check
if not check_gmail_config():
    st.error("❌ Gmail configuration not found. Please set GMAIL_USER and GMAIL_APP_PASSWORD in your .env file")
    st.stop()

# Preview section
with st.expander("👁️ Preview Emails (First 3)", expanded=False):
    preview_count = min(3, selected_count)
    selected_profs = professors_df.loc[st.session_state.selected_professors[:preview_count]]
    
    for i, (idx, prof) in enumerate(selected_profs.iterrows()):
        st.subheader(f"Email {i+1}: {prof['Name']}")
        
        # Replace placeholders in template
        preview_subject = common_subject.replace('[Name]', prof['Name'])
        preview_subject = preview_subject.replace('[Research Area]', prof['Research Area'])
        
        preview_body = common_body.replace('[Name]', prof['Name'])
        preview_body = preview_body.replace('[University]', prof['University'])  
        preview_body = preview_body.replace('[Research Area]', prof['Research Area'])
        
        st.text_area(f"Subject {i+1}", preview_subject, disabled=True, key=f"preview_subject_{i}")
        st.text_area(f"Body {i+1}", preview_body, height=200, disabled=True, key=f"preview_body_{i}")
        
        if i < preview_count - 1:
            st.divider()

# Send mode selection
send_mode = st.radio(
    "📤 Send Mode",
    ["Dry Run (Preview Only)", "Live Send"],
    help="Dry Run will show what would be sent without actually sending emails"
)

# Rate limiting warning
if send_mode == "Live Send":
    st.warning(f"⚠️ You are about to send {selected_count} emails. There will be a 2-5 second delay between each email to respect rate limits.")

# Send button
if st.button("🚀 Send Emails", type="primary", disabled=selected_count == 0):
    # Initialize Gmail sender
    try:
        gmail_sender = GmailSender(
            user=os.getenv('GMAIL_USER'),
            app_password=os.getenv('GMAIL_APP_PASSWORD'),
            log_path='followup_log.csv'  # Write to Follow-up log as requested
        )
    except Exception as e:
        st.error(f"❌ Failed to initialize Gmail sender: {e}")
        st.stop()
    
    # Initialize follow-up manager for logging
    try:
        followup_manager = get_followup_manager()
    except Exception as e:
        st.warning(f"⚠️ Follow-up manager not available: {e}")
        followup_manager = None
    
    # Process each selected professor
    selected_profs = professors_df.loc[st.session_state.selected_professors]
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    success_count = 0
    error_count = 0
    
    for i, (idx, prof) in enumerate(selected_profs.iterrows()):
        status_container.info(f"📧 Processing {i+1}/{selected_count}: {prof['Name']}")
        
        # Prepare email content
        email_subject = common_subject.replace('[Name]', prof['Name'])
        email_subject = email_subject.replace('[Research Area]', prof['Research Area'])
        
        email_body = common_body.replace('[Name]', prof['Name'])
        email_body = email_body.replace('[University]', prof['University'])
        email_body = email_body.replace('[Research Area]', prof['Research Area'])
        
        # Determine attachment path
        attachment_path = resume_path if attach_resume and resume_path else None
        
        if send_mode == "Dry Run (Preview Only)":
            # Just log the attempt
            st.session_state.sending_status[idx] = "dry_run"
            success_count += 1
            
            # Show preview
            with st.expander(f"📧 Dry Run - {prof['Name']}"):
                st.write(f"**To:** {prof.get('Email', 'No email')}")
                st.write(f"**Subject:** {email_subject}")
                st.write(f"**Attachment:** {'Yes' if attachment_path else 'No'}")
                st.text_area("Body Preview", email_body, height=150, key=f"dry_run_body_{i}")
        
        else:  # Live Send
            try:
                # Send the email
                success = gmail_sender.send_email(
                    to_email=prof.get('Email', ''),
                    subject=email_subject,
                    body=email_body,
                    attachment_path=attachment_path
                )
                
                if success:
                    st.session_state.sending_status[idx] = "sent"
                    success_count += 1
                    
                    # Create toast notification with details
                    st.toast(f"✅ Email sent to {prof['Name']} at {prof.get('University', 'Unknown')}!", icon="✅")
                    
                    # Log to follow-up system if available
                    if followup_manager:
                        try:
                            # Create campaign if it doesn't exist
                            campaign_name = "Manual Professor Messaging"
                            campaign_id = followup_manager.create_campaign(
                                campaign_name, 
                                "Manually sent emails to professors"
                            )
                            
                            followup_manager.log_email_sent(
                                campaign_id=campaign_id,
                                email=prof.get('Email', ''),
                                subject=email_subject
                            )
                        except Exception as e:
                            st.warning(f"⚠️ Could not log to follow-up system: {e}")
                
                else:
                    st.session_state.sending_status[idx] = "failed"
                    error_count += 1
                    st.toast(f"❌ Failed to send email to {prof['Name']} - Check logs for details", icon="❌")
                    
            except Exception as e:
                st.session_state.sending_status[idx] = "error"
                error_count += 1
                st.toast(f"❌ Error sending to {prof['Name']}: {str(e)[:50]}...", icon="❌")
        
        # Update progress
        progress_bar.progress((i + 1) / selected_count)
        
        # Rate limiting for live sends
        if send_mode == "Live Send" and i < selected_count - 1:
            time.sleep(2)  # 2 second delay between emails
    
    # Final status
    progress_bar.progress(1.0)
    
    if send_mode == "Dry Run (Preview Only)":
        status_container.success(f"✅ Dry run completed! {success_count} emails would be sent.")
    else:
        if error_count == 0:
            status_container.success(f"🎉 All {success_count} emails sent successfully!")
        else:
            status_container.warning(f"⚠️ Completed: {success_count} sent, {error_count} failed")

# 5. Status Display Section
if st.session_state.sending_status:
    st.header("📊 5. Sending Status")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    status_counts = {}
    for status in st.session_state.sending_status.values():
        status_counts[status] = status_counts.get(status, 0) + 1
    
    with col1:
        st.metric("✅ Sent", status_counts.get('sent', 0))
    with col2:
        st.metric("🔍 Dry Run", status_counts.get('dry_run', 0))
    with col3:
        st.metric("❌ Failed", status_counts.get('failed', 0) + status_counts.get('error', 0))
    
    # Detailed status
    if st.checkbox("Show detailed status"):
        for idx, status in st.session_state.sending_status.items():
            if idx in professors_df.index:
                prof = professors_df.loc[idx]
                status_emoji = {"sent": "✅", "dry_run": "🔍", "failed": "❌", "error": "❌"}
                emoji = status_emoji.get(status, "❓")
                st.write(f"{emoji} **{prof['Name']}** ({prof['University']}) - {status}")

# Footer with tips
st.markdown("---")
st.info("""
💡 **Tips:**
- Use the search and filters to target specific professors
- Generate personalized content for better response rates  
- Always test with Dry Run first
- Check the Follow-ups page to track responses and schedule follow-ups
""")
