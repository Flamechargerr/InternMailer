"""
Enhanced Email Campaign System with Advanced Duplicate Prevention

This module provides a comprehensive email campaign system that integrates
with the enhanced professor tracker to prevent duplicates at all stages.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import uuid
from dataclasses import dataclass
from enum import Enum

from professor_tracker import ProfessorTracker

logger = logging.getLogger(__name__)

class CampaignMode(Enum):
    DRY_RUN = "dry_run"
    LIVE_SEND = "live_send"
    PREVIEW_ONLY = "preview_only"

@dataclass
class EmailCandidate:
    """Represents a potential email recipient."""
    email: str
    name: str
    university: str
    research_area: str
    homepage_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'name': self.name,
            'university': self.university,
            'research_area': self.research_area,
            'homepage_text': self.homepage_text
        }

@dataclass
class CampaignResult:
    """Results of a campaign execution."""
    campaign_id: str
    mode: CampaignMode
    total_candidates: int
    eligible_count: int
    emails_prepared: int
    emails_sent: int
    skipped_count: int
    failed_count: int
    duration_seconds: float
    errors: List[str]
    email_previews: List[Dict]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of email sending."""
        if self.emails_prepared == 0:
            return 0.0
        return (self.emails_sent / self.emails_prepared) * 100.0

