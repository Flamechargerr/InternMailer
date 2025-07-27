"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2025-01-26 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('tenant_type', sa.String(length=20), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('email_preferences', sa.JSON(), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('monthly_email_limit', sa.Integer(), nullable=True),
        sa.Column('monthly_emails_sent', sa.Integer(), nullable=True),
        sa.CheckConstraint("tenant_type IN ('academic', 'corporate')", name='check_tenant_type'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_user_tenant_active', 'users', ['tenant_type', 'is_active'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create templates table
    op.create_table('templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject_template', sa.String(length=500), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('tenant_type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.CheckConstraint("tenant_type IN ('academic', 'corporate')", name='check_template_tenant'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_template_name')
    )
    op.create_index('idx_template_tenant_category', 'templates', ['tenant_type', 'category'])
    op.create_index('idx_template_user_public', 'templates', ['user_id', 'is_public'])

    # Create campaigns table
    op.create_table('campaigns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('target_criteria', sa.JSON(), nullable=True),
        sa.Column('contact_filters', sa.JSON(), nullable=True),
        sa.Column('send_schedule', sa.DateTime(timezone=True), nullable=True),
        sa.Column('daily_send_limit', sa.Integer(), nullable=True),
        sa.Column('time_between_emails', sa.Integer(), nullable=True),
        sa.Column('enable_followups', sa.Boolean(), nullable=True),
        sa.Column('followup_delay_days', sa.Integer(), nullable=True),
        sa.Column('max_followups', sa.Integer(), nullable=True),
        sa.Column('total_contacts', sa.Integer(), nullable=True),
        sa.Column('emails_sent', sa.Integer(), nullable=True),
        sa.Column('emails_delivered', sa.Integer(), nullable=True),
        sa.Column('emails_opened', sa.Integer(), nullable=True),
        sa.Column('emails_clicked', sa.Integer(), nullable=True),
        sa.Column('replies_received', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'active', 'paused', 'completed', 'cancelled')", name='check_campaign_status'),
        sa.CheckConstraint("tenant_id IN ('academic', 'corporate')", name='check_campaign_tenant'),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_campaign_name')
    )
    op.create_index('idx_campaign_tenant_status', 'campaigns', ['tenant_id', 'status'])
    op.create_index('idx_campaign_user_tenant', 'campaigns', ['user_id', 'tenant_id'])
    op.create_index(op.f('ix_campaigns_tenant_id'), 'campaigns', ['tenant_id'], unique=False)

    # Create contacts table
    op.create_table('contacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.Column('research_areas', sa.JSON(), nullable=True),
        sa.Column('publications_count', sa.Integer(), nullable=True),
        sa.Column('h_index', sa.Float(), nullable=True),
        sa.Column('university_ranking', sa.Integer(), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_stage', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('orcid', sa.String(length=100), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=True),
        sa.Column('last_verified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_method', sa.String(length=100), nullable=True),
        sa.Column('bounce_count', sa.Integer(), nullable=True),
        sa.Column('contact_count', sa.Integer(), nullable=True),
        sa.Column('last_contacted', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_rate', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_contact_email_org', 'contacts', ['email', 'organization'])
    op.create_index('idx_contact_organization', 'contacts', ['organization'])
    op.create_index('idx_contact_research_areas', 'contacts', ['research_areas'])
    op.create_index('idx_contact_verification', 'contacts', ['email_verified', 'last_verified'])
    op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=False)

    # Create emails table
    op.create_table('emails',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=False),
        sa.Column('contact_id', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('personalization_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_id', sa.String(length=255), nullable=True),
        sa.Column('delivery_status', sa.String(length=100), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('open_count', sa.Integer(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=True),
        sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_response', sa.JSON(), nullable=True),
        sa.Column('bounce_type', sa.String(length=50), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('spam_score', sa.Float(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed', 'spam')", name='check_email_status'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_email_campaign_status', 'emails', ['campaign_id', 'status'])
    op.create_index('idx_email_contact_sent', 'emails', ['contact_id', 'sent_at'])
    op.create_index('idx_email_sent_delivered', 'emails', ['sent_at', 'delivered_at'])
    op.create_index('idx_email_status_scheduled', 'emails', ['status', 'scheduled_at'])

    # Create followups table
    op.create_table('followups',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=False),
        sa.Column('original_email_id', sa.String(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('template_id', sa.String(), nullable=True),
        sa.Column('subject_override', sa.String(length=500), nullable=True),
        sa.Column('body_override', sa.Text(), nullable=True),
        sa.Column('send_conditions', sa.JSON(), nullable=True),
        sa.Column('email_id', sa.String(), nullable=True),
        sa.Column('cancelled_reason', sa.String(length=255), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('scheduled', 'sent', 'cancelled', 'skipped')", name='check_followup_status'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.ForeignKeyConstraint(['original_email_id'], ['emails.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('original_email_id', 'sequence_number', name='uq_email_sequence')
    )
    op.create_index('idx_followup_campaign_scheduled', 'followups', ['campaign_id', 'scheduled_at'])
    op.create_index('idx_followup_status_scheduled', 'followups', ['status', 'scheduled_at'])

    # Create analytics table
    op.create_table('analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('date_period', sa.DateTime(timezone=True), nullable=False),
        sa.Column('emails_sent', sa.Integer(), nullable=True),
        sa.Column('emails_delivered', sa.Integer(), nullable=True),
        sa.Column('emails_bounced', sa.Integer(), nullable=True),
        sa.Column('emails_failed', sa.Integer(), nullable=True),
        sa.Column('emails_opened', sa.Integer(), nullable=True),
        sa.Column('unique_opens', sa.Integer(), nullable=True),
        sa.Column('emails_clicked', sa.Integer(), nullable=True),
        sa.Column('unique_clicks', sa.Integer(), nullable=True),
        sa.Column('replies_received', sa.Integer(), nullable=True),
        sa.Column('unsubscribes', sa.Integer(), nullable=True),
        sa.Column('spam_reports', sa.Integer(), nullable=True),
        sa.Column('delivery_rate', sa.Float(), nullable=True),
        sa.Column('open_rate', sa.Float(), nullable=True),
        sa.Column('click_rate', sa.Float(), nullable=True),
        sa.Column('reply_rate', sa.Float(), nullable=True),
        sa.Column('bounce_rate', sa.Float(), nullable=True),
        sa.Column('followups_sent', sa.Integer(), nullable=True),
        sa.Column('followup_open_rate', sa.Float(), nullable=True),
        sa.Column('followup_reply_rate', sa.Float(), nullable=True),
        sa.Column('average_spam_score', sa.Float(), nullable=True),
        sa.Column('average_delivery_time', sa.Float(), nullable=True),
        sa.Column('tenant_type', sa.String(length=20), nullable=False),
        sa.Column('custom_metrics', sa.JSON(), nullable=True),
        sa.CheckConstraint("tenant_type IN ('academic', 'corporate')", name='check_analytics_tenant'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'metric_type', 'date_period', name='uq_campaign_metric_period')
    )
    op.create_index('idx_analytics_campaign_period', 'analytics', ['campaign_id', 'date_period'])
    op.create_index('idx_analytics_metric_period', 'analytics', ['metric_type', 'date_period'])
    op.create_index('idx_analytics_tenant_period', 'analytics', ['tenant_type', 'date_period'])

    # Create logs table
    op.create_table('logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('logger_name', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('campaign_id', sa.String(), nullable=True),
        sa.Column('email_id', sa.String(), nullable=True),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('function', sa.String(length=100), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('memory_usage', sa.Integer(), nullable=True),
        sa.CheckConstraint("level IN ('debug', 'info', 'warning', 'error', 'critical')", name='check_log_level'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_log_campaign_created', 'logs', ['campaign_id', 'created_at'])
    op.create_index('idx_log_level_created', 'logs', ['level', 'created_at'])
    op.create_index('idx_log_logger_level', 'logs', ['logger_name', 'level'])
    op.create_index('idx_log_user_created', 'logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('logs')
    op.drop_table('analytics')
    op.drop_table('followups')
    op.drop_table('emails')
    op.drop_table('contacts')
    op.drop_table('campaigns')
    op.drop_table('templates')
    op.drop_table('users')
