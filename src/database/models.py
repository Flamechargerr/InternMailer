"""
Database models for the InternMailer application.

This module defines all database tables using SQLAlchemy ORM:
- Users: User accounts and authentication
- Campaigns: Email campaigns with tenant separation
- Contacts: Professor/company contact information
- Emails: Individual email records
- FollowUps: Scheduled follow-up emails
- Templates: Email templates
- Logs: System and audit logs
- Analytics: Campaign performance metrics
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, Float, JSON,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from .session import Base


class TenantType(str, Enum):
    """Tenant types for campaign separation."""
    ACADEMIC = "academic"
    CORPORATE = "corporate"


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmailStatus(str, Enum):
    """Email delivery status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"
    SPAM = "spam"


class FollowUpStatus(str, Enum):
    """Follow-up status enumeration."""
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Base model with common fields
class BaseModel(Base):
    """Base model with common fields and functionality."""
    
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Enum):
                value = value.value
            result[column.name] = value
        return result


class User(BaseModel):
    """
    User accounts and authentication.
    
    Stores user information, preferences, and authentication details.
    """
    
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # User preferences
    tenant_type = Column(String(20), nullable=False, default=TenantType.ACADEMIC.value)
    timezone = Column(String(50), default="UTC")
    email_preferences = Column(JSON, default=dict)
    
    # Profile information
    organization = Column(String(255))
    position = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    # Usage limits and quotas
    monthly_email_limit = Column(Integer, default=500)
    monthly_emails_sent = Column(Integer, default=0)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(tenant_type.in_([t.value for t in TenantType]), name="check_tenant_type"),
        Index("idx_user_tenant_active", "tenant_type", "is_active"),
    )
    
    @validates("email")
    def validate_email(self, key, email):
        """Validate email format."""
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email.lower()
    
    @validates("tenant_type")
    def validate_tenant_type(self, key, tenant_type):
        """Validate tenant type."""
        if tenant_type not in [t.value for t in TenantType]:
            raise ValueError("Invalid tenant type")
        return tenant_type


class Campaign(BaseModel):
    """
    Email campaigns with tenant separation.
    
    Represents individual email campaigns that can be either academic or corporate.
    Uses tenant_id for separation between campaign types.
    """
    
    __tablename__ = "campaigns"
    
    # Campaign identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Tenant separation
    tenant_id = Column(String(50), nullable=False, index=True)  # academic or corporate
    
    # Campaign configuration
    status = Column(String(20), nullable=False, default=CampaignStatus.DRAFT.value)
    template_id = Column(String, ForeignKey("templates.id"), nullable=False)
    
    # Targeting and filtering
    target_criteria = Column(JSON, default=dict)  # Research areas, universities, etc.
    contact_filters = Column(JSON, default=dict)  # Filtering criteria for contacts
    
    # Sending configuration
    send_schedule = Column(DateTime(timezone=True))  # When to start sending
    daily_send_limit = Column(Integer, default=50)
    time_between_emails = Column(Integer, default=300)  # seconds
    
    # Follow-up configuration
    enable_followups = Column(Boolean, default=True)
    followup_delay_days = Column(Integer, default=7)
    max_followups = Column(Integer, default=2)
    
    # Campaign statistics
    total_contacts = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_delivered = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    replies_received = Column(Integer, default=0)
    
    # User relationship
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    template = relationship("Template", back_populates="campaigns")
    emails = relationship("Email", back_populates="campaign", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="campaign", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="campaign", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in CampaignStatus]), name="check_campaign_status"),
        CheckConstraint(tenant_id.in_([t.value for t in TenantType]), name="check_campaign_tenant"),
        Index("idx_campaign_tenant_status", "tenant_id", "status"),
        Index("idx_campaign_user_tenant", "user_id", "tenant_id"),
        UniqueConstraint("user_id", "name", name="uq_user_campaign_name"),
    )


