"""
Email Service - Comprehensive email sending with async support.

This module provides both production email sending capabilities and mock
implementations for development and testing.
"""

import asyncio
import random
import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import BaseService, ServiceConfig, with_error_handling, ServiceError, RateLimitError


class EmailStatus(str, Enum):
    """Email sending status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    BLOCKED = "blocked"


@dataclass
class EmailRequest:
    """Email sending request."""
    recipient: str
    subject: str
    body: str
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    campaign_id: Optional[str] = None
    template_id: Optional[str] = None
    personalization_data: Optional[Dict[str, Any]] = None
    priority: int = 5  # 1-10, higher = more priority
    scheduled_at: Optional[datetime] = None


@dataclass
class EmailResult:
    """Email sending result."""
    request_id: str
    recipient: str
    status: EmailStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    provider_response: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None


class EmailService(BaseService):
    """Production email service with multiple provider support."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self._smtp_connection = None
        self._rate_limiter = None
        self._daily_count = 0
        self._daily_reset_time = time.time() + 86400
        
    async def _initialize_impl(self) -> None:
        """Initialize email service."""
        self._setup_rate_limiter()
        await self._initialize_provider()
        
    async def _cleanup_impl(self) -> None:
        """Cleanup email service resources."""
        if self._smtp_connection:
            try:
                self._smtp_connection.quit()
            except:
                pass
            self._smtp_connection = None
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Health check for email service."""
        return {
            "provider": self.config.email_provider,
            "daily_emails_sent": self._daily_count,
            "daily_limit": self.config.email_daily_limit,
            "rate_limit": self.config.email_rate_limit
        }
    
    def _setup_rate_limiter(self):
        """Setup rate limiting."""
        self._rate_limiter = {
            'tokens': self.config.email_rate_limit,
            'last_refill': time.time(),
            'max_tokens': self.config.email_rate_limit
        }
    
    async def _initialize_provider(self):
        """Initialize the email provider."""
        if self.config.email_provider == "smtp":
            await self._initialize_smtp()
        elif self.config.email_provider == "graph":
            await self._initialize_graph_api()
    
    async def _initialize_smtp(self):
        """Initialize SMTP connection."""
        smtp_config = self.config.email_config
        
        # Connection will be created on-demand
        self.smtp_config = {
            'host': smtp_config.get('host', 'smtp.gmail.com'),
            'port': smtp_config.get('port', 587),
            'username': smtp_config.get('username'),
            'password': smtp_config.get('password'),
            'use_tls': smtp_config.get('use_tls', True),
            'timeout': smtp_config.get('timeout', 30)
        }
    
    async def _initialize_graph_api(self):
        """Initialize Microsoft Graph API."""
        # Implementation for Graph API would go here
        pass
    
    def _check_rate_limit(self) -> bool:
        """Check if we can send an email based on rate limits."""
        current_time = time.time()
        
        # Reset daily counter if needed
        if current_time >= self._daily_reset_time:
            self._daily_count = 0
            self._daily_reset_time = current_time + 86400
        
        # Check daily limit
        if self._daily_count >= self.config.email_daily_limit:
            return False
        
        # Check per-minute rate limit using token bucket
        time_passed = current_time - self._rate_limiter['last_refill']
        tokens_to_add = time_passed * (self.config.email_rate_limit / 60.0)
        
        self._rate_limiter['tokens'] = min(
            self._rate_limiter['max_tokens'],
            self._rate_limiter['tokens'] + tokens_to_add
        )
        self._rate_limiter['last_refill'] = current_time
        
        if self._rate_limiter['tokens'] >= 1.0:
            self._rate_limiter['tokens'] -= 1.0
            self._daily_count += 1
            return True
        
        return False
    
    @with_error_handling
    async def send_email(self, request: EmailRequest) -> EmailResult:
        """Send a single email."""
        async with self._ensure_initialized():
            start_time = time.time()
            request_id = f"email_{int(time.time() * 1000000)}"
            
            # Check rate limits
            if not self._check_rate_limit():
                raise RateLimitError(
                    "Email rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # Validate request
            self._validate_email_request(request)
            
            try:
                # Send via configured provider
                if self.config.email_provider == "smtp":
                    result = await self._send_via_smtp(request_id, request)
                elif self.config.email_provider == "graph":
                    result = await self._send_via_graph(request_id, request)
                else:
                    raise ServiceError(
                        f"Unsupported email provider: {self.config.email_provider}",
                        error_code="UNSUPPORTED_PROVIDER"
                    )
                
                result.execution_time = time.time() - start_time
                
                self.logger.info(
                    "Email sent successfully",
                    recipient=request.recipient,
                    status=result.status.value,
                    execution_time=result.execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.logger.error(
                    "Failed to send email",
                    recipient=request.recipient,
                    error=str(e),
                    execution_time=execution_time
                )
                
                return EmailResult(
                    request_id=request_id,
                    recipient=request.recipient,
                    status=EmailStatus.FAILED,
                    error_message=str(e),
                    execution_time=execution_time
                )
    
    def _validate_email_request(self, request: EmailRequest):
        """Validate email request."""
        if not request.recipient or "@" not in request.recipient:
            raise ServiceError(
                "Invalid recipient email address",
                error_code="INVALID_RECIPIENT"
            )
        
        if not request.subject:
            raise ServiceError(
                "Email subject is required",
                error_code="MISSING_SUBJECT"
            )
        
        if not request.body:
            raise ServiceError(
                "Email body is required",
                error_code="MISSING_BODY"
            )
    
    async def _send_via_smtp(self, request_id: str, request: EmailRequest) -> EmailResult:
        """Send email via SMTP."""
        try:
            # Create email message
            msg = EmailMessage()
            msg['Subject'] = request.subject
            msg['From'] = f"{request.sender_name or 'Sender'} <{request.sender_email or self.smtp_config['username']}>"
            msg['To'] = request.recipient
            msg['Message-ID'] = f"<{request_id}@{self.smtp_config['host']}>"
            
            # Set content
            if '<html>' in request.body.lower():
                msg.set_content(request.body, subtype='html')
            else:
                msg.set_content(request.body)
            
            # Send via SMTP
            await self._send_smtp_message(msg)
            
            return EmailResult(
                request_id=request_id,
                recipient=request.recipient,
                status=EmailStatus.SENT,
                message_id=msg['Message-ID'],
                sent_at=datetime.now(timezone.utc)
            )
            
        except smtplib.SMTPRecipientsRefused as e:
            return EmailResult(
                request_id=request_id,
                recipient=request.recipient,
                status=EmailStatus.BOUNCED,
                error_message=f"Recipient refused: {str(e)}"
            )
        
        except smtplib.SMTPAuthenticationError as e:
            return EmailResult(
                request_id=request_id,
                recipient=request.recipient,
                status=EmailStatus.FAILED,
                error_message=f"Authentication failed: {str(e)}"
            )
        
        except Exception as e:
            return EmailResult(
                request_id=request_id,
                recipient=request.recipient,
                status=EmailStatus.FAILED,
                error_message=str(e)
            )
    
    async def _send_smtp_message(self, msg: EmailMessage):
        """Send SMTP message with connection management."""
        # Run SMTP operations in thread pool to avoid blocking
        def _smtp_send():
            if self.smtp_config['port'] == 465:
                # SSL connection
                server = smtplib.SMTP_SSL(
                    self.smtp_config['host'], 
                    self.smtp_config['port'], 
                    timeout=self.smtp_config['timeout']
                )
            else:
                # TLS connection
                server = smtplib.SMTP(
                    self.smtp_config['host'], 
                    self.smtp_config['port'], 
                    timeout=self.smtp_config['timeout']
                )
                if self.smtp_config['use_tls']:
                    server.starttls()
            
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
            server.quit()
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _smtp_send)
    
    async def _send_via_graph(self, request_id: str, request: EmailRequest) -> EmailResult:
        """Send email via Microsoft Graph API."""
        # Implementation would go here
        raise NotImplementedError("Graph API support not yet implemented")
    
    @with_error_handling
    async def send_bulk_emails(self, requests: List[EmailRequest]) -> List[EmailResult]:
        """Send multiple emails concurrently."""
        async with self._ensure_initialized():
            self.logger.info(f"Starting bulk email send", count=len(requests))
            
            # Create tasks for concurrent sending
            tasks = [self.send_email(request) for request in requests]
            
            # Wait for all emails to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to failed results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(EmailResult(
                        request_id=f"bulk_{i}",
                        recipient=requests[i].recipient,
                        status=EmailStatus.FAILED,
                        error_message=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            # Log summary
            success_count = sum(1 for r in processed_results if r.status == EmailStatus.SENT)
            self.logger.info(
                "Bulk email send completed",
                total=len(requests),
                successful=success_count,
                failed=len(requests) - success_count
            )
            
            return processed_results
    
    @with_error_handling
    async def get_sending_stats(self) -> Dict[str, Any]:
        """Get current sending statistics."""
        return {
            "daily_emails_sent": self._daily_count,
            "daily_limit": self.config.email_daily_limit,
            "rate_limit_per_minute": self.config.email_rate_limit,
            "tokens_available": self._rate_limiter['tokens'] if self._rate_limiter else 0,
            "provider": self.config.email_provider
        }


class MockEmailService(BaseService):
    """Mock email service for development and testing."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self._sent_emails = []
        self._daily_count = 0
        
    async def _initialize_impl(self) -> None:
        """Initialize mock email service."""
        self.logger.info("Mock email service initialized")
    
    async def _cleanup_impl(self) -> None:
        """Cleanup mock email service."""
        self._sent_emails.clear()
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Health check for mock email service."""
        return {
            "provider": "mock",
            "emails_sent": len(self._sent_emails),
            "daily_count": self._daily_count,
            "failure_rate": self.config.mock_failure_rate
        }
    
    @with_error_handling
    async def send_email(self, request: EmailRequest) -> EmailResult:
        """Mock email sending with realistic delays and occasional failures."""
        async with self._ensure_initialized():
            start_time = time.time()
            request_id = f"mock_{int(time.time() * 1000000)}"
            
            # Simulate processing delay
            delay = random.uniform(
                self.config.mock_delay_min, 
                self.config.mock_delay_max
            )
            await asyncio.sleep(delay)
            
            # Simulate failures based on configured rate
            if random.random() < self.config.mock_failure_rate:
                return EmailResult(
                    request_id=request_id,
                    recipient=request.recipient,
                    status=EmailStatus.FAILED,
                    error_message="Mock failure for testing",
                    execution_time=time.time() - start_time
                )
            
            # Simulate successful send
            result = EmailResult(
                request_id=request_id,
                recipient=request.recipient,
                status=EmailStatus.SENT,
                message_id=f"<mock_{request_id}@example.com>",
                sent_at=datetime.now(timezone.utc),
                execution_time=time.time() - start_time
            )
            
            # Store for inspection
            self._sent_emails.append({
                'request': request,
                'result': result,
                'timestamp': datetime.now(timezone.utc)
            })
            
            self._daily_count += 1
            
            self.logger.info(
                "Mock email sent",
                recipient=request.recipient,
                subject=request.subject,
                execution_time=result.execution_time
            )
            
            return result
    
    @with_error_handling
    async def send_bulk_emails(self, requests: List[EmailRequest]) -> List[EmailResult]:
        """Mock bulk email sending."""
        async with self._ensure_initialized():
            self.logger.info(f"Mock bulk email send started", count=len(requests))
            
            results = []
            for request in requests:
                result = await self.send_email(request)
                results.append(result)
                
                # Small delay between emails to simulate realistic timing
                await asyncio.sleep(0.01)
            
            return results
    
    @with_error_handling
    async def get_sending_stats(self) -> Dict[str, Any]:
        """Get mock sending statistics."""
        return {
            "provider": "mock",
            "emails_sent": len(self._sent_emails),
            "daily_count": self._daily_count,
            "failure_rate": self.config.mock_failure_rate,
            "last_sent": self._sent_emails[-1]['timestamp'].isoformat() if self._sent_emails else None
        }
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get list of sent emails for inspection (mock only)."""
        return self._sent_emails.copy()
    
    def clear_sent_emails(self):
        """Clear sent emails history (mock only)."""
        self._sent_emails.clear()
        self._daily_count = 0
