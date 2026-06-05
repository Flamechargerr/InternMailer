"""
Tests for HTTP Client with Retry Logic and Exponential Backoff
==============================================================

Tests validate:
- HTTP retry logic with exponential backoff
- Connection pooling
- Timeout handling
- Error recovery

Validates Requirements: 6.4, 6.6
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException

from utils.http_client import HTTPClient, HTTPConfig, get_http_client, reset_http_client


class TestHTTPConfig:
    """Test HTTP configuration"""
    
    def test_default_config(self):
        """Test default HTTP configuration values"""
        config = HTTPConfig()
        
        assert config.timeout == 15.0
        assert config.max_retries == 3
        assert config.backoff_factor == 0.5
        assert config.retry_statuses == (408, 429, 500, 502, 503, 504)
        assert config.pool_connections == 10
        assert config.pool_maxsize == 20
        assert config.pool_block is False
    
    def test_custom_config(self):
        """Test custom HTTP configuration"""
        config = HTTPConfig(
            timeout=30.0,
            max_retries=5,
            backoff_factor=1.0,
            pool_connections=20,
        )
        
        assert config.timeout == 30.0
        assert config.max_retries == 5
        assert config.backoff_factor == 1.0
        assert config.pool_connections == 20


class TestHTTPClient:
    """Test HTTP client with retry logic"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = HTTPConfig(
            timeout=5.0,
            max_retries=3,
            backoff_factor=0.1,  # Small backoff for faster tests
        )
        self.client = HTTPClient(self.config)
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.client.close()
        reset_http_client()
    
    def test_successful_get_request(self):
        """Test successful GET request"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_request.return_value = mock_response
            
            response = self.client.get("https://example.com/api")
            
            assert response.status_code == 200
            mock_request.assert_called_once()
    
    def test_successful_post_request(self):
        """Test successful POST request"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_request.return_value = mock_response
            
            response = self.client.post("https://example.com/api", json={"data": "test"})
            
            assert response.status_code == 201
            mock_request.assert_called_once()
    
    def test_retry_on_timeout(self):
        """Test retry logic on timeout"""
        with patch.object(self.client.session, 'request') as mock_request:
            # First 2 attempts timeout, 3rd succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.side_effect = [
                Timeout("Connection timeout"),
                Timeout("Connection timeout"),
                mock_response,
            ]
            
            start_time = time.time()
            response = self.client.get("https://example.com/api")
            duration = time.time() - start_time
            
            assert response.status_code == 200
            assert mock_request.call_count == 3
            # Verify exponential backoff occurred (0.1 + 0.2 = 0.3 seconds minimum)
            assert duration >= 0.3
    
    def test_retry_on_connection_error(self):
        """Test retry logic on connection error"""
        with patch.object(self.client.session, 'request') as mock_request:
            # First attempt fails, second succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.side_effect = [
                ConnectionError("Connection refused"),
                mock_response,
            ]
            
            response = self.client.get("https://example.com/api")
            
            assert response.status_code == 200
            assert mock_request.call_count == 2
    
    def test_retry_on_server_error(self):
        """Test retry logic on server error status codes"""
        with patch.object(self.client.session, 'request') as mock_request:
            # First 2 attempts return 503, 3rd returns 200
            mock_response_503 = Mock()
            mock_response_503.status_code = 503
            
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            
            mock_request.side_effect = [
                mock_response_503,
                mock_response_503,
                mock_response_200,
            ]
            
            response = self.client.get("https://example.com/api")
            
            assert response.status_code == 200
            assert mock_request.call_count == 3
    
    def test_max_retries_exhausted(self):
        """Test behavior when max retries are exhausted"""
        with patch.object(self.client.session, 'request') as mock_request:
            # All attempts timeout
            mock_request.side_effect = Timeout("Connection timeout")
            
            with pytest.raises(Timeout):
                self.client.get("https://example.com/api")
            
            # Should try initial + 3 retries = 4 total
            assert mock_request.call_count == 4
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff calculation"""
        # backoff_factor = 0.1 (from setup)
        # attempt 1: 0.1 * (2^0) = 0.1
        # attempt 2: 0.1 * (2^1) = 0.2
        # attempt 3: 0.1 * (2^2) = 0.4
        
        assert self.client._calculate_backoff(1) == 0.1   # 0.1 * (2^0)
        assert self.client._calculate_backoff(2) == 0.2   # 0.1 * (2^1)
        assert self.client._calculate_backoff(3) == 0.4   # 0.1 * (2^2)
    
    def test_get_json_success(self):
        """Test get_json helper method"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            mock_request.return_value = mock_response
            
            result = self.client.get_json("https://example.com/api")
            
            assert result == {"data": "test"}
    
    def test_get_json_error_returns_empty_dict(self):
        """Test get_json returns empty dict on error"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response
            
            result = self.client.get_json("https://example.com/api")
            
            assert result == {}
    
    def test_get_json_invalid_json_returns_empty_dict(self):
        """Test get_json returns empty dict on invalid JSON"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_request.return_value = mock_response
            
            result = self.client.get_json("https://example.com/api")
            
            assert result == {}
    
    def test_context_manager(self):
        """Test HTTP client as context manager"""
        with HTTPClient(self.config) as client:
            assert client.session is not None
        
        # Session should be closed after context exit
        # Note: We can't directly test if session is closed, but we verify no errors
    
    def test_custom_timeout(self):
        """Test custom timeout parameter"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            self.client.get("https://example.com/api", timeout=30.0)
            
            # Verify timeout was passed
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['timeout'] == 30.0
    
    def test_default_timeout_used(self):
        """Test default timeout is used when not specified"""
        with patch.object(self.client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            self.client.get("https://example.com/api")
            
            # Verify default timeout was used
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['timeout'] == self.config.timeout


class TestGlobalHTTPClient:
    """Test global HTTP client instance"""
    
    def teardown_method(self):
        """Cleanup after tests"""
        reset_http_client()
    
    def test_get_http_client_singleton(self):
        """Test global HTTP client is singleton"""
        client1 = get_http_client()
        client2 = get_http_client()
        
        assert client1 is client2
    
    def test_reset_http_client(self):
        """Test resetting global HTTP client"""
        client1 = get_http_client()
        reset_http_client()
        client2 = get_http_client()
        
        assert client1 is not client2
    
    def test_get_http_client_with_custom_config(self):
        """Test getting HTTP client with custom config"""
        config = HTTPConfig(timeout=30.0)
        client = get_http_client(config)
        
        assert client.config.timeout == 30.0


class TestHTTPRetryIntegration:
    """Integration tests for HTTP retry logic"""
    
    def test_retry_with_rate_limiting(self):
        """Test retry logic respects rate limiting (429 status)"""
        config = HTTPConfig(
            timeout=5.0,
            max_retries=2,
            backoff_factor=0.1,
        )
        client = HTTPClient(config)
        
        with patch.object(client.session, 'request') as mock_request:
            # Simulate rate limiting then success
            mock_response_429 = Mock()
            mock_response_429.status_code = 429
            
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            
            mock_request.side_effect = [
                mock_response_429,
                mock_response_200,
            ]
            
            start_time = time.time()
            response = client.get("https://example.com/api")
            duration = time.time() - start_time
            
            assert response.status_code == 200
            assert mock_request.call_count == 2
            # Verify backoff occurred
            assert duration >= 0.1
        
        client.close()
    
    def test_no_retry_on_client_error(self):
        """Test no retry on client errors (4xx except 408, 429)"""
        config = HTTPConfig(
            timeout=5.0,
            max_retries=3,
            backoff_factor=0.1,
        )
        client = HTTPClient(config)
        
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response
            
            response = client.get("https://example.com/api")
            
            # Should not retry on 404
            assert response.status_code == 404
            assert mock_request.call_count == 1
        
        client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
