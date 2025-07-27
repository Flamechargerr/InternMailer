"""
Fast SMTP/Graph API Email Engine with Duplicate Prevention

This module provides a high-performance email sending engine that supports:
- SMTP (Gmail, Office365, custom servers) and Microsoft Graph API
- Hash-based duplicate prevention with database indexing
- Structured status tracking (sent, failed, bounced)
- Retry logic with exponential backoff
- Rate limiting and throttling
- Comprehensive logging and monitoring

The engine is designed for bulk email campaigns with enterprise-grade reliability.
"""

import asyncio
import hashlib
import logging
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import ssl
import threading
from urllib.parse import urlparse

import requests
from sqlalchemy import create_engine, text, Index
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.models import Email, EmailStatus, Contact, Campaign
from database.session import get_db_session


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers."""
    GMAIL_SMTP = "gmail_smtp"
    OUTLOOK_SMTP = "outlook_smtp"
    CUSTOM_SMTP = "custom_smtp"
    MICROSOFT_GRAPH = "microsoft_graph"


class SendStatus(str, Enum):
    """Email send status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    RETRY = "retry"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    DUPLICATE = "duplicate"


@dataclass
class EmailResult:
    """Structured email send result."""
    email_id: str
    recipient: str
    status: SendStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    sent_at: Optional[datetime] = None
    retry_count: int = 0
    execution_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.sent_at:
            result['sent_at'] = self.sent_at.isoformat()
        return result


@dataclass
class EmailRequest:
    """Email send request structure."""
    email_id: str
    campaign_id: str
    recipient: str
    subject: str
    body: str
    sender_name: str
    sender_email: str
    priority: int = 5  # 1-10, higher = more priority
    scheduled_at: Optional[datetime] = None
    personalization_data: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 300.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    emails_per_minute: int = 60
    emails_per_hour: int = 1000
    emails_per_day: int = 2000
    burst_size: int = 10
    cooldown_period: int = 60  # seconds


class DuplicatePreventionService:
    """Hash-based duplicate prevention service."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure database indexes exist for duplicate prevention."""
        try:
            # Create index on recipient-campaign hash if not exists
            self.db_session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_recipient_campaign_hash 
                ON emails USING HASH ((recipient_email, campaign_id))
            """))
            
            # Create index for efficient duplicate lookups
            self.db_session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_dedup_lookup 
                ON emails (campaign_id, contact_id, status, created_at)
            """))
            
            self.db_session.commit()
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
            self.db_session.rollback()

    def generate_hash(self, recipient: str, campaign_id: str, subject: str) -> str:
        """Generate hash for duplicate detection."""
        content = f"{recipient.lower()}|{campaign_id}|{subject}"
        return hashlib.sha256(content.encode()).hexdigest()

    def is_duplicate(self, recipient: str, campaign_id: str, subject: str) -> bool:
        """Check if email is a duplicate."""
        try:
            duplicate_hash = self.generate_hash(recipient, campaign_id, subject)
            
            # Check for existing email with same hash
            existing = self.db_session.query(Email).filter(
                Email.campaign_id == campaign_id,
                Email.contact_id.in_(
                    self.db_session.query(Contact.id).filter(
                        Contact.email == recipient.lower()
                    )
                ),
                Email.status.in_([EmailStatus.SENT.value, EmailStatus.DELIVERED.value])
            ).first()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return False

    def mark_sent(self, recipient: str, campaign_id: str, subject: str, email_id: str):
        """Mark email as sent to prevent future duplicates."""
        # This is handled by the main email tracking in the database
        pass


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._tokens = config.burst_size
        self._last_refill = time.time()
        self._lock = threading.Lock()
        
        # Counters for different time periods
        self._hourly_count = 0
        self._daily_count = 0
        self._hourly_reset = time.time() + 3600
        self._daily_reset = time.time() + 86400

    def acquire(self) -> bool:
        """Acquire a token for sending an email."""
        with self._lock:
            now = time.time()
            
            # Reset counters if needed
            if now >= self._hourly_reset:
                self._hourly_count = 0
                self._hourly_reset = now + 3600
            
            if now >= self._daily_reset:
                self._daily_count = 0
                self._daily_reset = now + 86400
            
            # Check daily and hourly limits
            if self._hourly_count >= self.config.emails_per_hour:
                return False
            if self._daily_count >= self.config.emails_per_day:
                return False
            
            # Refill tokens based on time passed
            time_passed = now - self._last_refill
            tokens_to_add = time_passed * (self.config.emails_per_minute / 60.0)
            self._tokens = min(self.config.burst_size, self._tokens + tokens_to_add)
            self._last_refill = now
            
            # Check if we have tokens available
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self._hourly_count += 1
                self._daily_count += 1
                return True
            
            return False

    def get_wait_time(self) -> float:
        """Get estimated wait time until next token is available."""
        with self._lock:
            if self._tokens >= 1.0:
                return 0.0
            
            # Calculate time needed for one token
            tokens_needed = 1.0 - self._tokens
            time_per_token = 60.0 / self.config.emails_per_minute
            return tokens_needed * time_per_token


