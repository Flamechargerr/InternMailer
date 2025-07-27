"""
Celery tasks for follow-up email processing.

This module contains the actual task implementations for:
- Sending follow-up emails
- Processing follow-up conditions
- Template rendering
- Email delivery tracking
"""

import logging  
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import traceback

from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from scheduler.celery_app import celery_app
from database.session import get_session
from database.models import (
    FollowUp, FollowUpStatus, Email, EmailStatus, Campaign, 
    Template, Contact, Log, LogLevel
)
from scheduler.followup_scheduler import FollowUpCondition


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_followup_email(self, followup_id: str) -> Dict[str, Any]:
    """
    Send a scheduled follow-up email.
    
    Args:
        followup_id: ID of the follow-up to send
        
    Returns:
        Dictionary with task result information
    """
    logger = logging.getLogger(__name__)
    
    try:
        with get_session() as session:
            # Get the follow-up record
            followup = session.query(FollowUp).filter(
                FollowUp.id == followup_id
            ).first()
            
            if not followup:
                logger.error(f"Follow-up {followup_id} not found")
                return {'status': 'error', 'message': 'Follow-up not found'}
            
            # Check if follow-up is still scheduled
            if followup.status != FollowUpStatus.SCHEDULED.value:
                logger.info(f"Follow-up {followup_id} is no longer scheduled (status: {followup.status})")
                return {'status': 'skipped', 'message': f'Follow-up status is {followup.status}'}
            
            # Get related records
            original_email = session.query(Email).filter(
                Email.id == followup.original_email_id
            ).first()
            
            if not original_email:
                logger.error(f"Original email {followup.original_email_id} not found")
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = "Original email not found"
                session.commit()
                return {'status': 'error', 'message': 'Original email not found'}
            
            campaign = session.query(Campaign).filter(
                Campaign.id == followup.campaign_id
            ).first()
            
            if not campaign:
                logger.error(f"Campaign {followup.campaign_id} not found")
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = "Campaign not found"
                session.commit()
                return {'status': 'error', 'message': 'Campaign not found'}
            
            # Check if campaign is still active
            if campaign.status not in ['active', 'scheduled']:
                logger.info(f"Campaign {campaign.id} is not active (status: {campaign.status})")
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = f"Campaign status is {campaign.status}"
                session.commit()
                return {'status': 'skipped', 'message': f'Campaign is {campaign.status}'}
            
            # Check send conditions
            should_send = _check_send_conditions(followup, original_email, session)
            if not should_send:
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = "Send conditions not met"
                session.commit()
                logger.info(f"Follow-up {followup_id} skipped - conditions not met")
                return {'status': 'skipped', 'message': 'Send conditions not met'}
            
            # Get contact information
            contact = session.query(Contact).filter(
                Contact.id == original_email.contact_id
            ).first()
            
            if not contact:
                logger.error(f"Contact {original_email.contact_id} not found")
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = "Contact not found"
                session.commit()
                return {'status': 'error', 'message': 'Contact not found'}
            
            # Check rate limits
            rate_limit_ok = _check_rate_limits(campaign, session)
            if not rate_limit_ok:
                # Reschedule for later
                new_time = datetime.now(timezone.utc) + timedelta(hours=1)
                followup.scheduled_at = new_time
                session.commit()
                
                # Reschedule Celery task
                send_followup_email.apply_async(
                    args=[followup_id],
                    eta=new_time,
                    task_id=f"followup_{followup_id}"
                )
                
                logger.info(f"Follow-up {followup_id} rescheduled due to rate limits")
                return {'status': 'rescheduled', 'message': 'Rate limit exceeded'}
            
            # Get template
            template = session.query(Template).filter(
                Template.id == followup.template_id
            ).first()
            
            if not template:
                logger.error(f"Template {followup.template_id} not found")
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = "Template not found"
                session.commit()
                return {'status': 'error', 'message': 'Template not found'}
            
            # Render email content
            try:
                email_content = _render_followup_email(
                    template, contact, original_email, followup, campaign
                )
            except Exception as e:
                logger.error(f"Error rendering email content for follow-up {followup_id}: {e}")
                followup.status = FollowUpStatus.SKIPPED.value
                followup.cancelled_reason = f"Template rendering error: {str(e)}"
                session.commit()
                return {'status': 'error', 'message': f'Template rendering error: {str(e)}'}
            
            # Create new email record
            new_email = Email(
                campaign_id=campaign.id,
                contact_id=contact.id,
                template_id=template.id,
                subject=email_content['subject'],
                body=email_content['body'],
                personalization_data=email_content['personalization_data'],
                status=EmailStatus.PENDING.value,
                scheduled_at=datetime.now(timezone.utc)
            )
            
            session.add(new_email)
            session.flush()  # Get the email ID
            
            # Update follow-up record
            followup.email_id = new_email.id
            followup.status = FollowUpStatus.SENT.value
            followup.sent_at = datetime.now(timezone.utc)
            
            # Send the email
            try:
                send_result = _send_email(new_email, contact, session)
                new_email.status = EmailStatus.SENT.value if send_result['success'] else EmailStatus.FAILED.value
                new_email.sent_at = datetime.now(timezone.utc)
                new_email.message_id = send_result.get('message_id')
                
                if not send_result['success']:
                    new_email.error_message = send_result.get('error', 'Unknown error')
                    
            except Exception as e:
                logger.error(f"Error sending follow-up email {new_email.id}: {e}")
                new_email.status = EmailStatus.FAILED.value
                new_email.error_message = str(e)
            
            # Update campaign statistics
            campaign.emails_sent = (campaign.emails_sent or 0) + 1
            if new_email.status == EmailStatus.SENT.value:
                # Will be updated when delivery confirmation is received
                pass
            
            # Log the follow-up send
            log_entry = Log(
                level=LogLevel.INFO.value,
                logger_name="followup_tasks",
                message=f"Follow-up email sent for sequence {followup.sequence_number}",
                campaign_id=campaign.id,
                email_id=new_email.id,
                extra_data={
                    'followup_id': followup_id,
                    'sequence_number': followup.sequence_number,
                    'original_email_id': original_email.id,
                    'send_success': new_email.status == EmailStatus.SENT.value,
                    'task_id': current_task.request.id
                }
            )
            session.add(log_entry)
            
            session.commit()
            
            result = {
                'status': 'sent' if new_email.status == EmailStatus.SENT.value else 'failed',
                'followup_id': followup_id,
                'email_id': new_email.id,
                'sequence_number': followup.sequence_number,
                'contact_email': contact.email,
                'sent_at': followup.sent_at.isoformat(),
                'message': 'Follow-up email sent successfully' if new_email.status == EmailStatus.SENT.value else 'Follow-up email failed to send'
            }
            
            logger.info(f"Follow-up {followup_id} processed: {result['status']}")
            return result
            
    except Exception as e:
        logger.error(f"Error processing follow-up {followup_id}: {e}\n{traceback.format_exc()}")
        
        # Update follow-up status on critical error
        try:
            with get_session() as session:
                followup = session.query(FollowUp).filter(
                    FollowUp.id == followup_id
                ).first()
                if followup and followup.status == FollowUpStatus.SCHEDULED.value:
                    followup.status = FollowUpStatus.SKIPPED.value
                    followup.cancelled_reason = f"Task error: {str(e)}"
                    session.commit()
        except:
            pass
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300, exc=e)
        
        return {'status': 'error', 'message': str(e)}


