import streamlit as st
import os
import logging
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from resume_parser import ResumeParser
from professor_scraper import ProfessorScraper
from semantic_matcher import SemanticMatcher
from email_generator import EmailGenerator, generate_with_ollama
from gmail_sender import GmailSender
from followup_scheduler import FollowupScheduler
import requests
import csv
import pandas as pd

# --- Always show data directory contents for debugging ---
try:
    st.write("Files in InternMailer/data/:", os.listdir('InternMailer/data'))
except Exception as e:
    st.write("Error reading InternMailer/data/ directory:", e)

st.set_page_config(page_title="InternMailer", layout="wide")
load_dotenv()

st.title("InternMailer: AI-Powered Academic Outreach")

# Check if Ollama is running
def is_ollama_running():
    try:
        r = requests.get("http://localhost:11434")
        return r.status_code == 200
    except Exception:
        return False

ollama_available = is_ollama_running()
if not ollama_available:
    st.warning("Ollama server is not running. Please start Ollama with a model (e.g., 'ollama run mistral') for LLM-powered email generation. Fallback to template-based emails will be used.")

# Upload resume
st.header("1. Upload Your Resume")
st.caption("Upload your latest PDF resume. Skills and projects will be extracted automatically.")
uploaded_file = st.file_uploader("Upload your PDF resume", type=["pdf"])
if uploaded_file:
    resume_path = os.path.join("resumes", uploaded_file.name)
    with open(resume_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Uploaded {uploaded_file.name}")
else:
    resume_path = None

# Select countries (optional)
st.header("2. Select Target Countries (Optional)")
st.caption("Choose countries to target for outreach. Leave blank for global search.")
countries = ["US", "UK", "Europe", "Singapore", "Canada", "Australia", "Other"]
selected_countries = st.multiselect("Countries", countries)

# Internship season and funding preference
st.header("3. Campaign Preferences")
col1, col2 = st.columns(2)
with col1:
    season = st.selectbox("Internship Season", ["Any", "Winter", "Summer"], help="Select the preferred internship season.")
with col2:
    funding = st.selectbox("Funding Preference", ["Any", "Paid", "Unpaid"], help="Select if you prefer paid, unpaid, or any internship.")

# Add a preview email section after preferences
st.header("4. Preview Sample Email")
preview_button = st.button("Preview Email", disabled=not resume_path)
preview_email_subject = ""
preview_email_body = ""

if preview_button and resume_path:
    # Use a mock professor if no real data yet
    mock_prof = {
        "name": "Dr. Smith",
        "research_area": "Natural Language Processing",
        "season": season,
        "funding": funding
    }
    parser = ResumeParser(resume_path)
    student_info = parser.parse()
    student_info['name'] = "Anamay Tripathy"
    student_info['email'] = "tripathy.anamay23@gmail.com"
    student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
    student_info['season'] = season
    student_info['funding'] = funding
    email_gen = EmailGenerator(student_info, use_ollama=ollama_available, ollama_model='mistral')
    preview_email_subject = email_gen.generate_subject(mock_prof)
    if ollama_available:
        preview_email_body = email_gen.generate_with_llm(mock_prof)
    else:
        preview_email_body = email_gen.generate_body(mock_prof)
    with st.expander("Show Preview Email"):
        st.markdown(f"**Subject:** {preview_email_subject}")
        st.markdown("---")
        st.markdown(preview_email_body)

# Add outreach mode selection
st.header("3.5. Outreach Mode")
outreach_mode = st.radio(
    "Choose outreach strategy:",
    ["Smart Match (Recommended)", "Cold Outreach (All Professors)"]
)

# Launch outreach
st.header("4. Launch Outreach")
run_button = st.button("Start Outreach", disabled=not resume_path)

log_placeholder = st.empty()
progress_bar = st.progress(0)

# Analytics placeholders
professors_matched = 0
emails_sent = 0
response_rate = 0.0
followups_scheduled = 0

if run_button and resume_path:
    try:
        log_placeholder.write(":mag: **Parsing resume...**")
        parser = ResumeParser(resume_path)
        student_info = parser.parse()
        student_info['name'] = "Anamay Tripathy"
        student_info['email'] = "tripathy.anamay23@gmail.com"
        student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
        student_info['season'] = season
        student_info['funding'] = funding
        progress_bar.progress(10)

        log_placeholder.write(":mag: **Scraping professors from CSVs...**")
        # Use proffesor_verified_emails.csv as the data source
        professors = []
        df = pd.read_csv('InternMailer/data/proffesor_verified_emails.csv')
        for _, row in df.iterrows():
            email = row.get('Email', '')
            email_valid = row.get('email_valid')
            
            # Enhanced email validation - check both format and validation status
            is_valid_format = (isinstance(email, str) and 
                             '@' in email and 
                             '.' in email.split('@')[1] and  # Check domain has TLD
                             len(email.split('@')[0]) > 0 and  # Check local part not empty
                             len(email.split('@')[1]) > 0)    # Check domain not empty
            
            # Check if email was validated (not nan, not None, and truthy)
            is_validated = (email_valid is not None and 
                          str(email_valid).lower() not in ['nan', 'none', 'false', '0'] and
                          email_valid == True)
            
            if is_valid_format and is_validated:
                professors.append({k.strip(): str(v).strip() for k, v in row.items()})
            else:
                reason = []
                if not is_valid_format:
                    reason.append("invalid format")
                if not is_validated:
                    reason.append(f"not validated (status: {email_valid})")
                st.warning(f"Skipping email {email}: {' and '.join(reason)}")

        st.write("Number of professors with valid emails:", len(professors))
        if len(professors) > 0:
            st.write("Sample professor record:", professors[0])

        # Optionally filter by country
        if selected_countries:
            filtered = []
            for prof in professors:
                if 'country' in prof and prof['country'] in selected_countries:
                    filtered.append(prof)
            professors = filtered
        
        # Initialize scraper if needed
        try:
            scraper = ProfessorScraper()
            # Scrape homepages (optional, can be skipped if causing issues)
            for i, prof in enumerate(professors):
                if prof.get('Homepage') and i < 10:  # Limit to first 10 to avoid timeouts
                    try:
                        prof['homepage_text'] = scraper.scrape_homepage(prof['Homepage'])
                    except Exception as e:
                        st.warning(f"Could not scrape homepage for {prof.get('Name', 'Unknown')}: {e}")
                if i % 10 == 0:
                    progress_bar.progress(10 + int(20 * i / max(1, len(professors))))
        except Exception as e:
            st.warning(f"Scraper initialization failed: {e}")
            progress_bar.progress(30)
        log_placeholder.write(f":mag: **Total professors after deduplication: {len(professors)}**")
        st.write("Number of deduplicated professors with valid emails:", len(professors))
        if len(professors) > 0:
            st.write("Sample deduplicated professor:", professors[0])
        # Force cold outreach: email all deduplicated professors
        matches = professors
        professors_matched = len(matches)
        progress_bar.progress(50)

        log_placeholder.write(":email: **Generating personalized emails...**")
        # Use parsed resume data for student_info, but always use LLM for email body
        parser = ResumeParser(resume_path)
        student_info = parser.parse()
        student_info['name'] = "Anamay Tripathy"
        student_info['email'] = "tripathy.anamay23@gmail.com"
        student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
        student_info['season'] = season
        student_info['funding'] = funding
        email_gen = EmailGenerator(student_info, use_ollama=True, ollama_model='gemma3')
        emails = []
        for prof in professors:
            subject = email_gen.generate_subject(prof)
            
            # Build a comprehensive prompt with all available data
            research_area = prof.get('Research Area', '')
            professor_name = prof.get('Name', '')
            university = prof.get('University', '')
            
            prompt = f"""
Write a professional, personalized research internship inquiry email from Anamay Tripathy to Prof. {professor_name} at {university}.
Their research area is: {research_area}.
My background: {student_info.get('summary', 'Data Science Engineering student with strong technical skills')}
My skills: {', '.join(student_info.get('skills', ['Python', 'Machine Learning', 'Data Analysis']))}
My projects: {', '.join(student_info.get('projects', ['Web applications', 'Data analysis projects']))}
My courses: {', '.join(student_info.get('courses', ['Computer Science', 'Mathematics', 'Statistics']))}
My email: {student_info['email']}
The email should be concise, polite, and mention why I am interested in their work.
"""
            st.write(f"LLM prompt for {professor_name}:", prompt)
            
            # Try LLM generation first
            body = ""
            try:
                body = email_gen.generate_with_llm(prof, custom_prompt=prompt)
                if body and body.strip():
                    st.write("✅ LLM generated email successfully")
                else:
                    st.warning("LLM returned empty response, using template fallback.")
                    body = email_gen.generate_body(prof)
            except Exception as e:
                st.error(f"LLM error for {professor_name}: {e}")
                st.warning("Using template fallback due to LLM error.")
                body = email_gen.generate_body(prof)
            
            # Final validation
            if not body or body.strip() == "":
                st.error(f"Failed to generate email for {professor_name}")
                continue
                
            st.write("Email subject:", subject)
            st.write("Email body preview:", body[:200] + "..." if len(body) > 200 else body)
            emails.append({'to': prof['Email'], 'subject': subject, 'body': body})
        progress_bar.progress(60)

        log_placeholder.write(":outbox_tray: **Sending emails...** (this may take a while)")
        sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
        sent_count = 0
        for i, email in enumerate(emails):
            sent = sender.send_email(email['to'], email['subject'], email['body'], resume_path)
            if sent:
                sent_count += 1
            progress_bar.progress(60 + int(30 * (i+1) / max(1, len(emails))))
            log_placeholder.write(f"Sent to {email['to']} - {'✅' if sent else '❌'}")
        emails_sent = sent_count
        progress_bar.progress(90)

        log_placeholder.write(":alarm_clock: **Scheduling follow-ups...**")
        scheduler = FollowupScheduler()
        for email in emails:
            scheduler.log_first_send(email['to'])
        scheduler.schedule_followups()
        followups_scheduled = len(emails)
        progress_bar.progress(100)
        log_placeholder.write(":white_check_mark: **Outreach complete!**")
    except Exception as e:
        log_placeholder.error(f"Error: {e}")
        progress_bar.progress(0)

# Analytics
st.header("5. Analytics")
st.markdown(f"- Professors matched: **{professors_matched}**\n- Emails sent: **{emails_sent}**\n- Response rate: _TBD_\n- Follow-ups scheduled: **{followups_scheduled}**")

st.header("6. Real-Time Logs")
log_placeholder.text("Logs will appear here during outreach.")

st.caption("InternMailer © 2024 | Built by Anamay Tripathy") 