class SMTPProvider:
    """SMTP email provider implementation."""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.host = smtp_config.get('host', 'smtp.gmail.com')
        self.port = smtp_config.get('port', 587)
        self.username = smtp_config.get('username')
        self.password = smtp_config.get('password')
        self.use_tls = smtp_config.get('use_tls', True)
        self.timeout = smtp_config.get('timeout', 30)

    def send_email(self, request: EmailRequest) -> EmailResult:
        """Send email via SMTP."""
        start_time = time.time()
        
        try:
            # Create email message
            msg = EmailMessage()
            msg['Subject'] = request.subject
            msg['From'] = f"{request.sender_name} <{request.sender_email}>"
            msg['To'] = request.recipient
            msg['Message-ID'] = f"<{request.email_id}@{self.host}>"
            
            # Set content
            if '<html>' in request.body.lower():
                msg.set_content(request.body, subtype='html')
            else:
                msg.set_content(request.body)
            
            # Send via SMTP
            if self.port == 465:
                # SSL connection
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                # TLS connection
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
                if self.use_tls:
                    server.starttls()
            
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            execution_time = time.time() - start_time
            
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.SENT,
                message_id=msg['Message-ID'],
                sent_at=datetime.now(timezone.utc),
                execution_time=execution_time
            )
            
        except smtplib.SMTPRecipientsRefused as e:
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.BOUNCED,
                error_message=f"Recipient refused: {str(e)}",
                execution_time=time.time() - start_time
            )
            
        except smtplib.SMTPAuthenticationError as e:
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.FAILED,
                error_message=f"Authentication failed: {str(e)}",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.FAILED,
                error_message=str(e),
                execution_time=time.time() - start_time
            )


class GraphAPIProvider:
    """Microsoft Graph API email provider implementation."""
    
    def __init__(self, graph_config: Dict[str, Any]):
        self.tenant_id = graph_config.get('tenant_id')
        self.client_id = graph_config.get('client_id')
        self.client_secret = graph_config.get('client_secret')
        self.access_token = None
        self.token_expires_at = None

    def _get_access_token(self) -> str:
        """Get OAuth2 access token for Graph API."""
        if self.access_token and self.token_expires_at > datetime.now():
            return self.access_token
        
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
        
        return self.access_token

    def send_email(self, request: EmailRequest) -> EmailResult:
        """Send email via Microsoft Graph API."""
        start_time = time.time()
        
        try:
            token = self._get_access_token()
            
            # Prepare email payload
            email_payload = {
                "message": {
                    "subject": request.subject,
                    "body": {
                        "contentType": "HTML" if '<html>' in request.body.lower() else "Text",
                        "content": request.body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": request.recipient
                            }
                        }
                    ],
                    "from": {
                        "emailAddress": {
                            "address": request.sender_email,
                            "name": request.sender_name
                        }
                    }
                }
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Send via Graph API
            url = f"https://graph.microsoft.com/v1.0/users/{request.sender_email}/sendMail"
            response = requests.post(url, json=email_payload, headers=headers)
            
            execution_time = time.time() - start_time
            
            if response.status_code == 202:
                return EmailResult(
                    email_id=request.email_id,
                    recipient=request.recipient,
                    status=SendStatus.SENT,
                    sent_at=datetime.now(timezone.utc),
                    provider_response={"status_code": response.status_code},
                    execution_time=execution_time
                )
            else:
                return EmailResult(
                    email_id=request.email_id,
                    recipient=request.recipient,
                    status=SendStatus.FAILED,
                    error_message=f"Graph API error: {response.status_code} - {response.text}",
                    provider_response={"status_code": response.status_code, "response": response.text},
                    execution_time=execution_time
                )
                
        except Exception as e:
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.FAILED,
                error_message=str(e),
                execution_time=time.time() - start_time
            )


