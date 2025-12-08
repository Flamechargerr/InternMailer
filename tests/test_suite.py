"""
InternMailer - Test Suite
Pytest-based tests for all major components
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_validator import get_email_validator
from reply_classifier import get_reply_classifier, ReplyCategory
from config_manager import get_config
from adaptive_rate_limiter import AdaptiveRateLimiter

class TestEmailValidator:
    """Test email validation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = get_email_validator()
    
    def test_valid_email(self):
        """Test validation of valid email"""
        result = self.validator.validate_email("professor@mit.edu")
        assert result['is_valid'] == True
        assert result['confidence'] > 0.8
    
    def test_invalid_format(self):
        """Test rejection of invalid email format"""
        result = self.validator.validate_email("invalid-email")
        assert result['is_valid'] == False
        assert "Invalid email format" in result['reason']
    
    def test_disposable_email(self):
        """Test detection of disposable emails"""
        result = self.validator.validate_email("test@tempmail.com")
        assert result['is_disposable'] == True
        assert result['is_valid'] == False
    
    def test_role_based_email(self):
        """Test rejection of role-based emails"""
        result = self.validator.validate_email("admin@example.com")
        assert result['is_valid'] == False
        assert "Role-based" in result['reason']

class TestReplyClassifier:
    """Test reply categorization"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.classifier = get_reply_classifier()
    
    def test_interested_reply(self):
        """Test classification of interested reply"""
        body = "Thanks for reaching out! I'm interested in discussing this further."
        result = self.classifier.classify_reply(body)
        assert result['category'] == ReplyCategory.INTERESTED
        assert result['confidence'] > 0.5
    
    def test_not_interested_reply(self):
        """Test classification of not interested reply"""
        body = "Thank you, but I'm not interested at this time."
        result = self.classifier.classify_reply(body)
        assert result['category'] == ReplyCategory.NOT_INTERESTED
    
    def test_out_of_office_reply(self):
        """Test detection of out of office"""
        body = "I am currently out of office and will return on Monday."
        result = self.classifier.classify_reply(body)
        assert result['category'] == ReplyCategory.OUT_OF_OFFICE
    
    def test_question_reply(self):
        """Test classification of question"""
        body = "Could you send me more information about your background?"
        result = self.classifier.classify_reply(body)
        assert result['category'] == ReplyCategory.QUESTION

class TestConfigManager:
    """Test configuration management"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = get_config()
    
    def test_get_config_value(self):
        """Test getting configuration values"""
        daily_limit = self.config.get('campaign.daily_limit')
        assert daily_limit is not None
        assert isinstance(daily_limit, int)
    
    def test_get_nested_config(self):
        """Test getting nested configuration"""
        smtp_server = self.config.get('email.smtp_server')
        assert smtp_server == 'smtp.gmail.com'
    
    def test_get_default_value(self):
        """Test default value for missing config"""
        value = self.config.get('nonexistent.key', 'default')
        assert value == 'default'
    
    def test_set_config_value(self):
        """Test setting configuration value"""
        self.config.set('test.value', 123)
        assert self.config.get('test.value') == 123

class TestAdaptiveRateLimiter:
    """Test adaptive rate limiting"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.limiter = AdaptiveRateLimiter()
    
    def test_calculate_safe_limit(self):
        """Test calculation of safe daily limit"""
        limit = self.limiter.calculate_safe_daily_limit()
        assert isinstance(limit, int)
        assert 10 <= limit <= 500
    
    def test_reputation_status(self):
        """Test reputation status generation"""
        status = self.limiter.get_reputation_status()
        assert 'bounce_rate' in status
        assert 'success_rate' in status
        assert 'recommended_limit' in status
        assert 'reputation_tier' in status

# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_email_validation_flow(self):
        """Test complete email validation workflow"""
        validator = get_email_validator()
        
        # Valid email should pass all checks
        result = validator.validate_email("valid@university.edu")
        if result['is_valid']:
            assert result['has_mx'] is not None
            assert result['confidence'] > 0
    
    def test_config_loading(self):
        """Test configuration can be loaded and accessed"""
        config = get_config()
        
        # Check critical config values exist
        assert config.get('email.smtp_server') is not None
        assert config.get('campaign.daily_limit') is not None
        assert config.get('logging.level') is not None

# Fixtures
@pytest.fixture
def sample_email_data():
    """Fixture providing sample email data for testing"""
    return {
        'valid_emails': [
            'professor@mit.edu',
            'researcher@stanford.edu',
            'admin@harvard.edu'
        ],
        'invalid_emails': [
            'invalid-email',
            'test@tempmail.com',
            '@nodomain.com'
        ]
    }

@pytest.fixture
def sample_replies():
    """Fixture providing sample email replies"""
    return {
        'interested': "I'm very interested! Let's schedule a call.",
        'not_interested': "Thanks, but we're not hiring right now.",
        'out_of_office': "I'm out of office until next week."
    }

if __name__ == '__main__':
    # Run tests
    pytest.main(['-v', __file__])
