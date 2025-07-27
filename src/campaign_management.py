"""
Campaign Management Core - CRUD APIs, Bulk Operations, and State Management

This module provides comprehensive campaign management functionality including:
- CRUD operations for campaigns
- Bulk operations (send now, schedule, cancel)
- Campaign state machine with history logging
- Campaign cloning and template management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from uuid import uuid4
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.session import get_session
from database.models import (
    Campaign, CampaignStatus, User, Template, Contact, Email, 
    EmailStatus, FollowUp, Log, LogLevel, Analytics
)


class CampaignState(str, Enum):
    """Campaign state enumeration for state machine."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BulkOperationType(str, Enum):
    """Bulk operation types."""
    SEND_NOW = "send_now"
    SCHEDULE = "schedule"
    CANCEL = "cancel"
    PAUSE = "pause"
    RESUME = "resume"


@dataclass
class CampaignStateTransition:
    """Represents a campaign state transition."""
    from_state: CampaignState
    to_state: CampaignState
    action: str
    timestamp: datetime
    user_id: str
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BulkOperationResult:
    """Result of a bulk operation."""
    success_count: int
    failure_count: int
    total_count: int
    errors: List[Dict[str, str]]
    operation_id: str
    completed_at: datetime


class CampaignStateMachine:
    """Manages campaign state transitions and validation."""
    
    # Define valid state transitions
    VALID_TRANSITIONS = {
        CampaignState.DRAFT: [CampaignState.SCHEDULED, CampaignState.ACTIVE, CampaignState.CANCELLED],
        CampaignState.SCHEDULED: [CampaignState.ACTIVE, CampaignState.CANCELLED, CampaignState.PAUSED],
        CampaignState.ACTIVE: [CampaignState.PAUSED, CampaignState.COMPLETED, CampaignState.CANCELLED, CampaignState.FAILED],
        CampaignState.PAUSED: [CampaignState.ACTIVE, CampaignState.CANCELLED],
        CampaignState.COMPLETED: [],  # Terminal state
        CampaignState.CANCELLED: [],  # Terminal state
        CampaignState.FAILED: [CampaignState.DRAFT, CampaignState.SCHEDULED, CampaignState.CANCELLED]
    }
    
    @classmethod
    def can_transition(cls, from_state: CampaignState, to_state: CampaignState) -> bool:
        """Check if a state transition is valid."""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, [])
    
    @classmethod
    def get_valid_transitions(cls, from_state: CampaignState) -> List[CampaignState]:
        """Get all valid transitions from a given state."""
        return cls.VALID_TRANSITIONS.get(from_state, [])


class CampaignHistoryLogger:
    """Logs campaign state changes and operations."""
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    def log_state_transition(self, campaign_id: str, transition: CampaignStateTransition):
        """Log a campaign state transition."""
        log_entry = Log(
            level=LogLevel.INFO.value,
            logger_name="campaign_manager",
            message=f"Campaign {campaign_id} transitioned from {transition.from_state.value} to {transition.to_state.value}",
            campaign_id=campaign_id,
            user_id=transition.user_id,
            extra_data={
                "action": transition.action,
                "from_state": transition.from_state.value,
                "to_state": transition.to_state.value,
                "reason": transition.reason,
                "metadata": transition.metadata or {}
            }
        )
        self.session.add(log_entry)
    
    def log_bulk_operation(self, operation_type: BulkOperationType, result: BulkOperationResult, user_id: str):
        """Log a bulk operation."""
        log_entry = Log(
            level=LogLevel.INFO.value,
            logger_name="campaign_manager",
            message=f"Bulk operation {operation_type.value} completed: {result.success_count}/{result.total_count} successful",
            user_id=user_id,
            extra_data={
                "operation_type": operation_type.value,
                "operation_id": result.operation_id,
                "success_count": result.success_count,
                "failure_count": result.failure_count,
                "total_count": result.total_count,
                "errors": result.errors
            }
        )
        self.session.add(log_entry)
    
    def log_campaign_operation(self, campaign_id: str, operation: str, user_id: str, details: Dict[str, Any]):
        """Log a general campaign operation."""
        log_entry = Log(
            level=LogLevel.INFO.value,
            logger_name="campaign_manager",
            message=f"Campaign {campaign_id}: {operation}",
            campaign_id=campaign_id,
            user_id=user_id,
            extra_data=details
        )
        self.session.add(log_entry)