class EnhancedCampaignSystem:
    """
    Advanced email campaign system with comprehensive duplicate prevention.
    
    Features:
    - Multi-stage duplicate prevention
    - Pending email tracking
    - Cooldown period management
    - Thread-safe operations
    - Comprehensive logging and statistics
    """
    
    def __init__(self, 
                 data_dir: str = "data",
                 cooldown_days: int = 30,
                 pending_expires_hours: int = 24,
                 email_delay_seconds: int = 30):
        """
        Initialize the enhanced campaign system.
        
        Args:
            data_dir: Directory for data storage
            cooldown_days: Days before allowing re-contact
            pending_expires_hours: Hours before pending emails expire
            email_delay_seconds: Delay between emails in live mode
        """
        self.data_dir = data_dir
        self.cooldown_days = cooldown_days
        self.pending_expires_hours = pending_expires_hours
        self.email_delay_seconds = email_delay_seconds
        
        # Initialize tracker with enhanced features
        self.tracker = ProfessorTracker(data_dir, cooldown_days)
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"Enhanced campaign system initialized with {cooldown_days}-day cooldown")
    
    def _setup_logging(self):
        """Setup campaign-specific logging."""
        log_dir = os.path.join(self.data_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create campaign-specific log file
        log_filename = os.path.join(log_dir, f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Configure logger
        handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        campaign_logger = logging.getLogger(f"{__name__}.campaign")
        campaign_logger.addHandler(handler)
        campaign_logger.setLevel(logging.INFO)
        
        self.campaign_logger = campaign_logger
    
    def analyze_candidates(self, 
                          candidates: List[EmailCandidate],
                          respect_cooldown: bool = True,
                          prioritize_dry_runs: bool = True) -> Dict[str, Any]:
        """
        Analyze email candidates for eligibility with smart prioritization.
        
        Args:
            candidates: List of email candidates
            respect_cooldown: Whether to respect cooldown periods
            prioritize_dry_runs: Whether to prioritize dry run professors for live sending
            
        Returns:
            Analysis results with eligibility breakdown and prioritization
        """
        logger.info(f"Analyzing {len(candidates)} email candidates with smart prioritization")
        
        # Extract emails for batch checking
        emails = [candidate.email for candidate in candidates]
        eligibility_results = self.tracker.batch_check_eligibility(emails, respect_cooldown)
        
        # Categorize results with prioritization
        dry_run_upgrades = []
        new_professors = []
        cooldown_expired = []
        ineligible = []
        pending = []
        cooldown = []
        
        for candidate in candidates:
            result = eligibility_results[candidate.email]
            
            if result['can_email']:
                priority = result.get('priority', 'new')
                if priority == 'dry_run_upgrade':
                    dry_run_upgrades.append((candidate, result))
                elif priority == 'new':
                    new_professors.append((candidate, result))
                elif priority == 'cooldown_expired':
                    cooldown_expired.append((candidate, result))
                else:
                    new_professors.append((candidate, result))  # fallback
            else:
                reason = result['reason']
                priority = result.get('priority', 'blocked')
                if 'pending' in reason.lower():
                    pending.append((candidate, result))
                elif 'cooldown' in reason.lower() or priority == 'cooldown':
                    cooldown.append((candidate, result))
                else:
                    ineligible.append((candidate, result))
        
        # Create prioritized eligible list
        eligible_candidates = []
        eligible_details = []
        
        # Priority 1: Dry run upgrades (if prioritizing)
        if prioritize_dry_runs:
            for candidate, result in dry_run_upgrades:
                eligible_candidates.append(candidate)
                eligible_details.append((candidate, result))
        
        # Priority 2: New professors
        for candidate, result in new_professors:
            eligible_candidates.append(candidate)
            eligible_details.append((candidate, result))
        
        # Priority 3: Cooldown expired (if applicable)
        for candidate, result in cooldown_expired:
            eligible_candidates.append(candidate)
            eligible_details.append((candidate, result))
        
        # If not prioritizing dry runs, add them to the end
        if not prioritize_dry_runs:
            for candidate, result in dry_run_upgrades:
                eligible_candidates.append(candidate)
                eligible_details.append((candidate, result))
        
        analysis = {
            'total_candidates': len(candidates),
            'eligible': {
                'count': len(eligible_candidates),
                'candidates': eligible_candidates,
                'details': eligible_details
            },
            'prioritization': {
                'dry_run_upgrades': len(dry_run_upgrades),
                'new_professors': len(new_professors),
                'cooldown_expired': len(cooldown_expired)
            },
            'ineligible': {
                'count': len(ineligible),
                'reasons': [result[1]['reason'] for result in ineligible]
            },
            'pending': {
                'count': len(pending),
                'details': pending
            },
            'cooldown': {
                'count': len(cooldown),
                'details': cooldown
            },
            'eligibility_rate': len(eligible_candidates) / len(candidates) * 100 if candidates else 0
        }
        
        logger.info(f"Smart candidate analysis: {len(eligible_candidates)} eligible ")
        logger.info(f"  - {len(dry_run_upgrades)} dry run upgrades (priority)")
        logger.info(f"  - {len(new_professors)} new professors")
        logger.info(f"  - {len(cooldown_expired)} cooldown expired")
        logger.info(f"  - {len(ineligible)} ineligible, {len(pending)} pending, {len(cooldown)} in cooldown")
        
        return analysis
    
    def prepare_campaign(self,
                        candidates: List[EmailCandidate], 
                        campaign_name: str,
                        mode: CampaignMode = CampaignMode.DRY_RUN,
                        respect_cooldown: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare a campaign by analyzing candidates and marking eligible ones as pending.
        
        Args:
            candidates: List of email candidates
            campaign_name: Name for the campaign
            mode: Campaign mode
            respect_cooldown: Whether to respect cooldown periods
            
        Returns:
            Tuple of (campaign_id, preparation_results)
        """
        campaign_id = str(uuid.uuid4())
        
        logger.info(f"Preparing campaign '{campaign_name}' (ID: {campaign_id}) with {len(candidates)} candidates")
        
        # Analyze candidates
        analysis = self.analyze_candidates(candidates, respect_cooldown)
        eligible_candidates = analysis['eligible']['candidates']
        
        # Mark eligible candidates as pending (except for preview mode)
        if mode != CampaignMode.PREVIEW_ONLY:
            for candidate in eligible_candidates:
                self.tracker.add_pending_email(
                    email=candidate.email,
                    name=candidate.name,
                    university=candidate.university,
                    subject=f"Research Inquiry - {candidate.research_area}",
                    campaign_id=campaign_id,
                    expires_hours=self.pending_expires_hours
                )
        
        preparation_results = {
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'mode': mode.value,
            'prepared_at': datetime.now().isoformat(),
            'analysis': analysis,
            'eligible_for_sending': len(eligible_candidates)
        }
        
        logger.info(f"Campaign prepared: {len(eligible_candidates)} emails ready for {mode.value}")
        
        return campaign_id, preparation_results
    
    def execute_campaign(self,
                        campaign_id: str,
                        candidates: List[EmailCandidate],
                        email_generator_func: callable,
                        email_sender_func: callable = None,
                        mode: CampaignMode = CampaignMode.DRY_RUN,
                        max_emails: int = None) -> CampaignResult:
        """
        Execute a prepared campaign.
        
        Args:
            campaign_id: ID of the prepared campaign
            candidates: List of email candidates (should match preparation)
            email_generator_func: Function to generate email content
            email_sender_func: Function to send emails (required for live mode)
            mode: Campaign execution mode
            max_emails: Maximum number of emails to send (None for no limit)
            
        Returns:
            Campaign execution results
        """
        start_time = time.time()
        
        logger.info(f"Executing campaign {campaign_id} in {mode.value} mode")
        self.campaign_logger.info(f"Starting campaign execution: {campaign_id}")
        
        # Initialize result tracking
        result = CampaignResult(
            campaign_id=campaign_id,
            mode=mode,
            total_candidates=len(candidates),
            eligible_count=0,
            emails_prepared=0,
            emails_sent=0,
            skipped_count=0,
            failed_count=0,
            duration_seconds=0.0,
            errors=[],
            email_previews=[]
        )
        
        # Filter candidates to only those that are eligible and pending (if not preview mode)
        eligible_candidates = []
        for candidate in candidates:
            if mode == CampaignMode.PREVIEW_ONLY:
                # In preview mode, use original eligibility check
                can_email_result = self.tracker.can_email_professor(candidate.email)
                if can_email_result['can_email']:
                    eligible_candidates.append(candidate)
            else:
                # In other modes, only process pending emails for this campaign
                if self.tracker.is_email_pending(candidate.email):
                    eligible_candidates.append(candidate)
        
        result.eligible_count = len(eligible_candidates)
        
        # Apply max_emails limit if specified
        if max_emails and len(eligible_candidates) > max_emails:
            eligible_candidates = eligible_candidates[:max_emails]
            logger.info(f"Limited to {max_emails} emails as requested")
        
        # Process each eligible candidate
        for i, candidate in enumerate(eligible_candidates):
            try:
                # Generate email content
                email_content = email_generator_func(candidate.to_dict())
                
                if not email_content:
                    error_msg = f"Failed to generate email for {candidate.email}"
                    result.errors.append(error_msg)
                    result.failed_count += 1
                    continue
                
                result.emails_prepared += 1
                
                # Store preview for first few emails
                if len(result.email_previews) < 3:
                    result.email_previews.append({
                        'email': candidate.email,
                        'name': candidate.name,
                        'university': candidate.university,
                        'subject': email_content.get('subject', 'Research Inquiry'),
                        'body_preview': email_content.get('body', '')[:500] + '...'
                    })
                
                # Handle different execution modes
                if mode == CampaignMode.DRY_RUN or mode == CampaignMode.PREVIEW_ONLY:
                    # Simulate sending
                    result.emails_sent += 1
                    self.campaign_logger.info(f"[{mode.value.upper()}] Would send to {candidate.email}")
                    
                    # For dry run, clear pending status and mark as "sent" in tracking
                    if mode == CampaignMode.DRY_RUN:
                        self.tracker.clear_pending_email(candidate.email)
                        self.tracker.add_emailed_professor(
                            email=candidate.email,
                            name=candidate.name,
                            university=candidate.university,
                            subject=email_content.get('subject', 'Research Inquiry'),
                            status="dry_run",
                            notes=f"Dry run - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                
                elif mode == CampaignMode.LIVE_SEND:
                    if not email_sender_func:
                        error_msg = "Email sender function required for live mode"
                        result.errors.append(error_msg)
                        result.failed_count += 1
                        continue
                    
                    # Attempt to send email
                    try:
                        send_success = email_sender_func(
                            candidate.email,
                            email_content.get('subject', 'Research Inquiry'),
                            email_content.get('body', '')
                        )
                        
                        if send_success:
                            result.emails_sent += 1
                            self.campaign_logger.info(f"[LIVE] Successfully sent to {candidate.email}")
                            
                            # Clear pending and mark as sent
                            self.tracker.clear_pending_email(candidate.email)
                            self.tracker.add_emailed_professor(
                                email=candidate.email,
                                name=candidate.name,
                                university=candidate.university,
                                subject=email_content.get('subject', 'Research Inquiry'),
                                status="sent",
                                notes=f"Live send - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                            )
                            
                            # Add delay between emails
                            if i < len(eligible_candidates) - 1:  # Don't delay after last email
                                time.sleep(self.email_delay_seconds)
                        
                        else:
                            result.failed_count += 1
                            self.campaign_logger.error(f"[LIVE] Failed to send to {candidate.email}")
                            # Clear pending on failure
                            self.tracker.clear_pending_email(candidate.email)
                    
                    except Exception as send_error:
                        error_msg = f"Error sending to {candidate.email}: {str(send_error)}"
                        result.errors.append(error_msg)
                        result.failed_count += 1
                        self.campaign_logger.error(error_msg)
                        # Clear pending on error
                        self.tracker.clear_pending_email(candidate.email)
            
            except Exception as e:
                error_msg = f"Error processing {candidate.email}: {str(e)}"
                result.errors.append(error_msg)
                result.failed_count += 1
                logger.error(error_msg)
                continue
        
        # Calculate final results
        result.duration_seconds = time.time() - start_time
        
        # Log campaign summary
        self.campaign_logger.info(f"Campaign {campaign_id} completed:")
        self.campaign_logger.info(f"  Mode: {mode.value}")
        self.campaign_logger.info(f"  Duration: {result.duration_seconds:.2f}s")
        self.campaign_logger.info(f"  Processed: {result.emails_prepared}")
        self.campaign_logger.info(f"  Sent: {result.emails_sent}")
        self.campaign_logger.info(f"  Failed: {result.failed_count}")
        self.campaign_logger.info(f"  Success Rate: {result.success_rate:.1f}%")
        
        logger.info(f"Campaign {campaign_id} completed: {result.emails_sent}/{result.emails_prepared} sent "
                   f"({result.success_rate:.1f}% success rate)")
        
        return result
    
    def get_campaign_eligibility_report(self, 
                                      candidates: List[EmailCandidate],
                                      respect_cooldown: bool = True) -> Dict[str, Any]:
        """
        Generate a detailed eligibility report for candidates.
        
        Args:
            candidates: List of email candidates
            respect_cooldown: Whether to respect cooldown periods
            
        Returns:
            Detailed eligibility report
        """
        analysis = self.analyze_candidates(candidates, respect_cooldown)
        
        # Get comprehensive stats from tracker
        tracker_stats = self.tracker.get_comprehensive_stats()
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'candidate_analysis': analysis,
            'tracker_statistics': tracker_stats,
            'recommendations': self._generate_recommendations(analysis, tracker_stats)
        }
        
        return report
    
    def _generate_recommendations(self, 
                                analysis: Dict[str, Any], 
                                tracker_stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis and tracker stats."""
        recommendations = []
        
        eligible_count = analysis['eligible']['count']
        total_count = analysis['total_candidates']
        eligibility_rate = analysis['eligibility_rate']
        
        if eligibility_rate < 20:
            recommendations.append(
                f"Low eligibility rate ({eligibility_rate:.1f}%). Consider expanding your professor list "
                "or adjusting cooldown settings."
            )
        
        if analysis['cooldown']['count'] > 0:
            recommendations.append(
                f"{analysis['cooldown']['count']} professors are in cooldown. "
                f"Consider waiting or using respect_cooldown=False for re-contact campaigns."
            )
        
        if analysis['pending']['count'] > 0:
            recommendations.append(
                f"{analysis['pending']['count']} emails are currently pending in other campaigns. "
                f"Wait for those campaigns to complete or expire."
            )
        
        if eligible_count > 50:
            recommendations.append(
                f"Large batch ({eligible_count} emails). Consider splitting into smaller campaigns "
                f"for better deliverability and monitoring."
            )
        
        pending_stats = tracker_stats['pending']
        if pending_stats['total_pending'] > 0:
            recommendations.append(
                f"{pending_stats['total_pending']} emails are currently pending across all campaigns. "
                f"Monitor pending email expiration to avoid conflicts."
            )
        
        return recommendations

    def cleanup_expired_pending(self) -> int:
        """
        Clean up expired pending emails.
        
        Returns:
            Number of expired emails cleaned up
        """
        initial_stats = self.tracker.get_pending_stats()
        initial_count = initial_stats['total_pending']
        
        # Trigger cleanup by accessing pending stats
        final_stats = self.tracker.get_pending_stats()
        final_count = final_stats['total_pending']
        
        cleaned_count = initial_count - final_count
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired pending emails")
        
        return cleaned_count
