"""
Simple Interface Functions - Streamlit-compatible convenience functions.

This module provides simple, synchronous interface functions that wrap the
async services, making them easy to use from Streamlit pages.

These functions handle service initialization, async/sync conversion, and
provide clean error handling for UI consumption.
"""

import asyncio
from typing import Any, Dict, List, Optional

from .base import ServiceConfig, create_sync_adapter
from .factory import create_services
from .email import EmailRequest
from .database import QueryFilters
from .analytics import AnalyticsQuery, TimeRange

# Global service instances (cached for Streamlit compatibility)
_services_cache = None


def _get_services():
    """Get or create cached service instances."""
    global _services_cache
    
    if _services_cache is None:
        # Create services with default configuration
        config = ServiceConfig()
        email_service, database_service, analytics_service = create_services(config)
        
        # Create sync adapters for Streamlit compatibility
        _services_cache = {
            'email': create_sync_adapter(email_service),
            'database': create_sync_adapter(database_service),
            'analytics': create_sync_adapter(analytics_service)
        }
        
        # Initialize services
        asyncio.run(_initialize_services_async(email_service, database_service, analytics_service))
    
    return _services_cache


async def _initialize_services_async(email_service, database_service, analytics_service):
    """Initialize all services asynchronously."""
    await email_service.initialize()
    await database_service.initialize()
    await analytics_service.initialize()