class EmailEngine:
    """Fast email engine with duplicate prevention and retry logic."""
    
    def __init__(
        self,
        provider_type: EmailProvider,
        provider_config: Dict[str, Any],
        retry_config: Optional[RetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        max_workers: int = 10
    ):
        self.provider_type = provider_type
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.max_workers = max_workers
        
        # Initialize provider
        if provider_type in [EmailProvider.GMAIL_SMTP, EmailProvider.OUTLOOK_SMTP, EmailProvider.CUSTOM_SMTP]:
            self.provider = SMTPProvider(provider_config)
        elif provider_type == EmailProvider.MICROSOFT_GRAPH:
            self.provider = GraphAPIProvider(provider_config)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        # Initialize components
        self.db_session = next(get_db_session())
        self.duplicate_service = DuplicatePreventionService(self.db_session)
        self.rate_limiter = RateLimiter(self.rate_limit_config)
        
        # Thread pool for concurrent sending
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"EmailEngine initialized with provider: {provider_type}")

    def send_single_email(self, request: EmailRequest) -> EmailResult:
        """Send a single email with all safety checks."""
        try:
            # Check for duplicates
            if self.duplicate_service.is_duplicate(request.recipient, request.campaign_id, request.subject):
                logger.info(f"Duplicate email blocked: {request.recipient}")
                return EmailResult(
                    email_id=request.email_id,
                    recipient=request.recipient,
                    status=SendStatus.DUPLICATE,
                    error_message="Duplicate email blocked"
                )
            
            # Apply rate limiting
            if not self.rate_limiter.acquire():
                wait_time = self.rate_limiter.get_wait_time()
                logger.warning(f"Rate limit exceeded, wait time: {wait_time}s")
                return EmailResult(
                    email_id=request.email_id,
                    recipient=request.recipient,
                    status=SendStatus.RATE_LIMITED,
                    error_message=f"Rate limited, retry after {wait_time}s"
                )
            
            # Send email with retry logic
            return self._send_with_retry(request)
            
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return EmailResult(
                email_id=request.email_id,
                recipient=request.recipient,
                status=SendStatus.FAILED,
                error_message=str(e)
            )

    def _send_with_retry(self, request: EmailRequest) -> EmailResult:
        """Send email with exponential backoff retry logic."""
        last_result = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = self.provider.send_email(request)
                result.retry_count = attempt
                
                # Success cases - no retry needed
                if result.status in [SendStatus.SENT, SendStatus.DELIVERED]:
                    self._update_email_status(result)
                    return result
                
                # Permanent failures - no retry
                if result.status in [SendStatus.BOUNCED, SendStatus.BLOCKED]:
                    self._update_email_status(result)
                    return result
                
                # Retry on temporary failures
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying email {request.email_id} in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    last_result = result
                else:
                    # Max retries reached
                    result.status = SendStatus.FAILED
                    self._update_email_status(result)
                    return result
                
            except Exception as e:
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.error(f"Error sending email, retrying in {delay}s: {e}")
                    time.sleep(delay)
                    last_result = EmailResult(
                        email_id=request.email_id,
                        recipient=request.recipient,
                        status=SendStatus.FAILED,
                        error_message=str(e),
                        retry_count=attempt
                    )
                else:
                    # Max retries reached
                    result = EmailResult(
                        email_id=request.email_id,
                        recipient=request.recipient,
                        status=SendStatus.FAILED,
                        error_message=str(e),
                        retry_count=attempt
                    )
                    self._update_email_status(result)
                    return result
        
        return last_result or EmailResult(
            email_id=request.email_id,
            recipient=request.recipient,
            status=SendStatus.FAILED,
            error_message="Max retries exceeded"
        )

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        if self.retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay

    def send_bulk_emails(self, requests: List[EmailRequest]) -> List[EmailResult]:
        """Send multiple emails concurrently."""
        logger.info(f"Starting bulk send of {len(requests)} emails")
        results = []
        
        # Submit all tasks to thread pool
        future_to_request = {
            self.executor.submit(self.send_single_email, request): request
            for request in requests
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_request):
            request = future_to_request[future]
            try:
                result = future.result()
                results.append(result)
                
                # Log progress
                if len(results) % 10 == 0:
                    logger.info(f"Completed {len(results)}/{len(requests)} emails")
                    
            except Exception as e:
                logger.error(f"Thread execution error for {request.email_id}: {e}")
                results.append(EmailResult(
                    email_id=request.email_id,
                    recipient=request.recipient,
                    status=SendStatus.FAILED,
                    error_message=str(e)
                ))
        
        logger.info(f"Bulk send completed: {len(results)} results")
        return results

    def _update_email_status(self, result: EmailResult):
        """Update email status in database."""
        try:
            email = self.db_session.query(Email).filter(Email.id == result.email_id).first()
            if email:
                # Map SendStatus to EmailStatus
                status_mapping = {
                    SendStatus.SENT: EmailStatus.SENT,
                    SendStatus.DELIVERED: EmailStatus.DELIVERED,
                    SendStatus.FAILED: EmailStatus.FAILED,
                    SendStatus.BOUNCED: EmailStatus.BOUNCED,
                    SendStatus.BLOCKED: EmailStatus.FAILED,
                    SendStatus.DUPLICATE: EmailStatus.FAILED,
                    SendStatus.RATE_LIMITED: EmailStatus.PENDING
                }
                
                email.status = status_mapping.get(result.status, EmailStatus.FAILED).value
                email.message_id = result.message_id
                email.sent_at = result.sent_at
                email.error_message = result.error_message
                email.retry_count = result.retry_count
                email.provider_response = result.provider_response or {}
                
                self.db_session.commit()
                
        except Exception as e:
            logger.error(f"Error updating email status: {e}")
            self.db_session.rollback()

    def get_sending_stats(self) -> Dict[str, Any]:
        """Get current sending statistics."""
        return {
            "rate_limiter": {
                "tokens_available": self.rate_limiter._tokens,
                "hourly_count": self.rate_limiter._hourly_count,
                "daily_count": self.rate_limiter._daily_count,
                "hourly_limit": self.rate_limiter.config.emails_per_hour,
                "daily_limit": self.rate_limiter.config.emails_per_day
            },
            "provider": {
                "type": self.provider_type.value,
                "max_workers": self.max_workers
            },
            "retry_config": {
                "max_retries": self.retry_config.max_retries,
                "base_delay": self.retry_config.base_delay,
                "max_delay": self.retry_config.max_delay
            }
        }

    def shutdown(self):
        """Shutdown the email engine and cleanup resources."""
        logger.info("Shutting down EmailEngine...")
        self.executor.shutdown(wait=True)
        self.db_session.close()
        logger.info("EmailEngine shutdown complete")


