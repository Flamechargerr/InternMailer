"""
Error Handling and Logging System for InternMailer
Provides centralized error handling, logging, and recovery mechanisms
"""

import logging
import traceback
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class InternMailerLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up logging configuration
        self.setup_logging()
        
        # Error tracking
        self.error_count = 0
        self.critical_errors = []
        self.warning_count = 0
        
    def setup_logging(self):
        """Set up comprehensive logging configuration"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # Main log file (DEBUG and above)
        main_log_file = self.log_dir / 'internmailer.log'
        file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file (ERROR and above)
        error_log_file = self.log_dir / 'errors.log'
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Performance log file
        perf_log_file = self.log_dir / 'performance.log'
        self.perf_handler = logging.FileHandler(perf_log_file, encoding='utf-8')
        self.perf_handler.setLevel(logging.INFO)
        self.perf_handler.setFormatter(simple_formatter)
        
        # Create performance logger
        self.perf_logger = logging.getLogger('performance')
        self.perf_logger.addHandler(self.perf_handler)
        self.perf_logger.setLevel(logging.INFO)
        self.perf_logger.propagate = False
        
        # Application-specific loggers
        self.setup_component_loggers()
    
    def setup_component_loggers(self):
        """Set up loggers for specific components"""
        components = [
            'scheduler', 'job_scraper', 'ai_matcher', 'resume_tailor',
            'cover_letter_generator', 'contact_finder', 'prestige_scorer',
            'application_tracker', 'email_notifier', 'database_manager',
            'bundle_generator', 'reporting_dashboard'
        ]
        
        for component in components:
            logger = logging.getLogger(component)
            
            # Component-specific log file
            component_log_file = self.log_dir / f'{component}.log'
            component_handler = logging.FileHandler(component_log_file, encoding='utf-8')
            component_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                f'%(asctime)s - {component.upper()} - %(levelname)s - %(message)s'
            )
            component_handler.setFormatter(formatter)
            
            logger.addHandler(component_handler)
            logger.setLevel(logging.DEBUG)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  component: str = 'unknown', critical: bool = False):
        """Log error with context and tracking"""
        self.error_count += 1
        
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'critical': critical
        }
        
        # Log to appropriate logger
        logger = logging.getLogger(component)
        
        if critical:
            logger.critical(f"CRITICAL ERROR: {error}", extra={'error_data': error_data})
            self.critical_errors.append(error_data)
        else:
            logger.error(f"ERROR: {error}", extra={'error_data': error_data})
        
        # Save error to JSON file for analysis
        self.save_error_to_file(error_data)
        
        # Send alert for critical errors
        if critical:
            self.send_error_alert(error_data)
    
    def log_warning(self, message: str, context: Dict[str, Any] = None, 
                   component: str = 'unknown'):
        """Log warning with context"""
        self.warning_count += 1
        
        logger = logging.getLogger(component)
        logger.warning(f"WARNING: {message}", extra={'context': context or {}})
    
    def log_performance(self, operation: str, duration: float, 
                       details: Dict[str, Any] = None):
        """Log performance metrics"""
        perf_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_seconds': duration,
            'details': details or {}
        }
        
        self.perf_logger.info(f"PERFORMANCE: {operation} took {duration:.2f}s", 
                             extra={'perf_data': perf_data})
    
    def save_error_to_file(self, error_data: Dict[str, Any]):
        """Save error data to JSON file for analysis"""
        try:
            error_file = self.log_dir / 'error_details.jsonl'
            
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, default=str) + '\n')
                
        except Exception as e:
            # Fallback logging if file write fails
            logging.getLogger('error_handler').error(f"Failed to save error to file: {e}")
    
    def send_error_alert(self, error_data: Dict[str, Any]):
        """Send email alert for critical errors"""
        try:
            # Only send alerts for critical errors
            if not error_data.get('critical', False):
                return
            
            # Email configuration
            sender_email = os.getenv('SENDER_EMAIL', 'internmailer.alerts@gmail.com')
            sender_password = os.getenv('SENDER_PASSWORD', '')
            recipient_email = 'tripathy.anamay23@gmail.com'
            
            if not sender_password:
                logging.getLogger('error_handler').warning("No email password configured for alerts")
                return
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"🚨 CRITICAL ERROR in InternMailer - {error_data['component']}"
            
            body = f"""
            A critical error occurred in the InternMailer system:
            
            Component: {error_data['component']}
            Error Type: {error_data['error_type']}
            Error Message: {error_data['error_message']}
            Timestamp: {error_data['timestamp']}
            
            Context:
            {json.dumps(error_data['context'], indent=2)}
            
            Traceback:
            {error_data['traceback']}
            
            Please check the system logs for more details.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            
            logging.getLogger('error_handler').info("Critical error alert sent successfully")
            
        except Exception as e:
            logging.getLogger('error_handler').error(f"Failed to send error alert: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors and warnings"""
        return {
            'total_errors': self.error_count,
            'critical_errors': len(self.critical_errors),
            'warnings': self.warning_count,
            'recent_critical_errors': self.critical_errors[-5:] if self.critical_errors else []
        }
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns from log files"""
        try:
            error_file = self.log_dir / 'error_details.jsonl'
            
            if not error_file.exists():
                return {'message': 'No error data available'}
            
            errors = []
            with open(error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        errors.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            if not errors:
                return {'message': 'No valid error data found'}
            
            # Analyze patterns
            error_types = {}
            components = {}
            recent_errors = []
            
            for error in errors:
                # Count by error type
                error_type = error.get('error_type', 'Unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Count by component
                component = error.get('component', 'unknown')
                components[component] = components.get(component, 0) + 1
                
                # Collect recent errors (last 24 hours)
                error_time = datetime.fromisoformat(error.get('timestamp', ''))
                if (datetime.now() - error_time).days < 1:
                    recent_errors.append(error)
            
            return {
                'total_errors_analyzed': len(errors),
                'error_types': dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)),
                'components_with_errors': dict(sorted(components.items(), key=lambda x: x[1], reverse=True)),
                'recent_errors_24h': len(recent_errors),
                'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
                'most_problematic_component': max(components.items(), key=lambda x: x[1])[0] if components else None
            }
            
        except Exception as e:
            logging.getLogger('error_handler').error(f"Failed to analyze error patterns: {e}")
            return {'error': f'Analysis failed: {str(e)}'}

# Decorator for automatic error handling
def handle_errors(component: str = 'unknown', critical: bool = False, 
                 retry_count: int = 0, fallback_value: Any = None):
    """Decorator for automatic error handling and logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger_instance = getattr(wrapper, '_logger_instance', None)
            if not logger_instance:
                logger_instance = InternMailerLogger()
                wrapper._logger_instance = logger_instance
            
            attempts = 0
            max_attempts = retry_count + 1
            
            while attempts < max_attempts:
                try:
                    # Log function start
                    logging.getLogger(component).debug(f"Starting {func.__name__} (attempt {attempts + 1})")
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Log successful completion
                    logging.getLogger(component).debug(f"Completed {func.__name__} successfully")
                    
                    return result
                    
                except Exception as e:
                    attempts += 1
                    
                    # Prepare context
                    context = {
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()),
                        'attempt': attempts,
                        'max_attempts': max_attempts
                    }
                    
                    # Log error
                    logger_instance.log_error(e, context, component, critical)
                    
                    # If we have more attempts, wait and retry
                    if attempts < max_attempts:
                        import time
                        wait_time = 2 ** (attempts - 1)  # Exponential backoff
                        logging.getLogger(component).info(f"Retrying {func.__name__} in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        # All attempts failed
                        logging.getLogger(component).error(f"All {max_attempts} attempts failed for {func.__name__}")
                        
                        # Return fallback value or re-raise
                        if fallback_value is not None:
                            logging.getLogger(component).info(f"Returning fallback value for {func.__name__}")
                            return fallback_value
                        else:
                            raise
            
        return wrapper
    return decorator

# Performance monitoring decorator
def monitor_performance(operation_name: str = None):
    """Decorator for monitoring function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            logger_instance = getattr(wrapper, '_logger_instance', None)
            if not logger_instance:
                logger_instance = InternMailerLogger()
                wrapper._logger_instance = logger_instance
            
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log performance
                details = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'success': True
                }
                
                logger_instance.log_performance(operation, duration, details)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log performance even for failed operations
                details = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'success': False,
                    'error': str(e)
                }
                
                logger_instance.log_performance(f"{operation}_FAILED", duration, details)
                
                raise
        
        return wrapper
    return decorator

# Global logger instance
_global_logger = None

def get_logger() -> InternMailerLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = InternMailerLogger()
    return _global_logger

# Convenience functions
def log_error(error: Exception, context: Dict[str, Any] = None, 
             component: str = 'unknown', critical: bool = False):
    """Convenience function to log errors"""
    get_logger().log_error(error, context, component, critical)

def log_warning(message: str, context: Dict[str, Any] = None, 
               component: str = 'unknown'):
    """Convenience function to log warnings"""
    get_logger().log_warning(message, context, component)

def log_performance(operation: str, duration: float, 
                   details: Dict[str, Any] = None):
    """Convenience function to log performance"""
    get_logger().log_performance(operation, duration, details)

if __name__ == "__main__":
    # Test the error handling system
    logger = InternMailerLogger()
    
    # Test error logging
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        logger.log_error(e, {'test_context': 'demo'}, 'test_component')
    
    # Test warning logging
    logger.log_warning("This is a test warning", {'test_data': 123}, 'test_component')
    
    # Test performance logging
    import time
    start = time.time()
    time.sleep(0.1)
    duration = time.time() - start
    logger.log_performance("test_operation", duration, {'test': True})
    
    # Test decorator
    @handle_errors(component='test', retry_count=2, fallback_value="fallback")
    def test_function():
        raise Exception("Test exception")
    
    result = test_function()
    print(f"Result: {result}")
    
    # Get error summary
    summary = logger.get_error_summary()
    print(f"Error summary: {summary}")
    
    print("\n✅ Error handling system test completed!")