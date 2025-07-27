"""
Email service for InternMailer UI

Handles email campaign operations and API interactions.
"""

import requests
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime


class EmailService:
    """Service for managing email campaigns and operations."""
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize the email service.
        
        Args:
            api_url: Base URL for the API
            api_key: API authentication key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def get_campaigns(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve email campaigns.
        
        Args:
            status: Filter by campaign status (optional)
            
        Returns:
            List of campaign dictionaries
        """
        try:
            params = {}
            if status:
                params['status'] = status
            
            response = self.session.get(f"{self.api_url}/campaigns", params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch campaigns: {e}")
            return []
    
    def create_campaign(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new email campaign.
        
        Args:
            campaign_data: Campaign configuration data
            
        Returns:
            Created campaign data or None if failed
        """
        try:
            response = self.session.post(f"{self.api_url}/campaigns", json=campaign_data)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to create campaign: {e}")
            return None
    
    def send_campaign(self, campaign_id: str) -> bool:
        """
        Send an email campaign.
        
        Args:
            campaign_id: ID of the campaign to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.post(f"{self.api_url}/campaigns/{campaign_id}/send")
            response.raise_for_status()
            return True
        
        except requests.RequestException as e:
            st.error(f"Failed to send campaign: {e}")
            return False
    
    def get_campaign_stats(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get campaign statistics.
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Campaign statistics or None if failed
        """
        try:
            response = self.session.get(f"{self.api_url}/campaigns/{campaign_id}/stats")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch campaign stats: {e}")
            return None
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Retrieve email templates.
        
        Returns:
            List of template dictionaries
        """
        try:
            response = self.session.get(f"{self.api_url}/templates")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch templates: {e}")
            return []
    
    def validate_email_list(self, emails: List[str]) -> Dict[str, List[str]]:
        """
        Validate a list of email addresses.
        
        Args:
            emails: List of email addresses to validate
            
        Returns:
            Dict with 'valid' and 'invalid' email lists
        """
        try:
            response = self.session.post(
                f"{self.api_url}/validate-emails", 
                json={"emails": emails}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to validate emails: {e}")
            return {"valid": [], "invalid": emails}
    
    def get_contact_segments(self) -> List[Dict[str, Any]]:
        """
        Retrieve contact segments.
        
        Returns:
            List of segment dictionaries
        """
        try:
            response = self.session.get(f"{self.api_url}/segments")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch segments: {e}")
            return []


# Global service instance
@st.cache_resource
def get_email_service() -> EmailService:
    """Get a cached email service instance."""
    api_url = st.secrets.get("api_url", "http://localhost:8000")
    api_key = st.secrets.get("api_key")
    return EmailService(api_url, api_key)


# Convenience functions for common operations
def get_recent_campaigns(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent campaigns."""
    service = get_email_service()
    campaigns = service.get_campaigns()
    return sorted(campaigns, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]


def get_campaign_metrics() -> Dict[str, Any]:
    """Get overall campaign metrics."""
    service = get_email_service()
    campaigns = service.get_campaigns()
    
    if not campaigns:
        return {
            "total_campaigns": 0,
            "total_sent": 0,
            "avg_open_rate": 0,
            "avg_click_rate": 0
        }
    
    total_sent = sum(c.get('sent_count', 0) for c in campaigns)
    total_opens = sum(c.get('open_count', 0) for c in campaigns)
    total_clicks = sum(c.get('click_count', 0) for c in campaigns)
    
    return {
        "total_campaigns": len(campaigns),
        "total_sent": total_sent,
        "avg_open_rate": (total_opens / total_sent * 100) if total_sent > 0 else 0,
        "avg_click_rate": (total_clicks / total_opens * 100) if total_opens > 0 else 0
    }
