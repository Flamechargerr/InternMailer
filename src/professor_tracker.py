"""
Professor Tracking System

This module maintains a persistent record of professors who have been emailed
to prevent duplicate emails and enable follow-up tracking.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import logging
import threading

logger = logging.getLogger(__name__)

class ProfessorTracker:
    """Tracks professors who have been emailed to prevent duplicates and enable follow-ups."""
    
    def __init__(self, data_dir: str = "data", cooldown_days: int = 30):
        """
        Initialize the professor tracker.
        
        Args:
            data_dir: Directory to store tracking data
            cooldown_days: Number of days before allowing re-contact
        """
        self.data_dir = data_dir
        self.tracker_file = os.path.join(data_dir, "emailed_professors.json")
        self.pending_file = os.path.join(data_dir, "pending_emails.json")
        self.cooldown_days = cooldown_days
        self.emailed_professors = self._load_tracker()
        self.pending_emails = self._load_pending()
        self._lock = threading.Lock()  # Thread safety for concurrent operations
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def _load_tracker(self) -> Dict:
        """Load the existing emailed professors tracker from JSON file."""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('professors', []))} emailed professors from tracker")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading tracker file: {e}")
                return {"professors": [], "last_updated": None}
        else:
            logger.info("No existing tracker file found, starting fresh")
            return {"professors": [], "last_updated": None}
    
    def _save_tracker(self):
        """Save the current tracker state to JSON file."""
        try:
            self.emailed_professors["last_updated"] = datetime.now().isoformat()
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self.emailed_professors, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved tracker with {len(self.emailed_professors['professors'])} professors")
        except IOError as e:
            logger.error(f"Error saving tracker file: {e}")
    
    def is_professor_emailed(self, email: str) -> bool:
        """
        Check if a professor has already been emailed.
        
        Args:
            email: Professor's email address
            
        Returns:
            True if professor has been emailed, False otherwise
        """
        emailed_emails = {prof.get('email', '').lower() for prof in self.emailed_professors['professors']}
        return email.lower() in emailed_emails
    
    def add_emailed_professor(self, email: str, name: str = "", university: str = "", 
                            subject: str = "", status: str = "sent", notes: str = ""):
        """
        Add a professor to the emailed list.
        
        Args:
            email: Professor's email address
            name: Professor's name
            university: Professor's university
            subject: Email subject that was sent
            status: Email status (sent, failed, etc.)
            notes: Additional notes
        """
        # Check if already exists to avoid duplicates
        if self.is_professor_emailed(email):
            logger.info(f"Professor {email} already in tracker, updating entry")
            # Update existing entry
            for prof in self.emailed_professors['professors']:
                if prof.get('email', '').lower() == email.lower():
                    prof.update({
                        'name': name or prof.get('name', ''),
                        'university': university or prof.get('university', ''),
                        'last_subject': subject,
                        'status': status,
                        'last_emailed': datetime.now().isoformat(),
                        'notes': notes
                    })
                    break
        else:
            # Add new entry
            professor_entry = {
                'email': email.lower(),
                'name': name,
                'university': university,
                'first_emailed': datetime.now().isoformat(),
                'last_emailed': datetime.now().isoformat(),
                'last_subject': subject,
                'status': status,
                'email_count': 1,
                'notes': notes
            }
            self.emailed_professors['professors'].append(professor_entry)
            logger.info(f"Added new professor {email} to tracker")
        
        self._save_tracker()
    
    def bulk_add_emailed_professors(self, professor_emails: List[str]):
        """
        Add multiple professors to the emailed list (for initial setup).
        
        Args:
            professor_emails: List of professor email addresses
        """
        added_count = 0
        for email in professor_emails:
            if not self.is_professor_emailed(email):
                professor_entry = {
                    'email': email.lower(),
                    'name': '',
                    'university': '',
                    'first_emailed': datetime.now().isoformat(),
                    'last_emailed': datetime.now().isoformat(),
                    'last_subject': 'Previously emailed (bulk import)',
                    'status': 'sent',
                    'email_count': 1,
                    'notes': 'Imported from previous campaign'
                }
                self.emailed_professors['professors'].append(professor_entry)
                added_count += 1
        
        if added_count > 0:
            self._save_tracker()
            logger.info(f"Bulk added {added_count} professors to tracker")
    
    def get_emailed_professors(self) -> List[Dict]:
        """Get list of all emailed professors."""
        return self.emailed_professors['professors']
    
    def get_emailed_emails(self) -> Set[str]:
        """Get set of all emailed professor email addresses."""
        return {prof.get('email', '').lower() for prof in self.emailed_professors['professors']}
    
    def get_stats(self) -> Dict:
        """Get statistics about emailed professors."""
        professors = self.emailed_professors['professors']
        total_count = len(professors)
        status_counts = {}
        
        for prof in professors:
            status = prof.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_emailed': total_count,
            'status_breakdown': status_counts,
            'last_updated': self.emailed_professors.get('last_updated')
        }
    
    def remove_professor(self, email: str) -> bool:
        """
        Remove a professor from the tracker.
        
        Args:
            email: Professor's email address
            
        Returns:
            True if professor was removed, False if not found
        """
        initial_count = len(self.emailed_professors['professors'])
        self.emailed_professors['professors'] = [
            prof for prof in self.emailed_professors['professors'] 
            if prof.get('email', '').lower() != email.lower()
        ]
        
        removed = len(self.emailed_professors['professors']) < initial_count
        if removed:
            self._save_tracker()
            logger.info(f"Removed professor {email} from tracker")
        
        return removed
    
    def clear_all(self):
        """Clear all tracked professors (use with caution)."""
        self.emailed_professors = {"professors": [], "last_updated": None}
        self._save_tracker()
        logger.warning("Cleared all tracked professors")

    def _load_pending(self) -> Dict:
        """Load pending emails that are prepared but not yet sent."""
        if os.path.exists(self.pending_file):
            try:
                with open(self.pending_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('pending', []))} pending emails")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading pending file: {e}")
                return {"pending": [], "last_updated": None}
        return {"pending": [], "last_updated": None}

    def _save_pending(self):
        """Save pending emails to file."""
        try:
            self.pending_emails["last_updated"] = datetime.now().isoformat()
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending_emails, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.pending_emails['pending'])} pending emails")
        except IOError as e:
            logger.error(f"Error saving pending file: {e}")

    def add_pending_email(self, email: str, name: str = "", university: str = "", 
                         subject: str = "", campaign_id: str = "", expires_hours: int = 24):
        """
        Add an email to pending list to prevent duplicates during campaign preparation.
        
        Args:
            email: Professor's email address
            name: Professor's name
            university: Professor's university
            subject: Email subject being prepared
            campaign_id: ID of the campaign
            expires_hours: Hours until this pending entry expires
        """
        with self._lock:
            # Clean expired pending emails first
            self._clean_expired_pending()
            
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            pending_entry = {
                'email': email.lower(),
                'name': name,
                'university': university,
                'subject': subject,
                'campaign_id': campaign_id,
                'added_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat()
            }
            
            # Remove any existing pending entry for this email
            self.pending_emails['pending'] = [
                p for p in self.pending_emails['pending'] 
                if p.get('email', '').lower() != email.lower()
            ]
            
            self.pending_emails['pending'].append(pending_entry)
            self._save_pending()
            logger.info(f"Added pending email for {email} (expires in {expires_hours}h)")

    def is_email_pending(self, email: str) -> bool:
        """
        Check if an email is currently pending (prepared but not sent).
        
        Args:
            email: Professor's email address
            
        Returns:
            True if email is pending, False otherwise
        """
        with self._lock:
            self._clean_expired_pending()
            pending_emails = {p.get('email', '').lower() for p in self.pending_emails['pending']}
            return email.lower() in pending_emails

    def _clean_expired_pending(self):
        """Remove expired pending emails."""
        now = datetime.now()
        initial_count = len(self.pending_emails['pending'])
        
        self.pending_emails['pending'] = [
            p for p in self.pending_emails['pending']
            if datetime.fromisoformat(p.get('expires_at', now.isoformat())) > now
        ]
        
        removed_count = initial_count - len(self.pending_emails['pending'])
        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} expired pending emails")
            self._save_pending()

    def clear_pending_email(self, email: str):
        """Remove a specific email from pending list (when successfully sent or failed)."""
        with self._lock:
            initial_count = len(self.pending_emails['pending'])
            self.pending_emails['pending'] = [
                p for p in self.pending_emails['pending']
                if p.get('email', '').lower() != email.lower()
            ]
            
            if len(self.pending_emails['pending']) < initial_count:
                self._save_pending()
                logger.info(f"Cleared pending email for {email}")

    def can_email_professor(self, email: str, respect_cooldown: bool = True, allow_dry_run_upgrade: bool = True) -> Dict[str, any]:
        """
        Check if a professor can be emailed, considering all constraints with smart prioritization.
        
        Args:
            email: Professor's email address
            respect_cooldown: Whether to respect cooldown period
            allow_dry_run_upgrade: Whether to allow dry run professors to be upgraded to live send
            
        Returns:
            Dict with 'can_email' bool, 'reason' string, and 'priority' level
        """
        email = email.lower()
        
        # Check if email is currently pending
        if self.is_email_pending(email):
            return {
                'can_email': False,
                'reason': 'Email is currently pending in another campaign',
                'last_emailed': None,
                'cooldown_remaining': None,
                'priority': 'blocked'
            }
        
        # Check if professor has been emailed before
        professor_record = None
        for prof in self.emailed_professors['professors']:
            if prof.get('email', '').lower() == email:
                professor_record = prof
                break
        
        if not professor_record:
            return {
                'can_email': True,
                'reason': 'Professor has not been contacted before',
                'last_emailed': None,
                'cooldown_remaining': None,
                'priority': 'new'
            }
        
        # Check if this was a dry run that can be upgraded to live send
        if allow_dry_run_upgrade and professor_record.get('status') == 'dry_run':
            return {
                'can_email': True,
                'reason': 'Dry run professor - ready for live email sending',
                'last_emailed': professor_record.get('last_emailed'),
                'cooldown_remaining': None,
                'priority': 'dry_run_upgrade'
            }
        
        # If already sent live email, check cooldown
        if professor_record.get('status') == 'sent':
            if not respect_cooldown:
                return {
                    'can_email': False,
                    'reason': 'Professor has received live email (cooldown ignored)',
                    'last_emailed': professor_record.get('last_emailed'),
                    'cooldown_remaining': None,
                    'priority': 'blocked'
                }
            
            # Check cooldown period for live emails
            last_emailed_str = professor_record.get('last_emailed')
            if last_emailed_str:
                try:
                    last_emailed = datetime.fromisoformat(last_emailed_str)
                    cooldown_until = last_emailed + timedelta(days=self.cooldown_days)
                    now = datetime.now()
                    
                    if now < cooldown_until:
                        remaining_days = (cooldown_until - now).days
                        return {
                            'can_email': False,
                            'reason': f'Professor received live email - in cooldown ({remaining_days} days remaining)',
                            'last_emailed': last_emailed_str,
                            'cooldown_remaining': remaining_days,
                            'priority': 'cooldown'
                        }
                    else:
                        return {
                            'can_email': True,
                            'reason': 'Cooldown period has expired, can re-contact',
                            'last_emailed': last_emailed_str,
                            'cooldown_remaining': 0,
                            'priority': 'cooldown_expired'
                        }
                except ValueError:
                    logger.warning(f"Invalid date format for professor {email}: {last_emailed_str}")
        
        return {
            'can_email': False,
            'reason': 'Professor has been contacted before',
            'last_emailed': professor_record.get('last_emailed'),
            'cooldown_remaining': None,
            'priority': 'blocked'
        }

    def batch_check_eligibility(self, emails: List[str], respect_cooldown: bool = True) -> Dict[str, Dict]:
        """
        Check eligibility for multiple emails at once.
        
        Args:
            emails: List of email addresses to check
            respect_cooldown: Whether to respect cooldown period
            
        Returns:
            Dict mapping email addresses to eligibility results
        """
        results = {}
        for email in emails:
            results[email] = self.can_email_professor(email, respect_cooldown)
        return results

    def get_pending_stats(self) -> Dict:
        """Get statistics about pending emails."""
        with self._lock:
            self._clean_expired_pending()
            return {
                'total_pending': len(self.pending_emails['pending']),
                'pending_by_campaign': self._group_pending_by_campaign(),
                'oldest_pending': self._get_oldest_pending(),
                'expires_soon': self._get_expires_soon()
            }

    def _group_pending_by_campaign(self) -> Dict[str, int]:
        """Group pending emails by campaign ID."""
        campaigns = {}
        for pending in self.pending_emails['pending']:
            campaign_id = pending.get('campaign_id', 'unknown')
            campaigns[campaign_id] = campaigns.get(campaign_id, 0) + 1
        return campaigns

    def _get_oldest_pending(self) -> Optional[str]:
        """Get the timestamp of the oldest pending email."""
        if not self.pending_emails['pending']:
            return None
        
        oldest = min(self.pending_emails['pending'], 
                    key=lambda x: x.get('added_at', datetime.now().isoformat()))
        return oldest.get('added_at')

    def _get_expires_soon(self, hours: int = 2) -> int:
        """Get count of emails expiring within specified hours."""
        cutoff = datetime.now() + timedelta(hours=hours)
        count = 0
        
        for pending in self.pending_emails['pending']:
            expires_at = datetime.fromisoformat(pending.get('expires_at', cutoff.isoformat()))
            if expires_at <= cutoff:
                count += 1
        
        return count

    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive statistics about all tracking data."""
        basic_stats = self.get_stats()
        pending_stats = self.get_pending_stats()
        
        return {
            'emailed': basic_stats,
            'pending': pending_stats,
            'summary': {
                'total_contacts': basic_stats['total_emailed'],
                'pending_contacts': pending_stats['total_pending'],
                'unique_professors': len(set(
                    list(self.get_emailed_emails()) + 
                    [p.get('email', '').lower() for p in self.pending_emails['pending']]
                ))
            }
        }
