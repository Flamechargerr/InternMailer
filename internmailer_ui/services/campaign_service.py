"""
Campaign Service for InternMailer UI

Handles campaign-related operations and integrates with the backend API.
"""

import requests
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class CampaignService:
    """Service for managing campaigns and integrating with backend."""
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize the campaign service.
        
        Args:
            api_url: Base URL for the campaign API
            api_key: API authentication key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def create(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new campaign using the backend API.
        
        Args:
            campaign_data: Campaign configuration data
            
        Returns:
            Created campaign data or None if failed
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/campaigns/", 
                json=campaign_data
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error creating campaign: {e}")
            st.error(f"Failed to create campaign: {e}")
            return None
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a campaign by ID.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign data or None if not found
        """
        try:
            response = self.session.get(f"{self.api_url}/api/campaigns/{campaign_id}")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting campaign {campaign_id}: {e}")
            return None
    
    def get_campaigns(
        self, 
        status_filter: Optional[str] = None,
        tenant_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get campaigns with optional filtering.
        
        Args:
            status_filter: Filter by campaign status
            tenant_id: Filter by tenant ID
            page: Page number
            page_size: Page size
            
        Returns:
            Dict with campaigns and pagination info
        """
        try:
            params = {
                'page': page,
                'page_size': page_size
            }
            
            if status_filter:
                params['status_filter'] = status_filter
            if tenant_id:
                params['tenant_id'] = tenant_id
            
            response = self.session.get(
                f"{self.api_url}/api/campaigns/", 
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting campaigns: {e}")
            return {
                'campaigns': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
    
    def update_campaign(
        self, 
        campaign_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a campaign.
        
        Args:
            campaign_id: Campaign ID
            updates: Updates to apply
            
        Returns:
            Updated campaign data or None if failed
        """
        try:
            response = self.session.put(
                f"{self.api_url}/api/campaigns/{campaign_id}", 
                json=updates
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error updating campaign {campaign_id}: {e}")
            return None
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(f"{self.api_url}/api/campaigns/{campaign_id}")
            response.raise_for_status()
            return True
        
        except requests.RequestException as e:
            self.logger.error(f"Error deleting campaign {campaign_id}: {e}")
            return False
    
    def start_campaign(
        self, 
        campaign_id: str, 
        send_immediately: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Start a campaign.
        
        Args:
            campaign_id: Campaign ID
            send_immediately: Whether to send immediately
            
        Returns:
            Updated campaign data or None if failed
        """
        try:
            params = {'send_immediately': send_immediately}
            response = self.session.post(
                f"{self.api_url}/api/campaigns/{campaign_id}/start",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error starting campaign {campaign_id}: {e}")
            return None
    
    def pause_campaign(
        self, 
        campaign_id: str, 
        reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Pause a campaign.
        
        Args:
            campaign_id: Campaign ID
            reason: Reason for pausing
            
        Returns:
            Updated campaign data or None if failed
        """
        try:
            params = {}
            if reason:
                params['reason'] = reason
            
            response = self.session.post(
                f"{self.api_url}/api/campaigns/{campaign_id}/pause",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error pausing campaign {campaign_id}: {e}")
            return None
    
    def resume_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume a paused campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Updated campaign data or None if failed
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/campaigns/{campaign_id}/resume"
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error resuming campaign {campaign_id}: {e}")
            return None
    
    def cancel_campaign(
        self, 
        campaign_id: str, 
        reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cancel a campaign.
        
        Args:
            campaign_id: Campaign ID
            reason: Reason for cancelling
            
        Returns:
            Updated campaign data or None if failed
        """
        try:
            params = {}
            if reason:
                params['reason'] = reason
            
            response = self.session.post(
                f"{self.api_url}/api/campaigns/{campaign_id}/cancel",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error cancelling campaign {campaign_id}: {e}")
            return None
    
    def get_campaign_analytics(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Analytics data or None if failed
        """
        try:
            response = self.session.get(
                f"{self.api_url}/api/campaigns/{campaign_id}/analytics"
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting analytics for campaign {campaign_id}: {e}")
            return None
    
    def get_campaign_history(self, campaign_id: str) -> List[Dict[str, Any]]:
        """
        Get history for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of history items
        """
        try:
            response = self.session.get(
                f"{self.api_url}/api/campaigns/{campaign_id}/history"
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting history for campaign {campaign_id}: {e}")
            return []
    
    def clone_campaign(
        self, 
        campaign_id: str, 
        new_name: str, 
        modifications: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Clone a campaign.
        
        Args:
            campaign_id: Original campaign ID
            new_name: Name for the cloned campaign
            modifications: Optional modifications to apply
            
        Returns:
            Cloned campaign data or None if failed
        """
        try:
            clone_data = {
                'new_name': new_name,
                'modifications': modifications or {}
            }
            
            response = self.session.post(
                f"{self.api_url}/api/campaigns/{campaign_id}/clone",
                json=clone_data
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error cloning campaign {campaign_id}: {e}")
            return None
    
    def bulk_send_now(self, campaign_ids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Send multiple campaigns immediately.
        
        Args:
            campaign_ids: List of campaign IDs
            
        Returns:
            Bulk operation result or None if failed
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/campaigns/bulk/send-now",
                json={'campaign_ids': campaign_ids}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error in bulk send now: {e}")
            return None
    
    def bulk_schedule(
        self, 
        campaign_ids: List[str], 
        schedule_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Schedule multiple campaigns.
        
        Args:
            campaign_ids: List of campaign IDs
            schedule_time: When to schedule the campaigns
            
        Returns:
            Bulk operation result or None if failed
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/campaigns/bulk/schedule",
                json={
                    'campaign_ids': campaign_ids,
                    'schedule_time': schedule_time.isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error in bulk schedule: {e}")
            return None
    
    def get_campaigns_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get summary statistics for all campaigns.
        
        Returns:
            Summary statistics or None if failed
        """
        try:
            response = self.session.get(f"{self.api_url}/api/campaigns/stats/summary")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting campaigns summary: {e}")
            return None
    
    def get_real_time_status(self) -> Optional[Dict[str, Any]]:
        """
        Get real-time status of all campaigns.
        
        Returns:
            Real-time status data or None if failed
        """
        try:
            response = self.session.get(f"{self.api_url}/api/campaigns/realtime/status")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting real-time status: {e}")
            return None
    
    def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """
        Get currently active campaigns.
        
        Returns:
            List of active campaigns
        """
        try:
            response = self.session.get(
                f"{self.api_url}/api/campaigns/",
                params={'status_filter': 'running,paused,scheduled'}
            )
            response.raise_for_status()
            result = response.json()
            return result.get('campaigns', [])
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting active campaigns: {e}")
            return []
    
    def get_campaign_logs(self, campaign_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent logs for a specific campaign.
        
        Args:
            campaign_id: Campaign ID
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries
        """
        try:
            params = {'limit': limit}
            response = self.session.get(
                f"{self.api_url}/api/campaigns/{campaign_id}/logs",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting logs for campaign {campaign_id}: {e}")
            return []
    
    def get_all_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent logs from all campaigns.
        
        Args:
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries from all campaigns
        """
        try:
            params = {'limit': limit}
            response = self.session.get(
                f"{self.api_url}/api/campaigns/logs/recent",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting recent logs: {e}")
            return []


# Global service instance
@st.cache_resource
def get_campaign_service() -> CampaignService:
    """Get a cached campaign service instance."""
    api_url = st.secrets.get("api_url", "http://localhost:8000")
    api_key = st.secrets.get("api_key")
    return CampaignService(api_url, api_key)


# Convenience functions for common operations
def create_campaign(campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a campaign using the service."""
    service = get_campaign_service()
    return service.create(campaign_data)


def get_recent_campaigns(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent campaigns."""
    service = get_campaign_service()
    result = service.get_campaigns(page_size=limit)
    return result.get('campaigns', [])


def get_campaign_metrics() -> Dict[str, Any]:
    """Get overall campaign metrics."""
    service = get_campaign_service()
    summary = service.get_campaigns_summary()
    
    if summary:
        return summary
    
    # Fallback to basic data if API fails
    return {
        "total_campaigns": 0,
        "status_breakdown": {},
        "tenant_breakdown": {},
        "recent_campaigns": 0
    }