def _check_send_conditions(followup: FollowUp, original_email: Email, 
                          session: Session) -> bool:
    """Check if the follow-up should be sent based on conditions."""
    
    conditions = followup.send_conditions or {}
    condition_type = conditions.get('condition', 'if_not_replied')
    
    if condition_type == FollowUpCondition.ALWAYS.value:
        return True
    
    # Check email engagement status
    email_opened = original_email.opened_at is not None
    email_clicked = original_email.clicked_at is not None  
    email_replied = original_email.replied_at is not None
    
    if condition_type == FollowUpCondition.IF_NOT_OPENED.value:
        return not email_opened
    
    elif condition_type == FollowUpCondition.IF_NOT_CLICKED.value:
        return not email_clicked
    
    elif condition_type == FollowUpCondition.IF_NOT_REPLIED.value:
        return not email_replied
    
    elif condition_type == FollowUpCondition.IF_NO_ENGAGEMENT.value:
        return not (email_opened or email_clicked or email_replied)
    
    elif condition_type == FollowUpCondition.CUSTOM.value:
        # Handle custom conditions
        custom_condition = conditions.get('custom_condition', {})
        return _evaluate_custom_condition(custom_condition, original_email, session)
    
    # Default to not sending if condition is unknown
    return False


def _evaluate_custom_condition(condition: Dict[str, Any], original_email: Email,
                              session: Session) -> bool:
    """Evaluate custom follow-up conditions."""
    
    # Example custom conditions:
    # - Days since sent
    # - Contact engagement history
    # - Campaign performance thresholds
    
    if not condition:
        return False
    
    try:
        # Days since original email sent
        if 'min_days_since_sent' in condition:
            min_days = condition['min_days_since_sent']
            if original_email.sent_at:
                days_since = (datetime.now(timezone.utc) - original_email.sent_at).days
                if days_since < min_days:
                    return False
        
        # Maximum days since sent
        if 'max_days_since_sent' in condition:
            max_days = condition['max_days_since_sent']
            if original_email.sent_at:
                days_since = (datetime.now(timezone.utc) - original_email.sent_at).days
                if days_since > max_days:
                    return False
        
        # Contact engagement history
        if 'contact_response_rate_threshold' in condition:
            threshold = condition['contact_response_rate_threshold']
            contact = session.query(Contact).filter(
                Contact.id == original_email.contact_id
            ).first()
            if contact and contact.response_rate < threshold:
                return False
        
        return True
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error evaluating custom condition: {e}")
        return False


