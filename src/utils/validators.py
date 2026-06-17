"""
Data Validation Layer - Input validation and sanitization
Comprehensive validation for all inputs
"""

import re
import email
import html
import json
from typing import Any, Optional, List, Dict, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from utils.exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    value: Any
    errors: List[str]
    warnings: List[str]
    
    @classmethod
    def success(cls, value: Any, warnings: List[str] = None) -> 'ValidationResult':
        """Create successful validation result"""
        return cls(
            is_valid=True,
            value=value,
            errors=[],
            warnings=warnings or []
        )
    
    @classmethod
    def failure(cls, errors: List[str], value: Any = None) -> 'ValidationResult':
        """Create failed validation result"""
        return cls(
            is_valid=False,
            value=value,
            errors=errors,
            warnings=[]
        )


class EmailValidator:
    """Email validation and sanitization"""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.com', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com', 'yopmail.com'
    }
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email is valid"""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        return bool(EmailValidator.EMAIL_REGEX.match(email))
    
    @staticmethod
    def is_disposable_email(email: str) -> bool:
        """Check if email is from disposable domain"""
        if not email:
            return False
        
        domain = email.split('@')[-1].lower()
        return domain in EmailValidator.DISPOSABLE_DOMAINS
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email address"""
        if not email:
            return ''
        
        # Strip whitespace and lowercase
        email = email.strip().lower()
        
        # Remove extra dots (for Gmail-like addresses)
        if '@gmail.com' in email:
            local, domain = email.split('@')
            local = local.replace('.', '')
            email = f"{local}@{domain}"
        
        return email
    
    @staticmethod
    def validate_email_list(emails: Union[str, List[str]]) -> ValidationResult:
        """
        Validate a list of emails
        
        Args:
            emails: String of comma-separated emails or list of emails
            
        Returns:
            ValidationResult with list of valid emails
        """
        if isinstance(emails, str):
            emails = [e.strip() for e in emails.split(',')]
        
        valid_emails = []
        errors = []
        
        for email in emails:
            if not email:
                continue
            
            if EmailValidator.is_valid_email(email):
                if not EmailValidator.is_disposable_email(email):
                    valid_emails.append(EmailValidator.sanitize_email(email))
                else:
                    errors.append(f"Disposable email not allowed: {email}")
            else:
                errors.append(f"Invalid email: {email}")
        
        if errors:
            return ValidationResult.failure(errors, valid_emails)
        
        return ValidationResult.success(valid_emails)


