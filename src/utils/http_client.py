"""
HTTP Client with Retry Logic and Exponential Backoff
====================================================

Provides HTTP client with:
- Configurable timeouts
- Retry logic with exponential backoff
- Connection pooling
- Error handling and logging

Validates Requirements: 6.4, 6.6
"""

import time
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class HTTPConfig:
    """HTTP client configuration"""
    timeout: float = 15.0  # Default timeout in seconds
    max_retries: int = 3  # Maximum number of retries
    backoff_factor: float = 0.5  # Exponential backoff factor
    retry_statuses: tuple = (408, 429, 500, 502, 503, 504)  # HTTP status codes to retry
    pool_connections: int = 10  # Connection pool size
    pool_maxsize: int = 20  # Maximum pool size
    pool_block: bool = False  # Block when pool is full


class HTTPClient:
    """
    HTTP client with retry logic and exponential backoff
    
    Features:
    - Automatic retries with exponential backoff
    - Connection pooling for efficiency
    - Configurable timeouts
    - Comprehensive error handling
    """
    
    def __init__(self, config: Optional[HTTPConfig] = None):
        """
        Initialize HTTP client
        
        Args:
            config: HTTP configuration (uses defaults if None)
        """
        self.config = config or HTTPConfig()
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry logic and connection pooling
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=self.config.retry_statuses,
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            raise_on_status=False,
        )
        
        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize,
            pool_block=self.config.pool_block,
        )
        
        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform GET request with retry logic
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.get
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure after retries
        """
        return self._request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Perform POST request with retry logic
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.post
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure after retries
        """
        return self._request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """
        Perform PUT request with retry logic
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.put
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure after retries
        """
        return self._request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """
        Perform DELETE request with retry logic
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.delete
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure after retries
        """
        return self._request("DELETE", url, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP request with retry logic and error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure after retries
        """
        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.config.timeout
        
        attempt = 0
        last_exception = None
        
        while attempt <= self.config.max_retries:
            try:
                # Log attempt
                if attempt > 0:
                    logger.debug(f"Retry attempt {attempt}/{self.config.max_retries} for {method} {url}")
                
                # Perform request
                response = self.session.request(method, url, **kwargs)
                
                # Check if we should retry based on status code
                if response.status_code in self.config.retry_statuses and attempt < self.config.max_retries:
                    logger.warning(f"Request returned {response.status_code}, retrying...")
                    attempt += 1
                    time.sleep(self._calculate_backoff(attempt))
                    continue
                
                # Return response (even if error status, let caller handle)
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout on attempt {attempt + 1}: {str(e)}")
                attempt += 1
                if attempt <= self.config.max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                attempt += 1
                if attempt <= self.config.max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                
            except requests.exceptions.RequestException as e:
                # For other request exceptions, don't retry
                logger.error(f"Request failed: {str(e)}")
                raise
        
        # All retries exhausted
        logger.error(f"Request failed after {self.config.max_retries} retries")
        if last_exception:
            raise last_exception
        else:
            raise requests.exceptions.RequestException(f"Request failed after {self.config.max_retries} retries")
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: backoff_factor * (2 ^ (attempt - 1))
        delay = self.config.backoff_factor * (2 ** (attempt - 1))
        logger.debug(f"Backing off for {delay:.2f} seconds")
        return delay
    
    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Perform GET request and return JSON response
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.get
            
        Returns:
            JSON response as dictionary (empty dict on error)
        """
        try:
            response = self.get(url, **kwargs)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"GET {url} returned status {response.status_code}")
                return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get JSON from {url}: {str(e)}")
            return {}
        except ValueError as e:
            logger.error(f"Failed to parse JSON from {url}: {str(e)}")
            return {}
    
    def close(self):
        """Close the session and release resources"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global HTTP client instance
_global_client: Optional[HTTPClient] = None


def get_http_client(config: Optional[HTTPConfig] = None) -> HTTPClient:
    """
    Get global HTTP client instance
    
    Args:
        config: HTTP configuration (uses defaults if None)
        
    Returns:
        HTTP client instance
    """
    global _global_client
    
    if _global_client is None:
        _global_client = HTTPClient(config)
    
    return _global_client


def reset_http_client():
    """Reset global HTTP client (useful for testing)"""
    global _global_client
    
    if _global_client:
        _global_client.close()
        _global_client = None
