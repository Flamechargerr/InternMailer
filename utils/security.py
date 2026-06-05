"""
Security Utilities for Production
=================================
Security helpers: input sanitization, secret masking, validation
"""

import re
import logging
from typing import Any, Dict, Optional
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


class SecretMasker:
    """Mask sensitive data in logs and output"""
    
    SENSITIVE_PATTERNS = [
        r'password["\s:=]+([^\s"\'}]+)',
        r'api[_-]?key["\s:=]+([^\s"\'}]+)',
        r'token["\s:=]+([^\s"\'}]+)',
        r'secret["\s:=]+([^\s"\'}]+)',
        r'credential["\s:=]+([^\s"\'}]+)',
        r'app[_-]?password["\s:=]+([^\s"\'}]+)',
    ]
    
    @classmethod
    def mask_string(cls, value: str, mask_char: str = '*', visible_chars: int = 4) -> str:
        """Mask a string value, showing only first few characters"""
        if not value or len(value) <= visible_chars:
            return mask_char * len(value) if value else ''
        return value[:visible_chars] + mask_char * (len(value) - visible_chars)
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive keys in a dictionary"""
        masked = {}
        sensitive_keys = ['password', 'api_key', 'token', 'secret', 'credential', 
                         'app_password', 'gmail_app_password', 'email_password']
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(sk in key_lower for sk in sensitive_keys):
                if isinstance(value, str):
                    masked[key] = cls.mask_string(value)
                else:
                    masked[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            else:
                masked[key] = value
        
        return masked
    
    @classmethod
    def sanitize_log_message(cls, message: str) -> str:
        """Remove sensitive data from log messages"""
        sanitized = message
        for pattern in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, lambda m: f'{m.group(0).split("=")[0]}="***MASKED***"', 
                             sanitized, flags=re.IGNORECASE)
        return sanitized


class InputValidator:
    """Validate and sanitize user input"""
    
    @staticmethod
    def sanitize_string(value: Any, max_length: int = 1000) -> str:
        """Sanitize a string input"""
        if not isinstance(value, str):
            value = str(value)
        # Remove null bytes and control characters
        value = value.replace('\x00', '').replace('\r', '')
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        return value.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_table_name(table: str) -> bool:
        """Validate SQL table name (prevent injection)"""
        if not table or not isinstance(table, str):
            return False
        # Only allow alphanumeric and underscore
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, table))
    
    @staticmethod
    def validate_positive_int(value: Any, max_value: int = 10000) -> Optional[int]:
        """Validate and convert to positive integer"""
        try:
            if isinstance(value, str):
                value = int(value)
            if isinstance(value, int) and 0 < value <= max_value:
                return value
        except (ValueError, TypeError):
            pass
        return None


def require_json(f):
    """Decorator to require JSON request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


def validate_input(required_fields: list = None, optional_fields: dict = None):
    """Decorator to validate request input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json(silent=True) or {}
            errors = []
            
            # Check required fields
            if required_fields:
                for field in required_fields:
                    if field not in data or not data[field]:
                        errors.append(f"Missing required field: {field}")
            
            # Validate optional fields
            if optional_fields:
                for field, validator in optional_fields.items():
                    if field in data:
                        if not validator(data[field]):
                            errors.append(f"Invalid value for field: {field}")
            
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_sql_identifier(identifier: str) -> str:
    """Sanitize SQL identifier (table/column name)"""
    if not InputValidator.validate_table_name(identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier


def rate_limit_check(max_per_minute: int = 60):
    """Simple rate limit check decorator"""
    from collections import defaultdict
    from time import time
    
    # In-memory rate limit tracking (use Redis in production)
    request_times = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            now = time()
            
            # Clean old entries
            request_times[client_ip] = [
                t for t in request_times[client_ip] 
                if now - t < 60
            ]
            
            # Check limit
            if len(request_times[client_ip]) >= max_per_minute:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': 60
                }), 429
            
            # Record request
            request_times[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
