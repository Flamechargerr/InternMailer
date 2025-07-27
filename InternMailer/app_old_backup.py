import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scheduler'))
from scheduler.streamlit_api import get_followup_manager
import requests
from datetime import datetime

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
    
    # Check data files
    if not os.path.exists('data/proffesor.csv'):
        issues.append("Professor CSV file not found at 'data/proffesor.csv'")
    
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

# Check if Ollama is running
def is_ollama_running():
    try:
        r = requests.get("http://localhost:11434")
        return r.status_code == 200
    except Exception:
        return False

ollama_available = is_ollama_running()
if not ollama_available:
    st.warning("Ollama server is not running. Please start Ollama with a model (e.g., 'ollama run gemma3') for LLM-powered email generation. Fallback to template-based emails will be used.")
else:
    st.success("✅ Ollama server detected! Using Gemma3 for AI-powered email generation.")

# Upload resume
st.header("1. Upload Your Resume")
st.caption("Upload your latest PDF resume. Skills and projects will be extracted automatically.")
uploaded_file = st.file_uploader("Upload your PDF resume", type=["pdf"])

# Check if resume already exists
resume_path = None
if uploaded_file:
    resume_path = os.path.join("resumes", uploaded_file.name)
    with open(resume_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Uploaded {uploaded_file.name}")
else:
    # Check for existing resume files
    resume_dir = "resumes"
    if os.path.exists(resume_dir):
        resume_files = [f for f in os.listdir(resume_dir) if f.endswith('.pdf')]
        if resume_files:
            resume_path = os.path.join(resume_dir, resume_files[0])
            st.info(f"Using existing resume: {resume_files[0]}")

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

# Display professors preview table
st.header("4. Professors Preview")
professors_df = pd.read_csv('professors_next.csv')
with st.expander("Show Professors Data"):
    st.dataframe(professors_df)

# Email Template
try:
    with open('templates/email_template.txt', 'r') as f:
        email_template_content = f.read()
    email_template = Template(email_template_content)
except FileNotFoundError:
    st.error("Email template not found. Creating default template...")
    # Create a simple default template
    email_template_content = "Dear Professor {{ professor.name }},\n\nI am {{ student.name }}, interested in research opportunities.\n\nBest regards,\n{{ student.name }}"
    email_template = Template(email_template_content)

# Add a preview email section
st.header("5. Preview Sample Email")
if resume_path:
    professor_to_preview = st.selectbox("Select Professor", professors_df["Name"])
    selected_professor = professors_df[professors_df["Name"] == professor_to_preview].iloc[0]
    mock_prof = {
        "name": selected_professor["Name"],
        "research_area": selected_professor["Research Area"],
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
    
    # Add informal/formal toggle for template
    informal = st.checkbox("Use informal tone", value=False)
    student_info['informal'] = informal
    
    preview_email_body = email_template.render(professor=mock_prof, student=student_info, informal=informal)
    with st.expander("Show Email Preview"):
        st.markdown(preview_email_body)
else:
    st.info("Please upload a resume first to preview emails.")

# Outreach mode selection
st.header("6. Outreach Mode")
mode = st.radio("Choose Mode:", ["Dry Run", "Live Send"])

# Display selected mode
if mode == "Live Send":
    st.warning("Emails will be sent!")
else:
    st.info("This is a dry run.")


# Launch outreach
st.header("7. Launch Outreach")
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
        log_placeholder.write(":mag: **Initializing professor tracker...**")
        # Initialize professor tracker to avoid duplicates
        tracker = ProfessorTracker()
        
        # Bulk add already emailed professors to prevent duplicates
        already_emailed = [
            {'email': 'liskov@csail.mit.edu', 'name': 'Barbara H. Liskov', 'university': 'MIT'},
            {'email': 'asuman@mit.edu', 'name': 'Asuman E. Ozdaglar', 'university': 'MIT'},
            {'email': 'arvind@csail.mit.edu', 'name': 'Arvind', 'university': 'MIT'},
            {'email': 'asolar@csail.mit.edu', 'name': 'Armando Solar-Lezama', 'university': 'MIT'},
            {'email': 'torralba@csail.mit.edu', 'name': 'Antonio Torralba', 'university': 'MIT'},
            {'email': 'moitra@mit.edu', 'name': 'Ankur Moitra', 'university': 'MIT'},
            {'email': 'anant@csail.mit.edu', 'name': 'Anant Agarwal', 'university': 'MIT'},
            {'email': 'rakhlin@mit.edu', 'name': 'Alexander Rakhlin', 'university': 'MIT'},
            {'email': 'adamc@csail.mit.edu', 'name': 'Adam Chlipala', 'university': 'MIT'},
            {'email': 'abelay@mit.edu', 'name': 'Adam Belay', 'university': 'MIT'}
        ]
        
        tracker.bulk_add_professors(already_emailed)
        stats = tracker.get_stats()
        log_placeholder.write(f":mag: **Professor tracker initialized - {stats['total_emailed']} professors already contacted**")
        
        log_placeholder.write(":mag: **Parsing resume...**")
        parser = ResumeParser(resume_path)
        student_info = parser.parse()
        student_info['name'] = "Anamay Tripathy"
        student_info['email'] = "tripathy.anamay23@gmail.com"
        student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
        student_info['season'] = season
        student_info['funding'] = funding
        progress_bar.progress(10)

        log_placeholder.write(":mag: **Loading professors from CSV...**")
        professors = []
        
        try:
            # Read CSV with better error handling for malformed data
            df = pd.read_csv('data/proffesor.csv', on_bad_lines='skip', encoding='utf-8')
            
            # Filter out any duplicate header rows that might be in the middle
            df = df[df['University'] != 'University']  # Remove header rows
            df = df.dropna(subset=['Email'])  # Remove rows without email
            
            log_placeholder.write(f"Found {len(df)} professor records in CSV (after cleaning)")
            
            for _, row in df.iterrows():
                email = row.get('Email', '')
                
                # Skip if email is NaN or empty
                if pd.isna(email) or not email or email.strip() == '':
                    continue
                    
                # Enhanced email validation - focus on format since the CSV doesn't have email_valid column
                try:
                    is_valid_format = (isinstance(email, str) and 
                                     email.strip() != '' and
                                     '@' in email and 
                                     '.' in email.split('@')[1] and  # Check domain has TLD
                                     len(email.split('@')[0]) > 0 and  # Check local part not empty
                                     len(email.split('@')[1]) > 0)    # Check domain not empty
                except (IndexError, AttributeError):
                    is_valid_format = False
                
                if is_valid_format:
                    # Clean and add the professor data
                    prof_data = {}
                    for k, v in row.items():
                        if pd.notna(v) and str(v).strip() != '':  # Only add non-null, non-empty values
                            prof_data[k.strip()] = str(v).strip()
                    
                    # Only add if we have the essential fields
                    if prof_data.get('Name') and prof_data.get('Email'):
                        professors.append(prof_data)
                else:
                    # Only show warning for first few invalid emails to avoid spam
                    if len([p for p in professors]) < 5:
                        st.warning(f"Skipping invalid email: {email}")
                        
        except FileNotFoundError:
            st.error("Professor CSV file not found. Please ensure 'data/proffesor.csv' exists.")
            st.stop()
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            st.stop()

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
            scraper = ProfessorScraper(data_dir='data')
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
        email_gen = EmailGenerator(student_info, use_ollama=True, ollama_model='gemma3:latest')
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

        # Handle dry-run vs live send mode
        if mode == "Dry Run":
            log_placeholder.write(":mag: **DRY RUN MODE - No emails will be sent**")
            st.info("🔍 **DRY RUN MODE ACTIVE** - Emails are being generated and displayed but not sent.")
            
            # Show detailed email previews for first 3 professors
            st.subheader("📧 Email Previews (First 3 Professors)")
            for i, email in enumerate(emails[:3]):
                with st.expander(f"📧 Email {i+1}: {email['to']}", expanded=True):
                    st.write(f"**To:** {email['to']}")
                    st.write(f"**Subject:** {email['subject']}")
                    st.write("**Body:**")
                    st.text_area(f"Email Body {i+1}", email['body'], height=200, key=f"email_body_{i}")
                    
                    # Show personalization variables used
                    prof_name = next((prof.get('Name', 'Unknown') for prof in professors if prof.get('Email') == email['to']), 'Unknown')
                    research_area = next((prof.get('Research Area', 'Unknown') for prof in professors if prof.get('Email') == email['to']), 'Unknown')
                    st.write(f"**Personalization Variables:**")
                    st.write(f"- Professor Name: {prof_name}")
                    st.write(f"- Research Area: {research_area}")
                    st.write(f"- Student Name: {student_info.get('name', 'Not set')}")
                    st.write(f"- Student Email: {student_info.get('email', 'Not set')}")
                    st.write(f"- Top Skills: {', '.join(student_info.get('skills', [])[:5])}")
                    st.write(f"- Projects: {', '.join(student_info.get('projects', [])[:3])}")
                    
            # Simulate sending for progress tracking with duplicate checking
            sent_count = 0
            skipped_count = 0
            for i, email in enumerate(emails):
                # Check if professor already contacted
                if tracker.is_professor_contacted(email['to']):
                    skipped_count += 1
                    log_placeholder.write(f"[DRY RUN] Skipping {email['to']} - Already contacted ⏭️")
                else:
                    # Simulate processing time
                    time.sleep(0.1)
                    sent_count += 1  # In dry run, count as "sent" for analytics
                    log_placeholder.write(f"[DRY RUN] Would send to {email['to']} - ✅ (Email prepared)")
                    
                progress_bar.progress(60 + int(30 * (i+1) / max(1, len(emails))))
            
            emails_sent = sent_count
            st.success(f"🔍 **DRY RUN COMPLETE**: {sent_count} emails prepared, {skipped_count} duplicates skipped!")
            st.info("💡 **Tip**: Switch to 'Live Send' mode to actually send the emails.")
            
        else:  # Live Send mode
            log_placeholder.write(":outbox_tray: **Sending emails...** (this may take a while)")
            st.warning("📧 **LIVE MODE**: Emails are being sent!")
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
        
        # Initialize follow-up manager and create campaign
        followup_manager = get_followup_manager()
        campaign_name = f"Outreach {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        campaign_id = followup_manager.create_campaign(campaign_name, f"Academic outreach for {season} internships")
        
        # Log emails and schedule follow-ups
        for email in emails:
            followup_manager.log_email_sent(campaign_id, email['to'], email['subject'])
        followups_scheduled = len(emails)
        
        # Store campaign ID in session state for later use
        st.session_state['current_campaign_id'] = campaign_id
        
        progress_bar.progress(100)
        log_placeholder.write(":white_check_mark: **Outreach complete!**")
    except Exception as e:
        log_placeholder.error(f"Error: {e}")
        progress_bar.progress(0)

# Analytics
st.header("5. Analytics")
st.markdown(f"- Professors matched: **{professors_matched}**\n- Emails sent: **{emails_sent}**\n- Response rate: _TBD_\n- Follow-ups scheduled: **{followups_scheduled}**")

# Follow-up Scheduler Interface
st.header("📅 Follow-up Scheduler")

# Initialize follow-up manager
followup_manager = get_followup_manager()

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 All Follow-ups", "⚙️ Campaign Settings", "📈 Analytics"])

with tab1:
    st.subheader("Follow-up Dashboard")
    
    # Get analytics
    analytics = followup_manager.get_analytics()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Follow-ups", analytics['total_followups'])
    with col2:
        st.metric("Scheduled", analytics['scheduled_followups'])
    with col3:
        st.metric("Sent", analytics['sent_followups'])
    with col4:
        st.metric("Overdue", analytics['overdue_followups'], delta_color="inverse")
    
    # Process overdue follow-ups button
    if st.button("🚀 Process Overdue Follow-ups"):
        processed = followup_manager.process_overdue_followups()
        if processed > 0:
            st.success(f"Processed {processed} overdue follow-ups!")
            st.rerun()
        else:
            st.info("No overdue follow-ups to process.")
    
    # Campaign breakdown chart
    if analytics['campaigns']:
        st.subheader("Follow-ups by Campaign")
        campaign_df = pd.DataFrame(analytics['campaigns'])
        if not campaign_df.empty:
            fig = px.bar(campaign_df, x='name', y='followup_count', 
                        title="Follow-ups by Campaign")
            fig.update_layout(xaxis_title="Campaign", yaxis_title="Follow-up Count")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("All Follow-ups")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", 
                                   ["All", "scheduled", "sent", "cancelled"])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get all follow-ups
    all_followups = followup_manager.get_all_followups()
    
    if status_filter != "All":
        all_followups = [f for f in all_followups if f['status'] == status_filter]
    
    if all_followups:
        # Display follow-ups in a table format
        for i, followup in enumerate(all_followups):
            with st.expander(f"📧 {followup['contact_name']} ({followup['contact_email']}) - {followup['status'].title()}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Campaign:** {followup.get('campaign_name', 'Unknown')}")
                    st.write(f"**Sequence:** {followup['sequence_number']}")
                    st.write(f"**Scheduled:** {followup['scheduled_at'][:16]}")
                    if followup['is_overdue'] and followup['status'] == 'scheduled':
                        st.error("⚠️ OVERDUE")
                    
                    if followup['sent_at']:
                        st.write(f"**Sent:** {followup['sent_at'][:16]}")
                
                with col2:
                    if followup['status'] == 'scheduled':
                        # Reschedule option
                        new_date = st.date_input(f"New Date", 
                                                value=followup['scheduled_at_parsed'].date(),
                                                key=f"date_{followup['id']}")
                        new_time = st.time_input(f"New Time", 
                                                value=followup['scheduled_at_parsed'].time(),
                                                key=f"time_{followup['id']}")
                        
                        if st.button(f"📅 Reschedule", key=f"reschedule_{followup['id']}"):
                            new_datetime = datetime.combine(new_date, new_time)
                            if followup_manager.reschedule_followup(followup['id'], new_datetime):
                                st.success("Rescheduled successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to reschedule.")
                
                with col3:
                    if followup['status'] == 'scheduled':
                        if st.button(f"❌ Cancel", key=f"cancel_{followup['id']}"):
                            if followup_manager.cancel_followup(followup['id'], "Cancelled by user"):
                                st.success("Cancelled successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to cancel.")
    else:
        st.info("No follow-ups found.")

with tab3:
    st.subheader("Campaign Settings")
    
    # Get all campaigns
    campaigns = followup_manager.get_campaigns()
    
    if campaigns:
        selected_campaign = st.selectbox("Select Campaign", 
                                       options=[c['id'] for c in campaigns],
                                       format_func=lambda x: next(c['name'] for c in campaigns if c['id'] == x))
        
        # Find selected campaign data
        campaign_data = next(c for c in campaigns if c['id'] == selected_campaign)
        
        st.write(f"**Campaign:** {campaign_data['name']}")
        st.write(f"**Description:** {campaign_data['description']}")
        st.write(f"**Total Follow-ups:** {campaign_data['total_followups']}")
        
        # Settings form
        with st.form(f"campaign_settings_{selected_campaign}"):
            st.subheader("Follow-up Settings")
            
            followup_enabled = st.checkbox("Enable Follow-ups", 
                                         value=bool(campaign_data['followup_enabled']))
            
            followup_delay = st.slider("Follow-up Delay (days)", 
                                     min_value=1, max_value=30, 
                                     value=campaign_data['followup_delay_days'])
            
            max_followups = st.slider("Maximum Follow-ups", 
                                    min_value=1, max_value=5, 
                                    value=campaign_data['max_followups'])
            
            if st.form_submit_button("💾 Save Settings"):
                settings = {
                    'followup_enabled': followup_enabled,
                    'followup_delay_days': followup_delay,
                    'max_followups': max_followups
                }
                
                if followup_manager.update_campaign_settings(selected_campaign, settings):
                    st.success("Settings updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update settings.")
        
        # Campaign-specific follow-ups
        st.subheader("Campaign Follow-ups")
        campaign_followups = followup_manager.get_campaign_followups(selected_campaign)
        
        if campaign_followups:
            # Status breakdown
            status_counts = {}
            for f in campaign_followups:
                status_counts[f['status']] = status_counts.get(f['status'], 0) + 1
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Scheduled", status_counts.get('scheduled', 0))
            with col2:
                st.metric("Sent", status_counts.get('sent', 0))
            with col3:
                st.metric("Cancelled", status_counts.get('cancelled', 0))
            
            # Bulk actions
            st.subheader("Bulk Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📅 Reschedule All Pending"):
                    new_bulk_date = st.date_input("New Date for All", value=datetime.now().date())
                    # Implementation would go here
                    st.info("Bulk reschedule feature - implementation needed")
            
            with col2:
                if st.button("❌ Cancel All Pending"):
                    pending_count = len([f for f in campaign_followups if f['status'] == 'scheduled'])
                    st.warning(f"This will cancel {pending_count} pending follow-ups. Feature coming soon.")
                    # Implementation would go here
                    st.info("Bulk cancel feature - implementation needed")
        else:
            st.info("No follow-ups found for this campaign.")
    else:
        st.info("No campaigns found. Run an outreach first to create a campaign.")

with tab4:
    st.subheader("Follow-up Analytics")
    
    # Get analytics data
    analytics = followup_manager.get_analytics()
    
    # Overall statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Overall Statistics")
        total = analytics['total_followups']
        if total > 0:
            success_rate = (analytics['sent_followups'] / total) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Status distribution pie chart
            status_data = {
                'Scheduled': analytics['scheduled_followups'],
                'Sent': analytics['sent_followups'],
                'Cancelled': analytics['cancelled_followups']
            }
            
            fig = px.pie(values=list(status_data.values()), 
                        names=list(status_data.keys()),
                        title="Follow-up Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Performance Metrics")
        
        # Time-based analysis would go here
        st.info("Advanced analytics coming soon...")
        
        # Show some basic stats
        if analytics['total_followups'] > 0:
            overdue_rate = (analytics['overdue_followups'] / analytics['scheduled_followups']) * 100 if analytics['scheduled_followups'] > 0 else 0
            st.metric("Overdue Rate", f"{overdue_rate:.1f}%", delta_color="inverse")
    
    # Recent activity
    st.subheader("Recent Follow-up Activity")
    recent_followups = followup_manager.get_all_followups()
    recent_followups.sort(key=lambda x: x.get('updated_at', x['created_at']), reverse=True)
    
    if recent_followups:
        for followup in recent_followups[:5]:  # Show last 5
            status_emoji = {"scheduled": "⏰", "sent": "✅", "cancelled": "❌"}
            emoji = status_emoji.get(followup['status'], "❓")
            st.write(f"{emoji} **{followup['contact_name']}** - {followup['status'].title()} ({followup['scheduled_at'][:10]})")
    else:
        st.info("No recent activity.")

st.header("6. Real-Time Logs")
log_placeholder.text("Logs will appear here during outreach.")

st.caption("InternMailer © 2024 | Built by Anamay Tripathy")
