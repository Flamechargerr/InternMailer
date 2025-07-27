"""
Secure email validation module to prevent injection attacks and ensure data integrity.
"""

import re
import logging

logger = logging.getLogger(__name__)

class SecureEmailValidator:
    """Secure email validator with comprehensive security checks."""
    
    def __init__(self):
        # Comprehensive email regex pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
        )
        
        # Dangerous characters that could indicate injection attempts
        self.dangerous_chars = ['<', '>', '"', "'", ';', '(', ')', '{', '}', '[', ']', '\\', '/', '`', '|', '&']
        
        # Maximum allowed email length
        self.max_length = 254  # RFC 5321 limit
        
    def is_valid_email(self, email: str) -> bool:
        """
        Validate email address with comprehensive security checks.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email is valid and secure, False otherwise
        """
        if not isinstance(email, str):
            logger.warning(f"Invalid email type: {type(email)}")
            return False
            
        email = email.strip()
        
        # Basic checks
        if not email or len(email) == 0:
            return False
            
        # Length check
        if len(email) > self.max_length:
            logger.warning(f"Email too long: {len(email)} chars")
            return False
            
        # Check for dangerous characters (injection prevention)
        if any(char in email for char in self.dangerous_chars):
            logger.warning(f"Dangerous characters found in email: {email}")
            return False
            
        # Check for exactly one @ symbol
        if email.count('@') != 1:
            logger.warning(f"Invalid @ count in email: {email}")
            return False
            
        # Split into local and domain parts
        try:
            local_part, domain_part = email.split('@')
        except ValueError:
            return False
            
        # Local part checks
        if not local_part or len(local_part) == 0 or len(local_part) > 64:
            return False
            
        # Domain part checks
        if not domain_part or len(domain_part) == 0 or len(domain_part) > 253:
            return False
            
        # No consecutive dots
        if '..' in email:
            return False
            
        # Cannot start or end with dot
        if email.startswith('.') or email.endswith('.'):
            return False
            
        # Local part cannot start or end with dot
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
            
        # Domain must contain at least one dot
        if '.' not in domain_part:
            return False
            
        # Use regex for final validation
        if not self.email_pattern.match(email):
            logger.warning(f"Email failed regex validation: {email}")
            return False
            
        logger.debug(f"Email validated successfully: {email}")
        return True
        
    def sanitize_email(self, email: str) -> str:
        """
        Sanitize email address by removing potentially dangerous characters.
        
        Args:
            email: Email address to sanitize
            
        Returns:
            str: Sanitized email address
        """
        if not isinstance(email, str):
            return ""
            
        # Remove dangerous characters
        sanitized = email.strip()
        for char in self.dangerous_chars:
            sanitized = sanitized.replace(char, '')
            
        return sanitized

# Global validator instance
_email_validator = SecureEmailValidator()

def validate_email(email: str) -> bool:
    """Validate email using the global validator instance."""
    return _email_validator.is_valid_email(email)

def sanitize_email(email: str) -> str:
    """Sanitize email using the global validator instance."""
    return _email_validator.sanitize_email(email)