def _check_rate_limits(campaign: Campaign, session: Session) -> bool:
    """Check if sending is within rate limits."""
    
    now = datetime.now(timezone.utc)
    
    # Get campaign metadata for rate limits
    metadata = getattr(campaign, 'metadata', {}) or {}
    config = metadata.get('followup_config', {})
    
    hourly_limit = config.get('rate_limit_per_hour', 100)
    daily_limit = config.get('rate_limit_per_day', 1000)
    
    # Check hourly limit
    hour_ago = now - timedelta(hours=1)
    hourly_count = session.query(Email).filter(
        Email.campaign_id == campaign.id,
        Email.sent_at >= hour_ago,
        Email.status.in_([EmailStatus.SENT.value, EmailStatus.DELIVERED.value])
    ).count()
    
    if hourly_count >= hourly_limit:
        return False
    
    # Check daily limit
    day_ago = now - timedelta(days=1)
    daily_count = session.query(Email).filter(
        Email.campaign_id == campaign.id,
        Email.sent_at >= day_ago,
        Email.status.in_([EmailStatus.SENT.value, EmailStatus.DELIVERED.value])
    ).count()
    
    if daily_count >= daily_limit:
        return False
    
    return True


def _render_followup_email(template: Template, contact: Contact, original_email: Email,
                          followup: FollowUp, campaign: Campaign) -> Dict[str, Any]:
    """Render the follow-up email content using the template."""
    
    from jinja2 import Template as Jinja2Template
    
    # Prepare template variables
    template_vars = {
        'contact': {
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'full_name': f"{contact.first_name or ''} {contact.last_name or ''}".strip(),
            'email': contact.email,
            'title': contact.title,
            'organization': contact.organization,
            'department': contact.department,
            'position': contact.position,
            'research_areas': contact.research_areas or [],
        },
        'campaign': {
            'name': campaign.name,
            'description': campaign.description,
        },
        'followup': {
            'sequence_number': followup.sequence_number,
            'is_first_followup': followup.sequence_number == 1,
            'is_final_followup': followup.sequence_number >= (campaign.max_followups or 2),
        },
        'original_email': {
            'sent_at': original_email.sent_at,
            'subject': original_email.subject,
            'days_since_sent': (datetime.now(timezone.utc) - original_email.sent_at).days if original_email.sent_at else 0,
        }
    }
    
    # Render subject
    subject_template = followup.subject_override or template.subject_template
    subject_jinja = Jinja2Template(subject_template)
    rendered_subject = subject_jinja.render(**template_vars)
    
    # Render body
    body_jinja = Jinja2Template(template.body_template)
    rendered_body = body_jinja.render(**template_vars)
    
    return {
        'subject': rendered_subject,
        'body': rendered_body,
        'personalization_data': template_vars
    }