class CampaignManager:
    """Main campaign management class with CRUD operations and state management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state_machine = CampaignStateMachine()
    
    # CRUD Operations
    
    def create_campaign(self, user_id: str, campaign_data: Dict[str, Any]) -> Campaign:
        """Create a new campaign."""
        with get_session() as session:
            try:
                # Validate required fields
                required_fields = ['name', 'tenant_id', 'template_id']
                for field in required_fields:
                    if field not in campaign_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Validate template exists and belongs to user
                template = session.query(Template).filter(
                    Template.id == campaign_data['template_id'],
                    or_(Template.user_id == user_id, Template.is_public == True)
                ).first()
                
                if not template:
                    raise ValueError("Template not found or not accessible")
                
                # Create campaign
                campaign = Campaign(
                    name=campaign_data['name'],
                    description=campaign_data.get('description', ''),
                    tenant_id=campaign_data['tenant_id'],
                    status=CampaignStatus.DRAFT.value,
                    template_id=campaign_data['template_id'],
                    target_criteria=campaign_data.get('target_criteria', {}),
                    contact_filters=campaign_data.get('contact_filters', {}),
                    send_schedule=campaign_data.get('send_schedule'),
                    daily_send_limit=campaign_data.get('daily_send_limit', 50),
                    time_between_emails=campaign_data.get('time_between_emails', 300),
                    enable_followups=campaign_data.get('enable_followups', True),
                    followup_delay_days=campaign_data.get('followup_delay_days', 7),
                    max_followups=campaign_data.get('max_followups', 2),
                    user_id=user_id
                )
                
                session.add(campaign)
                session.flush()  # Get the campaign ID
                
                # Log creation
                history_logger = CampaignHistoryLogger(session)
                history_logger.log_campaign_operation(
                    campaign.id, "created", user_id,
                    {"template_id": campaign_data['template_id'], "tenant_id": campaign_data['tenant_id']}
                )
                
                session.commit()
                return campaign
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error creating campaign: {e}")
                raise
    
    def get_campaign(self, campaign_id: str, user_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        with get_session() as session:
            return session.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
    
    def get_campaigns(self, user_id: str, filters: Optional[Dict[str, Any]] = None, 
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get campaigns with optional filtering and pagination."""
        with get_session() as session:
            query = session.query(Campaign).filter(Campaign.user_id == user_id)
            
            # Apply filters
            if filters:
                if 'status' in filters:
                    query = query.filter(Campaign.status == filters['status'])
                if 'tenant_id' in filters:
                    query = query.filter(Campaign.tenant_id == filters['tenant_id'])
                if 'name_contains' in filters:
                    query = query.filter(Campaign.name.contains(filters['name_contains']))
                if 'created_after' in filters:
                    query = query.filter(Campaign.created_at >= filters['created_after'])
                if 'created_before' in filters:
                    query = query.filter(Campaign.created_at <= filters['created_before'])
            
            # Count total
            total_count = query.count()
            
            # Apply pagination and ordering
            campaigns = query.order_by(desc(Campaign.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            return {
                'campaigns': campaigns,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
    
    def update_campaign(self, campaign_id: str, user_id: str, updates: Dict[str, Any]) -> Campaign:
        """Update a campaign."""
        with get_session() as session:
            try:
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found")
                
                # Check if campaign can be updated based on current state
                current_state = CampaignState(campaign.status)
                if current_state in [CampaignState.COMPLETED, CampaignState.CANCELLED]:
                    raise ValueError("Cannot update completed or cancelled campaigns")
                
                # Update allowed fields
                updatable_fields = [
                    'name', 'description', 'target_criteria', 'contact_filters',
                    'send_schedule', 'daily_send_limit', 'time_between_emails',
                    'enable_followups', 'followup_delay_days', 'max_followups'
                ]
                
                updated_fields = []
                for field in updatable_fields:
                    if field in updates:
                        old_value = getattr(campaign, field)
                        setattr(campaign, field, updates[field])
                        updated_fields.append(f"{field}: {old_value} -> {updates[field]}")
                
                # Log update
                history_logger = CampaignHistoryLogger(session)
                history_logger.log_campaign_operation(
                    campaign_id, "updated", user_id,
                    {"updated_fields": updated_fields}
                )
                
                session.commit()
                return campaign
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error updating campaign {campaign_id}: {e}")
                raise
    
    def delete_campaign(self, campaign_id: str, user_id: str) -> bool:
        """Delete a campaign (soft delete by setting status to cancelled)."""
        with get_session() as session:
            try:
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found")
                
                # Check if campaign can be deleted
                current_state = CampaignState(campaign.status)
                if current_state == CampaignState.ACTIVE:
                    raise ValueError("Cannot delete active campaigns. Pause or cancel first.")
                
                # Transition to cancelled state
                self._transition_campaign_state(
                    session, campaign, CampaignState.CANCELLED, user_id, "deleted"
                )
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error deleting campaign {campaign_id}: {e}")
                raise
    
    def clone_campaign(self, campaign_id: str, user_id: str, new_name: str, 
                      modifications: Optional[Dict[str, Any]] = None) -> Campaign:
        """Clone an existing campaign with optional modifications."""
        with get_session() as session:
            try:
                # Get original campaign
                original = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not original:
                    raise ValueError("Original campaign not found")
                
                # Create clone data
                clone_data = {
                    'name': new_name,
                    'description': f"Clone of: {original.description or original.name}",
                    'tenant_id': original.tenant_id,
                    'template_id': original.template_id,
                    'target_criteria': original.target_criteria.copy() if original.target_criteria else {},
                    'contact_filters': original.contact_filters.copy() if original.contact_filters else {},
                    'send_schedule': None,  # Reset schedule for cloned campaign
                    'daily_send_limit': original.daily_send_limit,
                    'time_between_emails': original.time_between_emails,
                    'enable_followups': original.enable_followups,
                    'followup_delay_days': original.followup_delay_days,
                    'max_followups': original.max_followups
                }
                
                # Apply modifications if provided
                if modifications:
                    clone_data.update(modifications)
                
                # Create the cloned campaign
                cloned_campaign = self.create_campaign(user_id, clone_data)
                
                # Log cloning operation
                history_logger = CampaignHistoryLogger(session)
                history_logger.log_campaign_operation(
                    cloned_campaign.id, "cloned", user_id,
                    {"original_campaign_id": campaign_id, "modifications": modifications or {}}
                )
                
                return cloned_campaign
                
            except Exception as e:
                self.logger.error(f"Error cloning campaign {campaign_id}: {e}")
                raise
    
    # State Management
    
    def _transition_campaign_state(self, session: Session, campaign: Campaign, 
                                 new_state: CampaignState, user_id: str, 
                                 action: str, reason: Optional[str] = None):
        """Internal method to transition campaign state."""
        current_state = CampaignState(campaign.status)
        
        # Validate transition
        if not self.state_machine.can_transition(current_state, new_state):
            raise ValueError(f"Invalid state transition from {current_state.value} to {new_state.value}")
        
        # Update campaign status
        old_status = campaign.status
        campaign.status = new_state.value
        
        # Log transition
        transition = CampaignStateTransition(
            from_state=current_state,
            to_state=new_state,
            action=action,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            reason=reason
        )
        
        history_logger = CampaignHistoryLogger(session)
        history_logger.log_state_transition(campaign.id, transition)
        
        self.logger.info(f"Campaign {campaign.id} transitioned from {old_status} to {new_state.value}")
    
    def start_campaign(self, campaign_id: str, user_id: str, send_immediately: bool = False) -> Campaign:
        """Start a campaign (transition to active state)."""
        with get_session() as session:
            try:
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found")
                
                current_state = CampaignState(campaign.status)
                
                if send_immediately:
                    # Set schedule to now if sending immediately
                    campaign.send_schedule = datetime.now(timezone.utc)
                    new_state = CampaignState.ACTIVE
                    action = "started_immediately"
                else:
                    # Check if campaign has a schedule
                    if not campaign.send_schedule:
                        raise ValueError("Campaign must have a send schedule or be started immediately")
                    
                    if campaign.send_schedule <= datetime.now(timezone.utc):
                        new_state = CampaignState.ACTIVE
                        action = "started"
                    else:
                        new_state = CampaignState.SCHEDULED
                        action = "scheduled"
                
                self._transition_campaign_state(session, campaign, new_state, user_id, action)
                
                session.commit()
                return campaign
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error starting campaign {campaign_id}: {e}")
                raise
    
    def pause_campaign(self, campaign_id: str, user_id: str, reason: Optional[str] = None) -> Campaign:
        """Pause an active campaign."""
        with get_session() as session:
            try:
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found")
                
                self._transition_campaign_state(
                    session, campaign, CampaignState.PAUSED, user_id, "paused", reason
                )
                
                session.commit()
                return campaign
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error pausing campaign {campaign_id}: {e}")
                raise
    
    def resume_campaign(self, campaign_id: str, user_id: str) -> Campaign:
        """Resume a paused campaign."""
        with get_session() as session:
            try:
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found")
                
                self._transition_campaign_state(
                    session, campaign, CampaignState.ACTIVE, user_id, "resumed"
                )
                
                session.commit()
                return campaign
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error resuming campaign {campaign_id}: {e}")
                raise
    
    def cancel_campaign(self, campaign_id: str, user_id: str, reason: Optional[str] = None) -> Campaign:
        """Cancel a campaign."""
        with get_session() as session:
            try:
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found")
                
                self._transition_campaign_state(
                    session, campaign, CampaignState.CANCELLED, user_id, "cancelled", reason
                )
                
                # Cancel any pending emails
                pending_emails = session.query(Email).filter(
                    Email.campaign_id == campaign_id,
                    Email.status == EmailStatus.PENDING.value
                ).all()
                
                for email in pending_emails:
                    email.status = EmailStatus.FAILED.value
                    email.error_message = "Campaign cancelled"
                
                # Cancel any scheduled follow-ups
                from database.models import FollowUpStatus
                scheduled_followups = session.query(FollowUp).filter(
                    FollowUp.campaign_id == campaign_id,
                    FollowUp.status == FollowUpStatus.SCHEDULED.value
                ).all()
                
                for followup in scheduled_followups:
                    followup.status = FollowUpStatus.CANCELLED.value
                    followup.cancelled_reason = "Campaign cancelled"
                    followup.cancelled_at = datetime.now(timezone.utc)
                
                session.commit()
                return campaign
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error cancelling campaign {campaign_id}: {e}")
                raise
    
    # Bulk Operations
    
    def bulk_send_now(self, campaign_ids: List[str], user_id: str) -> BulkOperationResult:
        """Send multiple campaigns immediately."""
        return self._perform_bulk_operation(
            campaign_ids, user_id, BulkOperationType.SEND_NOW,
            lambda campaign, session: self.start_campaign(campaign.id, user_id, send_immediately=True)
        )
    
    def bulk_schedule(self, campaign_ids: List[str], user_id: str, 
                     schedule_time: datetime) -> BulkOperationResult:
        """Schedule multiple campaigns."""
        def schedule_operation(campaign, session):
            campaign.send_schedule = schedule_time
            self._transition_campaign_state(
                session, campaign, CampaignState.SCHEDULED, user_id, "bulk_scheduled"
            )
            return campaign
        
        return self._perform_bulk_operation(
            campaign_ids, user_id, BulkOperationType.SCHEDULE, schedule_operation
        )
    
    def bulk_cancel(self, campaign_ids: List[str], user_id: str, 
                   reason: Optional[str] = None) -> BulkOperationResult:
        """Cancel multiple campaigns."""
        def cancel_operation(campaign, session):
            return self.cancel_campaign(campaign.id, user_id, reason)
        
        return self._perform_bulk_operation(
            campaign_ids, user_id, BulkOperationType.CANCEL, cancel_operation
        )
    
    def bulk_pause(self, campaign_ids: List[str], user_id: str, 
                  reason: Optional[str] = None) -> BulkOperationResult:
        """Pause multiple campaigns."""
        def pause_operation(campaign, session):
            return self.pause_campaign(campaign.id, user_id, reason)
        
        return self._perform_bulk_operation(
            campaign_ids, user_id, BulkOperationType.PAUSE, pause_operation
        )
    
    def bulk_resume(self, campaign_ids: List[str], user_id: str) -> BulkOperationResult:
        """Resume multiple campaigns."""
        def resume_operation(campaign, session):
            return self.resume_campaign(campaign.id, user_id)
        
        return self._perform_bulk_operation(
            campaign_ids, user_id, BulkOperationType.RESUME, resume_operation
        )
    
    def _perform_bulk_operation(self, campaign_ids: List[str], user_id: str,
                              operation_type: BulkOperationType,
                              operation_func) -> BulkOperationResult:
        """Perform a bulk operation on multiple campaigns."""
        operation_id = str(uuid4())
        success_count = 0
        failure_count = 0
        errors = []
        
        with get_session() as session:
            try:
                # Get campaigns
                campaigns = session.query(Campaign).filter(
                    Campaign.id.in_(campaign_ids),
                    Campaign.user_id == user_id
                ).all()
                
                campaign_dict = {c.id: c for c in campaigns}
                
                # Process each campaign
                for campaign_id in campaign_ids:
                    try:
                        if campaign_id not in campaign_dict:
                            errors.append({
                                "campaign_id": campaign_id,
                                "error": "Campaign not found"
                            })
                            failure_count += 1
                            continue
                        
                        campaign = campaign_dict[campaign_id]
                        operation_func(campaign, session)
                        success_count += 1
                        
                    except Exception as e:
                        errors.append({
                            "campaign_id": campaign_id,
                            "error": str(e)
                        })
                        failure_count += 1
                        self.logger.error(f"Bulk operation failed for campaign {campaign_id}: {e}")
                
                # Create result
                result = BulkOperationResult(
                    success_count=success_count,
                    failure_count=failure_count,
                    total_count=len(campaign_ids),
                    errors=errors,
                    operation_id=operation_id,
                    completed_at=datetime.now(timezone.utc)
                )
                
                # Log bulk operation
                history_logger = CampaignHistoryLogger(session)
                history_logger.log_bulk_operation(operation_type, result, user_id)
                
                session.commit()
                return result
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error in bulk operation {operation_type.value}: {e}")
                raise
    
    # Analytics and History
    
    def get_campaign_history(self, campaign_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get campaign history and state transitions."""
        with get_session() as session:
            # Verify campaign belongs to user
            campaign = session.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                raise ValueError("Campaign not found")
            
            # Get logs for this campaign
            logs = session.query(Log).filter(
                Log.campaign_id == campaign_id
            ).order_by(desc(Log.created_at)).all()
            
            history = []
            for log in logs:
                history.append({
                    "timestamp": log.created_at,
                    "level": log.level,
                    "message": log.message,
                    "user_id": log.user_id,
                    "extra_data": log.extra_data or {}
                })
            
            return history
    
    def get_campaign_analytics(self, campaign_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a campaign."""
        with get_session() as session:
            # Verify campaign belongs to user
            campaign = session.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                raise ValueError("Campaign not found")
            
            # Get analytics data
            analytics = session.query(Analytics).filter(
                Analytics.campaign_id == campaign_id
            ).order_by(desc(Analytics.date_period)).all()
            
            # Get email statistics
            email_stats = session.query(Email).filter(
                Email.campaign_id == campaign_id
            ).all()
            
            # Calculate current statistics
            total_emails = len(email_stats)
            sent_emails = len([e for e in email_stats if e.status in [EmailStatus.SENT.value, EmailStatus.DELIVERED.value, EmailStatus.OPENED.value, EmailStatus.CLICKED.value, EmailStatus.REPLIED.value]])
            delivered_emails = len([e for e in email_stats if e.status in [EmailStatus.DELIVERED.value, EmailStatus.OPENED.value, EmailStatus.CLICKED.value, EmailStatus.REPLIED.value]])
            opened_emails = len([e for e in email_stats if e.status in [EmailStatus.OPENED.value, EmailStatus.CLICKED.value, EmailStatus.REPLIED.value]])
            clicked_emails = len([e for e in email_stats if e.status in [EmailStatus.CLICKED.value, EmailStatus.REPLIED.value]])
            replied_emails = len([e for e in email_stats if e.status == EmailStatus.REPLIED.value])
            bounced_emails = len([e for e in email_stats if e.status == EmailStatus.BOUNCED.value])
            failed_emails = len([e for e in email_stats if e.status == EmailStatus.FAILED.value])
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "current_status": campaign.status,
                "created_at": campaign.created_at,
                "statistics": {
                    "total_emails": total_emails,
                    "sent_emails": sent_emails,
                    "delivered_emails": delivered_emails,
                    "opened_emails": opened_emails,
                    "clicked_emails": clicked_emails,
                    "replied_emails": replied_emails,
                    "bounced_emails": bounced_emails,
                    "failed_emails": failed_emails,
                    "delivery_rate": delivered_emails / sent_emails if sent_emails > 0 else 0,
                    "open_rate": opened_emails / delivered_emails if delivered_emails > 0 else 0,
                    "click_rate": clicked_emails / delivered_emails if delivered_emails > 0 else 0,
                    "reply_rate": replied_emails / delivered_emails if delivered_emails > 0 else 0,
                    "bounce_rate": bounced_emails / sent_emails if sent_emails > 0 else 0
                },
                "historical_analytics": [
                    {
                        "date_period": a.date_period,
                        "metric_type": a.metric_type,
                        "emails_sent": a.emails_sent,
                        "emails_delivered": a.emails_delivered,
                        "emails_opened": a.emails_opened,
                        "emails_clicked": a.emails_clicked,
                        "replies_received": a.replies_received,
                        "delivery_rate": a.delivery_rate,
                        "open_rate": a.open_rate,
                        "click_rate": a.click_rate,
                        "reply_rate": a.reply_rate
                    } for a in analytics
                ]
            }
