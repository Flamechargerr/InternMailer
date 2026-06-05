"""
Test SMTP connection pool improvements for Task 4.2

This test validates the fixes made to the SMTP connection pool:
- Proper error handling
- Connection validation
- Connection reuse
- Error tracking
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import smtplib
from queue import Empty, Full


def test_smtp_connection_pool_initialization():
    """Test that connection pool initializes with proper error handling"""
    with patch('core.email_system.smtplib.SMTP') as mock_smtp:
        # Mock successful connection
        mock_server = MagicMock()
        mock_server.noop.return_value = (250, b'OK')
        mock_smtp.return_value = mock_server
        
        from core.email_system import SMTPConnectionPool
        
        pool = SMTPConnectionPool(
            email="test@example.com",
            password="test_password",
            pool_size=3
        )
        
        # Verify pool was initialized
        assert pool.pool_size == 3
        assert pool.total_connections_created == 3
        assert pool.failed_connections == 0
        assert pool.connections.qsize() == 3


def test_smtp_connection_pool_partial_initialization():
    """Test that connection pool handles partial initialization failures"""
    with patch('core.email_system.smtplib.SMTP') as mock_smtp:
        # First 2 connections succeed, 3rd fails
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                mock_server = MagicMock()
                mock_server.noop.return_value = (250, b'OK')
                return mock_server
            else:
                raise smtplib.SMTPConnectError(421, "Connection failed")
        
        mock_smtp.side_effect = side_effect
        
        from core.email_system import SMTPConnectionPool
        
        pool = SMTPConnectionPool(
            email="test@example.com",
            password="test_password",
            pool_size=3
        )
        
        # Verify partial initialization
        assert pool.total_connections_created == 2
        assert pool.failed_connections == 1
        assert pool.connections.qsize() == 2


def test_smtp_connection_pool_complete_failure():
    """Test that connection pool raises error when all connections fail"""
    with patch('core.email_system.smtplib.SMTP') as mock_smtp:
        # All connections fail
        mock_smtp.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        
        from core.email_system import SMTPConnectionPool
        
        with pytest.raises(ConnectionError, match="Failed to create any SMTP connections"):
            pool = SMTPConnectionPool(
                email="test@example.com",
                password="wrong_password",
                pool_size=3
            )


def test_smtp_connection_validation():
    """Test that connection pool validates connections before returning them"""
    with patch('core.email_system.smtplib.SMTP') as mock_smtp:
        # Create mock connections
        mock_server_alive = MagicMock()
        mock_server_alive.noop.return_value = (250, b'OK')
        
        mock_server_dead = MagicMock()
        mock_server_dead.noop.side_effect = smtplib.SMTPServerDisconnected("Connection lost")
        
        # First call returns dead connection, second returns alive
        mock_smtp.side_effect = [mock_server_dead, mock_server_alive, mock_server_alive]
        
        from core.email_system import SMTPConnectionPool
        
        pool = SMTPConnectionPool(
            email="test@example.com",
            password="test_password",
            pool_size=1
        )
        
        # Get connection - should detect dead connection and create new one
        with pool.get_connection() as conn:
            assert conn is not None
            # Should be the alive connection
            assert conn.noop() == (250, b'OK')


def test_smtp_connection_reuse():
    """Test that connections are properly reused"""
    with patch('core.email_system.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_server.noop.return_value = (250, b'OK')
        mock_smtp.return_value = mock_server
        
        from core.email_system import SMTPConnectionPool
        
        pool = SMTPConnectionPool(
            email="test@example.com",
            password="test_password",
            pool_size=2
        )
        
        initial_created = pool.total_connections_created
        
        # Use connection and return it
        with pool.get_connection() as conn:
            pass
        
        # Use connection again - should reuse, not create new
        with pool.get_connection() as conn:
            pass
        
        # Should not have created additional connections
        assert pool.total_connections_created == initial_created


def test_smtp_connection_pool_stats():
    """Test that connection pool tracks statistics correctly"""
    with patch('core.email_system.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_server.noop.return_value = (250, b'OK')
        mock_smtp.return_value = mock_server
        
        from core.email_system import SMTPConnectionPool
        
        pool = SMTPConnectionPool(
            email="test@example.com",
            password="test_password",
            pool_size=3
        )
        
        stats = pool.get_stats()
        
        assert stats['pool_size'] == 3
        assert stats['available_connections'] == 3
        assert stats['total_created'] == 3
        assert stats['failed_connections'] == 0


def test_send_single_email_error_handling():
    """Test that send_single_email handles various SMTP errors correctly"""
    with patch('core.email_system.config') as mock_config, \
         patch('core.email_system.get_profile') as mock_profile, \
         patch('core.email_system.AI_AVAILABLE', False), \
         patch('core.email_system.smtplib.SMTP') as mock_smtp:
        
        # Setup mocks
        mock_config.EMAIL_ADDRESS = "test@example.com"
        mock_config.EMAIL_PASSWORD = "test_password"
        mock_config.MAX_EMAILS_PER_DAY = 100
        mock_config.MAX_CONCURRENT_EMAILS = 5
        mock_config.RATE_LIMIT_DELAY = 0.01
        mock_config.DATABASE_PATH = ":memory:"
        mock_config.CONTACTS_DB_PATH = ":memory:"
        mock_config.AUTO_APPROVE_SENDS = True
        
        mock_profile_obj = Mock()
        mock_profile_obj.get = Mock(return_value="Test User")
        mock_profile_obj.signature_html = Mock(return_value="Test Signature")
        mock_profile_obj.resume_paths = Mock(return_value=[])
        mock_profile.return_value = mock_profile_obj
        
        # Test authentication error (not retryable)
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPAuthenticationError(535, "Auth failed")
        mock_server.noop.return_value = (250, b'OK')
        mock_smtp.return_value = mock_server
        
        from core.email_system import EmailSystem
        
        # Create email system (will validate credentials)
        with patch.object(EmailSystem, '_validate_credentials', return_value=True):
            email_system = EmailSystem()
            
            # Test sending with auth error
            result = email_system.send_single_email(
                to_email="recipient@example.com",
                subject="Test",
                html_body="<p>Test</p>",
                max_retries=3
            )
            
            # Should fail immediately without retries
            assert result is False
            assert email_system.stats['auth_errors'] == 1
            assert email_system.stats['failed'] == 1


def test_send_single_email_retry_logic():
    """Test that send_single_email retries transient failures"""
    with patch('core.email_system.config') as mock_config, \
         patch('core.email_system.get_profile') as mock_profile, \
         patch('core.email_system.AI_AVAILABLE', False), \
         patch('core.email_system.smtplib.SMTP') as mock_smtp, \
         patch('core.email_system.time.sleep'):  # Mock sleep to speed up test
        
        # Setup mocks
        mock_config.EMAIL_ADDRESS = "test@example.com"
        mock_config.EMAIL_PASSWORD = "test_password"
        mock_config.MAX_EMAILS_PER_DAY = 100
        mock_config.MAX_CONCURRENT_EMAILS = 5
        mock_config.RATE_LIMIT_DELAY = 0.01
        mock_config.DATABASE_PATH = ":memory:"
        mock_config.CONTACTS_DB_PATH = ":memory:"
        mock_config.AUTO_APPROVE_SENDS = True
        
        mock_profile_obj = Mock()
        mock_profile_obj.get = Mock(return_value="Test User")
        mock_profile_obj.signature_html = Mock(return_value="Test Signature")
        mock_profile_obj.resume_paths = Mock(return_value=[])
        mock_profile.return_value = mock_profile_obj
        
        # Test transient error with retry
        call_count = [0]
        
        def send_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise smtplib.SMTPServerDisconnected("Connection lost")
            # Success on second try
            return None
        
        mock_server = MagicMock()
        mock_server.send_message.side_effect = send_side_effect
        mock_server.noop.return_value = (250, b'OK')
        mock_smtp.return_value = mock_server
        
        from core.email_system import EmailSystem
        
        with patch.object(EmailSystem, '_validate_credentials', return_value=True):
            email_system = EmailSystem()
            
            # Test sending with transient error
            result = email_system.send_single_email(
                to_email="recipient@example.com",
                subject="Test",
                html_body="<p>Test</p>",
                max_retries=3
            )
            
            # Should succeed after retry
            assert result is True
            assert call_count[0] == 2  # Failed once, succeeded on second try
            assert email_system.stats['sent'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
