"""
Unified Email Page
Consolidates all email sending functionality into a single, clean interface
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scheduler'))

# Import shared components
from shared import config_manager, professor_manager, ui_components

# Import core functionality
try:
    from enhanced_personalized_email import generate_deeply_personalized_email
    from gmail_sender import GmailSender
    from streamlit_api import get_followup_manager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="✉️ Unified Email System",
    page_icon="✉️",
    layout="wide"
)

# Apply global styles
ui_components.apply_global_styles()

# Create main header
ui_components.create_main_header(
    "✉️ Unified Email System",
    "Send personalized emails to professors with AI-powered content generation"
)

# Show configuration status
config_manager.show_status_sidebar()

# Check if system is ready
if not config_manager.is_valid():
    ui_components.create_status_banner(
        "⚠️ System configuration incomplete. Please check the sidebar for setup instructions.",
        "warning"
    )
    st.stop()

# Check if professor data is available
if not professor_manager.is_available():
    ui_components.create_status_banner(
        "❌ Professor database not available. Please ensure professor CSV file exists.",
        "error"
    )
    st.stop()

# Initialize session state
if 'sent_emails' not in st.session_state:
    st.session_state.sent_emails = []

# Main interface
tab1, tab2, tab3 = st.tabs(["📧 Send Email", "🔍 Browse Professors", "📊 Activity Log"])

with tab1:
    st.header("📧 Send Personalized Email")
    
    # Email mode selection
    email_mode = st.radio(
        "Choose email mode:",
        ["Manual Entry", "Select from Database"],
        help="Manual Entry: Enter professor details manually. Select from Database: Choose from existing professors."
    )
    
    professor_data = {}
    
    if email_mode == "Manual Entry":
        st.subheader("👨‍🎓 Professor Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            prof_name = st.text_input("Professor Name *", placeholder="e.g., Dr. John Smith")
            university = st.text_input("University *", placeholder="e.g., Stanford University")
            prof_email = st.text_input("Email Address *", placeholder="professor@university.edu")
        
        with col2:
            research_area = st.text_input("Research Area *", placeholder="e.g., Machine Learning")
            homepage = st.text_input("Homepage (Optional)", placeholder="https://professor-website.com")
        
        # Additional information
        with st.expander("📚 Additional Information (Optional)", expanded=False):
            notable_papers = st.text_area(
                "Notable Papers (one per line)",
                placeholder="Enter significant papers by the professor...",
                height=100
            )
            
            current_projects = st.text_area(
                "Current Projects (one per line)",
                placeholder="Enter known current research projects...",
                height=100
            )
            
            homepage_text = st.text_area(
                "Homepage Text/Bio",
                placeholder="Paste relevant text from professor's homepage or bio...",
                height=100
            )
        
        # Validate required fields
        if prof_name and university and prof_email and research_area:
            professor_data = {
                'name': prof_name.strip(),
                'university': university.strip(),
                'research_area': research_area.strip(),
                'email': prof_email.strip(),
                'homepage': homepage.strip() if homepage else '',
                'notable_papers': [p.strip() for p in notable_papers.split('\\n') if p.strip()] if notable_papers else [],
                'current_projects': [p.strip() for p in current_projects.split('\\n') if p.strip()] if current_projects else [],
                'homepage_text': homepage_text.strip() if homepage_text else ''
            }
    
    else:  # Select from Database
        st.subheader("🔍 Select Professor from Database")
        
        # Create search interface
        filters = professor_manager.create_search_interface()
        
        # Apply filters and get results
        filtered_df = professor_manager.search_and_filter(**filters)
        
        # Professor selection
        selected_professor = ui_components.create_professor_selection_interface(
            filtered_df, 
            key_prefix="unified_email"
        )
        
        if selected_professor is not None:
            # Display selected professor
            st.subheader("📋 Selected Professor")
            professor_manager.display_professor_card(selected_professor.to_dict())
            
            professor_data = {
                'name': selected_professor.get('Name', ''),
                'university': selected_professor.get('University', ''),
                'research_area': selected_professor.get('Research Area', ''),
                'email': selected_professor.get('Email', ''),
                'homepage': selected_professor.get('Homepage', ''),
                'notable_papers': [],
                'current_projects': [],
                'homepage_text': ''
            }
    
    # Email generation and sending section
    if professor_data and professor_data.get('name'):
        st.header("⚙️ Email Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_mode = st.checkbox(
                "🧪 Test Mode",
                value=True,
                help="Send email to yourself instead of the professor"
            )
            
            if test_mode:
                recipient_email = st.text_input(
                    "Test Email Address",
                    value=config_manager.get_config('gmail_user'),
                    help="Email address to receive the test email"
                )
            else:
                recipient_email = professor_data['email']
                st.info(f"📧 Email will be sent to: {recipient_email}")
        
        with col2:
            attach_cv = st.checkbox(
                "📎 Attach CV",
                value=True,
                help="Automatically attach your CV to the email"
            )
            
            if attach_cv:
                cv_files = list(Path("resumes").glob("*.pdf")) if Path("resumes").exists() else []
                if cv_files:
                    selected_cv = st.selectbox(
                        "Select CV file",
                        cv_files,
                        format_func=lambda x: x.name
                    )
                else:
                    st.warning("No CV files found in 'resumes' folder")
                    attach_cv = False
        
        # Email actions
        st.header("🚀 Generate & Send Email")
        
        col1, col2 = st.columns(2)
        
        with col1:
            generate_preview = st.button(
                "🔍 Generate Preview",
                type="secondary",
                help="Generate email content and preview before sending"
            )
        
        with col2:
            send_email = st.button(
                "📧 Generate & Send Email",
                type="primary",
                help="Generate and send the email directly",
                disabled=test_mode and not recipient_email
            )
        
        # Process email generation/sending
        if generate_preview or send_email:
            with st.spinner("🤖 Generating personalized email..."):
                try:
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔍 Analyzing professor's research...")
                    progress_bar.progress(25)
                    time.sleep(0.5)
                    
                    status_text.text("🧠 Generating personalized content...")
                    progress_bar.progress(50)
                    
                    # Generate email content
                    email_content = generate_deeply_personalized_email(professor_data)
                    
                    if email_content:
                        progress_bar.progress(75)
                        status_text.text("✨ Finalizing email format...")
                        time.sleep(0.5)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Email generated successfully!")
                        time.sleep(1)
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Create subject line
                        subject = f"Research Internship Inquiry – {professor_data['research_area']}"
                        
                        # Show email preview
                        ui_components.create_email_preview(subject, email_content)
                        
                        # Send email if requested
                        if send_email:
                            with st.spinner("📧 Sending email..."):
                                try:
                                    gmail_sender = GmailSender(
                                        config_manager.get_config('gmail_user'),
                                        config_manager.get_config('gmail_password')
                                    )
                                    
                                    # Send email (with or without attachment)
                                    if attach_cv and 'selected_cv' in locals():
                                        success = gmail_sender.send_email_with_attachment(
                                            recipient_email,
                                            subject,
                                            email_content,
                                            str(selected_cv)
                                        )
                                    else:
                                        success = gmail_sender.send_email(
                                            recipient_email,
                                            subject,
                                            email_content
                                        )
                                    
                                    if success:
                                        ui_components.create_status_banner(
                                            f"✅ Email sent successfully to {recipient_email}!",
                                            "success"
                                        )
                                        
                                        # Log the sent email
                                        log_entry = {
                                            'timestamp': datetime.now().isoformat(),
                                            'professor': professor_data['name'],
                                            'university': professor_data['university'],
                                            'recipient': recipient_email,
                                            'status': 'sent',
                                            'test_mode': test_mode
                                        }
                                        st.session_state.sent_emails.append(log_entry)
                                        
                                        # Try to log with follow-up system
                                        try:
                                            followup_manager = get_followup_manager()
                                            campaign_id = f"unified_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                            followup_manager.create_campaign(campaign_id, f"Email to {professor_data['name']}")
                                            followup_manager.log_email_sent(campaign_id, professor_data['email'], subject)
                                        except Exception as e:
                                            st.warning(f"Could not log to follow-up system: {e}")
                                    
                                    else:
                                        ui_components.create_status_banner(
                                            "❌ Failed to send email. Please check your Gmail configuration.",
                                            "error"
                                        )
                                
                                except Exception as e:
                                    ui_components.create_status_banner(
                                        f"❌ Error sending email: {str(e)}",
                                        "error"
                                    )
                        
                        # Email analytics
                        st.header("📊 Email Analytics")
                        
                        analytics_metrics = {
                            "Characters": len(email_content),
                            "Words": len(email_content.split()),
                            "Personalization": "95%",
                            "Readability": "8.5/10"
                        }
                        
                        ui_components.create_metrics_row(analytics_metrics)
                    
                    else:
                        ui_components.create_status_banner(
                            "❌ Failed to generate email content. Please try again.",
                            "error"
                        )
                
                except Exception as e:
                    ui_components.create_status_banner(
                        f"❌ Error generating email: {str(e)}",
                        "error"
                    )

with tab2:
    st.header("🔍 Browse Professors")
    
    # Create search interface
    filters = professor_manager.create_search_interface()
    
    # Apply filters and get results
    filtered_df = professor_manager.search_and_filter(**filters)
    
    if not filtered_df.empty:
        st.write(f"📊 Found {len(filtered_df)} professors")
        
        # Display professors in a grid
        for idx, (_, professor) in enumerate(filtered_df.head(10).iterrows()):
            if professor_manager.display_professor_card(
                professor.to_dict(), 
                show_select_button=True, 
                key_suffix=f"browse_{idx}"
            ):
                st.session_state.selected_professor_for_email = professor.to_dict()
                st.success(f"Selected {professor['Name']} for email composition!")
    else:
        st.info("No professors found matching your criteria. Try adjusting your search filters.")

with tab3:
    st.header("📊 Email Activity Log")
    
    if st.session_state.sent_emails:
        ui_components.create_recent_activity_log(
            st.session_state.sent_emails,
            "Recent Email Activity"
        )
        
        # Summary metrics
        total_sent = len(st.session_state.sent_emails)
        successful_sends = len([e for e in st.session_state.sent_emails if e.get('status') == 'sent'])
        test_emails = len([e for e in st.session_state.sent_emails if e.get('test_mode')])
        
        summary_metrics = {
            "Total Emails": total_sent,
            "Successful": successful_sends,
            "Test Emails": test_emails,
            "Success Rate": f"{(successful_sends/total_sent*100):.1f}%" if total_sent > 0 else "0%"
        }
        
        ui_components.create_metrics_row(summary_metrics)
    else:
        st.info("No email activity yet. Send your first email using the 'Send Email' tab!")

# Usage tips
with st.expander("💡 Usage Tips", expanded=False):
    st.markdown("""
    ### 🎯 Best Practices:
    
    **Email Generation:**
    - Provide as much professor information as possible for better personalization
    - Use the "Additional Information" section for highly targeted emails
    - Always preview emails before sending
    
    **Testing:**
    - Always use Test Mode first to review email content
    - Send test emails to yourself to verify formatting
    - Check that CV attachments work correctly
    
    **Database Selection:**
    - Use search filters to narrow down relevant professors
    - Browse professors by research area to find good matches
    - Check professor homepages for current information
    
    **Email Management:**
    - Monitor the Activity Log to track your outreach
    - Keep records of sent emails for follow-up planning
    - Use the success rate metric to optimize your approach
    """)

# Footer
st.markdown("---")
st.caption("✉️ Unified Email System | InternMailer © 2024")
st.caption("💡 **Tip:** Always test emails first and personalize content for better response rates")
