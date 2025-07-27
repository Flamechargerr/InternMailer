# InternMailer Services Layer

A comprehensive, reusable services layer that provides clean abstractions for email sending, database operations, and analytics with both production and mock implementations for local development.

## Features

- **Async-first design** with Streamlit-compatible synchronous wrappers
- **Mock adapters** for local development and testing
- **Production-ready** with proper connection pooling and resource management
- **Simple interfaces** (`send_email`, `fetch_metrics`, `list_contacts`) for easy Streamlit integration
- **Comprehensive error handling** and structured logging
- **Clean separation** between production and development concerns

## Architecture

```
services/
├── __init__.py           # Main module exports
├── base.py              # Base classes, configuration, error handling
├── email.py             # Email sending (SMTP, Graph API, Mock) 
├── database.py          # Database operations (SQLAlchemy, Mock)
├── analytics.py         # Analytics and metrics (Production, Mock)
├── factory.py           # Service factory and creation utilities
└── interfaces.py        # Simple Streamlit-compatible functions
```

## Quick Start

### 1. Basic Usage in Streamlit

```python
import streamlit as st
from services import send_email, fetch_metrics, list_contacts

# Send an email
result = send_email(
    recipient="professor@university.edu",
    subject="Research Collaboration Inquiry", 
    body="Dear Professor, I am interested in..."
)

if result['status'] == 'sent':
    st.success("Email sent successfully!")
else:
    st.error(f"Failed: {result['error_message']}")

# Get analytics metrics
metrics = fetch_metrics(time_range="30d")
st.metric("Total Sent", metrics['total_emails_sent'])
st.metric("Open Rate", f"{metrics['open_rate']:.1f}%")

# List contacts
contacts = list_contacts(limit=10, organization="MIT")
for contact in contacts:
    st.write(f"{contact['first_name']} {contact['last_name']} - {contact['email']}")
```

### 2. Advanced Configuration

```python
from services import ServiceConfig, create_services

# Configure services
config = ServiceConfig(
    environment="development",  # Uses mock services
    database_url="sqlite:///local.db",
    email_provider="smtp",
    email_config={
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password'
    }
)

# Create services
email_service, database_service, analytics_service = create_services(config)

# Use async services directly
import asyncio

async def send_bulk_emails():
    await email_service.initialize()
    
    requests = [
        EmailRequest(
            recipient="contact1@example.com",
            subject="Hello",
            body="Test message"
        ),
        EmailRequest(
            recipient="contact2@example.com", 
            subject="Hello",
            body="Test message"
        )
    ]
    
    results = await email_service.send_bulk_emails(requests)
    return results

# Run async function
results = asyncio.run(send_bulk_emails())
```

## Services Overview

### Email Service

Handles email sending with multiple provider support:

- **SMTP** (Gmail, Outlook, custom servers)
- **Microsoft Graph API** (planned)
- **Mock service** for development

Features:
- Rate limiting and daily quotas
- Retry logic with exponential backoff
- Comprehensive error handling
- Bulk sending with concurrency

### Database Service  

Manages data operations for contacts, campaigns, and other entities:

- **SQLAlchemy** integration with async support
- **Mock service** with sample data
- Query filtering and pagination
- Connection pooling

Features:
- Contact management (CRUD operations)
- Campaign tracking
- Flexible filtering and sorting
- Raw query execution (with caution)

### Analytics Service

Provides metrics collection and reporting:

- **Time-series metrics** tracking
- **Campaign performance** analysis
- **Mock service** with realistic data
- Batch processing for performance

Features:
- Real-time metric recording
- Flexible time range queries
- Campaign-specific analytics
- Background metric flushing

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///local.db
# DATABASE_URL=postgresql://user:pass@localhost/internmailer

# Email Provider  
EMAIL_PROVIDER=smtp  # smtp, graph, mock
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Development
USE_MOCKS=true
MOCK_FAILURE_RATE=0.1  # 10% failure rate for testing
```

### ServiceConfig Options

```python
config = ServiceConfig(
    # Environment
    environment="development",  # development, staging, production
    debug=True,
    use_mocks=True,  # Force mock services
    
    # Database
    database_url="sqlite:///local.db",
    database_pool_size=5,
    database_timeout=30,
    
    # Email
    email_provider="smtp",
    email_config={
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': 'user@gmail.com',
        'password': 'app-password'
    },
    email_rate_limit=60,  # emails per minute
    email_daily_limit=2000,
    
    # Analytics
    analytics_batch_size=100,
    analytics_flush_interval=300,  # seconds
    
    # Cache
    cache_enabled=True,
    cache_ttl=300,  # seconds
    
    # Mock settings
    mock_delay_min=0.1,
    mock_delay_max=0.5,
    mock_failure_rate=0.0  # 0.0 to 1.0
)
```

## Simple Interface Functions

The `interfaces.py` module provides Streamlit-compatible functions:

### `send_email(recipient, subject, body, ...)`

Send a single email with simple parameters.

```python
result = send_email(
    recipient="professor@mit.edu",
    subject="Research Inquiry",
    body="Hello Professor...",
    sender_name="John Doe",
    campaign_id="campaign_123"
)

