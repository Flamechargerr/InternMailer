"""
Comprehensive test suite for the EmailEngine module.

Tests cover:
- SMTP and Graph API providers
- Duplicate prevention
- Retry logic with exponential backoff  
- Rate limiting
- Database integration
- Concurrent email sending
- Error handling
"""

import pytest
import time
import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import smtplib

from src.email_engine import (
    EmailEngine, SMTPProvider, GraphAPIProvider, DuplicatePreventionService,
    RateLimiter, EmailRequest, EmailResult, SendStatus, EmailProvider,
    RetryConfig, RateLimitConfig, create_email_engine
)
from src.database.models import Email, EmailStatus, Contact, Campaign
from src.database.session import get_db_session


class TestEmailRequest:
    """Test EmailRequest dataclass."""
    
    def test_email_request_creation(self):
        """Test creating EmailRequest with required fields."""
        request = EmailRequest(
            email_id="test-001",
            campaign_id="campaign-001", 
            recipient="test@example.com",
            subject="Test Subject",
            body="Test body",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        assert request.email_id == "test-001"
        assert request.campaign_id == "campaign-001"
        assert request.recipient == "test@example.com"
        assert request.priority == 5  # default value
        assert request.scheduled_at is None
        assert request.personalization_data is None

    def test_email_request_with_optional_fields(self):
        """Test EmailRequest with all optional fields."""
        scheduled_time = datetime.now(timezone.utc)
        personalization = {"name": "John", "company": "ACME"}
        
        request = EmailRequest(
            email_id="test-002",
            campaign_id="campaign-002",
            recipient="john@acme.com",
            subject="Hello {{name}}",
            body="Welcome to {{company}}",
            sender_name="Sales Team",
            sender_email="sales@company.com",
            priority=8,
            scheduled_at=scheduled_time,
            personalization_data=personalization,
            template_id="template-001"
        )
        
        assert request.priority == 8
        assert request.scheduled_at == scheduled_time
        assert request.personalization_data == personalization
        assert request.template_id == "template-001"


class TestEmailResult:
    """Test EmailResult dataclass."""
    
    def test_email_result_creation(self):
        """Test creating EmailResult."""
        sent_time = datetime.now(timezone.utc)
        
        result = EmailResult(
            email_id="test-001",
            recipient="test@example.com",
            status=SendStatus.SENT,
            message_id="<msg123@smtp.gmail.com>",
            sent_at=sent_time,
            execution_time=1.5
        )
        
        assert result.email_id == "test-001"
        assert result.recipient == "test@example.com"
        assert result.status == SendStatus.SENT
        assert result.message_id == "<msg123@smtp.gmail.com>"
        assert result.sent_at == sent_time
        assert result.execution_time == 1.5
        assert result.retry_count == 0

    def test_email_result_to_dict(self):
        """Test converting EmailResult to dictionary."""
        sent_time = datetime.now(timezone.utc)
        
        result = EmailResult(
            email_id="test-001",
            recipient="test@example.com",
            status=SendStatus.SENT,
            sent_at=sent_time
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["email_id"] == "test-001"
        assert result_dict["recipient"] == "test@example.com"
        assert result_dict["status"] == SendStatus.SENT
        assert result_dict["sent_at"] == sent_time.isoformat()

    def test_email_result_failed(self):
        """Test EmailResult for failed email."""
        result = EmailResult(
            email_id="test-002",
            recipient="invalid@example.com",
            status=SendStatus.FAILED,
            error_message="SMTP connection failed",
            retry_count=3,
            execution_time=30.0
        )
        
        assert result.status == SendStatus.FAILED
        assert result.error_message == "SMTP connection failed"
        assert result.retry_count == 3
        assert result.sent_at is None
        assert result.message_id is None


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_rate_limiter_creation(self):
        """Test creating RateLimiter."""
        config = RateLimitConfig(
            emails_per_minute=60,
            emails_per_hour=1000,
            emails_per_day=5000,
            burst_size=10
        )
        
        limiter = RateLimiter(config)
        
        assert limiter.config == config
        assert limiter._tokens == config.burst_size
        assert limiter._hourly_count == 0
        assert limiter._daily_count == 0

    def test_rate_limiter_acquire_tokens(self):
        """Test acquiring tokens from rate limiter."""
        config = RateLimitConfig(
            emails_per_minute=60,
            emails_per_hour=1000,
            emails_per_day=5000,
            burst_size=5
        )
        
        limiter = RateLimiter(config)
        
        # Should be able to acquire burst_size tokens immediately
        for i in range(config.burst_size):
            assert limiter.acquire() == True
            
        # Next acquisition should fail (no tokens left)
        assert limiter.acquire() == False

    def test_rate_limiter_token_refill(self):
        """Test token refill over time."""
        config = RateLimitConfig(
            emails_per_minute=60,  # 1 token per second
            emails_per_hour=1000,
            emails_per_day=5000,
            burst_size=2
        )
        
        limiter = RateLimiter(config)
        
        # Exhaust all tokens
        limiter.acquire()
        limiter.acquire()
        assert limiter.acquire() == False
        
        # Wait for token refill
        time.sleep(1.1)  # Wait slightly more than 1 second
        
        # Should be able to acquire one token
        assert limiter.acquire() == True

    def test_rate_limiter_hourly_limit(self):
        """Test hourly email limit."""
        config = RateLimitConfig(
            emails_per_minute=60,
            emails_per_hour=5,  # Very low hourly limit
            emails_per_day=1000,
            burst_size=10
        )
        
        limiter = RateLimiter(config)
        
        # Acquire up to hourly limit
        for i in range(5):
            assert limiter.acquire() == True
            
        # Next acquisition should fail due to hourly limit
        assert limiter.acquire() == False

    def test_rate_limiter_get_wait_time(self):
        """Test getting wait time for next token."""
        config = RateLimitConfig(
            emails_per_minute=60,  # 1 token per second
            emails_per_hour=1000,
            emails_per_day=5000,
            burst_size=1
        )
        
        limiter = RateLimiter(config)
        
        # Exhaust tokens
        limiter.acquire()
        
        # Should need to wait approximately 1 second
        wait_time = limiter.get_wait_time()
        assert 0.5 <= wait_time <= 1.5  # Allow some tolerance


class TestDuplicatePreventionService:
    """Test DuplicatePreventionService class."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.execute.return_value = None
        session.commit.return_value = None
        return session

    def test_duplicate_service_creation(self, mock_db_session):
        """Test creating DuplicatePreventionService."""
        service = DuplicatePreventionService(mock_db_session)
        assert service.db_session == mock_db_session

    def test_generate_hash(self, mock_db_session):
        """Test hash generation for duplicate detection."""
        service = DuplicatePreventionService(mock_db_session)
        
        hash1 = service.generate_hash("test@example.com", "campaign-001", "Test Subject")
        hash2 = service.generate_hash("test@example.com", "campaign-001", "Test Subject")
        hash3 = service.generate_hash("test@example.com", "campaign-002", "Test Subject")
        
        # Same inputs should produce same hash
        assert hash1 == hash2
        
        # Different campaign should produce different hash
        assert hash1 != hash3
        
        # Hash should be consistent length (SHA256)
        assert len(hash1) == 64

    def test_is_duplicate_false(self, mock_db_session):
        """Test duplicate check when no duplicate exists."""
        # Mock query to return None (no existing email)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        service = DuplicatePreventionService(mock_db_session)
        
        is_dup = service.is_duplicate("test@example.com", "campaign-001", "Test Subject")
        assert is_dup == False

    def test_is_duplicate_true(self, mock_db_session):
        """Test duplicate check when duplicate exists."""
        # Mock query to return an existing email
        existing_email = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_email
        
        service = DuplicatePreventionService(mock_db_session)
        
        is_dup = service.is_duplicate("test@example.com", "campaign-001", "Test Subject")
        assert is_dup == True


class TestSMTPProvider:
    """Test SMTPProvider class."""
    
    def test_smtp_provider_creation(self):
        """Test creating SMTPProvider."""
        config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'test@gmail.com',
            'password': 'app_password',
            'use_tls': True,
            'timeout': 30
        }
        
        provider = SMTPProvider(config)
        
        assert provider.host == 'smtp.gmail.com'
        assert provider.port == 587
        assert provider.username == 'test@gmail.com'
        assert provider.password == 'app_password'
        assert provider.use_tls == True
        assert provider.timeout == 30

    def test_smtp_provider_defaults(self):
        """Test SMTPProvider with default values."""
        config = {
            'username': 'test@gmail.com',
            'password': 'password'
        }
        
        provider = SMTPProvider(config)
        
        assert provider.host == 'smtp.gmail.com'  # default
        assert provider.port == 587  # default
        assert provider.use_tls == True  # default
        assert provider.timeout == 30  # default

    @patch('src.email_engine.smtplib.SMTP')
    def test_smtp_send_email_success(self, mock_smtp):
        """Test successful email sending via SMTP."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'test@gmail.com',
            'password': 'password'
        }
        
        provider = SMTPProvider(config)
        
        request = EmailRequest(
            email_id="test-001",
            campaign_id="campaign-001",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        result = provider.send_email(request)
        
        # Verify SMTP interactions
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@gmail.com', 'password')
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
        
        # Verify result
        assert result.status == SendStatus.SENT
        assert result.email_id == "test-001"
        assert result.recipient == "recipient@example.com"
        assert result.message_id is not None
        assert result.sent_at is not None
        assert result.execution_time is not None

    @patch('src.email_engine.smtplib.SMTP')
    def test_smtp_send_email_auth_failure(self, mock_smtp):
        """Test SMTP authentication failure."""
        # Mock SMTP server to raise authentication error
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value = mock_server
        
        config = {
            'username': 'test@gmail.com',
            'password': 'wrong_password'
        }
        
        provider = SMTPProvider(config)
        
        request = EmailRequest(
            email_id="test-002",
            campaign_id="campaign-001",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        result = provider.send_email(request)
        
        assert result.status == SendStatus.FAILED
        assert result.email_id == "test-002"
        assert "Authentication failed" in result.error_message
        assert result.sent_at is None

    @patch('src.email_engine.smtplib.SMTP')
    def test_smtp_send_email_recipient_refused(self, mock_smtp):
        """Test SMTP recipient refused error."""
        # Mock SMTP server to raise recipient refused error
        mock_server = Mock()
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused({
            'invalid@example.com': (550, 'User unknown')
        })
        mock_smtp.return_value = mock_server
        
        config = {
            'username': 'test@gmail.com',
            'password': 'password'
        }
        
        provider = SMTPProvider(config)
        
        request = EmailRequest(
            email_id="test-003",
            campaign_id="campaign-001",
            recipient="invalid@example.com",
            subject="Test Subject",
            body="Test body",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        result = provider.send_email(request)
        
        assert result.status == SendStatus.BOUNCED
        assert result.email_id == "test-003"
        assert "Recipient refused" in result.error_message


class TestGraphAPIProvider:
    """Test GraphAPIProvider class."""
    
    def test_graph_provider_creation(self):
        """Test creating GraphAPIProvider."""
        config = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789'
        }
        
        provider = GraphAPIProvider(config)
        
        assert provider.tenant_id == 'tenant-123'
        assert provider.client_id == 'client-456'
        assert provider.client_secret == 'secret-789'
        assert provider.access_token is None

    @patch('src.email_engine.requests.post')
    def test_graph_get_access_token(self, mock_post):
        """Test getting OAuth2 access token."""
        # Mock token response
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'fake-token-123',
            'expires_in': 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        config = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789'
        }
        
        provider = GraphAPIProvider(config)
        token = provider._get_access_token()
        
        assert token == 'fake-token-123'
        assert provider.access_token == 'fake-token-123'
        assert provider.token_expires_at is not None

    @patch('src.email_engine.requests.post')
    def test_graph_send_email_success(self, mock_post):
        """Test successful email sending via Graph API."""
        # Mock token and send responses
        token_response = Mock()
        token_response.json.return_value = {
            'access_token': 'fake-token-123',
            'expires_in': 3600
        }
        token_response.raise_for_status.return_value = None
        
        send_response = Mock()
        send_response.status_code = 202
        
        mock_post.side_effect = [token_response, send_response]
        
        config = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789'
        }
        
        provider = GraphAPIProvider(config)
        
        request = EmailRequest(
            email_id="test-001",
            campaign_id="campaign-001",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="<html><body>Test HTML body</body></html>",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        result = provider.send_email(request)
        
        assert result.status == SendStatus.SENT
        assert result.email_id == "test-001"
        assert result.recipient == "recipient@example.com"
        assert result.sent_at is not None
        assert result.provider_response['status_code'] == 202

    @patch('src.email_engine.requests.post')
    def test_graph_send_email_failure(self, mock_post):
        """Test Graph API email sending failure."""
        # Mock token response
        token_response = Mock()
        token_response.json.return_value = {
            'access_token': 'fake-token-123',
            'expires_in': 3600
        }
        token_response.raise_for_status.return_value = None
        
        # Mock failed send response
        send_response = Mock()
        send_response.status_code = 400
        send_response.text = "Bad Request: Invalid recipient"
        
        mock_post.side_effect = [token_response, send_response]
        
        config = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789'
        }
        
        provider = GraphAPIProvider(config)
        
        request = EmailRequest(
            email_id="test-002",
            campaign_id="campaign-001",
            recipient="invalid@example.com",
            subject="Test Subject",
            body="Test body",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        result = provider.send_email(request)
        
        assert result.status == SendStatus.FAILED
        assert result.email_id == "test-002"
        assert "Graph API error: 400" in result.error_message
        assert result.provider_response['status_code'] == 400


class TestEmailEngine:
    """Test EmailEngine main class."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        return session

    @pytest.fixture
    def smtp_config(self):
        """SMTP configuration for testing."""
        return {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'test@gmail.com',
            'password': 'password'
        }

    @pytest.fixture
    def sample_email_request(self):
        """Sample email request for testing."""
        return EmailRequest(
            email_id="test-001",
            campaign_id="campaign-001",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )

    @patch('src.email_engine.get_db_session')
    def test_email_engine_creation(self, mock_get_db, smtp_config):
        """Test creating EmailEngine."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            max_workers=5
        )
        
        assert engine.provider_type == EmailProvider.GMAIL_SMTP
        assert engine.max_workers == 5
        assert isinstance(engine.provider, SMTPProvider)
        assert isinstance(engine.retry_config, RetryConfig)
        assert isinstance(engine.rate_limit_config, RateLimitConfig)

    @patch('src.email_engine.get_db_session')
    def test_email_engine_with_graph_provider(self, mock_get_db):
        """Test creating EmailEngine with Graph API provider."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        graph_config = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789'
        }
        
        engine = EmailEngine(
            provider_type=EmailProvider.MICROSOFT_GRAPH,
            provider_config=graph_config
        )
        
        assert engine.provider_type == EmailProvider.MICROSOFT_GRAPH
        assert isinstance(engine.provider, GraphAPIProvider)

    @patch('src.email_engine.get_db_session')
    def test_email_engine_unsupported_provider(self, mock_get_db):
        """Test EmailEngine with unsupported provider."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        with pytest.raises(ValueError) as exc_info:
            EmailEngine(
                provider_type="unsupported_provider",
                provider_config={}
            )
        
        assert "Unsupported provider type" in str(exc_info.value)

    @patch('src.email_engine.get_db_session')
    def test_send_single_email_duplicate_blocked(self, mock_get_db, smtp_config, sample_email_request):
        """Test single email send blocked by duplicate prevention."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config
        )
        
        # Mock duplicate service to return True
        engine.duplicate_service.is_duplicate = Mock(return_value=True)
        
        result = engine.send_single_email(sample_email_request)
        
        assert result.status == SendStatus.DUPLICATE
        assert result.email_id == "test-001"
        assert "Duplicate email blocked" in result.error_message

    @patch('src.email_engine.get_db_session')
    def test_send_single_email_rate_limited(self, mock_get_db, smtp_config, sample_email_request):
        """Test single email send blocked by rate limiting."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        rate_config = RateLimitConfig(
            emails_per_minute=1,
            emails_per_hour=1,
            emails_per_day=1,
            burst_size=0  # No burst tokens
        )
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            rate_limit_config=rate_config
        )
        
        # Mock duplicate service to return False
        engine.duplicate_service.is_duplicate = Mock(return_value=False)
        
        result = engine.send_single_email(sample_email_request)
        
        assert result.status == SendStatus.RATE_LIMITED
        assert "Rate limited" in result.error_message

    @patch('src.email_engine.get_db_session')
    def test_calculate_retry_delay(self, mock_get_db, smtp_config):
        """Test retry delay calculation with exponential backoff."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        retry_config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=False
        )
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            retry_config=retry_config
        )
        
        # Test exponential backoff
        delay0 = engine._calculate_retry_delay(0)
        delay1 = engine._calculate_retry_delay(1)
        delay2 = engine._calculate_retry_delay(2)
        
        assert delay0 == 1.0  # base_delay * (2 ^ 0)
        assert delay1 == 2.0  # base_delay * (2 ^ 1)
        assert delay2 == 4.0  # base_delay * (2 ^ 2)

    @patch('src.email_engine.get_db_session')
    def test_calculate_retry_delay_with_jitter(self, mock_get_db, smtp_config):
        """Test retry delay calculation with jitter."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        retry_config = RetryConfig(
            base_delay=2.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=True
        )
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            retry_config=retry_config
        )
        
        # Test with jitter - delay should be between 50% and 100% of base delay
        delay = engine._calculate_retry_delay(0)
        assert 1.0 <= delay <= 2.0  # 50% to 100% of base_delay

    @patch('src.email_engine.get_db_session')
    def test_calculate_retry_delay_max_limit(self, mock_get_db, smtp_config):
        """Test retry delay respects maximum limit."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        retry_config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,  # Low max delay
            jitter=False
        )
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            retry_config=retry_config
        )
        
        # Even with high attempt number, delay should not exceed max_delay
        delay = engine._calculate_retry_delay(10)
        assert delay <= 5.0

    @patch('src.email_engine.get_db_session')
    def test_send_bulk_emails(self, mock_get_db, smtp_config):
        """Test sending multiple emails concurrently."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            max_workers=2
        )
        
        # Mock send_single_email to return success
        def mock_send_single(request):
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.SENT
            )
        
        engine.send_single_email = Mock(side_effect=mock_send_single)
        
        # Create multiple requests
        requests = [
            EmailRequest(
                email_id=f"test-{i:03d}",
                campaign_id="campaign-001",
                recipient=f"user{i}@example.com",
                subject="Test Subject",
                body="Test body",
                sender_name="Test Sender",
                sender_email="sender@example.com"
            )
            for i in range(5)
        ]
        
        results = engine.send_bulk_emails(requests)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.email_id == f"test-{i:03d}"
            assert result.status == SendStatus.SENT

    @patch('src.email_engine.get_db_session')
    def test_get_sending_stats(self, mock_get_db, smtp_config):
        """Test getting sending statistics."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        retry_config = RetryConfig(max_retries=5, base_delay=2.0)
        rate_config = RateLimitConfig(emails_per_hour=500, emails_per_day=2000)
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config,
            retry_config=retry_config,
            rate_limit_config=rate_config,
            max_workers=8
        )
        
        stats = engine.get_sending_stats()
        
        assert "rate_limiter" in stats
        assert "provider" in stats
        assert "retry_config" in stats
        
        assert stats["rate_limiter"]["hourly_limit"] == 500
        assert stats["rate_limiter"]["daily_limit"] == 2000
        assert stats["provider"]["type"] == "gmail_smtp"
        assert stats["provider"]["max_workers"] == 8
        assert stats["retry_config"]["max_retries"] == 5
        assert stats["retry_config"]["base_delay"] == 2.0

    @patch('src.email_engine.get_db_session')
    def test_shutdown(self, mock_get_db, smtp_config):
        """Test engine shutdown."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=smtp_config
        )
        
        # Mock executor shutdown
        engine.executor.shutdown = Mock()
        
        engine.shutdown()
        
        engine.executor.shutdown.assert_called_once_with(wait=True)


