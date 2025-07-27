import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from resume_parser import ResumeParser
from email_generator import EmailGenerator
from gmail_sender import GmailSender

load_dotenv()

st.set_page_config(
    page_title="UI/UX Professor Outreach", 
    page_icon="📧",
    layout="wide"
)

st.title("📧 UI/UX Professor Outreach Test")

# Check configuration
def check_config():
    issues = []
    if not os.getenv('GMAIL_USER'):
        issues.append("GMAIL_USER not set in .env")
    if not os.getenv('GMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD') == 'your_app_password_here':
        issues.append("GMAIL_APP_PASSWORD not set in .env")
    if not os.path.exists('data/proffesor.csv'):
        issues.append("Professor CSV not found")
    return issues

config_issues = check_config()
if config_issues:
    st.error("Configuration Issues:")
    for issue in config_issues:
        st.write(f"❌ {issue}")
    st.stop()

st.success("✅ Configuration OK")

# Load UI/UX related professors
@st.cache_data
def load_uiux_professors():
    df = pd.read_csv('data/proffesor.csv')
    # Filter for UI/UX related research areas
    uiux_keywords = ['ui', 'ux', 'user interface', 'user experience', 'human-computer', 'hci', 
                     'human-ai interaction', 'interaction', 'visualization', 'interface']
    
    uiux_profs = []
    for _, row in df.iterrows():
        research_area = str(row.get('Research Area', '')).lower()
        if any(keyword in research_area for keyword in uiux_keywords):
            uiux_profs.append({
                'Name': row.get('Name', ''),
                'Email': row.get('Email', ''),
                'University': row.get('University', ''),
                'Research Area': row.get('Research Area', ''),
                'Homepage': row.get('Homepage', '')
            })
    
    return uiux_profs

uiux_professors = load_uiux_professors()
st.write(f"Found {len(uiux_professors)} UI/UX related professors")

# Display professors
if uiux_professors:
    st.subheader("UI/UX Related Professors")
    for i, prof in enumerate(uiux_professors[:5]):  # Show first 5
        with st.expander(f"{prof['Name']} - {prof['University']}"):
            st.write(f"**Research Area:** {prof['Research Area']}")
            st.write(f"**Email:** {prof['Email']}")
            if prof['Homepage']:
                st.write(f"**Homepage:** {prof['Homepage']}")

# Resume upload/selection
st.subheader("1. Resume")
resume_files = []
if os.path.exists('resumes'):
    resume_files = [f for f in os.listdir('resumes') if f.endswith('.pdf')]

if resume_files:
    selected_resume = st.selectbox("Select Resume:", resume_files)
    resume_path = os.path.join('resumes', selected_resume)
else:
    uploaded_file = st.file_uploader("Upload Resume", type=['pdf'])
    if uploaded_file:
        resume_path = os.path.join('resumes', uploaded_file.name)
        os.makedirs('resumes', exist_ok=True)
        with open(resume_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        st.success("Resume uploaded!")
    else:
        st.error("Please upload a resume")
        st.stop()

# Test email generation
st.subheader("2. Test Email Generation")

if st.button("Generate Test Email"):
    if uiux_professors:
        # Use first UI/UX professor for testing
        test_prof = uiux_professors[0]
        
        try:
            # Parse resume
            parser = ResumeParser(resume_path)
            student_info = parser.parse()
            student_info['name'] = "Anamay Tripathy"
            student_info['email'] = "tripathy.anamay23@gmail.com"
            student_info['resume_prefix'] = os.path.splitext(os.path.basename(resume_path))[0]
            
            # Generate email
            email_gen = EmailGenerator(student_info, use_ollama=False)
            subject = email_gen.generate_subject(test_prof, informal=False)
            body = email_gen.generate_body(test_prof, informal=False)
            
            st.subheader("Generated Test Email")
            st.write(f"**To:** {test_prof['Email']}")
            st.write(f"**Subject:** {subject}")
            st.write("**Body:**")
            st.text_area("Email Body", body, height=300, disabled=True)
            
            # Store in session state for sending
            st.session_state['test_email'] = {
                'to': test_prof['Email'],
                'subject': subject,
                'body': body
            }
            st.session_state['student_info'] = student_info
            
        except Exception as e:
            st.error(f"Error generating email: {e}")

# Send test email
st.subheader("3. Send Test Email")
test_email_recipient = st.text_input("Send test email to (your email):", "tripathy.anamay23@gmail.com")

if st.button("Send Test Email") and 'test_email' in st.session_state:
    if not test_email_recipient:
        st.error("Please enter your email address")
    elif not os.getenv('GMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD') == 'your_app_password_here':
        st.error("Please update GMAIL_APP_PASSWORD in .env file with your actual app password")
    else:
        try:
            sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
            
            # Send test email to user's email instead of professor
            test_subject = f"[TEST] {st.session_state['test_email']['subject']}"
            test_body = f"This is a test email for approval.\n\nOriginal recipient: {st.session_state['test_email']['to']}\n\n" + \
                       f"Subject: {st.session_state['test_email']['subject']}\n\n" + \
                       f"Body:\n{st.session_state['test_email']['body']}"
            
            success = sender.send_email(test_email_recipient, test_subject, test_body, resume_path)
            
            if success:
                st.success(f"✅ Test email sent to {test_email_recipient}")
                st.info("Please check your email and approve to proceed with bulk sending")
            else:
                st.error("❌ Failed to send test email. Check your email configuration.")
                
        except Exception as e:
            st.error(f"Error sending test email: {e}")

# Bulk sending section
st.subheader("4. Bulk Email Campaign")
st.warning("⚠️ Only proceed after approving the test email!")

if st.button("🚀 Start Bulk Campaign", type="primary"):
    if 'student_info' not in st.session_state:
        st.error("Please generate a test email first")
    elif not os.getenv('GMAIL_APP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD') == 'your_app_password_here':
        st.error("Please update GMAIL_APP_PASSWORD in .env file")
    else:
        st.info("Starting bulk email campaign...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            student_info = st.session_state['student_info']
            email_gen = EmailGenerator(student_info, use_ollama=False)
            sender = GmailSender(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
            
            total_profs = len(uiux_professors)
            sent_count = 0
            
            for i, prof in enumerate(uiux_professors):
                status_text.text(f"Processing {prof['Name']} ({i+1}/{total_profs})")
                
                try:
                    # Generate personalized email
                    subject = email_gen.generate_subject(prof, informal=False)
                    body = email_gen.generate_body(prof, informal=False)
                    
                    # Send email
                    success = sender.send_email(prof['Email'], subject, body, resume_path)
                    
                    if success:
                        sent_count += 1
                        st.write(f"✅ Sent to {prof['Name']} ({prof['Email']})")
                    else:
                        st.write(f"❌ Failed to send to {prof['Name']} ({prof['Email']})")
                        
                except Exception as e:
                    st.write(f"❌ Error with {prof['Name']}: {e}")
                
                progress_bar.progress((i + 1) / total_profs)
            
            status_text.text("Campaign Complete!")
            st.success(f"🎉 Campaign finished! Successfully sent {sent_count}/{total_profs} emails")
            
        except Exception as e:
            st.error(f"Campaign error: {e}")

# Email log viewer
st.subheader("5. Email Log")
if os.path.exists('email_log.csv'):
    log_df = pd.read_csv('email_log.csv')
    st.dataframe(log_df.tail(10))  # Show last 10 entries
else:
    st.info("No email log found yet")

st.markdown("---")
st.caption("Configure your Gmail App Password in .env before sending emails")