# Returns: {'status': 'sent', 'message_id': '...', 'sent_at': '...'}
```

### `fetch_metrics(time_range="30d", campaign_id=None)`

Get analytics metrics for a time period.

```python
# Overall metrics
metrics = fetch_metrics(time_range="7d")

# Campaign-specific metrics  
campaign_metrics = fetch_metrics(campaign_id="campaign_123")

# Returns: {'total_emails_sent': 100, 'open_rate': 25.5, ...}
```

### `list_contacts(limit=None, organization=None, tags=None, ...)`

List and filter contacts.

```python
# All contacts
contacts = list_contacts(limit=50)

# Filter by organization
mit_contacts = list_contacts(organization="MIT", limit=10)

# Filter by tags
academic_contacts = list_contacts(tags=["academic", "researcher"])

# Returns: [{'id': '...', 'email': '...', 'first_name': '...', ...}]
```

### Other Functions

- `list_campaigns(limit=None, status=None, ...)` - List campaigns
- `create_contact(contact_data)` - Create new contact
- `get_time_series_data(time_range="30d")` - Get time series analytics
- `health_check()` - Check service health status

## Mock Services for Development

Mock services provide realistic behavior for local development:

### Mock Email Service

- Simulates sending delays (0.1-0.5 seconds)
- Configurable failure rate for testing
- Stores sent emails for inspection
- No actual emails sent

### Mock Database Service

- In-memory storage with sample data
- Realistic query delays
- Sample contacts and campaigns
- Supports all database operations

### Mock Analytics Service

- Pre-generated sample metrics (30 days)
- Realistic time-series data
- Sample campaign performance data
- Configurable data generation

## Error Handling

All services use structured error handling:

```python
from services.base import ServiceError, ValidationError, RateLimitError

try:
    result = send_email(recipient="invalid-email", subject="Test", body="Test")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
except ServiceError as e:
    print(f"Service error: {e.message} (code: {e.error_code})")
```

Interface functions return error information in the response:

```python
result = send_email("invalid@email", "Test", "Body")
if result['status'] == 'failed':
    print(f"Error: {result['error_message']}")
```

## Logging

Services use structured logging with contextual information:

```python
import structlog

logger = structlog.get_logger(__name__)

# Logs include service name, method, execution time, and context
# Example log output:
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "info", 
  "logger": "EmailService",
  "message": "Email sent successfully",
  "method": "EmailService.send_email",
  "recipient": "user@example.com",
  "status": "sent",
  "execution_time": 0.85
}
```

## Production Deployment

### 1. Database Setup

```bash
# PostgreSQL with async support
pip install asyncpg psycopg2-binary

# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/internmailer"
```

### 2. Email Provider Configuration

```bash
# SMTP Configuration
export EMAIL_PROVIDER=smtp
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password

# Or Microsoft Graph API (future)
export EMAIL_PROVIDER=graph
export AZURE_TENANT_ID=your-tenant-id
export AZURE_CLIENT_ID=your-client-id
export AZURE_CLIENT_SECRET=your-client-secret
```

### 3. Production Configuration

```python
config = ServiceConfig(
    environment="production",
    debug=False,
    use_mocks=False,
    database_url=os.getenv("DATABASE_URL"),
    email_provider=os.getenv("EMAIL_PROVIDER", "smtp"),
    email_config={
        'host': os.getenv('SMTP_HOST'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD')
    },
    email_rate_limit=60,
    email_daily_limit=2000
)
```

## Testing

### Unit Tests

```python
import pytest
from services import ServiceConfig, create_services

@pytest.fixture
def mock_services():
    config = ServiceConfig(use_mocks=True, mock_failure_rate=0.0)
    return create_services(config)

async def test_send_email(mock_services):
    email_service, _, _ = mock_services
    await email_service.initialize()
    
    result = await email_service.send_email(EmailRequest(
        recipient="test@example.com",
        subject="Test",
        body="Test message"
    ))
    
    assert result.status == EmailStatus.SENT
    assert result.message_id is not None
```

### Integration Tests

```python
# Test with real services (requires configuration)
@pytest.mark.integration
async def test_real_email_service():
    config = ServiceConfig(
        use_mocks=False,
        email_provider="smtp",
        email_config={...}
    )
    
    email_service, _, _ = create_services(config)
    # ... test real email sending
```

## Contributing

1. **Add new service**: Create new service class inheriting from `BaseService`
2. **Add mock implementation**: Create corresponding mock service
3. **Update factory**: Add service creation logic to `factory.py`
4. **Add interface functions**: Add convenience functions to `interfaces.py`
5. **Update exports**: Add to `__init__.py`

### Example New Service

```python
# services/notification.py
from .base import BaseService, with_error_handling

class NotificationService(BaseService):
    async def _initialize_impl(self):
        # Initialize notification service
        pass
    
    @with_error_handling  
    async def send_notification(self, message):
        # Send notification logic
        pass

class MockNotificationService(BaseService):
    # Mock implementation
    pass
```

## License

MIT License - see LICENSE file for details.
