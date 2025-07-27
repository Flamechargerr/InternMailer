"""
Services module for InternMailer UI

Business logic and API integration services.
"""

from . import email_service
from . import user_service
from . import analytics_service
from . import campaign_service
from .email_service import get_email_service
from .user_service import get_user_service
from .analytics_service import get_analytics_service
from .campaign_service import get_campaign_service

__all__ = ["email_service", "user_service", "analytics_service", "campaign_service", "get_email_service", "get_user_service", "get_analytics_service", "get_campaign_service"]