def send_email(
    recipient: str,
    subject: str,
    body: str,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    campaign_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email using the email service.
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body: Email body content
        sender_name: Optional sender name
        sender_email: Optional sender email
        campaign_id: Optional campaign ID for tracking
        
    Returns:
        Dictionary with sending result information
        
    Example:
        result = send_email(
            recipient="professor@university.edu",
            subject="Research Collaboration Inquiry",
            body="Dear Professor, I am interested in..."
        )
        
        if result['status'] == 'sent':
            st.success(f"Email sent successfully!")
        else:
            st.error(f"Failed to send email: {result.get('error_message')}")
    """
    services = _get_services()
    email_service = services['email']
    
    try:
        # Create email request
        request = EmailRequest(
            recipient=recipient,
            subject=subject,
            body=body,
            sender_name=sender_name,
            sender_email=sender_email,
            campaign_id=campaign_id
        )
        
        # Send email (sync call)
        result = email_service.send_email(request)
        
        return {
            'status': result.status.value,
            'message_id': result.message_id,
            'sent_at': result.sent_at.isoformat() if result.sent_at else None,
            'error_message': result.error_message,
            'execution_time': result.execution_time
        }
        
    except Exception as e:
        return {
            'status': 'failed',
            'error_message': str(e),
            'execution_time': None
        }


def fetch_metrics(
    time_range: str = "30d",
    campaign_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch analytics metrics for the specified time range.
    
    Args:
        time_range: Time range for metrics ("24h", "7d", "30d", "90d", "1y", "all")
        campaign_id: Optional specific campaign ID
        
    Returns:
        Dictionary with metrics data
        
    Example:
        metrics = fetch_metrics(time_range="7d")
        
        st.metric("Total Sent", metrics['total_emails_sent'])
        st.metric("Open Rate", f"{metrics['open_rate']:.1f}%")
        st.metric("Click Rate", f"{metrics['click_rate']:.1f}%")
    """
    services = _get_services()
    analytics_service = services['analytics']
    
    try:
        # Map string to enum
        time_range_enum = getattr(TimeRange, f"LAST_{time_range.upper()}", TimeRange.LAST_30D)
        
        # Create query
        query = AnalyticsQuery(time_range=time_range_enum)
        
        if campaign_id:
            # Get specific campaign metrics
            campaign_metrics = analytics_service.get_campaign_metrics(campaign_id)
            if campaign_metrics:
                return {
                    'campaign_id': campaign_metrics.campaign_id,
                    'campaign_name': campaign_metrics.campaign_name,
                    'total_emails_sent': campaign_metrics.emails_sent,
                    'total_emails_delivered': campaign_metrics.emails_delivered,
                    'total_emails_opened': campaign_metrics.emails_opened,
                    'total_emails_clicked': campaign_metrics.emails_clicked,
                    'delivery_rate': campaign_metrics.delivery_rate,
                    'open_rate': campaign_metrics.open_rate,
                    'click_rate': campaign_metrics.click_rate,
                    'reply_rate': campaign_metrics.reply_rate,
                    'bounce_rate': campaign_metrics.bounce_rate
                }
        
        # Get overall metrics summary
        summary = analytics_service.get_metrics_summary(query)
        
        return {
            'total_emails_sent': summary.total_emails_sent,
            'total_emails_delivered': summary.total_emails_delivered,
            'total_emails_opened': summary.total_emails_opened,
            'total_emails_clicked': summary.total_emails_clicked,
            'total_emails_replied': summary.total_emails_replied,
            'total_emails_bounced': summary.total_emails_bounced,
            'delivery_rate': summary.delivery_rate,
            'open_rate': summary.open_rate,
            'click_rate': summary.click_rate,
            'reply_rate': summary.reply_rate,
            'bounce_rate': summary.bounce_rate,
            'total_campaigns': summary.total_campaigns,
            'active_campaigns': summary.active_campaigns,
            'total_contacts': summary.total_contacts,
            'time_range': summary.time_range.value,
            'start_date': summary.start_date.isoformat() if summary.start_date else None,
            'end_date': summary.end_date.isoformat() if summary.end_date else None
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'total_emails_sent': 0,
            'total_emails_delivered': 0,
            'total_emails_opened': 0,
            'total_emails_clicked': 0,
            'delivery_rate': 0.0,
            'open_rate': 0.0,
            'click_rate': 0.0
        }


def list_contacts(
    limit: Optional[int] = None,
    organization: Optional[str] = None,
    tags: Optional[List[str]] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> List[Dict[str, Any]]:
    """
    List contacts with optional filtering and sorting.
    
    Args:
        limit: Maximum number of contacts to return
        organization: Filter by organization name
        tags: Filter by tags
        sort_by: Field to sort by
        sort_order: Sort order ("asc" or "desc")
        
    Returns:
        List of contact dictionaries
        
    Example:
        contacts = list_contacts(limit=10, organization="MIT")
        
        for contact in contacts:
            st.write(f"{contact['first_name']} {contact['last_name']}")
            st.write(f"Email: {contact['email']}")
            st.write(f"Organization: {contact['organization']}")
    """
    services = _get_services()
    database_service = services['database']
    
    try:
        # Create filters
        filters = QueryFilters(
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Add filter conditions
        if organization or tags:
            filters.filters = {}
            if organization:
                filters.filters['organization'] = organization
            if tags:
                filters.filters['tags'] = tags
        
        # Get contacts
        contacts = database_service.list_contacts(filters)
        
        # Convert to dictionaries for easy Streamlit consumption
        result = []
        for contact in contacts:
            result.append({
                'id': contact.id,
                'email': contact.email,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'organization': contact.organization,
                'position': contact.position,
                'research_areas': contact.research_areas or [],
                'tags': contact.tags or [],
                'created_at': contact.created_at.isoformat() if contact.created_at else None,
                'updated_at': contact.updated_at.isoformat() if contact.updated_at else None
            })
        
        return result
        
    except Exception as e:
        # Return empty list on error, but log it
        print(f"Error listing contacts: {e}")
        return []


def list_campaigns(
    limit: Optional[int] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> List[Dict[str, Any]]:
    """
    List campaigns with optional filtering and sorting.
    
    Args:
        limit: Maximum number of campaigns to return
        status: Filter by campaign status
        sort_by: Field to sort by
        sort_order: Sort order ("asc" or "desc")
        
    Returns:
        List of campaign dictionaries
        
    Example:
        campaigns = list_campaigns(status="active")
        
        for campaign in campaigns:
            st.write(f"Campaign: {campaign['name']}")
            st.write(f"Status: {campaign['status']}")
            st.write(f"Emails sent: {campaign['emails_sent']}")
    """
    services = _get_services()
    database_service = services['database']
    
    try:
        # Create filters
        filters = QueryFilters(
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Add filter conditions
        if status:
            filters.filters = {'status': status}
        
        # Get campaigns
        campaigns = database_service.list_campaigns(filters)
        
        # Convert to dictionaries
        result = []
        for campaign in campaigns:
            result.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'status': campaign.status,
                'total_contacts': campaign.total_contacts,
                'emails_sent': campaign.emails_sent,
                'emails_delivered': campaign.emails_delivered,
                'emails_opened': campaign.emails_opened,
                'emails_clicked': campaign.emails_clicked,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'updated_at': campaign.updated_at.isoformat() if campaign.updated_at else None
            })
        
        return result
        
    except Exception as e:
        print(f"Error listing campaigns: {e}")
        return []


def get_time_series_data(
    time_range: str = "30d",
    granularity: str = "day"
) -> List[Dict[str, Any]]:
    """
    Get time series analytics data.
    
    Args:
        time_range: Time range for data ("24h", "7d", "30d", "90d", "1y")
        granularity: Data granularity ("hour", "day", "week", "month")
        
    Returns:
        List of time series data points
        
    Example:
        data = get_time_series_data(time_range="7d")
        
        dates = [point['timestamp'] for point in data]
        sent = [point['emails_sent'] for point in data]
        
        chart_data = pd.DataFrame({'Date': dates, 'Emails Sent': sent})
        st.line_chart(chart_data.set_index('Date'))
    """
    services = _get_services()
    analytics_service = services['analytics']
    
    try:
        # Map string to enum
        time_range_enum = getattr(TimeRange, f"LAST_{time_range.upper()}", TimeRange.LAST_30D)
        
        # Create query
        query = AnalyticsQuery(
            time_range=time_range_enum,
            granularity=granularity
        )
        
        # Get time series data
        return analytics_service.get_time_series_data(query)
        
    except Exception as e:
        print(f"Error getting time series data: {e}")
        return []


def create_contact(contact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new contact.
    
    Args:
        contact_data: Dictionary with contact information
        
    Returns:
        Created contact data or None if failed
        
    Example:
        contact = create_contact({
            'email': 'new.professor@university.edu',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'organization': 'University of Example',
            'position': 'Associate Professor',
            'research_areas': ['Machine Learning', 'AI'],
            'tags': ['academic', 'ml']
        })
        
        if contact:
            st.success(f"Contact created: {contact['email']}")
        else:
            st.error("Failed to create contact")
    """
    services = _get_services()
    database_service = services['database']
    
    try:
        contact = database_service.create_contact(contact_data)
        
        return {
            'id': contact.id,
            'email': contact.email,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'organization': contact.organization,
            'position': contact.position,
            'research_areas': contact.research_areas or [],
            'tags': contact.tags or [],
            'created_at': contact.created_at.isoformat() if contact.created_at else None
        }
        
    except Exception as e:
        print(f"Error creating contact: {e}")
        return None


def health_check() -> Dict[str, Any]:
    """
    Get health status of all services.
    
    Returns:
        Dictionary with health status information
        
    Example:
        health = health_check()
        
        if health['overall_status'] == 'healthy':
            st.success("All services are running properly")
        else:
            st.warning("Some services have issues")
            for service, status in health['services'].items():
                if status['status'] != 'healthy':
                    st.error(f"{service}: {status.get('error')}")
    """
    try:
        services = _get_services()
        
        # Get health status from each service
        email_health = services['email'].health_check()
        database_health = services['database'].health_check()
        analytics_health = services['analytics'].health_check()
        
        # Determine overall status
        all_healthy = all([
            email_health.get('status') == 'healthy',
            database_health.get('status') == 'healthy',
            analytics_health.get('status') == 'healthy'
        ])
        
        return {
            'overall_status': 'healthy' if all_healthy else 'unhealthy',
            'services': {
                'email': email_health,
                'database': database_health,
                'analytics': analytics_health
            }
        }
        
    except Exception as e:
        return {
            'overall_status': 'error',
            'error': str(e),
            'services': {}
        }
