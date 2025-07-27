"""
Form components for InternMailer UI

Reusable form components for data input and validation.
"""

import streamlit as st
from typing import Dict, Any, Optional


def email_campaign_form() -> Optional[Dict[str, Any]]:
    """
    Create an email campaign creation form.
    
    Returns:
        Dict with campaign data if form is submitted, None otherwise
    """
    with st.form("campaign_form"):
        st.subheader("📝 Create New Campaign")
        
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Campaign Name*", placeholder="Q1 Newsletter")
            subject = st.text_input("Email Subject*", placeholder="Welcome to our newsletter!")
        
        with col2:
            sender_name = st.text_input("Sender Name*", placeholder="InternMailer Team")
            sender_email = st.text_input("Sender Email*", placeholder="noreply@company.com")
        
        # Content
        st.subheader("📄 Content")
        
        template = st.selectbox("Template", ["Custom", "Newsletter", "Welcome", "Promotional"])
        
        if template == "Custom":
            content = st.text_area("Email Content*", height=200, 
                                 placeholder="Enter your email content here...")
        else:
            st.info(f"Using {template} template")
            content = f"Template: {template}"
        
        # Recipients
        st.subheader("👥 Recipients")
        
        recipient_type = st.radio("Send to:", ["All subscribers", "Segment", "Upload list"])
        
        if recipient_type == "Segment":
            segment = st.selectbox("Select Segment", ["Active Users", "New Subscribers", "High Engagement"])
        elif recipient_type == "Upload list":
            uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        # Schedule
        st.subheader("⏰ Schedule")
        
        send_type = st.radio("When to send:", ["Send now", "Schedule for later"])
        
        if send_type == "Schedule for later":
            col1, col2 = st.columns(2)
            with col1:
                send_date = st.date_input("Send Date")
            with col2:
                send_time = st.time_input("Send Time")
        
        # Submit
        submitted = st.form_submit_button("🚀 Create Campaign", type="primary")
        
        if submitted:
            # Validation
            if not all([name, subject, sender_name, sender_email, content]):
                st.error("Please fill in all required fields marked with *")
                return None
            
            campaign_data = {
                "name": name,
                "subject": subject,
                "sender_name": sender_name,
                "sender_email": sender_email,
                "content": content,
                "template": template,
                "recipient_type": recipient_type,
                "send_type": send_type
            }
            
            if send_type == "Schedule for later":
                campaign_data["send_date"] = send_date
                campaign_data["send_time"] = send_time
            
            return campaign_data
    
    return None


def contact_import_form() -> Optional[Dict[str, Any]]:
    """
    Create a contact import form.
    
    Returns:
        Dict with import data if form is submitted, None otherwise
    """
    with st.form("contact_import_form"):
        st.subheader("📇 Import Contacts")
        
        import_method = st.radio("Import method:", ["Upload CSV", "Manual entry", "API integration"])
        
        if import_method == "Upload CSV":
            uploaded_file = st.file_uploader("Select CSV file", type=['csv'])
            st.info("CSV should contain columns: email, first_name, last_name")
        
        elif import_method == "Manual entry":
            st.text_area("Email addresses (one per line)", height=150,
                        placeholder="john@example.com\njane@example.com")
        
        else:  # API integration
            api_endpoint = st.text_input("API Endpoint")
            api_key = st.text_input("API Key", type="password")
        
        # Options
        st.subheader("Import Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            update_existing = st.checkbox("Update existing contacts")
            send_welcome = st.checkbox("Send welcome email")
        
        with col2:
            segment = st.selectbox("Add to segment", ["None", "Imported", "Newsletter", "Prospects"])
            validate_emails = st.checkbox("Validate email addresses", value=True)
        
        submitted = st.form_submit_button("📥 Import Contacts", type="primary")
        
        if submitted:
            return {
                "import_method": import_method,
                "update_existing": update_existing,
                "send_welcome": send_welcome,
                "segment": segment,
                "validate_emails": validate_emails
            }
        
        return None
