"""Add indexes for email engine duplicate prevention

Revision ID: 002_email_engine_indexes
Revises: 001_initial_schema
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '002_email_engine_indexes'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for email engine performance and duplicate prevention."""
    
    # Index for duplicate prevention - composite index on recipient-campaign lookup
    op.create_index(
        'idx_email_recipient_campaign_dedup',
        'emails',
        ['campaign_id', 'contact_id', 'status'],
        unique=False
    )
    
    # Index for efficient email status queries
    op.create_index(
        'idx_email_status_sent_at',
        'emails',
        ['status', 'sent_at'],
        unique=False
    )
    
    # Index for retry logic - find emails that need retry
    op.create_index(
        'idx_email_retry_lookup',
        'emails',
        ['status', 'retry_count', 'last_retry_at'],
        unique=False
    )
    
    # Index for rate limiting - efficient counting by time periods
    op.create_index(
        'idx_email_sent_at_provider',
        'emails',
        ['provider', 'sent_at'],
        unique=False
    )
    
    # Index for campaign performance monitoring
    op.create_index(
        'idx_email_campaign_status_count',
        'emails',
        ['campaign_id', 'status', 'created_at'],
        unique=False
    )
    
    # Index on contact email for fast duplicate checking
    op.create_index(
        'idx_contact_email_lower',
        'contacts',
        [text('LOWER(email)')],
        unique=False
    )
    
    # Index for message ID lookups (bounce handling)
    op.create_index(
        'idx_email_message_id',
        'emails',
        ['message_id'],
        unique=False
    )
    
    # Partial index for pending emails (to optimize sending queues)
    op.execute(text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_pending_scheduled
        ON emails (scheduled_at, priority DESC, created_at)
        WHERE status = 'pending'
    """))
    
    # Partial index for failed emails that can retry
    op.execute(text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_failed_retryable
        ON emails (last_retry_at, retry_count)
        WHERE status = 'failed' AND retry_count < 3
    """))


def downgrade():
    """Remove email engine indexes."""
    
    # Drop all the indexes we created
    op.drop_index('idx_email_recipient_campaign_dedup', table_name='emails')
    op.drop_index('idx_email_status_sent_at', table_name='emails')
    op.drop_index('idx_email_retry_lookup', table_name='emails')
    op.drop_index('idx_email_sent_at_provider', table_name='emails')
    op.drop_index('idx_email_campaign_status_count', table_name='emails')
    op.drop_index('idx_contact_email_lower', table_name='contacts')
    op.drop_index('idx_email_message_id', table_name='emails')
    
    # Drop partial indexes
    op.execute(text("DROP INDEX CONCURRENTLY IF EXISTS idx_email_pending_scheduled"))
    op.execute(text("DROP INDEX CONCURRENTLY IF EXISTS idx_email_failed_retryable"))