class Contact(BaseModel):
    """
    Professor/company contact information.
    
    Stores contact details for both academic and corporate outreach.
    """
    
    __tablename__ = "contacts"
    
    # Basic contact information
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    title = Column(String(255))  # Professor, Dr., Manager, etc.
    
    # Organization details
    organization = Column(String(255), nullable=False)
    department = Column(String(255))
    position = Column(String(255))
    
    # Academic-specific fields
    research_areas = Column(JSON, default=list)  # List of research areas
    publications_count = Column(Integer)
    h_index = Column(Float)
    university_ranking = Column(Integer)
    
    # Corporate-specific fields
    company_size = Column(String(50))  # startup, small, medium, large
    industry = Column(String(100))
    company_stage = Column(String(50))  # seed, series-a, etc.
    
    # Contact details and social
    phone = Column(String(50))
    website = Column(String(500))
    linkedin_url = Column(String(500))
    orcid = Column(String(100))  # Academic identifier
    
    # Verification and quality
    email_verified = Column(Boolean, default=False)
    last_verified = Column(DateTime(timezone=True))
    verification_method = Column(String(100))
    bounce_count = Column(Integer, default=0)
    
    # Outreach tracking
    contact_count = Column(Integer, default=0)  # How many times contacted
    last_contacted = Column(DateTime(timezone=True))
    response_rate = Column(Float, default=0.0)  # Historical response rate
    
    # Data source and quality
    data_source = Column(String(100))  # csrankings, scraped, manual, etc.
    confidence_score = Column(Float, default=0.0)  # Data quality score
    tags = Column(JSON, default=list)  # Custom tags
    
    # Relationships
    emails = relationship("Email", back_populates="contact")
    
    __table_args__ = (
        Index("idx_contact_email_org", "email", "organization"),
        Index("idx_contact_research_areas", "research_areas"),
        Index("idx_contact_organization", "organization"),
        Index("idx_contact_verification", "email_verified", "last_verified"),
    )
    
    @validates("email")
    def validate_email(self, key, email):
        """Validate email format."""
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email.lower()


class Template(BaseModel):
    """
    Email templates for personalization.
    
    Stores email templates with Jinja2 templating support.
    """
    
    __tablename__ = "templates"
    
    # Template identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template content
    subject_template = Column(String(500), nullable=False)
    body_template = Column(Text, nullable=False)
    
    # Template configuration
    tenant_type = Column(String(20), nullable=False)  # academic or corporate
    category = Column(String(100))  # research_inquiry, follow_up, etc.
    language = Column(String(10), default="en")
    
    # Template metadata
    variables = Column(JSON, default=list)  # Required template variables
    tags = Column(JSON, default=list)  # Template tags
    
    # Usage and performance
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Response rate
    
    # Ownership
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)  # Can other users use this template
    is_system = Column(Boolean, default=False)  # System-provided template
    
    # Relationships
    user = relationship("User", back_populates="templates")
    campaigns = relationship("Campaign", back_populates="template")
    emails = relationship("Email", back_populates="template")
    
    __table_args__ = (
        CheckConstraint(tenant_type.in_([t.value for t in TenantType]), name="check_template_tenant"),
        Index("idx_template_tenant_category", "tenant_type", "category"),
        Index("idx_template_user_public", "user_id", "is_public"),
        UniqueConstraint("user_id", "name", name="uq_user_template_name"),
    )


class Email(BaseModel):
    """
    Individual email records.
    
    Tracks each email sent in campaigns with detailed delivery and engagement metrics.
    """
    
    __tablename__ = "emails"
    
    # Email identification and relationships
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    template_id = Column(String, ForeignKey("templates.id"), nullable=False)
    
    # Email content
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    personalization_data = Column(JSON, default=dict)  # Data used for personalization
    
    # Sending information
    status = Column(String(20), nullable=False, default=EmailStatus.PENDING.value)
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    
    # Delivery tracking
    message_id = Column(String(255))  # Email provider message ID
    delivery_status = Column(String(100))
    delivered_at = Column(DateTime(timezone=True))
    
    # Engagement tracking
    opened_at = Column(DateTime(timezone=True))
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime(timezone=True))
    click_count = Column(Integer, default=0)
    replied_at = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime(timezone=True))
    
    # Email provider details
    provider = Column(String(50), default="gmail")  # gmail, sendgrid, etc.
    provider_response = Column(JSON, default=dict)
    
    # Tracking and analytics
    bounce_type = Column(String(50))  # hard, soft, complaint
    unsubscribed_at = Column(DateTime(timezone=True))
    spam_score = Column(Float)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="emails")
    contact = relationship("Contact", back_populates="emails")
    template = relationship("Template", back_populates="emails")
    followups = relationship("FollowUp", back_populates="original_email")
    
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in EmailStatus]), name="check_email_status"),
        Index("idx_email_campaign_status", "campaign_id", "status"),
        Index("idx_email_contact_sent", "contact_id", "sent_at"),
        Index("idx_email_status_scheduled", "status", "scheduled_at"),
        Index("idx_email_sent_delivered", "sent_at", "delivered_at"),
    )


