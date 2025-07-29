"""
Centralized Email Management
Handles email generation, preview, and sending for the InternMailer application
"""

import streamlit as st
from email_generator import EmailGenerator
from gmail_sender import GmailSender
from datetime import datetime
import os

class EmailManager:
    """Class to manage email operations"""
    
    def __init__(self, config):
        self.email_generator = EmailGenerator()
        self.gmail_sender = GmailSender(config['gmail_user'], config['gmail_password'])
        self.config = config

    def generate_email(self, professor_data):
        """Generate personalized email content"""
        try:
            email_content = self.email_generator.generate_email(professor_data)
            return email_content
        except Exception as e:
            st.error(f"Failed to generate email: {str(e)}")
            return None

    def send_email(self, to_email, subject, body):
        """Send email using GmailSender"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'recipient': to_email,
                'status': 'sent'
            }
            success = self.gmail_sender.send_email(to_email, subject, body)
            if success:
                st.success("✅ Email sent successfully!")
                log_entry['status'] = 'sent'
            else:
                st.error("❌ Failed to send email. Check credentials.")
                log_entry['status'] = 'failed'

            # Log send attempt
            self._log_email(log_entry)

        except Exception as e:
            st.error(f"Error sending email: {str(e)}")


    def _log_email(self, log_entry):
        """Log email send attempts"""
        if 'sent_emails' not in st.session_state:
            st.session_state.sent_emails = []
        st.session_state.sent_emails.append(log_entry)

# Global email manager instance
email_manager = EmailManager(config_manager.config)