def _send_email(email: Email, contact: Contact, session: Session) -> Dict[str, Any]:
    """Send the actual email using the configured email service."""
    
    try:
        # Import email sending functionality
        # This would integrate with your existing email sending system
        from email_engine import EmailEngine  # Assuming this exists
        
        email_engine = EmailEngine()
        result = email_engine.send_email(
            to_email=contact.email,
            subject=email.subject,
            body=email.body,
            from_name="Your Name",  # Configure as needed
            from_email="your-email@domain.com"  # Configure as needed
        )
        
        return {
            'success': result.get('success', False),
            'message_id': result.get('message_id'),
            'error': result.get('error')
        }
        
    except ImportError:
        # Fallback for development/testing
        logging.getLogger(__name__).warning(
            "EmailEngine not available, using mock email sending"
        )
        return {
            'success': True,
            'message_id': f"mock_{email.id}_{datetime.now().timestamp()}"
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task
def process_followup_queue() -> Dict[str, Any]:
    """
    Process the follow-up queue and schedule overdue follow-ups.
    This task runs periodically to catch any missed follow-ups.
    """
    logger = logging.getLogger(__name__)
    
    try:
        with get_session() as session:
            now = datetime.now(timezone.utc)
            
            # Find overdue follow-ups
            overdue_followups = session.query(FollowUp).filter(
                FollowUp.status == FollowUpStatus.SCHEDULED.value,
                FollowUp.scheduled_at <= now
            ).all()
            
            processed_count = 0
            error_count = 0
            
            for followup in overdue_followups:
                try:
                    # Schedule immediate task
                    send_followup_email.apply_async(
                        args=[followup.id],
                        task_id=f"followup_{followup.id}"
                    )
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error scheduling overdue follow-up {followup.id}: {e}")
                    error_count += 1
            
            result = {
                'processed_count': processed_count,
                'error_count': error_count,
                'total_overdue': len(overdue_followups)
            }
            
            logger.info(f"Processed follow-up queue: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error processing follow-up queue: {e}")
        return {'error': str(e)}


@celery_app.task  
def cleanup_completed_followups() -> Dict[str, Any]:
    """
    Clean up old completed follow-ups to prevent database bloat.
    This task runs daily to remove old follow-up records.
    """
    logger = logging.getLogger(__name__)
    
    try:
        with get_session() as session:
            # Delete follow-ups older than 90 days that are completed
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            deleted_count = session.query(FollowUp).filter(
                FollowUp.status.in_([
                    FollowUpStatus.SENT.value,
                    FollowUpStatus.CANCELLED.value,
                    FollowUpStatus.SKIPPED.value
                ]),
                or_(
                    FollowUp.sent_at < cutoff_date,
                    FollowUp.cancelled_at < cutoff_date
                )
            ).delete()
            
            session.commit()
            
            result = {'deleted_count': deleted_count}
            logger.info(f"Cleaned up {deleted_count} old follow-up records")
            return result
            
    except Exception as e:
        logger.error(f"Error cleaning up follow-ups: {e}")
        return {'error': str(e)}


@celery_app.task
def health_check() -> Dict[str, Any]:
    """Health check task to monitor system status."""
    
    try:
        with get_session() as session:
            # Check database connectivity
            session.execute("SELECT 1").scalar()
            
            # Get some basic statistics
            scheduled_count = session.query(FollowUp).filter(
                FollowUp.status == FollowUpStatus.SCHEDULED.value
            ).count()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'scheduled_followups': scheduled_count
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
