# InternMailer Database Design

This document describes the database architecture for the InternMailer email campaign management system.

## Overview

The database is designed to support both **Academic** and **Corporate** email campaigns with proper tenant separation, comprehensive tracking, and analytics. It uses SQLAlchemy ORM with Alembic for migrations.

## Tenant Separation Strategy

The system implements tenant separation using a **tenant_id** field approach rather than separate schemas. This provides:

- **Single Database**: All data stored in one database for simplicity
- **Logical Separation**: Academic and corporate campaigns are separated by `tenant_id` field
- **Flexible Queries**: Easy to query across tenants or filter by tenant
- **Simpler Deployment**: No schema management complexity

### Tenant Types
- `academic`: For university professor outreach campaigns
- `corporate`: For company internship/job application campaigns

## Database Schema

### Core Tables

#### 1. Users Table
Stores user accounts and authentication information.

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    tenant_type VARCHAR(20) NOT NULL DEFAULT 'academic',
    timezone VARCHAR(50) DEFAULT 'UTC',
    email_preferences JSON,
    organization VARCHAR(255),
    position VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    monthly_email_limit INTEGER DEFAULT 500,
    monthly_emails_sent INTEGER DEFAULT 0
);
```

**Key Features:**
- Multi-tenant user support
- Email quota management
- User preferences stored as JSON
- Timezone awareness

#### 2. Campaigns Table
Central table for email campaigns with tenant separation.

```sql
CREATE TABLE campaigns (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tenant_id VARCHAR(50) NOT NULL,  -- 'academic' or 'corporate'
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    template_id VARCHAR NOT NULL REFERENCES templates(id),
    target_criteria JSON,
    contact_filters JSON,
    send_schedule TIMESTAMP WITH TIME ZONE,
    daily_send_limit INTEGER DEFAULT 50,
    time_between_emails INTEGER DEFAULT 300,
    enable_followups BOOLEAN DEFAULT TRUE,
    followup_delay_days INTEGER DEFAULT 7,
    max_followups INTEGER DEFAULT 2,
    total_contacts INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    replies_received INTEGER DEFAULT 0,
    user_id VARCHAR NOT NULL REFERENCES users(id)
);
```

**Key Features:**
- Tenant separation via `tenant_id`
- Flexible targeting criteria stored as JSON
- Campaign statistics tracking
- Follow-up configuration

#### 3. Contacts Table
Stores professor and company contact information.

```sql
CREATE TABLE contacts (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(255),
    organization VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    position VARCHAR(255),
    -- Academic-specific fields
    research_areas JSON,
    publications_count INTEGER,
    h_index FLOAT,
    university_ranking INTEGER,
    -- Corporate-specific fields
    company_size VARCHAR(50),
    industry VARCHAR(100),
    company_stage VARCHAR(50),
    -- Contact verification
    email_verified BOOLEAN DEFAULT FALSE,
    last_verified TIMESTAMP WITH TIME ZONE,
    verification_method VARCHAR(100),
    bounce_count INTEGER DEFAULT 0,
    -- Outreach tracking
    contact_count INTEGER DEFAULT 0,
    last_contacted TIMESTAMP WITH TIME ZONE,
    response_rate FLOAT DEFAULT 0.0,
    -- Data quality
    data_source VARCHAR(100),
    confidence_score FLOAT DEFAULT 0.0,
    tags JSON
);
```

**Key Features:**
- Unified contact storage for both academic and corporate
- Rich metadata for targeting
- Email verification tracking
- Historical performance metrics

#### 4. Templates Table
Email templates with Jinja2 support.

```sql
CREATE TABLE templates (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject_template VARCHAR(500) NOT NULL,
    body_template TEXT NOT NULL,
    tenant_type VARCHAR(20) NOT NULL,
    category VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    variables JSON,
    tags JSON,
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    is_public BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE
);
```

**Key Features:**
- Tenant-specific templates
- Jinja2 template variables tracking
- Public/private template sharing
- Performance metrics

#### 5. Emails Table
Individual email records with detailed tracking.

```sql
CREATE TABLE emails (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_id VARCHAR NOT NULL REFERENCES campaigns(id),
    contact_id VARCHAR NOT NULL REFERENCES contacts(id),
    template_id VARCHAR NOT NULL REFERENCES templates(id),
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    personalization_data JSON,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    message_id VARCHAR(255),
    delivery_status VARCHAR(100),
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    open_count INTEGER DEFAULT 0,
    clicked_at TIMESTAMP WITH TIME ZONE,
    click_count INTEGER DEFAULT 0,
    replied_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    provider VARCHAR(50) DEFAULT 'gmail',
    provider_response JSON,
    bounce_type VARCHAR(50),
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    spam_score FLOAT
);
```

**Key Features:**
- Complete email lifecycle tracking
- Engagement metrics (opens, clicks, replies)
- Error handling and retry logic
- Provider-specific data storage

#### 6. FollowUps Table
Automated follow-up email management.

```sql
CREATE TABLE followups (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_id VARCHAR NOT NULL REFERENCES campaigns(id),
    original_email_id VARCHAR NOT NULL REFERENCES emails(id),
    sequence_number INTEGER NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    template_id VARCHAR REFERENCES templates(id),
    subject_override VARCHAR(500),
    body_override TEXT,
    send_conditions JSON,
    email_id VARCHAR REFERENCES emails(id),
    cancelled_reason VARCHAR(255),
    cancelled_at TIMESTAMP WITH TIME ZONE
);
```

**Key Features:**
- Automated follow-up sequences
- Conditional sending logic
- Override capabilities for customization

#### 7. Analytics Table
Campaign performance metrics and reporting.

```sql
CREATE TABLE analytics (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_id VARCHAR NOT NULL REFERENCES campaigns(id),
    metric_type VARCHAR(50) NOT NULL,
    date_period TIMESTAMP WITH TIME ZONE NOT NULL,
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    emails_failed INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    unique_opens INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    replies_received INTEGER DEFAULT 0,
    unsubscribes INTEGER DEFAULT 0,
    spam_reports INTEGER DEFAULT 0,
    delivery_rate FLOAT DEFAULT 0.0,
    open_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    reply_rate FLOAT DEFAULT 0.0,
    bounce_rate FLOAT DEFAULT 0.0,
    followups_sent INTEGER DEFAULT 0,
    followup_open_rate FLOAT DEFAULT 0.0,
    followup_reply_rate FLOAT DEFAULT 0.0,
    average_spam_score FLOAT DEFAULT 0.0,
    average_delivery_time FLOAT DEFAULT 0.0,
    tenant_type VARCHAR(20) NOT NULL,
    custom_metrics JSON
);
```

**Key Features:**
- Time-series analytics data
- Calculated performance rates
- Tenant-specific metrics
- Custom metrics support

#### 8. Logs Table
Comprehensive system and audit logging.

```sql
CREATE TABLE logs (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    level VARCHAR(20) NOT NULL,
    logger_name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    user_id VARCHAR REFERENCES users(id),
    campaign_id VARCHAR REFERENCES campaigns(id),
    email_id VARCHAR REFERENCES emails(id),
    module VARCHAR(100),
    function VARCHAR(100),
    line_number INTEGER,
    request_id VARCHAR(100),
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    extra_data JSON,
    stack_trace TEXT,
    execution_time FLOAT,
    memory_usage INTEGER
);
```

**Key Features:**
- Structured logging with context
- Performance monitoring
- Audit trail for all operations
- Error tracking and debugging

## Indexes and Performance

### Primary Indexes
- All tables have UUID primary keys for scalability
- Unique constraints on email addresses and usernames
- Foreign key indexes for referential integrity

### Performance Indexes
```sql
-- User indexes
CREATE INDEX idx_user_tenant_active ON users(tenant_type, is_active);