class FollowUp(BaseModel):
    """
    Scheduled follow-up emails.
    
    Manages automated follow-up sequences for campaigns.
    """
    
    __tablename__ = "followups"
    
    # Follow-up identification
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    original_email_id = Column(String, ForeignKey("emails.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)  # 1st followup, 2nd, etc.
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default=FollowUpStatus.SCHEDULED.value)
    
    # Follow-up content (can be different from original)
    template_id = Column(String, ForeignKey("templates.id"))
    subject_override = Column(String(500))
    body_override = Column(Text)
    
    # Conditions for sending
    send_conditions = Column(JSON, default=dict)  # Only send if original not opened, etc.
    
    # Results
    email_id = Column(String, ForeignKey("emails.id"))  # Created email when sent
    cancelled_reason = Column(String(255))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Relationships
    campaign = relationship("Campaign", back_populates="followups")
    original_email = relationship("Email", foreign_keys=[original_email_id], back_populates="followups")
    template = relationship("Template")
    sent_email = relationship("Email", foreign_keys=[email_id])
    
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in FollowUpStatus]), name="check_followup_status"),
        Index("idx_followup_campaign_scheduled", "campaign_id", "scheduled_at"),
        Index("idx_followup_status_scheduled", "status", "scheduled_at"),
        UniqueConstraint("original_email_id", "sequence_number", name="uq_email_sequence"),
    )


class Log(BaseModel):
    """
    System and audit logs.
    
    Comprehensive logging for system events, errors, and user actions.
    """
    
    __tablename__ = "logs"
    
    # Log identification
    level = Column(String(20), nullable=False)
    logger_name = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context information
    user_id = Column(String, ForeignKey("users.id"))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    email_id = Column(String, ForeignKey("emails.id"))
    
    # Technical details
    module = Column(String(100))
    function = Column(String(100))
    line_number = Column(Integer)
    
    # Request context
    request_id = Column(String(100))
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv4 or IPv6
    
    # Additional data
    extra_data = Column(JSON, default=dict)
    stack_trace = Column(Text)
    
    # Performance metrics
    execution_time = Column(Float)  # seconds
    memory_usage = Column(Integer)  # bytes
    
    __table_args__ = (
        CheckConstraint(level.in_([l.value for l in LogLevel]), name="check_log_level"),
        Index("idx_log_level_created", "level", "created_at"),
        Index("idx_log_user_created", "user_id", "created_at"),
        Index("idx_log_campaign_created", "campaign_id", "created_at"),
        Index("idx_log_logger_level", "logger_name", "level"),
    )


class Analytics(BaseModel):
    """
    Campaign performance metrics and analytics.
    
    Stores aggregated analytics data for campaigns and overall system performance.
    """
    
    __tablename__ = "analytics"
    
    # Analytics identification
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # daily, weekly, monthly, campaign
    date_period = Column(DateTime(timezone=True), nullable=False)  # Start of period
    
    # Email metrics
    emails_sent = Column(Integer, default=0)
    emails_delivered = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)
    
    # Engagement metrics
    emails_opened = Column(Integer, default=0)
    unique_opens = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    unique_clicks = Column(Integer, default=0)
    replies_received = Column(Integer, default=0)
    
    # Unsubscribe and spam
    unsubscribes = Column(Integer, default=0)
    spam_reports = Column(Integer, default=0)
    
    # Calculated rates
    delivery_rate = Column(Float, default=0.0)  # delivered / sent
    open_rate = Column(Float, default=0.0)      # opened / delivered
    click_rate = Column(Float, default=0.0)     # clicked / delivered
    reply_rate = Column(Float, default=0.0)     # replied / delivered
    bounce_rate = Column(Float, default=0.0)    # bounced / sent
    
    # Follow-up metrics
    followups_sent = Column(Integer, default=0)
    followup_open_rate = Column(Float, default=0.0)
    followup_reply_rate = Column(Float, default=0.0)
    
    # Quality metrics
    average_spam_score = Column(Float, default=0.0)
    average_delivery_time = Column(Float, default=0.0)  # seconds
    
    # Tenant and segmentation
    tenant_type = Column(String(20), nullable=False)
    
    # Additional metrics
    custom_metrics = Column(JSON, default=dict)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")
    
    __table_args__ = (
        CheckConstraint(tenant_type.in_([t.value for t in TenantType]), name="check_analytics_tenant"),
        Index("idx_analytics_campaign_period", "campaign_id", "date_period"),
        Index("idx_analytics_tenant_period", "tenant_type", "date_period"),
        Index("idx_analytics_metric_period", "metric_type", "date_period"),
        UniqueConstraint("campaign_id", "metric_type", "date_period", name="uq_campaign_metric_period"),
    )


# Create indexes for performance optimization
def create_additional_indexes():
    """Create additional database indexes for performance optimization."""
    # This would be called after table creation to add complex indexes
    # Implementation would depend on specific query patterns
    pass