class StringValidator:
    """String validation and sanitization"""
    
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'expression\s*\(',
    ]
    
    @staticmethod
    def is_safe_string(text: str, max_length: int = 10000) -> bool:
        """Check if string is safe from XSS attacks"""
        if not text or not isinstance(text, str):
            return False
        
        if len(text) > max_length:
            return False
        
        # Check for dangerous patterns
        for pattern in StringValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def sanitize_string(text: str, allow_html: bool = False) -> str:
        """Sanitize string input"""
        if not text or not isinstance(text, str):
            return ''
        
        # HTML escape if not allowed
        if not allow_html:
            text = html.escape(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def validate_name(name: str) -> ValidationResult:
        """Validate person name"""
        if not name or not isinstance(name, str):
            return ValidationResult.failure(["Name is required"])
        
        name = name.strip()
        
        if len(name) < 2:
            return ValidationResult.failure(["Name is too short (min 2 chars)"])
        
        if len(name) > 100:
            return ValidationResult.failure(["Name is too long (max 100 chars)"])
        
        if not StringValidator.is_safe_string(name):
            return ValidationResult.failure(["Name contains invalid characters"])
        
        return ValidationResult.success(name)
    
    @staticmethod
    def validate_subject(subject: str, max_length: int = 200) -> ValidationResult:
        """Validate email subject"""
        if not subject or not isinstance(subject, str):
            return ValidationResult.failure(["Subject is required"])
        
        subject = subject.strip()
        
        if len(subject) == 0:
            return ValidationResult.failure(["Subject cannot be empty"])
        
        if len(subject) > max_length:
            return ValidationResult.failure([f"Subject too long (max {max_length} chars)"])
        
        return ValidationResult.success(subject)
    
    @staticmethod
    def validate_text(text: str, min_length: int = 1, 
                     max_length: int = 10000) -> ValidationResult:
        """Validate text content"""
        if not text or not isinstance(text, str):
            return ValidationResult.failure(["Text is required"])
        
        text = text.strip()
        
        if len(text) < min_length:
            return ValidationResult.failure([f"Text too short (min {min_length} chars)"])
        
        if len(text) > max_length:
            return ValidationResult.failure([f"Text too long (max {max_length} chars)"])
        
        return ValidationResult.success(text)


class NumberValidator:
    """Number validation"""
    
    @staticmethod
    def validate_positive_integer(value: Any, field_name: str = "value") -> ValidationResult:
        """Validate positive integer"""
        try:
            num = int(value)
            if num <= 0:
                return ValidationResult.failure([f"{field_name} must be positive"])
            return ValidationResult.success(num)
        except (TypeError, ValueError):
            return ValidationResult.failure([f"{field_name} must be a valid integer"])
    
    @staticmethod
    def validate_range(value: Any, min_val: int, max_val: int,
                     field_name: str = "value") -> ValidationResult:
        """Validate integer in range"""
        result = NumberValidator.validate_positive_integer(value, field_name)
        
        if not result.is_valid:
            return result
        
        if result.value < min_val or result.value > max_val:
            return ValidationResult.failure([
                f"{field_name} must be between {min_val} and {max_val}"
            ])
        
        return result
    
    @staticmethod
    def validate_email_count(count: Any) -> ValidationResult:
        """Validate email count (1-500 per day)"""
        return NumberValidator.validate_range(
            count, 1, 500, "Email count"
        )


class UrlValidator:
    """URL validation"""
    
    @staticmethod
    def is_valid_url(url: str, allowed_schemes: List[str] = None) -> bool:
        """Check if URL is valid"""
        if not url or not isinstance(url, str):
            return False
        
        try:
            result = re.match(
                r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*/?',
                url
            )
            
            if not result:
                return False
            
            if allowed_schemes:
                scheme = url.split(':')[0].lower()
                return scheme in allowed_schemes
            
            return True
        except:
            return False
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL"""
        if not url:
            return ''
        
        url = url.strip()
        
        # Ensure scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url


class JSONValidator:
    """JSON validation"""
    
    @staticmethod
    def is_valid_json(text: str) -> bool:
        """Check if string is valid JSON"""
        try:
            json.loads(text)
            return True
        except:
            return False
    
    @staticmethod
    def validate_json(text: str) -> ValidationResult:
        """Validate and parse JSON"""
        if not text or not isinstance(text, str):
            return ValidationResult.failure(["JSON is required"])
        
        try:
            data = json.loads(text)
            return ValidationResult.success(data)
        except json.JSONDecodeError as e:
            return ValidationResult.failure([f"Invalid JSON: {str(e)}"])


class DateValidator:
    """Date validation"""
    
    @staticmethod
    def validate_date_string(date_str: str, 
                          formats: List[str] = None) -> ValidationResult:
        """Validate date string"""
        if not date_str or not isinstance(date_str, str):
            return ValidationResult.failure(["Date is required"])
        
        formats = formats or [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in formats:
            try:
                date = datetime.strptime(date_str, fmt)
                return ValidationResult.success(date)
            except ValueError:
                continue
        
        return ValidationResult.failure(["Invalid date format"])
    
    @staticmethod
    def validate_future_date(date_str: str) -> ValidationResult:
        """Validate date is in the future"""
        result = DateValidator.validate_date_string(date_str)
        
        if not result.is_valid:
            return result
        
        if result.value < datetime.now():
            return ValidationResult.failure(["Date must be in the future"])
        
        return result


class FileValidator:
    """File validation"""
    
    ALLOWED_EXTENSIONS = {
        'pdf', 'csv', 'txt', 'doc', 'docx', 'jpg', 'png'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_extension(filename: str) -> ValidationResult:
        """Validate file extension"""
        if not filename:
            return ValidationResult.failure(["Filename is required"])
        
        ext = Path(filename).suffix[1:].lower()
        
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            return ValidationResult.failure([
                f"File type not allowed. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"
            ])
        
        return ValidationResult.success(filename)
    
    @staticmethod
    def validate_file_size(size: int) -> ValidationResult:
        """Validate file size"""
        if size > FileValidator.MAX_FILE_SIZE:
            return ValidationResult.failure([
                f"File too large (max {FileValidator.MAX_FILE_SIZE / (1024*1024)}MB)"
            ])
        
        return ValidationResult.success(size)


class RequestValidator:
    """Request payload validation"""
    
    @staticmethod
    def validate_email_request(data: Dict[str, Any]) -> ValidationResult:
        """Validate email send request"""
        errors = []
        
        # Validate required fields
        if 'to_email' not in data or not data['to_email']:
            errors.append("to_email is required")
        
        if 'subject' not in data or not data['subject']:
            errors.append("subject is required")
        
        if 'body' not in data or not data['body']:
            errors.append("body is required")
        
        if errors:
            return ValidationResult.failure(errors)
        
        # Validate email
        email_result = EmailValidator.validate_email(data['to_email'])
        if not email_result.is_valid:
            return ValidationResult.failure(email_result.errors)
        
        # Validate subject
        subject_result = StringValidator.validate_subject(data['subject'])
        if not subject_result.is_valid:
            return ValidationResult.failure(subject_result.errors)
        
        # Validate body
        body_result = StringValidator.validate_text(data['body'])
        if not body_result.is_valid:
            return ValidationResult.failure(body_result.errors)
        
        return ValidationResult.success(data)
    
    @staticmethod
    def validate_campaign_request(data: Dict[str, Any]) -> ValidationResult:
        """Validate campaign send request"""
        errors = []
        
        # Validate count
        if 'count' in data:
            count_result = NumberValidator.validate_email_count(data['count'])
            if not count_result.is_valid:
                errors.extend(count_result.errors)
        
        # Validate use_ai
        if 'use_ai' in data and not isinstance(data['use_ai'], bool):
            errors.append("use_ai must be a boolean")
        
        # Validate dry_run
        if 'dry_run' in data and not isinstance(data['dry_run'], bool):
            errors.append("dry_run must be a boolean")
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success(data)


def validate_and_raise(validator: callable, *args, **kwargs) -> Any:
    """
    Validate using a validator and raise ValidationError if invalid
    
    Args:
        validator: Validator function
        *args: Arguments to pass to validator
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    result = validator(*args, **kwargs)
    
    if not result.is_valid:
        raise ValidationError('; '.join(result.errors))
    
    return result.value


def sanitize_input(data: Any, field_types: Dict[str, callable] = None) -> Dict[str, Any]:
    """
    Sanitize input data based on field types
    
    Args:
        data: Input data dictionary
        field_types: Dictionary mapping field names to sanitizer functions
        
    Returns:
        Sanitized data
    """
    if not isinstance(data, dict):
        return {}
    
    sanitized = {}
    field_types = field_types or {}
    
    for key, value in data.items():
        if value is None:
            continue
        
        sanitizer = field_types.get(key, StringValidator.sanitize_string)
        
        if isinstance(value, list):
            sanitized[key] = [sanitizer(v) for v in value]
        elif isinstance(value, dict):
            sanitized[key] = sanitize_input(value, field_types)
        else:
            sanitized[key] = sanitizer(str(value))
    
    return sanitized
