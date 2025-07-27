"""
Follow-up Scheduler Module

This module provides comprehensive follow-up scheduling capabilities for InternMailer.
"""

from .streamlit_api import get_followup_manager, FollowUpManager

__all__ = ['get_followup_manager', 'FollowUpManager']
