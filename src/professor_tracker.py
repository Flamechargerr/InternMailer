"""
Professor Tracking System

This module maintains a persistent record of professors who have been emailed
to prevent duplicate emails and enable follow-up tracking.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class ProfessorTracker:
    """Tracks professors who have been emailed to prevent duplicates and enable follow-ups."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the professor tracker.
        
        Args:
            data_dir: Directory to store tracking data
        """
        self.data_dir = data_dir
        self.tracker_file = os.path.join(data_dir, "emailed_professors.json")
        self.emailed_professors = self._load_tracker()
        
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
