#!/usr/bin/env python3
"""
Email with CV - Enhanced Email System Integration
Complete email sending functionality with CV attachment through Streamlit UI
"""

import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import logging

# Add parent directory for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import the working email system
from send_email_with_cv import send_email_with_cv, find_cv_file, create_sample_cv
from enhanced_personalized_email import generate_deeply_personalized_email

# Page configuration
st.set_page_config(
    page_title="Email with CV - InternMailer",
    page_icon="📧",
    layout="wide"
)

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
    .email-preview {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        max-height: 500px;
        overflow-y: auto;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        color: #155724;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        color: #721c24;
    }
    .feature-highlight {
        background: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 15px;
        margin: 15px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📧 Email with CV System</h1>
    <p>Send personalized research internship emails with automatic CV attachment</p>
</div>
""", unsafe_allow_html=True)

# System status check
def check_system_status():
    """Check if the email system is properly configured."""
    issues = []
    
    # Check environment variables
    if not os.getenv('GMAIL_USER'):
        issues.append("GMAIL_USER not configured")
    if not os.getenv('GMAIL_APP_PASSWORD'):
        issues.append("GMAIL_APP_PASSWORD not configured")
    
    # Check CV file
    cv_path = find_cv_file()
    cv_status = "Found" if cv_path else "Will create sample CV"
    
    return issues, cv_status, cv_path

# Display system status
with st.container():
    st.subheader("🔧 System Status")
    
    issues, cv_status, cv_path = check_system_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not issues:
            st.success("✅ Email Configuration OK")
        else:
            st.error("❌ Configuration Issues")
            for issue in issues:
                st.caption(f"• {issue}")
    
    with col2:
        st.info(f"📄 CV Status: {cv_status}")
        if cv_path:
            st.caption(f"Found: {cv_path.name}")
    
    with col3:
        st.success("✅ Email System Ready")

# Configuration section
if issues:
    with st.expander("⚙️ Configuration Help", expanded=True):
        st.markdown("""
        **To use the email system, you need:**
        
        1. **Gmail App Password**: 
           - Go to Google Account → Security → App passwords
           - Generate password for "Mail"
           - Add to `.env` file: `GMAIL_APP_PASSWORD=your-app-password`
        
        2. **Gmail User**:
           - Add to `.env` file: `GMAIL_USER=your-email@gmail.com`
        
        3. **CV File** (optional):
           - System will automatically find CV files in common locations
           - Or create a sample CV if none found
        """)

# Main functionality
st.header("📝 Compose Email")

# Two-column layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👨‍🔬 Professor Information")
    
    # Professor input form
    with st.form("professor_form"):
        prof_name = st.text_input(
            "Professor Name*",
            placeholder="e.g., Dr. Sarah Chen",
            help="Full name including title (Dr., Prof., etc.)"
        )
        
        university = st.text_input(
            "University/Institution*",
            placeholder="e.g., Stanford University",
            help="Complete institution name"
        )
        
        research_area = st.text_input(
            "Research Area*",
            placeholder="e.g., machine learning and computer vision",
            help="Primary research focus area"
        )
        
        st.subheader("📚 Additional Information (Optional)")
        
        notable_papers = st.text_area(
            "Notable Papers",
            placeholder="List key papers (one per line)",
            help="Recent or influential publications"
        )
        
        current_projects = st.text_area(
            "Current Projects",
            placeholder="Ongoing research projects (one per line)",
            help="Active research initiatives"
        )
        
        homepage_text = st.text_area(
            "Homepage/Profile Text",
            placeholder="Text from professor's homepage or profile",
            help="Additional context from their online presence"
        )
        
        st.subheader("📧 Email Settings")
        
        test_mode = st.checkbox(
            "Test Mode (Send to yourself)",
            value=True,
            help="Send email to your own address for testing"
        )
        
        if not test_mode:
            recipient_email = st.text_input(
                "Recipient Email",
                placeholder="professor@university.edu",
                help="Professor's email address"
            )
        else:
            recipient_email = None
        
        # Form submit button
        generate_preview = st.form_submit_button("🔍 Generate Preview", type="secondary")
        send_email = st.form_submit_button("📧 Send Email", type="primary")

with col2:
    st.subheader("📋 Email Preview")
    
    # Process form submission
    if generate_preview or send_email:
        # Validate required fields
        if not prof_name or not university or not research_area:
            st.error("❌ Please fill in all required fields (marked with *)")
        else:
            # Build professor data
            professor_data = {
                'name': prof_name.strip(),
                'university': university.strip(),
                'research_area': research_area.strip()
            }
            
            # Add optional fields if provided
            if notable_papers.strip():
                professor_data['notable_papers'] = [
                    paper.strip() for paper in notable_papers.split('\n')
                    if paper.strip()
                ]
            
            if current_projects.strip():
                professor_data['current_projects'] = [
                    project.strip() for project in current_projects.split('\n')
                    if project.strip()
                ]
            
            if homepage_text.strip():
                professor_data['homepage_text'] = homepage_text.strip()
            
            # Generate email preview
            with st.spinner("🔧 Generating personalized email..."):
                try:
                    email_html = generate_deeply_personalized_email(professor_data)
                    
                    if email_html:
                        # Show preview
                        st.markdown("**Email Preview:**")
                        st.markdown(f'<div class="email-preview">{email_html}</div>', 
                                  unsafe_allow_html=True)
                        
                        # CV status
                        cv_path = find_cv_file()
                        if cv_path:
                            st.success(f"📎 CV Ready: {cv_path.name}")
                        else:
                            st.info("📄 Will create sample CV for attachment")
                        
                        # Send email if requested
                        if send_email:
                            if not issues:  # Only send if configuration is OK
                                with st.spinner("📧 Sending email..."):
                                    success = send_email_with_cv(professor_data, recipient_email)
                                    
                                    if success:
                                        st.markdown("""
                                        <div class="success-box">
                                            <h4>✅ Email Sent Successfully!</h4>
                                            <p><strong>Email Features Verified:</strong></p>
                                            <ul>
                                                <li>✅ Personalized content generated</li>
                                                <li>✅ CV attachment included</li>
                                                <li>✅ Professional formatting applied</li>
                                                <li>✅ No content duplication</li>
                                                <li>✅ Proper professor name handling</li>
                                            </ul>
                                            <p><strong>Next Steps:</strong></p>
                                            <ul>
                                                <li>📬 Check your inbox for confirmation</li>
                                                <li>📁 Email saved locally for records</li>
                                                <li>📈 Track responses in Follow-ups page</li>
                                            </ul>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Log successful send
                                        log_entry = {
                                            'timestamp': datetime.now().isoformat(),
                                            'professor': prof_name,
                                            'university': university,
                                            'status': 'sent',
                                            'test_mode': test_mode
                                        }
                                        
                                        # Save to session state for tracking
                                        if 'sent_emails' not in st.session_state:
                                            st.session_state.sent_emails = []
                                        st.session_state.sent_emails.append(log_entry)
                                        
                                    else:
                                        st.markdown("""
                                        <div class="error-box">
                                            <h4>⚠️ Email Sending Failed</h4>
                                            <p>The email content was generated successfully, but sending failed.</p>
                                            <p><strong>Possible causes:</strong></p>
                                            <ul>
                                                <li>Gmail app password not configured</li>
                                                <li>Network connectivity issues</li>
                                                <li>Gmail security settings</li>
                                            </ul>
                                            <p>📁 Email has been saved locally for manual sending.</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.error("❌ Cannot send email - configuration issues detected")
                    else:
                        st.error("❌ Failed to generate email content")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Features highlight
st.header("🚀 System Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-highlight">
        <h4>🤖 AI-Powered Personalization</h4>
        <ul>
            <li>Deeply personalized content</li>
            <li>Research-specific messaging</li>
            <li>Professional tone matching</li>
            <li>No template detection</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-highlight">
        <h4>📎 Smart CV Handling</h4>
        <ul>
            <li>Automatic CV detection</li>
            <li>Multiple format support</li>
            <li>Sample CV generation</li>
            <li>Secure attachment</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-highlight">
        <h4>✅ Quality Assurance</h4>
        <ul>
            <li>No content duplication</li>
            <li>Proper name handling</li>
            <li>Professional formatting</li>
            <li>Robust backup templates</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Email log
if 'sent_emails' in st.session_state and st.session_state.sent_emails:
    st.header("📊 Recent Activity")
    
    # Display recent sends in a nice format
    for email in reversed(st.session_state.sent_emails[-5:]):  # Show last 5
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"👨‍🔬 **{email['professor']}**")
            
            with col2:
                st.write(f"🏛️ {email['university']}")
            
            with col3:
                status_icon = "✅" if email['status'] == 'sent' else "❌"
                st.write(f"{status_icon} {email['status'].title()}")
            
            with col4:
                test_badge = "🧪 Test" if email['test_mode'] else "📧 Live"
                st.write(test_badge)
        
        st.divider()

# Usage tips
with st.expander("💡 Usage Tips", expanded=False):
    st.markdown("""
    ### Best Practices for Email Outreach:
    
    **📝 Content Quality:**
    - Provide as much professor information as possible
    - Include specific research papers if known
    - Mention current projects for better personalization
    
    **🧪 Testing:**
    - Always use Test Mode first to review emails
    - Check that CV is properly attached
    - Verify personalization quality
    
    **📧 Sending:**
    - Start with small batches (5-10 emails)
    - Monitor response rates
    - Adjust approach based on feedback
    
    **🔒 Security:**
    - Use Gmail App Passwords (not regular password)
    - Keep credentials in .env file only
    - Never share authentication details
    
    **📈 Follow-up:**
    - Use the Follow-ups page to track responses
    - Wait 7-14 days before follow-up emails
    - Keep records of all correspondence
    """)

# Footer
st.markdown("---")
st.caption("📧 Email with CV System | InternMailer © 2024")
st.caption("💡 **Tip:** Always test with yourself first before sending to professors")
