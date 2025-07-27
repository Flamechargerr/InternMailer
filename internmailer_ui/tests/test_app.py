"""
Test suite for InternMailer UI application

Basic tests to verify application functionality and structure.
"""

import sys
import os
import pytest

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import app
from services import email_service, user_service, analytics_service


class TestAppStructure:
    """Test the basic application structure and imports."""
    
    def test_app_main_function_exists(self):
        """Test that the main function exists in app.py."""
        assert hasattr(app, 'main')
        assert callable(app.main)
    
    def test_services_import(self):
        """Test that service modules can be imported."""
        assert email_service is not None
        assert user_service is not None
        assert analytics_service is not None
    
    def test_email_service_class_exists(self):
        """Test that EmailService class exists."""
        assert hasattr(email_service, 'EmailService')
        assert hasattr(email_service, 'get_email_service')
    
    def test_user_service_class_exists(self):
        """Test that UserService class exists."""
        assert hasattr(user_service, 'UserService')
        assert hasattr(user_service, 'get_user_service')
    
    def test_analytics_service_class_exists(self):
        """Test that AnalyticsService class exists."""
        assert hasattr(analytics_service, 'AnalyticsService')
        assert hasattr(analytics_service, 'get_analytics_service')


class TestEmailService:
    """Test EmailService functionality."""
    
    def test_email_service_initialization(self):
        """Test EmailService can be initialized."""
        service = email_service.EmailService()
        assert service.api_url == "http://localhost:8000"
        assert service.api_key is None
    
    def test_email_service_with_api_key(self):
        """Test EmailService with API key."""
        service = email_service.EmailService(api_key="test-key")
        assert "Authorization" in service.session.headers
        assert service.session.headers["Authorization"] == "Bearer test-key"


class TestUserService:
    """Test UserService functionality."""
    
    def test_user_service_initialization(self):
        """Test UserService can be initialized."""
        service = user_service.UserService()
        assert service.api_url == "http://localhost:8000"
        assert service.api_key is None


class TestAnalyticsService:
    """Test AnalyticsService functionality."""
    
    def test_analytics_service_initialization(self):
        """Test AnalyticsService can be initialized."""
        service = analytics_service.AnalyticsService()
        assert service.api_url == "http://localhost:8000"
        assert service.api_key is None


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_campaign_metrics_calculation(self):
        """Test campaign metrics calculation."""
        metrics = email_service.get_campaign_metrics()
        assert isinstance(metrics, dict)
        assert "total_campaigns" in metrics
        assert "total_sent" in metrics
        assert "avg_open_rate" in metrics
        assert "avg_click_rate" in metrics
    
    def test_kpi_summary_calculation(self):
        """Test KPI summary calculation."""
        kpi = analytics_service.get_kpi_summary()
        assert isinstance(kpi, dict)
        assert "total_sent" in kpi
        assert "avg_open_rate" in kpi
        assert "delivery_rate" in kpi


if __name__ == "__main__":
    pytest.main([__file__])
