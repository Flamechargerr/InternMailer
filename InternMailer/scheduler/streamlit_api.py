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
        try:
            # Handle different date formats
            if 'T' in dt_str:
                if '+' in dt_str or 'Z' in dt_str:
                    # Has timezone info
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    # No timezone, assume UTC
                    dt = datetime.fromisoformat(dt_str)
                    return dt.replace(tzinfo=timezone.utc)
            else:
                # Simple date format - assume it's in the future relative to now
                try:
                    dt = datetime.fromisoformat(dt_str)
                    # If it's a naive datetime, make it timezone-aware (UTC)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except:
                    # If all else fails, assume it's a future date
                    return datetime.now(timezone.utc)
        except Exception as e:
            print(f"Warning: Could not parse date '{dt_str}': {e}")
            # Return current time as fallback
            return datetime.now(timezone.utc)
    
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
                if followup.get('scheduled_at'):
                    try:
                        scheduled_dt = self._parse_datetime(followup['scheduled_at'])
                        # Check if the follow-up is more than 24 hours overdue
                        time_diff = (now - scheduled_dt).total_seconds()
                        if time_diff > 86400:  # More than 24 hours overdue
                            overdue_followups += 1
                        else:
                            scheduled_followups += 1
                    except:
                        # If we can't parse the date, assume it's scheduled
                        scheduled_followups += 1
                else:
                    scheduled_followups += 1
        
        # Count followups per campaign and add to campaign data
        campaigns_with_counts = []
        for campaign in campaigns.values():
            campaign_copy = campaign.copy()
            # Count followups for this campaign
            followup_count = len([f for f in followups.values() if f.get('campaign_id') == campaign['id']])
            campaign_copy['followup_count'] = followup_count
            campaigns_with_counts.append(campaign_copy)
        
        return {
            'total_followups': total_followups,
            'scheduled_followups': scheduled_followups,
            'sent_followups': sent_followups,
            'overdue_followups': overdue_followups,
            'cancelled_followups': cancelled_followups,
            'campaigns': campaigns_with_counts
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
        
        # Create a followup record (scheduled for 7 days later by default)
        from datetime import timedelta
        followup_delay_days = 7  # default delay
        scheduled_time = datetime.now(timezone.utc) + timedelta(days=followup_delay_days)
        
        followup_id = str(uuid.uuid4())
        followup = {
            'id': followup_id,
            'campaign_id': campaign_id,
            'email': email,
            'subject': subject,
            'status': 'scheduled',
            'scheduled_at': scheduled_time.isoformat(),
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
    
    def schedule_followup(self, campaign_id: str, email: str, scheduled_datetime, subject: str) -> str:
        """Schedule a new followup for a specific email."""
        data = self._read_data()
        
        # Create a new followup record
        followup_id = str(uuid.uuid4())
        followup = {
            'id': followup_id,
            'campaign_id': campaign_id,
            'email': email,
            'subject': subject,
            'status': 'scheduled',
            'scheduled_at': scheduled_datetime.isoformat() if hasattr(scheduled_datetime, 'isoformat') else str(scheduled_datetime),
            'created_at': self._get_utc_now()
        }
        
        data['followups'][followup_id] = followup
        self._write_data(data)
        
        return followup_id
    
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
    
    def cleanup_test_campaigns(self) -> int:
        """Remove test campaigns and their associated data."""
        data = self._read_data()
        campaigns = data.get('campaigns', {})
        followups = data.get('followups', {})
        email_logs = data.get('email_logs', [])
        
        # Find test campaign IDs
        test_campaign_ids = []
        for campaign_id, campaign in campaigns.items():
            if 'Test Campaign' in campaign.get('name', ''):
                test_campaign_ids.append(campaign_id)
        
        if not test_campaign_ids:
            return 0
        
        # Remove test campaigns
        for campaign_id in test_campaign_ids:
            del campaigns[campaign_id]
        
        # Remove associated followups
        followups_to_remove = []
        for followup_id, followup in followups.items():
            if followup.get('campaign_id') in test_campaign_ids:
                followups_to_remove.append(followup_id)
        
        for followup_id in followups_to_remove:
            del followups[followup_id]
        
        # Remove associated email logs
        email_logs[:] = [log for log in email_logs if log.get('campaign_id') not in test_campaign_ids]
        
        self._write_data(data)
        return len(test_campaign_ids)
    
    def get_campaign_summary(self) -> Dict[str, Any]:
        """Get a summary of all campaigns with their status."""
        data = self._read_data()
        campaigns = data.get('campaigns', {})
        followups = data.get('followups', {})
        email_logs = data.get('email_logs', [])
        
        summary = []
        for campaign in campaigns.values():
            campaign_followups = [f for f in followups.values() if f.get('campaign_id') == campaign['id']]
            campaign_emails = [log for log in email_logs if log.get('campaign_id') == campaign['id']]
            
            summary.append({
                'id': campaign['id'],
                'name': campaign['name'],
                'description': campaign['description'],
                'created_at': campaign['created_at'],
                'total_followups': len(campaign_followups),
                'total_emails': len(campaign_emails),
                'is_test': 'Test Campaign' in campaign['name']
            })
        
        return {'campaigns': summary, 'total_campaigns': len(campaigns)}


def get_followup_manager(data_dir='data'):
    return FollowupManager(data_dir)