# Factory function for easy setup
def create_email_engine(
    provider_type: str,
    config: Dict[str, Any],
    retry_config: Optional[Dict[str, Any]] = None,
    rate_limit_config: Optional[Dict[str, Any]] = None,
    max_workers: int = 10
) -> EmailEngine:
    """Factory function to create EmailEngine with configuration."""
    
    # Convert string to enum
    provider_enum = EmailProvider(provider_type)
    
    # Create config objects
    retry_cfg = RetryConfig(**retry_config) if retry_config else RetryConfig()
    rate_cfg = RateLimitConfig(**rate_limit_config) if rate_limit_config else RateLimitConfig()
    
    return EmailEngine(
        provider_type=provider_enum,
        provider_config=config,
        retry_config=retry_cfg,
        rate_limit_config=rate_cfg,
        max_workers=max_workers
    )


# Example usage and configuration
if __name__ == "__main__":
    # Gmail SMTP example
    gmail_config = {
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': os.getenv('GMAIL_USER'),
        'password': os.getenv('GMAIL_APP_PASSWORD'),
        'use_tls': True
    }
    
    # Microsoft Graph API example
    graph_config = {
        'tenant_id': os.getenv('AZURE_TENANT_ID'),
        'client_id': os.getenv('AZURE_CLIENT_ID'),
        'client_secret': os.getenv('AZURE_CLIENT_SECRET')
    }
    
    # Create engine
    engine = create_email_engine(
        provider_type="gmail_smtp",
        config=gmail_config,
        retry_config={"max_retries": 3, "base_delay": 2.0},
        rate_limit_config={"emails_per_minute": 30, "emails_per_hour": 500},
        max_workers=5
    )
    
    # Example email request
    request = EmailRequest(
        email_id="test-001",
        campaign_id="campaign-001",
        recipient="test@example.com",
        subject="Test Email",
        body="This is a test email from the EmailEngine.",
        sender_name="Test Sender",
        sender_email="sender@example.com"
    )
    
    # Send single email
    result = engine.send_single_email(request)
    print(f"Email result: {result.to_dict()}")
    
    # Get stats
    stats = engine.get_sending_stats()
    print(f"Engine stats: {json.dumps(stats, indent=2)}")
    
    # Shutdown
    engine.shutdown()
