"""Custom exceptions for the application."""

class InternMailerError(Exception):
    """Base exception."""
    pass

class EmailSendError(InternMailerError):
    """SMTP or API failure."""
    pass

class RateLimitError(InternMailerError):
    """Too many requests."""
    pass

class AuthError(InternMailerError):
    """Credential or token issue."""
    pass
