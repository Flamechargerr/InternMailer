"""
Analytics service for InternMailer UI

Handles analytics data processing and reporting.
"""

import requests
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class AnalyticsService:
    """Service for managing analytics and reporting."""
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize the analytics service.
        
        Args:
            api_url: Base URL for the API
            api_key: API authentication key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def get_campaign_analytics(self, campaign_id: str, 
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get analytics for a specific campaign.
        
        Args:
            campaign_id: ID of the campaign
            start_date: Start date for analytics (optional)
            end_date: End date for analytics (optional)
            
        Returns:
            Campaign analytics data or None if failed
        """
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            
            response = self.session.get(
                f"{self.api_url}/analytics/campaigns/{campaign_id}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch campaign analytics: {e}")
            return None
    
    def get_overall_metrics(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get overall email performance metrics.
        
        Args:
            start_date: Start date for metrics (optional)
            end_date: End date for metrics (optional)
            
        Returns:
            Overall metrics data or None if failed
        """
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            
            response = self.session.get(f"{self.api_url}/analytics/metrics", params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch overall metrics: {e}")
            return None
    
    def get_engagement_trends(self, period: str = "30d") -> Optional[List[Dict[str, Any]]]:
        """
        Get engagement trend data.
        
        Args:
            period: Time period for trends ("7d", "30d", "90d", "1y")
            
        Returns:
            List of engagement data points or None if failed
        """
        try:
            params = {"period": period}
            response = self.session.get(f"{self.api_url}/analytics/trends", params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch engagement trends: {e}")
            return None
    
    def get_top_performing_campaigns(self, limit: int = 10, 
                                   metric: str = "open_rate") -> Optional[List[Dict[str, Any]]]:
        """
        Get top performing campaigns.
        
        Args:
            limit: Number of campaigns to return
            metric: Metric to sort by ("open_rate", "click_rate", "conversion_rate")
            
        Returns:
            List of top performing campaigns or None if failed
        """
        try:
            params = {"limit": limit, "metric": metric}
            response = self.session.get(f"{self.api_url}/analytics/top-campaigns", params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch top campaigns: {e}")
            return None
    
    def get_audience_insights(self) -> Optional[Dict[str, Any]]:
        """
        Get audience demographic and behavioral insights.
        
        Returns:
            Audience insights data or None if failed
        """
        try:
            response = self.session.get(f"{self.api_url}/analytics/audience")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch audience insights: {e}")
            return None
    
    def get_delivery_analytics(self, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get email delivery analytics.
        
        Args:
            start_date: Start date for analytics (optional)
            end_date: End date for analytics (optional)
            
        Returns:
            Delivery analytics data or None if failed
        """
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            
            response = self.session.get(f"{self.api_url}/analytics/delivery", params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch delivery analytics: {e}")
            return None


# Global service instance
@st.cache_resource
def get_analytics_service() -> AnalyticsService:
    """Get a cached analytics service instance."""
    api_url = st.secrets.get("api_url", "http://localhost:8000")
    api_key = st.secrets.get("api_key")
    return AnalyticsService(api_url, api_key)


# Helper functions for data processing
def process_engagement_data(trends_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Process engagement trends data into a DataFrame.
    
    Args:
        trends_data: Raw trends data from API
        
    Returns:
        Processed DataFrame with engagement metrics
    """
    if not trends_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(trends_data)
    
    # Convert date strings to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Calculate derived metrics if needed
    if 'sent' in df.columns and 'opens' in df.columns:
        df['open_rate'] = (df['opens'] / df['sent'] * 100).round(2)
    
    if 'opens' in df.columns and 'clicks' in df.columns:
        df['click_rate'] = (df['clicks'] / df['opens'] * 100).fillna(0).round(2)
    
    return df


def calculate_period_comparison(current_data: Dict[str, Any], 
                               previous_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate percentage changes between two periods.
    
    Args:
        current_data: Current period metrics
        previous_data: Previous period metrics
        
    Returns:
        Dictionary with percentage changes
    """
    comparison = {}
    
    for key in current_data:
        if key in previous_data and isinstance(current_data[key], (int, float)):
            current_val = current_data[key]
            previous_val = previous_data[key]
            
            if previous_val != 0:
                change = ((current_val - previous_val) / previous_val) * 100
                comparison[f"{key}_change"] = round(change, 2)
            else:
                comparison[f"{key}_change"] = 0.0
    
    return comparison


def get_kpi_summary(period_days: int = 30) -> Dict[str, Any]:
    """
    Get a summary of key performance indicators.
    
    Args:
        period_days: Number of days to include in summary
        
    Returns:
        KPI summary dictionary
    """
    service = get_analytics_service()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    metrics = service.get_overall_metrics(start_date, end_date)
    
    if not metrics:
        return {
            "total_sent": 0,
            "total_delivered": 0,
            "total_opens": 0,
            "total_clicks": 0,
            "avg_open_rate": 0.0,
            "avg_click_rate": 0.0,
            "delivery_rate": 0.0
        }
    
    # Calculate rates
    total_sent = metrics.get('total_sent', 0)
    total_delivered = metrics.get('total_delivered', 0)
    total_opens = metrics.get('total_opens', 0)
    total_clicks = metrics.get('total_clicks', 0)
    
    return {
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_opens": total_opens,
        "total_clicks": total_clicks,
        "avg_open_rate": (total_opens / total_delivered * 100) if total_delivered > 0 else 0.0,
        "avg_click_rate": (total_clicks / total_opens * 100) if total_opens > 0 else 0.0,
        "delivery_rate": (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
    }
