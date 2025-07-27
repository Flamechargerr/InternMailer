"""
Advanced Follow-up Scheduler for InternMailer.

This module provides comprehensive follow-up scheduling capabilities including:
- Per-campaign interval configuration
- Dynamic template selection
- Conditional follow-up logic
- Integration with existing campaign system
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from uuid import uuid4
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from database.session import get_session
from database.models import (
    Campaign, Email, EmailStatus, FollowUp, FollowUpStatus, 
    Template, Contact, User, Log, LogLevel
)
from scheduler.celery_app import celery_app


class FollowUpCondition(str, Enum):
    """Conditions for sending follow-ups."""
    ALWAYS = "always"                    # Always send follow-up
    IF_NOT_OPENED = "if_not_opened"     # Only if original email not opened
    IF_NOT_CLICKED = "if_not_clicked"   # Only if original email not clicked
    IF_NOT_REPLIED = "if_not_replied"   # Only if original email not replied
    IF_NO_ENGAGEMENT = "if_no_engagement"  # No opens, clicks, or replies
    CUSTOM = "custom"                    # Custom condition logic


class FollowUpTrigger(str, Enum):
    """Triggers for follow-up scheduling."""
    TIME_BASED = "time_based"           # Based on time interval
    ENGAGEMENT_BASED = "engagement_based"  # Based on email engagement
    MIXED = "mixed"                     # Both time and engagement


@dataclass
class FollowUpRule:
    """Configuration for a follow-up rule."""
    sequence_number: int
    delay_days: int
    delay_hours: int = 0
    condition: FollowUpCondition = FollowUpCondition.IF_NOT_REPLIED
    template_id: Optional[str] = None  # If None, uses campaign template
    subject_override: Optional[str] = None
    enabled: bool = True
    max_attempts: int = 1
    priority: int = 0  # Higher priority = sent first
    tags: List[str] = None
    custom_condition: Optional[Dict[str, Any]] = None


@dataclass
class CampaignFollowUpConfig:
    """Follow-up configuration for a campaign."""
    campaign_id: str
    enabled: bool = True
    rules: List[FollowUpRule] = None
    global_conditions: Dict[str, Any] = None
    timezone: str = "UTC"
    business_hours_only: bool = False
    business_hours_start: int = 9  # 9 AM
    business_hours_end: int = 17   # 5 PM
    weekdays_only: bool = False
    exclude_dates: List[str] = None  # ISO date strings to exclude
    rate_limit_per_hour: int = 100
    rate_limit_per_day: int = 1000


class FollowUpScheduler:
    """Advanced follow-up scheduler with campaign integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_followup_config(self, campaign_id: str, user_id: str, 
                              config: CampaignFollowUpConfig) -> bool:
        """Create or update follow-up configuration for a campaign."""
        with get_session() as session:
            try:
                # Verify campaign belongs to user
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found or not accessible")
                
                # Update campaign follow-up settings
                campaign.enable_followups = config.enabled
                
                # Store detailed configuration in campaign metadata
                if not hasattr(campaign, 'metadata') or not campaign.metadata:
                    campaign.metadata = {}
                
                campaign.metadata['followup_config'] = {
                    'enabled': config.enabled,
                    'rules': [self._rule_to_dict(rule) for rule in (config.rules or [])],
                    'global_conditions': config.global_conditions or {},
                    'timezone': config.timezone,
                    'business_hours_only': config.business_hours_only,
                    'business_hours_start': config.business_hours_start,
                    'business_hours_end': config.business_hours_end,
                    'weekdays_only': config.weekdays_only,
                    'exclude_dates': config.exclude_dates or [],
                    'rate_limit_per_hour': config.rate_limit_per_hour,
                    'rate_limit_per_day': config.rate_limit_per_day
                }
                
                # Log configuration change
                self._log_operation(
                    session, campaign_id, user_id, "followup_config_updated",
                    {"rules_count": len(config.rules or []), "enabled": config.enabled}
                )
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error creating follow-up config for campaign {campaign_id}: {e}")
                raise
    
    def schedule_followups_for_email(self, original_email_id: str) -> List[str]:
        """Schedule follow-ups for a specific email."""
        with get_session() as session:
            try:
                # Get the original email and campaign
                email = session.query(Email).filter(
                    Email.id == original_email_id
                ).first()
                
                if not email:
                    raise ValueError("Original email not found")
                
                campaign = session.query(Campaign).filter(
                    Campaign.id == email.campaign_id
                ).first()
                
                if not campaign or not campaign.enable_followups:
                    self.logger.info(f"Follow-ups disabled for campaign {email.campaign_id}")
                    return []
                
                # Get follow-up configuration
                config = self._get_campaign_followup_config(campaign)
                if not config.enabled:
                    return []
                
                followup_ids = []
                base_time = email.sent_at or datetime.now(timezone.utc)
                
                # Create follow-ups based on rules
                for rule in sorted(config.rules or [], key=lambda r: r.sequence_number):
                    if not rule.enabled:
                        continue
                    
                    # Calculate schedule time
                    schedule_time = self._calculate_schedule_time(
                        base_time, rule, config
                    )
                    
                    # Determine template to use
                    template_id = rule.template_id or campaign.template_id
                    
                    # Create follow-up record
                    followup = FollowUp(
                        campaign_id=campaign.id,
                        original_email_id=original_email_id,
                        sequence_number=rule.sequence_number,
                        scheduled_at=schedule_time,
                        status=FollowUpStatus.SCHEDULED.value,
                        template_id=template_id,
                        subject_override=rule.subject_override,
                        send_conditions={
                            'condition': rule.condition.value,
                            'custom_condition': rule.custom_condition,
                            'max_attempts': rule.max_attempts,
                            'priority': rule.priority,
                            'tags': rule.tags or []
                        }
                    )
                    
                    session.add(followup)
                    session.flush()  # Get the followup ID
                    followup_ids.append(followup.id)
                    
                    # Schedule Celery task
                    self._schedule_celery_task(followup.id, schedule_time)
                
                # Log follow-up scheduling
                self._log_operation(
                    session, campaign.id, campaign.user_id, "followups_scheduled",
                    {
                        "original_email_id": original_email_id,
                        "followup_count": len(followup_ids),
                        "followup_ids": followup_ids
                    }
                )
                
                session.commit()
                return followup_ids
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error scheduling follow-ups for email {original_email_id}: {e}")
                raise
    
    def reschedule_followup(self, followup_id: str, new_schedule_time: datetime, 
                           user_id: str, reason: Optional[str] = None) -> bool:
        """Reschedule a specific follow-up."""
        with get_session() as session:
            try:
                followup = session.query(FollowUp).filter(
                    FollowUp.id == followup_id
                ).first()
                
                if not followup:
                    raise ValueError("Follow-up not found")
                
                # Verify user has permission to modify this follow-up
                campaign = session.query(Campaign).filter(
                    Campaign.id == followup.campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Not authorized to modify this follow-up")
                
                # Can only reschedule if not yet sent
                if followup.status != FollowUpStatus.SCHEDULED.value:
                    raise ValueError("Can only reschedule pending follow-ups")
                
                old_time = followup.scheduled_at
                followup.scheduled_at = new_schedule_time
                
                # Cancel old Celery task and schedule new one
                self._cancel_celery_task(followup_id)
                self._schedule_celery_task(followup_id, new_schedule_time)
                
                # Log rescheduling
                self._log_operation(
                    session, campaign.id, user_id, "followup_rescheduled",
                    {
                        "followup_id": followup_id,
                        "old_time": old_time.isoformat(),
                        "new_time": new_schedule_time.isoformat(),
                        "reason": reason
                    }
                )
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error rescheduling follow-up {followup_id}: {e}")
                raise
    
    def cancel_followup(self, followup_id: str, user_id: str, 
                       reason: Optional[str] = None) -> bool:
        """Cancel a scheduled follow-up."""
        with get_session() as session:
            try:
                followup = session.query(FollowUp).filter(
                    FollowUp.id == followup_id
                ).first()
                
                if not followup:
                    raise ValueError("Follow-up not found")
                
                # Verify user has permission
                campaign = session.query(Campaign).filter(
                    Campaign.id == followup.campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Not authorized to cancel this follow-up")
                
                # Can only cancel if not yet sent
                if followup.status not in [FollowUpStatus.SCHEDULED.value]:
                    raise ValueError("Can only cancel pending follow-ups")
                
                # Update status
                followup.status = FollowUpStatus.CANCELLED.value
                followup.cancelled_reason = reason
                followup.cancelled_at = datetime.now(timezone.utc)
                
                # Cancel Celery task
                self._cancel_celery_task(followup_id)
                
                # Log cancellation
                self._log_operation(
                    session, campaign.id, user_id, "followup_cancelled",
                    {
                        "followup_id": followup_id,
                        "sequence_number": followup.sequence_number,
                        "reason": reason
                    }
                )
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error cancelling follow-up {followup_id}: {e}")
                raise
    
    def cancel_campaign_followups(self, campaign_id: str, user_id: str, 
                                 reason: Optional[str] = None) -> int:
        """Cancel all pending follow-ups for a campaign."""
        with get_session() as session:
            try:
                # Verify user has permission
                campaign = session.query(Campaign).filter(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                ).first()
                
                if not campaign:
                    raise ValueError("Campaign not found or not accessible")
                
                # Get all pending follow-ups
                pending_followups = session.query(FollowUp).filter(
                    FollowUp.campaign_id == campaign_id,
                    FollowUp.status == FollowUpStatus.SCHEDULED.value
                ).all()
                
                cancelled_count = 0
                for followup in pending_followups:
                    followup.status = FollowUpStatus.CANCELLED.value
                    followup.cancelled_reason = reason
                    followup.cancelled_at = datetime.now(timezone.utc)
                    
                    # Cancel Celery task
                    self._cancel_celery_task(followup.id)
                    cancelled_count += 1
                
                # Log bulk cancellation
                self._log_operation(
                    session, campaign_id, user_id, "bulk_followups_cancelled",
                    {
                        "cancelled_count": cancelled_count,
                        "reason": reason
                    }
                )
                
                session.commit()
                return cancelled_count
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"Error cancelling follow-ups for campaign {campaign_id}: {e}")
                raise
    
    def get_campaign_followups(self, campaign_id: str, user_id: str, 
                              status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all follow-ups for a campaign."""
        with get_session() as session:
            # Verify user has permission
            campaign = session.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                raise ValueError("Campaign not found or not accessible")
            
            query = session.query(FollowUp).filter(
                FollowUp.campaign_id == campaign_id
            )
            
            if status_filter:
                query = query.filter(FollowUp.status == status_filter)
            
            followups = query.order_by(
                FollowUp.sequence_number.asc(),
                FollowUp.scheduled_at.asc()
            ).all()
            
            result = []
            for followup in followups:
                # Get original email info
                original_email = session.query(Email).filter(
                    Email.id == followup.original_email_id
                ).first()
                
                result.append({
                    'id': followup.id,
                    'sequence_number': followup.sequence_number,
                    'scheduled_at': followup.scheduled_at,
                    'sent_at': followup.sent_at,
                    'status': followup.status,
                    'template_id': followup.template_id,
                    'subject_override': followup.subject_override,
                    'send_conditions': followup.send_conditions,
                    'cancelled_reason': followup.cancelled_reason,
                    'cancelled_at': followup.cancelled_at,
                    'original_email_id': followup.original_email_id,
                    'original_email_status': original_email.status if original_email else None,
                    'original_email_sent_at': original_email.sent_at if original_email else None
                })
            
            return result
    
    def get_followup_analytics(self, campaign_id: str, user_id: str) -> Dict[str, Any]:
        """Get analytics for campaign follow-ups."""
        with get_session() as session:
            # Verify user has permission
            campaign = session.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            ).first()
            
            if not campaign:
                raise ValueError("Campaign not found or not accessible")
            
            # Get follow-up statistics
            total_followups = session.query(func.count(FollowUp.id)).filter(
                FollowUp.campaign_id == campaign_id
            ).scalar()
            
            sent_followups = session.query(func.count(FollowUp.id)).filter(
                FollowUp.campaign_id == campaign_id,
                FollowUp.status == FollowUpStatus.SENT.value
            ).scalar()
            
            scheduled_followups = session.query(func.count(FollowUp.id)).filter(
                FollowUp.campaign_id == campaign_id,
                FollowUp.status == FollowUpStatus.SCHEDULED.value
            ).scalar()
            
            cancelled_followups = session.query(func.count(FollowUp.id)).filter(
                FollowUp.campaign_id == campaign_id,
                FollowUp.status == FollowUpStatus.CANCELLED.value
            ).scalar()
            
            # Get performance by sequence
            sequence_stats = session.query(
                FollowUp.sequence_number,
                func.count(FollowUp.id).label('total'),
                func.count(FollowUp.sent_at).label('sent')
            ).filter(
                FollowUp.campaign_id == campaign_id
            ).group_by(FollowUp.sequence_number).all()
            
            return {
                'campaign_id': campaign_id,
                'total_followups': total_followups,
                'sent_followups': sent_followups,
                'scheduled_followups': scheduled_followups,
                'cancelled_followups': cancelled_followups,
                'send_rate': sent_followups / total_followups if total_followups > 0 else 0,
                'sequence_performance': [
                    {
                        'sequence_number': stat.sequence_number,
                        'total': stat.total,
                        'sent': stat.sent,
                        'send_rate': stat.sent / stat.total if stat.total > 0 else 0
                    }
                    for stat in sequence_stats
                ]
            }
    
    # Private helper methods
    
    def _get_campaign_followup_config(self, campaign: Campaign) -> CampaignFollowUpConfig:
        """Get follow-up configuration from campaign metadata."""
        if not hasattr(campaign, 'metadata') or not campaign.metadata:
            # Return default configuration
            return CampaignFollowUpConfig(
                campaign_id=campaign.id,
                enabled=campaign.enable_followups,
                rules=[
                    FollowUpRule(
                        sequence_number=1,
                        delay_days=campaign.followup_delay_days or 7,
                        condition=FollowUpCondition.IF_NOT_REPLIED
                    )
                ] if campaign.enable_followups else []
            )
        
        config_data = campaign.metadata.get('followup_config', {})
        rules = [self._dict_to_rule(rule_data) for rule_data in config_data.get('rules', [])]
        
        return CampaignFollowUpConfig(
            campaign_id=campaign.id,
            enabled=config_data.get('enabled', campaign.enable_followups),
            rules=rules,
            global_conditions=config_data.get('global_conditions', {}),
            timezone=config_data.get('timezone', 'UTC'),
            business_hours_only=config_data.get('business_hours_only', False),
            business_hours_start=config_data.get('business_hours_start', 9),
            business_hours_end=config_data.get('business_hours_end', 17),
            weekdays_only=config_data.get('weekdays_only', False),
            exclude_dates=config_data.get('exclude_dates', []),
            rate_limit_per_hour=config_data.get('rate_limit_per_hour', 100),
            rate_limit_per_day=config_data.get('rate_limit_per_day', 1000)
        )
    
    def _calculate_schedule_time(self, base_time: datetime, rule: FollowUpRule, 
                               config: CampaignFollowUpConfig) -> datetime:
        """Calculate when to schedule a follow-up."""
        # Add delay
        schedule_time = base_time + timedelta(
            days=rule.delay_days,
            hours=rule.delay_hours
        )
        
        # Adjust for business hours if required
        if config.business_hours_only:
            schedule_time = self._adjust_for_business_hours(
                schedule_time, config
            )
        
        # Adjust for weekdays only
        if config.weekdays_only:
            while schedule_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                schedule_time += timedelta(days=1)
        
        # Skip excluded dates
        date_str = schedule_time.date().isoformat()
        if config.exclude_dates and date_str in config.exclude_dates:
            schedule_time += timedelta(days=1)
            # Recursively check again in case the next day is also excluded
            return self._calculate_schedule_time(
                schedule_time - timedelta(days=rule.delay_days, hours=rule.delay_hours),
                rule, config
            )
        
        return schedule_time
    
    def _adjust_for_business_hours(self, schedule_time: datetime, 
                                 config: CampaignFollowUpConfig) -> datetime:
        """Adjust schedule time to fall within business hours."""
        hour = schedule_time.hour
        
        if hour < config.business_hours_start:
            # Too early, move to start of business hours
            schedule_time = schedule_time.replace(
                hour=config.business_hours_start,
                minute=0,
                second=0,
                microsecond=0
            )
        elif hour >= config.business_hours_end:
            # Too late, move to next business day
            schedule_time = schedule_time.replace(
                hour=config.business_hours_start,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=1)
        
        return schedule_time
    
    def _schedule_celery_task(self, followup_id: str, schedule_time: datetime):
        """Schedule a Celery task for sending follow-up."""
        from scheduler.followup_tasks import send_followup_email
        
        # Schedule the task
        send_followup_email.apply_async(
            args=[followup_id],
            eta=schedule_time,
            task_id=f"followup_{followup_id}"
        )
        
        self.logger.info(f"Scheduled follow-up {followup_id} for {schedule_time}")
    
    def _cancel_celery_task(self, followup_id: str):
        """Cancel a scheduled Celery task."""
        task_id = f"followup_{followup_id}"
        celery_app.control.revoke(task_id, terminate=True)
        self.logger.info(f"Cancelled Celery task for follow-up {followup_id}")
    
    def _rule_to_dict(self, rule: FollowUpRule) -> Dict[str, Any]:
        """Convert FollowUpRule to dictionary."""
        return {
            'sequence_number': rule.sequence_number,
            'delay_days': rule.delay_days,
            'delay_hours': rule.delay_hours,
            'condition': rule.condition.value,
            'template_id': rule.template_id,
            'subject_override': rule.subject_override,
            'enabled': rule.enabled,
            'max_attempts': rule.max_attempts,
            'priority': rule.priority,
            'tags': rule.tags or [],
            'custom_condition': rule.custom_condition
        }
    
    def _dict_to_rule(self, data: Dict[str, Any]) -> FollowUpRule:
        """Convert dictionary to FollowUpRule."""
        return FollowUpRule(
            sequence_number=data.get('sequence_number', 1),
            delay_days=data.get('delay_days', 7),
            delay_hours=data.get('delay_hours', 0),
            condition=FollowUpCondition(data.get('condition', 'if_not_replied')),
            template_id=data.get('template_id'),
            subject_override=data.get('subject_override'),
            enabled=data.get('enabled', True),
            max_attempts=data.get('max_attempts', 1),
            priority=data.get('priority', 0),
            tags=data.get('tags', []),
            custom_condition=data.get('custom_condition')
        )
    
    def _log_operation(self, session: Session, campaign_id: str, user_id: str, 
                      operation: str, details: Dict[str, Any]):
        """Log a follow-up operation."""
        log_entry = Log(
            level=LogLevel.INFO.value,
            logger_name="followup_scheduler",
            message=f"Follow-up operation: {operation}",
            campaign_id=campaign_id,
            user_id=user_id,
            extra_data={
                'operation': operation,
                **details
            }
        )
        session.add(log_entry)
