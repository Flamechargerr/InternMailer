"""
Exception Handling and Retry Logic
Unified exception handling with automatic retry and exponential backoff
"""

import time
import functools
from typing import Callable, Optional, Type, Tuple, Any, Dict
from dataclasses import dataclass
from enum import Enum


class InternMailerException(Exception):
    """Base exception for InternMailer"""
    pass


class ConfigurationError(InternMailerException):
    """Raised when configuration is invalid"""
    pass


class DatabaseError(InternMailerException):
    """Raised when database operation fails"""
    pass


class EmailError(InternMailerException):
    """Raised when email operation fails"""
    pass


class APIError(InternMailerException):
    """Raised when API call fails"""
    pass


class AuthenticationError(InternMailerException):
    """Raised when authentication fails"""
    pass


class RateLimitError(InternMailerException):
    """Raised when rate limit is reached"""
    pass


class ValidationError(InternMailerException):
    """Raised when input validation fails"""
    pass


class NetworkError(InternMailerException):
    """Raised when network operation fails"""
    pass


class FileError(InternMailerException):
    """Raised when file operation fails"""
    pass


class RetryPolicy(Enum):
    """Retry policies for different operations"""
    NO_RETRY = "no_retry"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL
    retry_on: Tuple[Type[Exception], ...] = (Exception,)
    ignore_on: Tuple[Type[Exception], ...] = ()
    on_retry_callback: Optional[Callable[[int, Exception], None]] = None


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    ignore_on: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    fallback: Optional[Any] = None
):
    """
    Decorator for automatic retry with exponential backoff
    
    Usage:
        @retry(max_attempts=3, retry_on=(NetworkError, APIError))
        def send_request(url):
            return requests.get(url)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                policy=policy,
                retry_on=retry_on or (Exception,),
                ignore_on=ignore_on or (),
                on_retry_callback=on_retry
            )
            
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except config.ignore_on as e:
                    # Don't retry on ignored exceptions
                    raise
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        # Final attempt failed
                        if fallback is not None:
                            return fallback
                        raise
                    
                    # Calculate delay based on policy
                    delay = _calculate_delay(
                        attempt - 1,
                        config.base_delay,
                        config.max_delay,
                        config.backoff_factor,
                        config.policy,
                        config.jitter
                    )
                    
                    # Call callback if provided
                    if config.on_retry_callback:
                        config.on_retry_callback(attempt, e)
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should never reach here
            raise last_exception
        
        return wrapper
    return decorator


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    backoff_factor: float,
    policy: RetryPolicy,
    jitter: bool
) -> float:
    """Calculate delay before next retry attempt"""
    import random
    
    if policy == RetryPolicy.IMMEDIATE:
        delay = 0
    elif policy == RetryPolicy.LINEAR:
        delay = base_delay * attempt
    else:  # EXPONENTIAL
        delay = base_delay * (backoff_factor ** attempt)
    
    # Cap at max delay
    delay = min(delay, max_delay)
    
    # Add jitter to avoid thundering herd
    if jitter and delay > 0:
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay


class ErrorHandler:
    """
    Centralized error handler for consistent error responses
    """
    
    @staticmethod
    def handle_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        raise_error: bool = False
    ) -> Dict[str, Any]:
        """
        Handle an error and return standardized response
        
        Args:
            error: The exception to handle
            context: Additional context information
            raise_error: Whether to re-raise the error
            
        Returns:
            Dictionary with error information
        """
        error_info = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        # Log the error
        from utils.logger import get_logger
        logger = get_logger('error_handler')
        logger.error(
            f"Error: {error_info['error_type']}: {error_info['error_message']}",
            exc_info=True
        )
        
        if raise_error:
            raise error
        
        return error_info
    
    @staticmethod
    def wrap_errors(
        error_types: Tuple[Type[Exception], ...] = (Exception,),
        wrap_as: Type[Exception] = InternMailerException
    ):
        """
        Decorator to wrap exceptions in custom error types
        
        Usage:
            @ErrorHandler.wrap_errors((ValueError, TypeError), ValidationError)
            def process_data(data):
                pass
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except error_types as e:
                    raise wrap_as(str(e)) from e
            return wrapper
        return decorator
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], 
                              required_fields: list[str]) -> None:
        """
        Validate that required fields are present in data
        
        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [
            field for field in required_fields 
            if field not in data or data[field] is None
        ]
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures
    
    Usage:
        circuit = CircuitBreaker(failure_threshold=5, timeout=60)
        
        @circuit
        def unreliable_function():
            # Code that might fail
            pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_attempts: int = 1
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before attempting to close circuit
            half_open_attempts: Number of successful attempts needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.state = 'closed'  # closed, open, half_open
        self._lock = __import__('threading').Lock()
    
    def __call__(self, func: Callable):
        """Decorator for circuit breaker protection"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        import time
        
        with self._lock:
            if self.state == 'open':
                if time.time() - self.last_failure_time > self.timeout:
                    # Try to close circuit
                    self.state = 'half_open'
                    self.success_count = 0
                else:
                    raise APIError(
                        f"Circuit breaker is open. Too many failures. "
                        f"Retry in {self.timeout - (time.time() - self.last_failure_time):.1f}s"
                    )
        
        try:
            result = func(*args, **kwargs)
            
            with self._lock:
                if self.state == 'half_open':
                    self.success_count += 1
                    if self.success_count >= self.half_open_attempts:
                        # Circuit recovered
                        self.state = 'closed'
                        self.failure_count = 0
                else:
                    # Reset failure count on success
                    self.failure_count = 0
            
            return result
            
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'open'
            
            raise
    
    def reset(self):
        """Manually reset circuit breaker"""
        with self._lock:
            self.failure_count = 0
            self.success_count = 0
            self.state = 'closed'
    
    def get_state(self) -> str:
        """Get current circuit breaker state"""
        with self._lock:
            return self.state


class Timeout(Exception):
    """Timeout exception for operations"""
    pass


def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to function execution
    
    Usage:
        @with_timeout(timeout_seconds=10)
        def slow_operation():
            pass
    """
    import signal
    
    def decorator(func: Callable):
        def handler(signum, frame):
            raise Timeout(f"Operation timed out after {timeout_seconds} seconds")
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Set signal handler
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)
                return result
            except Timeout as e:
                signal.alarm(0)
                raise
            finally:
                # Restore old handler
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator


class BulkError(Exception):
    """Raised when multiple operations fail in bulk"""
    
    def __init__(self, errors: list[tuple[Any, Exception]], message: str = None):
        """
        Args:
            errors: List of (item, error) tuples
            message: Optional custom message
        """
        self.errors = errors
        self.message = message or f"{len(errors)} operations failed"
        super().__init__(self.message)


def execute_bulk(
    items: list[Any],
    operation: Callable[[Any], Any],
    continue_on_error: bool = True,
    raise_on_any_error: bool = False
) -> dict[str, Any]:
    """
    Execute operation on multiple items with error handling
    
    Args:
        items: List of items to process
        operation: Function to execute on each item
        continue_on_error: Whether to continue on error
        raise_on_any_error: Whether to raise exception on any error
        
    Returns:
        Dictionary with 'success' and 'errors' lists
    """
    from utils.logger import get_logger
    logger = get_logger('bulk_executor')
    
    results = {
        'success': [],
        'errors': []
    }
    
    for item in items:
        try:
            result = operation(item)
            results['success'].append((item, result))
        except Exception as e:
            results['errors'].append((item, e))
            logger.error(f"Error processing item: {str(e)}", exc_info=True)
            
            if not continue_on_error:
                raise
            if raise_on_any_error:
                raise
    
    return results