-- Campaign indexes
CREATE INDEX idx_campaign_tenant_status ON campaigns(tenant_id, status);
CREATE INDEX idx_campaign_user_tenant ON campaigns(user_id, tenant_id);

-- Contact indexes
CREATE INDEX idx_contact_email_org ON contacts(email, organization);
CREATE INDEX idx_contact_research_areas ON contacts(research_areas);
CREATE INDEX idx_contact_verification ON contacts(email_verified, last_verified);

-- Email indexes
CREATE INDEX idx_email_campaign_status ON emails(campaign_id, status);
CREATE INDEX idx_email_contact_sent ON emails(contact_id, sent_at);
CREATE INDEX idx_email_status_scheduled ON emails(status, scheduled_at);

-- Analytics indexes
CREATE INDEX idx_analytics_campaign_period ON analytics(campaign_id, date_period);
CREATE INDEX idx_analytics_tenant_period ON analytics(tenant_type, date_period);

-- Log indexes
CREATE INDEX idx_log_level_created ON logs(level, created_at);
CREATE INDEX idx_log_user_created ON logs(user_id, created_at);
```

## Data Relationships

```
Users (1) ──→ (∞) Campaigns
Users (1) ──→ (∞) Templates
Campaigns (1) ──→ (∞) Emails
Campaigns (1) ──→ (∞) FollowUps
Campaigns (1) ──→ (∞) Analytics
Templates (1) ──→ (∞) Emails
Contacts (1) ──→ (∞) Emails
Emails (1) ──→ (∞) FollowUps
```

## Usage Examples

### Creating a Campaign
```python
from database import get_session
from database.models import Campaign, TenantType, CampaignStatus

