import json
import os
import uuid
from datetime import datetime, timezone
from threading import Lock, RLock
from typing import List, Dict, Optional, Any

class FollowupManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.followups_file = os.path.join(data_dir, 'followups.json')
        self._lock = RLock()  # For atomic operations, allows reentrant locking
        self._ensure_data_dir()
        self._init_followups_file()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _init_followups_file(self):
        """Initialize the followups.json file if it doesn't exist."""
        if not os.path.exists(self.followups_file):
            initial_data = {
                'campaigns': {},
                'followups': {},
                'email_logs': []
            }
            self._write_data(initial_data)
    
    def _read_data(self) -> Dict[str, Any]:
        """Atomically read data from the JSON file."""
        with self._lock:
            try:
                with open(self.followups_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # Return default structure if file doesn't exist or is corrupted
                return {
                    'campaigns': {},
                    'followups': {},
                    'email_logs': []
                }
    
    def _write_data(self, data: Dict[str, Any]):
        """Atomically write data to the JSON file."""
        with self._lock:
            # Write to a temporary file first, then rename for atomicity
            temp_file = self.followups_file + '.tmp'
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                # Atomic rename
                if os.path.exists(self.followups_file):
                    os.remove(self.followups_file)
                os.rename(temp_file, self.followups_file)
            except Exception as e:
                # Clean up temp file if something went wrong
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise e
    
    def _get_utc_now(self) -> str:
        """Get current UTC datetime as ISO string."""
        return datetime.now(timezone.utc).isoformat()
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse ISO datetime string to datetime object."""
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    
    def get_analytics(self):
        """Get analytics data for all followups and campaigns."""
        data = self._read_data()
        followups = data.get('followups', {})
        campaigns = data.get('campaigns', {})
        
        total_followups = len(followups)
        sent_followups = len([f for f in followups.values() if f.get('status') == 'sent'])
        cancelled_followups = len([f for f in followups.values() if f.get('status') == 'cancelled'])
        
        # Count scheduled and overdue followups properly
        now = datetime.now(timezone.utc)
        scheduled_followups = 0
        overdue_followups = 0
        
        for followup in followups.values():
            if followup.get('status') == 'scheduled':
                if (followup.get('scheduled_at') and
                    self._parse_datetime(followup['scheduled_at']) < now):
                    overdue_followups += 1
                else:
                    scheduled_followups += 1
        
        return {
            'total_followups': total_followups,
            'scheduled_followups': scheduled_followups,
            'sent_followups': sent_followups,
            'overdue_followups': overdue_followups,
            'cancelled_followups': cancelled_followups,
            'campaigns': list(campaigns.values())
        }
    
    def create_campaign(self, name: str, description: str) -> str:
        """Create a new campaign and return its ID."""
        campaign_id = str(uuid.uuid4())
        data = self._read_data()
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'description': description,
            'created_at': self._get_utc_now(),
            'settings': {}
        }
        
        data['campaigns'][campaign_id] = campaign
        self._write_data(data)
        
        return campaign_id
    
    def log_email_sent(self, campaign_id: str, email: str, subject: str):
        """Log a sent email and create/update followup records."""
        data = self._read_data()
        
        # Log the email
        email_log = {
            'id': str(uuid.uuid4()),
            'campaign_id': campaign_id,
            'email': email,
            'subject': subject,
            'sent_at': self._get_utc_now()
        }
        data['email_logs'].append(email_log)
        
        # Create a followup record (initially scheduled)
        followup_id = str(uuid.uuid4())
        followup = {
            'id': followup_id,
            'campaign_id': campaign_id,
            'email': email,
            'subject': subject,
            'status': 'scheduled',
            'scheduled_at': self._get_utc_now(),  # For now, schedule immediately
            'created_at': self._get_utc_now(),
            'email_log_id': email_log['id']
        }
        data['followups'][followup_id] = followup
        
        self._write_data(data)
        
        print(f"Email to {email} logged in campaign {campaign_id} with subject '{subject}'.")
    
    def get_all_followups(self) -> List[Dict[str, Any]]:
        """Get all followup records."""
        data = self._read_data()
        return list(data.get('followups', {}).values())
    
    def get_campaign_followups(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get all followups for a specific campaign."""
        data = self._read_data()
        followups = data.get('followups', {})
        return [f for f in followups.values() if f.get('campaign_id') == campaign_id]
    
    def update_campaign_settings(self, campaign_id: str, settings: Dict[str, Any]) -> bool:
        """Update campaign settings."""
        data = self._read_data()
        
        if campaign_id not in data.get('campaigns', {}):
            return False
        
        data['campaigns'][campaign_id]['settings'].update(settings)
        data['campaigns'][campaign_id]['updated_at'] = self._get_utc_now()
        
        self._write_data(data)
        return True
    
    def process_overdue_followups(self) -> int:
        """Process overdue followups and return count of overdue items."""
        data = self._read_data()
        followups = data.get('followups', {})
        now = datetime.now(timezone.utc)
        
        overdue_count = 0
        for followup_id, followup in followups.items():
            if (followup.get('status') == 'scheduled' and 
                followup.get('scheduled_at') and
                self._parse_datetime(followup['scheduled_at']) < now):
                # Mark as overdue
                followup['status'] = 'overdue'
                followup['overdue_at'] = self._get_utc_now()
                overdue_count += 1
        
        if overdue_count > 0:
            self._write_data(data)
        
        return overdue_count
    
    def cancel_followup(self, followup_id: str, reason: str) -> bool:
        """Cancel a followup with a reason."""
        data = self._read_data()
        followups = data.get('followups', {})
        
        if followup_id not in followups:
            return False
        
        followups[followup_id]['status'] = 'cancelled'
        followups[followup_id]['cancelled_at'] = self._get_utc_now()
        followups[followup_id]['cancellation_reason'] = reason
        
        self._write_data(data)
        return True
    
    def reschedule_followup(self, followup_id: str, new_datetime: str) -> bool:
        """Reschedule a followup to a new datetime."""
        data = self._read_data()
        followups = data.get('followups', {})
        
        if followup_id not in followups:
            return False
        
        followup = followups[followup_id]
        followup['scheduled_at'] = new_datetime
        followup['status'] = 'scheduled'  # Reset to scheduled if it was overdue
        followup['rescheduled_at'] = self._get_utc_now()
        
        self._write_data(data)
        return True
    
    def get_campaigns(self) -> List[Dict[str, Any]]:
        """Get all campaigns."""
        data = self._read_data()
        return list(data.get('campaigns', {}).values())
    
    def get_overdue_followups(self) -> List[Dict[str, Any]]:
        """Get all overdue followups based on scheduled_at vs current time."""
        data = self._read_data()
        followups = data.get('followups', {})
        now = datetime.now(timezone.utc)
        
        overdue = []
        for followup in followups.values():
            if (followup.get('status') == 'scheduled' and 
                followup.get('scheduled_at') and
                self._parse_datetime(followup['scheduled_at']) < now):
                overdue.append(followup)
        
        return overdue


def get_followup_manager(data_dir='data'):
    return FollowupManager(data_dir)