class TestFactoryFunction:
    """Test create_email_engine factory function."""
    
    @patch('src.email_engine.get_db_session')
    def test_create_email_engine_gmail(self, mock_get_db):
        """Test creating EmailEngine via factory function."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        config = {
            'host': 'smtp.gmail.com',
            'username': 'test@gmail.com',
            'password': 'password'
        }
        
        retry_config = {"max_retries": 5, "base_delay": 1.5}
        rate_config = {"emails_per_minute": 30, "emails_per_hour": 800}
        
        engine = create_email_engine(
            provider_type="gmail_smtp",
            config=config,
            retry_config=retry_config,
            rate_limit_config=rate_config,
            max_workers=8
        )
        
        assert isinstance(engine, EmailEngine)
        assert engine.provider_type == EmailProvider.GMAIL_SMTP
        assert engine.retry_config.max_retries == 5
        assert engine.retry_config.base_delay == 1.5
        assert engine.rate_limit_config.emails_per_minute == 30
        assert engine.rate_limit_config.emails_per_hour == 800
        assert engine.max_workers == 8

    @patch('src.email_engine.get_db_session')
    def test_create_email_engine_graph(self, mock_get_db):
        """Test creating EmailEngine with Graph API via factory."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        config = {
            'tenant_id': 'tenant-123',
            'client_id': 'client-456',
            'client_secret': 'secret-789'
        }
        
        engine = create_email_engine(
            provider_type="microsoft_graph",
            config=config
        )
        
        assert isinstance(engine, EmailEngine)
        assert engine.provider_type == EmailProvider.MICROSOFT_GRAPH
        assert isinstance(engine.provider, GraphAPIProvider)

    @patch('src.email_engine.get_db_session')
    def test_create_email_engine_invalid_provider(self, mock_get_db):
        """Test factory function with invalid provider type."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        with pytest.raises(ValueError):
            create_email_engine(
                provider_type="invalid_provider",
                config={}
            )


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @patch('src.email_engine.get_db_session')
    @patch('src.email_engine.smtplib.SMTP')
    def test_full_email_send_workflow(self, mock_smtp, mock_get_db):
        """Test complete email sending workflow."""
        # Setup mocks
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Mock database email record
        mock_email = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_email
        
        # Create engine
        config = {
            'username': 'test@gmail.com',
            'password': 'password'
        }
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config=config
        )
        
        # Mock duplicate service to allow sending
        engine.duplicate_service.is_duplicate = Mock(return_value=False)
        
        # Create email request
        request = EmailRequest(
            email_id="integration-001",
            campaign_id="campaign-001",
            recipient="recipient@example.com",
            subject="Integration Test",
            body="This is an integration test email.",
            sender_name="Test Sender",
            sender_email="sender@example.com"
        )
        
        # Send email
        result = engine.send_single_email(request)
        
        # Verify result
        assert result.status == SendStatus.SENT
        assert result.email_id == "integration-001"
        assert result.recipient == "recipient@example.com"
        
        # Verify SMTP was called
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
        
        # Verify database was updated
        mock_session.commit.assert_called()

    @patch('src.email_engine.get_db_session')
    def test_concurrent_sending_with_rate_limiting(self, mock_get_db):
        """Test concurrent sending respects rate limits."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        # Very restrictive rate limiting
        rate_config = RateLimitConfig(
            emails_per_minute=2,
            emails_per_hour=5,
            emails_per_day=5,
            burst_size=1
        )
        
        engine = EmailEngine(
            provider_type=EmailProvider.GMAIL_SMTP,
            provider_config={'username': 'test', 'password': 'pass'},
            rate_limit_config=rate_config,
            max_workers=3
        )
        
        # Mock duplicate service
        engine.duplicate_service.is_duplicate = Mock(return_value=False)
        
        # Mock provider to always succeed
        engine.provider.send_email = Mock(return_value=EmailResult(
            email_id="mock",
            recipient="mock@example.com",
            status=SendStatus.SENT
        ))
        
        # Create multiple requests
        requests = [
            EmailRequest(
                email_id=f"concurrent-{i:03d}",
                campaign_id="campaign-001",
                recipient=f"user{i}@example.com",
                subject="Concurrent Test",
                body="Test body",
                sender_name="Test Sender",
                sender_email="sender@example.com"
            )
            for i in range(10)
        ]
        
        # Send all emails
        results = engine.send_bulk_emails(requests)
        
        # Count rate limited vs sent
        sent_count = sum(1 for r in results if r.status == SendStatus.SENT)
        rate_limited_count = sum(1 for r in results if r.status == SendStatus.RATE_LIMITED)
        
        # Should have some rate limited due to restrictive limits
        assert rate_limited_count > 0
        assert sent_count <= rate_config.emails_per_hour


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
