"""
Utils Package - Utility modules for InternMailer
"""

from .logger import (
    get_logger,
    get_email_logger,
    get_daemon_logger,
    get_inbox_logger,
    get_ai_logger,
    setup_logging,
    log_function_call,
    log_execution_time
)

from .exceptions import (
    InternMailerException,
    ConfigurationError,
    DatabaseError,
    EmailError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError,
    FileError,
    retry,
    ErrorHandler,
    CircuitBreaker,
    Timeout,
    BulkError,
    execute_bulk
)

from .validators import (
    EmailValidator,
    StringValidator,
    NumberValidator,
    UrlValidator,
    JSONValidator,
    DateValidator,
    FileValidator,
    RequestValidator,
    validate_and_raise,
    sanitize_input,
    ValidationResult
)

from .config import (
    config,
    Config,
    Environment
)

from .backup_scheduler import BackupScheduler
from .profile import Profile, get_profile

__all__ = [
    # Logging
    'get_logger',
    'get_email_logger',
    'get_daemon_logger',
    'get_inbox_logger',
    'get_ai_logger',
    'setup_logging',
    'log_function_call',
    'log_execution_time',
    # Exceptions
    'InternMailerException',
    'ConfigurationError',
    'DatabaseError',
    'EmailError',
    'APIError',
    'AuthenticationError',
    'RateLimitError',
    'ValidationError',
    'NetworkError',
    'FileError',
    'retry',
    'ErrorHandler',
    'CircuitBreaker',
    'Timeout',
    'BulkError',
    'execute_bulk',
    # Validators
    'EmailValidator',
    'StringValidator',
    'NumberValidator',
    'UrlValidator',
    'JSONValidator',
    'DateValidator',
    'FileValidator',
    'RequestValidator',
    'validate_and_raise',
    'sanitize_input',
    'ValidationResult',
    # Configuration
    'config',
    'Config',
    'Environment',
    # Backup
    'BackupScheduler',
    # Profile
    'Profile',
    'get_profile',
]
