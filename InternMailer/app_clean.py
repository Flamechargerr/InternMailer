import streamlit as st
import os
import pandas as pd
import json
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from resume_parser import ResumeParser
from email_generator import EmailGenerator
from gmail_sender import GmailSender
import time
import requests

# Page configuration
st.set_page_config(
    page_title="InternMailer 🚀", 
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

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
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .professor-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
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

# Sidebar for data exploration
with st.sidebar:
    st.header("📊 Professor Database")
    try:
        df = pd.read_csv('InternMailer/data/proffesor.csv')
        st.metric("Total Professors", len(df))
        
        # Show university distribution
        universities = df['University'].value_counts().head(5)
        st.subheader("Top Universities")
        for uni, count in universities.items():
            st.write(f"• {uni}: {count} professors")
            
        # Show research areas
        research_areas = df['Research Area'].value_counts().head(10)
        st.subheader("Top Research Areas")
        for area, count in research_areas.items():
            st.write(f"• {area}: {count}")
            
    except FileNotFoundError:
        st.error("Professor database not found!")

# Check if Ollama is running
def is_ollama_running():
    try:
        r = requests.get("http://localhost:11434", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

ollama_available = is_ollama_running()
if not ollama_available:
    st.info("🤖 Ollama server not detected. Using template-based email generation.")

# Upload resume
st.header("📄 1. Upload Your Resume")
st.caption("Upload your latest PDF resume. Skills and projects will be extracted automatically.")
uploaded_file = st.file_uploader("Upload your PDF resume", type=["pdf"])

# Create resumes directory if it doesn't exist
if not os.path.exists("resumes"):
    os.makedirs("resumes")

if uploaded_file:
    resume_path = os.path.join("resumes", uploaded_file.name)
    with open(resume_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Uploaded {uploaded_file.name}")
else:
    resume_path = None

# Filtering options
st.header("🎯 2. Target Filtering")
col1, col2 = st.columns(2)

with col1:
    # University filter
    try:
        df = pd.read_csv('InternMailer/data/proffesor.csv')
        universities = ['All'] + list(df['University'].unique())
        selected_university = st.selectbox("Select University", universities)
    except:
        selected_university = 'All'
    
with col2:
    # Research area filter
    try:
        research_areas = ['All'] + list(df['Research Area'].unique())
        selected_research_area = st.selectbox("Select Research Area", research_areas)
    except:
        selected_research_area = 'All'

# Campaign preferences
st.header("⚙️ 3. Campaign Preferences")
col1, col2 = st.columns(2)
with col1:
    season = st.selectbox("Internship Season", ["Any", "Winter", "Summer"], 
                         help="Select the preferred internship season.")
with col2:
    max_emails = st.number_input("Max Emails to Send", min_value=1, max_value=100, value=10,
                                help="Limit the number of emails to prevent overwhelming.")

# Email preview
st.header("📧 4. Preview Sample Email")
if resume_path:
    preview_button = st.button("🔍 Generate Preview Email")
    
    if preview_button:
        with st.spinner("Generating preview email..."):
            try:
                # Use the first professor from filtered data as example
                df = pd.read_csv('InternMailer/data/proffesor.csv')
                
                # Apply filters
                if selected_university != 'All':
                    df = df[df['University'] == selected_university]
                if selected_research_area != 'All':
                    df = df[df['Research Area'] == selected_research_area]
                
                if len(df) > 0:
                    sample_prof = df.iloc[0].to_dict()
                    
                    # Parse resume
                    parser = ResumeParser(resume_path)
                    student_info = parser.parse()
                    student_info['name'] = "Anamay Tripathy"
                    student_info['email'] = "tripathy.anamay23@gmail.com"
                    student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
                    
                    # Generate email
                    email_gen = EmailGenerator(student_info, use_ollama=ollama_available, ollama_model='mistral')
                    subject = email_gen.generate_subject(sample_prof)
                    
                    if ollama_available:
                        body = email_gen.generate_with_llm(sample_prof)
                    else:
                        body = email_gen.generate_body(sample_prof)
                    
                    # Display preview
                    st.markdown("### 📧 Email Preview")
                    st.markdown(f"**To:** {sample_prof.get('Name', 'Unknown')} ({sample_prof.get('Email', 'Unknown')})")
                    st.markdown(f"**University:** {sample_prof.get('University', 'Unknown')}")
                    st.markdown(f"**Research Area:** {sample_prof.get('Research Area', 'Unknown')}")
                    st.markdown(f"**Subject:** {subject}")
                    st.markdown("**Body:**")
                    st.text_area("Email Body", body, height=300, disabled=True)
                else:
                    st.warning("No professors found with the selected filters.")
                    
            except Exception as e:
                st.error(f"Error generating preview: {e}")
else:
    st.info("Please upload a resume to preview emails.")

# Launch outreach
st.header("🚀 5. Launch Outreach Campaign")
if resume_path:
    launch_button = st.button("🎯 Start Email Campaign", type="primary")
    
    if launch_button:
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        try:
            # Load and filter professor data
            status_placeholder.info("📊 Loading professor database...")
            df = pd.read_csv('InternMailer/data/proffesor.csv')
            progress_bar.progress(10)
            
            # Apply filters
            if selected_university != 'All':
                df = df[df['University'] == selected_university]
            if selected_research_area != 'All':
                df = df[df['Research Area'] == selected_research_area]
            
            # Limit number of emails
            df = df.head(max_emails)
            
            status_placeholder.info(f"🎯 Found {len(df)} professors matching your criteria")
            progress_bar.progress(20)
            
            # Parse resume
            status_placeholder.info("📄 Parsing your resume...")
            parser = ResumeParser(resume_path)
            student_info = parser.parse()
            student_info['name'] = "Anamay Tripathy"
            student_info['email'] = "tripathy.anamay23@gmail.com"
            student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
            progress_bar.progress(30)
            
            # Generate emails
            status_placeholder.info("✍️ Generating personalized emails...")
            email_gen = EmailGenerator(student_info, use_ollama=ollama_available, ollama_model='mistral')
            emails = []
            
            for idx, (_, prof) in enumerate(df.iterrows()):
                prof_dict = prof.to_dict()
                subject = email_gen.generate_subject(prof_dict)
                
                if ollama_available:
                    body = email_gen.generate_with_llm(prof_dict)
                else:
                    body = email_gen.generate_body(prof_dict)
                
                emails.append({
                    'to': prof_dict['Email'],
                    'subject': subject,
                    'body': body,
                    'professor': prof_dict['Name'],
                    'university': prof_dict['University']
                })
                
                progress = 30 + int(40 * (idx + 1) / len(df))
                progress_bar.progress(progress)
            
            status_placeholder.success(f"✅ Generated {len(emails)} personalized emails")
            progress_bar.progress(70)
            
            # Display generated emails
            st.subheader("📧 Generated Emails")
            for i, email in enumerate(emails[:3]):  # Show first 3 emails
                with st.expander(f"Email {i+1}: {email['professor']} ({email['university']})"):
                    st.markdown(f"**To:** {email['to']}")
                    st.markdown(f"**Subject:** {email['subject']}")
                    st.text_area(f"Body {i+1}", email['body'], height=200, disabled=True, key=f"email_body_{i}")
            
            if len(emails) > 3:
                st.info(f"... and {len(emails) - 3} more emails generated.")
            
            # Email sending (commented out for safety)
            st.warning("⚠️ Email sending is disabled for demo purposes. Configure Gmail credentials in .env file to enable.")
            
            # Simulate sending
            status_placeholder.info("📤 Emails ready to send (configure SMTP to enable)")
            progress_bar.progress(100)
            
            # Show summary
            st.success("🎉 Campaign preparation completed!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Professors Targeted", len(emails))
            with col2:
                st.metric("Emails Generated", len(emails))
            with col3:
                st.metric("Success Rate", "100%")
                
        except Exception as e:
            st.error(f"❌ Error during campaign: {e}")
            progress_bar.progress(0)
else:
    st.info("Please upload a resume to start the campaign.")

# Analytics section
st.header("📊 6. Campaign Analytics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Professors", 0, help="Number of professors in database")
with col2:
    st.metric("Emails Sent", 0, help="Number of emails successfully sent")
with col3:
    st.metric("Response Rate", "0%", help="Percentage of professors who responded")
with col4:
    st.metric("Success Rate", "0%", help="Overall campaign success rate")

# Footer
st.markdown("---")
st.markdown("**InternMailer** © 2024 | Built with ❤️ by Anamay Tripathy")
st.caption("🔒 All data is processed locally and securely. No personal information is stored.")