with get_session() as session:
    campaign = Campaign(
        name="MIT CS Professors Outreach",
        tenant_id=TenantType.ACADEMIC.value,
        status=CampaignStatus.DRAFT.value,
        template_id="template_id_here",
        target_criteria={
            "universities": ["MIT"],
            "research_areas": ["Machine Learning", "AI"],
            "min_h_index": 20
        },
        user_id="user_id_here"
    )
    session.add(campaign)
```

### Querying by Tenant
```python
# Get all academic campaigns
academic_campaigns = session.query(Campaign).filter(
    Campaign.tenant_id == TenantType.ACADEMIC.value
).all()

# Get corporate campaigns for a user
corporate_campaigns = session.query(Campaign).filter(
    Campaign.tenant_id == TenantType.CORPORATE.value,
    Campaign.user_id == user_id
).all()
```

### Analytics Query
```python
# Get campaign performance metrics
analytics = session.query(Analytics).filter(
    Analytics.campaign_id == campaign_id,
    Analytics.metric_type == "daily",
    Analytics.date_period >= start_date,
    Analytics.date_period <= end_date
).all()
```

## Migration Management

### Using the Database Manager
```bash
# Initialize database
python -m database.management init

# Seed with initial data
python -m database.management seed

# Create test user
python -m database.management test-user --tenant-type academic

# Show statistics
python -m database.management stats

# Reset database (WARNING: destroys all data)
python -m database.management reset
```

### Creating Migrations
1. Modify models in `database/models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review and edit the generated migration file
4. Apply migration: `alembic upgrade head`

## Security Considerations

1. **Password Hashing**: User passwords are hashed using bcrypt
2. **SQL Injection Prevention**: SQLAlchemy ORM protects against SQL injection
3. **Data Validation**: Model validators ensure data integrity
4. **Audit Logging**: All operations are logged for security auditing
5. **Tenant Isolation**: Proper tenant separation prevents data leakage

## Performance Tuning

1. **Connection Pooling**: Configured for optimal connection reuse
2. **Indexing Strategy**: Comprehensive indexes for query performance
3. **JSON Fields**: Used for flexible schema without performance penalty
4. **Partitioning**: Large tables can be partitioned by tenant or date
5. **Caching**: Application-level caching for frequently accessed data

## Backup and Recovery

1. **Regular Backups**: Automated daily backups recommended
2. **Point-in-Time Recovery**: Transaction log backups for PostgreSQL
3. **Data Export**: SQLAlchemy models support easy data export/import
4. **Migration Rollback**: Alembic supports rollback to previous versions

## Environment Configuration

Database configuration is managed through environment variables:

```bash
# Database type
DB_TYPE=sqlite  # or postgresql

# PostgreSQL settings (if using PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=internmailer
DB_USER=username
DB_PASSWORD=password

# SQLAlchemy settings
DB_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Schema settings
DB_USE_SCHEMAS=true
DB_ACADEMIC_SCHEMA=academic
DB_CORPORATE_SCHEMA=corporate
```

This database design provides a robust foundation for the InternMailer application with proper tenant separation, comprehensive tracking, and scalability for future growth.
