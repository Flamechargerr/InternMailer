"""
Shared Backend Services Layer for InternMailer

This module provides a comprehensive, reusable services layer that abstracts
away the complexity of email sending, database operations, and analytics.

Key Features:
- Async-first design with sync wrappers for Streamlit compatibility
- Mock adapters for local development and testing
- Comprehensive error handling and logging
- Clean interfaces for Streamlit pages
- Production-ready with proper connection pooling and resource management
"""

from .base import BaseService, ServiceConfig
from .email import EmailService, MockEmailService
from .database import DatabaseService, MockDatabaseService
from .analytics import AnalyticsService, MockAnalyticsService
from .factory import ServiceFactory, create_services

# Convenience imports for common operations
from .interfaces import send_email, fetch_metrics, list_contacts

__all__ = [
    # Base classes
    "BaseService",
    "ServiceConfig",
    
    # Core services
    "EmailService", 
    "DatabaseService", 
    "AnalyticsService",
    
    # Mock services for development
    "MockEmailService",
    "MockDatabaseService", 
    "MockAnalyticsService",
    
    # Factory and creation utilities
    "ServiceFactory",
    "create_services",
    
    # Simple interface functions
    "send_email",
    "fetch_metrics", 
    "list_contacts",
]
