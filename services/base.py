"""
Base classes and configurations for the services layer.

Provides common functionality, error handling, and configuration management
that all services inherit from.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from functools import wraps

import structlog


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

T = TypeVar('T')


@dataclass
class ServiceConfig:
    """Configuration for services."""
    
    # Environment settings
    environment: str = "development"  # development, staging, production
    debug: bool = False
    log_level: str = "INFO"
    
    # Database configuration
    database_url: Optional[str] = None
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_timeout: int = 30
    
    # Email configuration
    email_provider: str = "smtp"  # smtp, graph, mock
    email_config: Dict[str, Any] = None
    email_rate_limit: int = 60  # emails per minute
    email_daily_limit: int = 2000
    
    # Analytics configuration
    analytics_batch_size: int = 100
    analytics_flush_interval: int = 300  # seconds
    
    # Cache configuration
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    
    # Mock service settings
    use_mocks: bool = False
    mock_delay_min: float = 0.1
    mock_delay_max: float = 0.5
    mock_failure_rate: float = 0.0  # 0.0 to 1.0
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.email_config is None:
            self.email_config = {}
        
        # Set use_mocks based on environment if not explicitly set
        if self.environment == "development" and not hasattr(self, '_use_mocks_set'):
            self.use_mocks = True


class ServiceError(Exception):
    """Base exception for service layer errors."""
    
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error
        self.timestamp = datetime.utcnow()


class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass


class ServiceUnavailableError(ServiceError):
    """Raised when a service is temporarily unavailable."""
    pass


class RateLimitError(ServiceError):
    """Raised when rate limits are exceeded."""
    pass


def with_error_handling(func):
    """Decorator to add consistent error handling to service methods."""
    
    @wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        method_name = f"{self.__class__.__name__}.{func.__name__}"
        start_time = time.time()
        
        try:
            logger.info("Service method started", method=method_name)
            result = await func(self, *args, **kwargs)
            
            duration = time.time() - start_time
            logger.info(
                "Service method completed successfully", 
                method=method_name, 
                duration=duration
            )
            return result
            
        except ServiceError:
            # Re-raise service errors as-is
            duration = time.time() - start_time
            logger.error(
                "Service method failed with service error",
                method=method_name,
                duration=duration,
                exc_info=True
            )
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Service method failed with unexpected error",
                method=method_name,
                duration=duration,
                error=str(e),
                exc_info=True
            )
            raise ServiceError(
                f"Unexpected error in {method_name}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                original_error=e
            )
    
    @wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        method_name = f"{self.__class__.__name__}.{func.__name__}"
        start_time = time.time()
        
        try:
            logger.info("Service method started", method=method_name)
            result = func(self, *args, **kwargs)
            
            duration = time.time() - start_time
            logger.info(
                "Service method completed successfully", 
                method=method_name, 
                duration=duration
            )
            return result
            
        except ServiceError:
            # Re-raise service errors as-is
            duration = time.time() - start_time
            logger.error(
                "Service method failed with service error",
                method=method_name,
                duration=duration,
                exc_info=True
            )
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Service method failed with unexpected error",
                method=method_name,
                duration=duration,
                error=str(e),
                exc_info=True
            )
            raise ServiceError(
                f"Unexpected error in {method_name}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                original_error=e
            )
    
    # Return appropriate wrapper based on whether the function is async
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class BaseService(ABC):
    """Base class for all services."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = structlog.get_logger(self.__class__.__name__)
        self._initialized = False
        self._cache = {} if config.cache_enabled else None
        
    async def initialize(self) -> None:
        """Initialize the service. Override in subclasses."""
        if self._initialized:
            return
            
        self.logger.info("Initializing service", service=self.__class__.__name__)
        await self._initialize_impl()
        self._initialized = True
        self.logger.info("Service initialized successfully", service=self.__class__.__name__)
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implement service-specific initialization logic."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup service resources. Override in subclasses."""
        if not self._initialized:
            return
            
        self.logger.info("Cleaning up service", service=self.__class__.__name__)
        await self._cleanup_impl()
        self._initialized = False
        self.logger.info("Service cleanup completed", service=self.__class__.__name__)
    
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implement service-specific cleanup logic."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        try:
            status = await self._health_check_impl()
            return {
                "service": self.__class__.__name__,
                "status": "healthy",
                "initialized": self._initialized,
                "timestamp": datetime.utcnow().isoformat(),
                **status
            }
        except Exception as e:
            return {
                "service": self.__class__.__name__,
                "status": "unhealthy",
                "initialized": self._initialized,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    @abstractmethod
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Implement service-specific health check logic."""
        pass
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key with service prefix."""
        return f"{self.__class__.__name__}:{key}"
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._cache:
            return None
        
        cache_key = self._get_cache_key(key)
        cached_item = self._cache.get(cache_key)
        
        if cached_item is None:
            return None
            
        # Check if cached item is expired
        if time.time() > cached_item['expires_at']:
            del self._cache[cache_key]
            return None
            
        return cached_item['value']
    
    def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        if not self._cache:
            return
        
        cache_key = self._get_cache_key(key)
        expires_at = time.time() + (ttl or self.config.cache_ttl)
        
        self._cache[cache_key] = {
            'value': value,
            'expires_at': expires_at
        }
        
        # Simple cache cleanup - remove expired items periodically
        if len(self._cache) > 1000:  # Arbitrary limit
            current_time = time.time()
            expired_keys = [
                k for k, v in self._cache.items() 
                if current_time > v['expires_at']
            ]
            for k in expired_keys:
                del self._cache[k]
    
    def _cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        if not self._cache:
            return
        
        cache_key = self._get_cache_key(key)
        self._cache.pop(cache_key, None)
    
    @asynccontextmanager
    async def _ensure_initialized(self):
        """Context manager to ensure service is initialized."""
        if not self._initialized:
            await self.initialize()
        
        try:
            yield self
        finally:
            # Context manager doesn't automatically cleanup
            # Services should be cleaned up by the service factory
            pass


class AsyncToSyncAdapter(Generic[T]):
    """Adapter to provide synchronous interface for async services."""
    
    def __init__(self, async_service: T):
        self._async_service = async_service
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop for sync operations."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, we need to use a thread pool
            # This is a simplified approach - in production you might want
            # to use asyncio.run_coroutine_threadsafe
            return loop
        except RuntimeError:
            # No event loop running, create a new one
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
            return self._loop
    
    def _run_async(self, coro):
        """Run async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, this is problematic
            # In a real implementation, you'd want to handle this better
            import concurrent.futures
            import threading
            
            # Run in a separate thread
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
                
        except RuntimeError:
            # No event loop running, safe to create one
            return asyncio.run(coro)
    
    def __getattr__(self, name):
        """Proxy attribute access to the async service."""
        attr = getattr(self._async_service, name)
        
        if asyncio.iscoroutinefunction(attr):
            # Wrap async methods to run synchronously
            def sync_wrapper(*args, **kwargs):
                coro = attr(*args, **kwargs)
                return self._run_async(coro)
            return sync_wrapper
        else:
            # Return non-async attributes as-is
            return attr


def create_sync_adapter(async_service: T) -> T:
    """Create a synchronous adapter for an async service."""
    return AsyncToSyncAdapter(async_service)
