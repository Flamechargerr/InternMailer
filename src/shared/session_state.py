"""
Centralized Session State Management
Provides a unified interface for managing Streamlit session state across all pages
"""

import streamlit as st
from typing import Any, Optional, Dict, List
from datetime import datetime, date
import json

class SessionStateManager:
    """Centralized manager for Streamlit session state"""
    
    # Define all session state keys used across the application
    RESUME_PATH = "resume_path"
    CAMPAIGN_RESULTS = "campaign_results"
    SENT_EMAILS = "sent_emails"
    EMAIL_RECIPIENT = "email_recipient"
    EMAILS_SENT_TODAY = "emails_sent_today"
    CURRENT_USER_PROFILE = "current_user_profile"
    SCRAPING_PROGRESS = "scraping_progress"
    SELECTED_PROFESSORS = "selected_professors"
    EMAIL_DRAFTS = "email_drafts"
    APPLICATION_STATUS = "application_status"
    LAST_SYNC_TIME = "last_sync_time"
    USER_PREFERENCES = "user_preferences"
    NAVIGATION_HISTORY = "navigation_history"
    ACTIVE_CAMPAIGNS = "active_campaigns"
    
    def __init__(self):
        """Initialize session state manager"""
        self._initialize_default_values()
    
    def _initialize_default_values(self):
        """Initialize default values for session state keys if they don't exist"""
        defaults = {
            self.RESUME_PATH: None,
            self.CAMPAIGN_RESULTS: {},
            self.SENT_EMAILS: [],
            self.EMAIL_RECIPIENT: None,
            self.EMAILS_SENT_TODAY: 0,
            self.CURRENT_USER_PROFILE: {},
            self.SCRAPING_PROGRESS: 0,
            self.SELECTED_PROFESSORS: [],
            self.EMAIL_DRAFTS: {},
            self.APPLICATION_STATUS: {},
            self.LAST_SYNC_TIME: None,
            self.USER_PREFERENCES: {
                "theme": "light",
                "email_signature": "",
                "default_batch_size": 10,
                "auto_save": True
            },
            self.NAVIGATION_HISTORY: [],
            self.ACTIVE_CAMPAIGNS: []
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from session state"""
        return st.session_state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in session state"""
        st.session_state[key] = value
    
    def update(self, **kwargs) -> None:
        """Update multiple session state values"""
        for key, value in kwargs.items():
            st.session_state[key] = value
    
    def delete(self, key: str) -> None:
        """Delete a key from session state"""
        if key in st.session_state:
            del st.session_state[key]
    
    def clear_all(self) -> None:
        """Clear all session state (use with caution)"""
        st.session_state.clear()
        self._initialize_default_values()
    
    def has_key(self, key: str) -> bool:
        """Check if a key exists in session state"""
        return key in st.session_state
    
    # Convenience methods for commonly used state
    
    def get_resume_path(self) -> Optional[str]:
        """Get the current resume path"""
        return self.get(self.RESUME_PATH)
    
    def set_resume_path(self, path: str) -> None:
        """Set the resume path"""
        self.set(self.RESUME_PATH, path)
    
    def get_emails_sent_today(self) -> int:
        """Get count of emails sent today"""
        return self.get(self.EMAILS_SENT_TODAY, 0)
    
    def increment_emails_sent_today(self, count: int = 1) -> None:
        """Increment the count of emails sent today"""
        current = self.get_emails_sent_today()
        self.set(self.EMAILS_SENT_TODAY, current + count)
    
    def reset_daily_email_count(self) -> None:
        """Reset the daily email count (called at midnight or app restart)"""
        self.set(self.EMAILS_SENT_TODAY, 0)
    
    def add_sent_email(self, email_data: Dict) -> None:
        """Add an email to the sent emails log"""
        sent_emails = self.get(self.SENT_EMAILS, [])
        email_entry = {
            'timestamp': datetime.now().isoformat(),
            'date': date.today().isoformat(),
            **email_data
        }
        sent_emails.append(email_entry)
        self.set(self.SENT_EMAILS, sent_emails)
        self.increment_emails_sent_today()
    
    def get_sent_emails_today(self) -> List[Dict]:
        """Get emails sent today"""
        today = date.today().isoformat()
        sent_emails = self.get(self.SENT_EMAILS, [])
        return [email for email in sent_emails if email.get('date') == today]
    
    def get_campaign_results(self) -> Dict:
        """Get current campaign results"""
        return self.get(self.CAMPAIGN_RESULTS, {})
    
    def set_campaign_results(self, results: Dict) -> None:
        """Set campaign results"""
        self.set(self.CAMPAIGN_RESULTS, results)
    
    def add_selected_professor(self, professor_data: Dict) -> None:
        """Add a professor to the selected list"""
        selected = self.get(self.SELECTED_PROFESSORS, [])
        # Avoid duplicates based on email
        if not any(p.get('email') == professor_data.get('email') for p in selected):
            selected.append(professor_data)
            self.set(self.SELECTED_PROFESSORS, selected)
    
    def remove_selected_professor(self, email: str) -> None:
        """Remove a professor from the selected list"""
        selected = self.get(self.SELECTED_PROFESSORS, [])
        updated = [p for p in selected if p.get('email') != email]
        self.set(self.SELECTED_PROFESSORS, updated)
    
    def clear_selected_professors(self) -> None:
        """Clear all selected professors"""
        self.set(self.SELECTED_PROFESSORS, [])
    
    def get_user_preferences(self) -> Dict:
        """Get user preferences"""
        return self.get(self.USER_PREFERENCES, {})
    
    def update_user_preference(self, key: str, value: Any) -> None:
        """Update a specific user preference"""
        prefs = self.get_user_preferences()
        prefs[key] = value
        self.set(self.USER_PREFERENCES, prefs)
    
    def get_scraping_progress(self) -> int:
        """Get current scraping progress"""
        return self.get(self.SCRAPING_PROGRESS, 0)
    
    def set_scraping_progress(self, progress: int) -> None:
        """Set scraping progress (0-100)"""
        self.set(self.SCRAPING_PROGRESS, max(0, min(100, progress)))
    
    def track_navigation(self, page_name: str) -> None:
        """Track navigation history"""
        history = self.get(self.NAVIGATION_HISTORY, [])
        history.append({
            'page': page_name,
            'timestamp': datetime.now().isoformat(),
            'visited_at': datetime.now().strftime('%H:%M:%S')
        })
        # Keep only last 10 pages
        if len(history) > 10:
            history = history[-10:]
        self.set(self.NAVIGATION_HISTORY, history)
    
    def get_navigation_history(self) -> List[Dict]:
        """Get navigation history"""
        return self.get(self.NAVIGATION_HISTORY, [])
    
    def save_email_draft(self, recipient: str, subject: str, body: str) -> None:
        """Save an email draft"""
        drafts = self.get(self.EMAIL_DRAFTS, {})
        drafts[recipient] = {
            'subject': subject,
            'body': body,
            'saved_at': datetime.now().isoformat()
        }
        self.set(self.EMAIL_DRAFTS, drafts)
    
    def get_email_draft(self, recipient: str) -> Optional[Dict]:
        """Get an email draft for a recipient"""
        drafts = self.get(self.EMAIL_DRAFTS, {})
        return drafts.get(recipient)
    
    def delete_email_draft(self, recipient: str) -> None:
        """Delete an email draft"""
        drafts = self.get(self.EMAIL_DRAFTS, {})
        if recipient in drafts:
            del drafts[recipient]
            self.set(self.EMAIL_DRAFTS, drafts)
    
    def update_last_sync_time(self) -> None:
        """Update the last sync time to now"""
        self.set(self.LAST_SYNC_TIME, datetime.now().isoformat())
    
    def get_last_sync_time(self) -> Optional[str]:
        """Get the last sync time"""
        return self.get(self.LAST_SYNC_TIME)
    
    def debug_info(self) -> Dict:
        """Get debug information about current session state"""
        return {
            'total_keys': len(st.session_state),
            'session_keys': list(st.session_state.keys()),
            'emails_sent_today': self.get_emails_sent_today(),
            'selected_professors_count': len(self.get(self.SELECTED_PROFESSORS, [])),
            'navigation_history_count': len(self.get_navigation_history()),
            'has_resume': self.get_resume_path() is not None,
            'has_campaign_results': bool(self.get_campaign_results()),
            'last_sync': self.get_last_sync_time()
        }

# Global session state manager instance
session_state = SessionStateManager()
