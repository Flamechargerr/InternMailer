"""
Service Factory - Convenient methods to create and configure services.

This module provides factory methods for creating and configuring service
instances to ensure consistent initialization and resource management.

The service factory supports both production and mock services for flexible
development and testing.
"""

from typing import Optional

from .base import ServiceConfig
from .email import EmailService, MockEmailService
from .database import DatabaseService, MockDatabaseService
from .analytics import AnalyticsService, MockAnalyticsService


class ServiceFactory:
    """Factory for creating and managing services."""
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig()
        self.email_service = None
        self.database_service = None
        self.analytics_service = None
        
    def create_services(self) -> None:
        """Create and initialize all required services."""
        self.email_service = self._create_email_service()
        self.database_service = self._create_database_service()
        self.analytics_service = self._create_analytics_service()
    
    def _create_email_service(self):
        """Create email service based on configuration."""
        if self.config.use_mocks:
            return MockEmailService(self.config)
        return EmailService(self.config)
    
    def _create_database_service(self):
        """Create database service based on configuration."""
        if self.config.use_mocks:
            return MockDatabaseService(self.config)
        return DatabaseService(self.config)
    
    def _create_analytics_service(self):
        """Create analytics service based on configuration."""
        if self.config.use_mocks:
            return MockAnalyticsService(self.config)
        return AnalyticsService(self.config)


def create_services(config: Optional[ServiceConfig] = None):
    """Convenience function to create services."""
    factory = ServiceFactory(config)
    factory.create_services()
    return factory.email_service, factory.database_service, factory.analytics_service

