"""
Logging Framework - Centralized logging with rotating file handlers
Replaces all print statements with proper logging
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
import json


class InternMailerLogger:
    """
    Centralized logging system for InternMailer
    Provides structured logging with file rotation and console output
    """
    
    _instances: dict[str, 'InternMailerLogger'] = {}
    _initialized = False
    
    def __init__(self, name: str, log_dir: str = 'logs'):
        """
        Initialize logger
        
        Args:
            name: Logger name (usually module name)
            log_dir: Directory to store log files
        """
        self.name = name
        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Test writability with .log extension — TCC specifically blocks .log file creation
            test_file = str(self.log_dir / '.write_test.log')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (PermissionError, OSError):
            # Fallback to /tmp/ if project dir is TCC-blocked
            self.log_dir = Path('/tmp/internmailer_logs')
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        self.logger.propagate = False
    
    @classmethod
    def get_logger(cls, name: str, log_dir: str = 'logs') -> 'InternMailerLogger':
        """Get or create logger instance"""
        if name not in cls._instances:
            cls._instances[name] = cls(name, log_dir)
        return cls._instances[name]
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (DEBUG and above with rotation)
        try:
            log_file = self.log_dir / f"{self.name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            print(f"⚠️ Warning: Could not setup file handler for {self.name}: {e}")
        
        # Error file handler (ERROR and above with daily rotation)
        try:
            error_file = self.log_dir / f"{self.name}_error.log"
            error_handler = TimedRotatingFileHandler(
                error_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)
        except (PermissionError, OSError) as e:
            print(f"⚠️ Warning: Could not setup error file handler for {self.name}: {e}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)
    
    def log_structured(self, level: str, event_type: str, data: dict):
        """Log structured data as JSON"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            **data
        }
        log_message = json.dumps(log_data)
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(log_message)
    
    def __getattr__(self, name):
        """Proxy to underlying logger"""
        return getattr(self.logger, name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class
    Usage:
        class MyClass(LoggerMixin):
            def __init__(self):
                self.logger = self.get_logger(__name__)
    """
    
    @property
    def logger(self) -> InternMailerLogger:
        """Get logger instance for this class"""
        class_name = self.__class__.__name__
        return InternMailerLogger.get_logger(class_name.lower())


def get_logger(name: str, log_dir: str = 'logs') -> InternMailerLogger:
    """
    Get logger instance
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    return InternMailerLogger.get_logger(name, log_dir)


def setup_logging(log_level: str = 'INFO', log_dir: str = 'logs'):
    """
    Setup global logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    InternMailerLogger._initialized = True


def log_function_call(logger: InternMailerLogger):
    """
    Decorator to log function calls
    
    Usage:
        @log_function_call(get_logger(__name__))
        def my_function(arg1, arg2):
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned successfully")
                return result
            except Exception as e:
                logger.exception(f"{func.__name__} failed with error: {str(e)}")
                raise
        return wrapper
    return decorator


def log_execution_time(logger: InternMailerLogger):
    """
    Decorator to log function execution time
    
    Usage:
        @log_execution_time(get_logger(__name__))
        def my_function():
            pass
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator


class EmailLogger(InternMailerLogger):
    """Specialized logger for email operations"""
    
    def log_email_sent(self, to_email: str, subject: str, 
                      metadata: Optional[dict] = None):
        """Log email sent event"""
        self.log_structured('info', 'email_sent', {
            'to_email': to_email,
            'subject': subject,
            'metadata': metadata or {}
        })
    
    def log_email_failed(self, to_email: str, error: str):
        """Log email failed event"""
        self.log_structured('error', 'email_failed', {
            'to_email': to_email,
            'error': error
        })
    
    def log_reply_received(self, from_email: str, category: str):
        """Log reply received event"""
        self.log_structured('info', 'reply_received', {
            'from_email': from_email,
            'category': category
        })
    
    def log_action_taken(self, action_type: str, email: str, details: Optional[dict] = None):
        """Log automated action taken"""
        self.log_structured('info', 'action_taken', {
            'action_type': action_type,
            'email': email,
            'details': details or {}
        })


class DaemonLogger(InternMailerLogger):
    """Specialized logger for daemon operations"""
    
    def log_cycle_start(self, cycle_type: str):
        """Log automation cycle start"""
        self.log_structured('info', 'cycle_start', {
            'cycle_type': cycle_type
        })
    
    def log_cycle_complete(self, cycle_type: str, stats: dict):
        """Log automation cycle complete"""
        self.log_structured('info', 'cycle_complete', {
            'cycle_type': cycle_type,
            'stats': stats
        })
    
    def log_daemon_start(self, config: dict):
        """Log daemon start"""
        self.log_structured('info', 'daemon_start', config)
    
    def log_daemon_stop(self, reason: str):
        """Log daemon stop"""
        self.log_structured('info', 'daemon_stop', {
            'reason': reason
        })


def get_email_logger() -> EmailLogger:
    """Get email logger instance"""
    return EmailLogger.get_logger('email')


def get_daemon_logger() -> DaemonLogger:
    """Get daemon logger instance"""
    return DaemonLogger.get_logger('daemon')


def get_inbox_logger() -> InternMailerLogger:
    """Get inbox monitor logger instance"""
    return InternMailerLogger.get_logger('inbox')


def get_ai_logger() -> InternMailerLogger:
    """Get AI provider logger instance"""
    return InternMailerLogger.get_logger('ai')
