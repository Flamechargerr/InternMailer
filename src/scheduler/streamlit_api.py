"""
Streamlit-compatible Follow-up Scheduler API

This module provides a simplified API for the Streamlit app to interact with 
the follow-up scheduler without requiring a separate FastAPI server.
"""

import logging
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import threading
import time

# Mock database for demonstration - in production, this would use the real database
class FollowUpManager:
    """Simplified follow-up manager for Streamlit integration."""
    
    def __init__(self, db_path: str = "followups.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT,
                original_email TEXT,
                contact_name TEXT,
                contact_email TEXT,
                sequence_number INTEGER,
                scheduled_at TEXT,
                sent_at TEXT,
                status TEXT DEFAULT 'scheduled',
                template_id TEXT,
                subject_override TEXT,
                conditions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                user_id TEXT,
                status TEXT DEFAULT 'active',
                followup_enabled INTEGER DEFAULT 1,
                followup_delay_days INTEGER DEFAULT 7,
                max_followups INTEGER DEFAULT 2,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT,
                contact_email TEXT,
                subject TEXT,
                status TEXT,
                sent_at TEXT,
                opened_at TEXT,
                replied_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_campaign(self, name: str, description: str = "", user_id: str = "default") -> str:
        """Create a new campaign."""
        campaign_id = f"camp_{int(time.time())}_{hash(name) % 1000}"
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO campaigns (id, name, description, user_id)
            VALUES (?, ?, ?, ?)
        """, (campaign_id, name, description, user_id))
        conn.commit()
        conn.close()
        
        return campaign_id
    
    def log_email_sent(self, campaign_id: str, contact_email: str, subject: str):
        """Log that an email was sent."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO email_logs (campaign_id, contact_email, subject, status, sent_at)
            VALUES (?, ?, ?, 'sent', ?)
        """, (campaign_id, contact_email, subject, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Schedule follow-up
        self.schedule_followup(campaign_id, contact_email, subject)
    
    def schedule_followup(self, campaign_id: str, contact_email: str, original_subject: str):
        """Schedule a follow-up email."""
        # Get campaign settings
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT followup_enabled, followup_delay_days, max_followups 
            FROM campaigns WHERE id = ?
        """, (campaign_id,))
        
        campaign_data = cursor.fetchone()
        if not campaign_data or not campaign_data[0]:
            conn.close()
            return
        
        followup_enabled, delay_days, max_followups = campaign_data
        
        # Check how many follow-ups already exist
        cursor = conn.execute("""
            SELECT COUNT(*) FROM followups 
            WHERE campaign_id = ? AND contact_email = ?
        """, (campaign_id, contact_email))
        
        existing_count = cursor.fetchone()[0]
        if existing_count >= max_followups:
            conn.close()
            return
        
        # Schedule the follow-up
        scheduled_time = datetime.now() + timedelta(days=delay_days)
        sequence_number = existing_count + 1
        
        conn.execute("""
            INSERT INTO followups (
                campaign_id, contact_email, sequence_number, 
                scheduled_at, status, original_email, contact_name
            ) VALUES (?, ?, ?, ?, 'scheduled', ?, ?)
        """, (
            campaign_id, contact_email, sequence_number,
            scheduled_time.isoformat(), original_subject, 
            contact_email.split('@')[0].title()
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Scheduled follow-up {sequence_number} for {contact_email}")
    
    def get_all_followups(self) -> List[Dict]:
        """Get all scheduled follow-ups."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT f.*, c.name as campaign_name
            FROM followups f
            LEFT JOIN campaigns c ON f.campaign_id = c.id
            ORDER BY f.scheduled_at ASC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        followups = []
        
        for row in cursor.fetchall():
            followup = dict(zip(columns, row))
            followup['scheduled_at_parsed'] = datetime.fromisoformat(followup['scheduled_at'])
            followup['is_overdue'] = followup['scheduled_at_parsed'] < datetime.now()
            followups.append(followup)
        
        conn.close()
        return followups
    
    def get_campaign_followups(self, campaign_id: str) -> List[Dict]:
        """Get follow-ups for a specific campaign."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM followups 
            WHERE campaign_id = ?
            ORDER BY scheduled_at ASC
        """, (campaign_id,))
        
        columns = [desc[0] for desc in cursor.description]
        followups = []
        
        for row in cursor.fetchall():
            followup = dict(zip(columns, row))
            followup['scheduled_at_parsed'] = datetime.fromisoformat(followup['scheduled_at'])
            followup['is_overdue'] = followup['scheduled_at_parsed'] < datetime.now()
            followups.append(followup)
        
        conn.close()
        return followups
    
    def reschedule_followup(self, followup_id: int, new_datetime: datetime) -> bool:
        """Reschedule a follow-up."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                UPDATE followups 
                SET scheduled_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'scheduled'
            """, (new_datetime.isoformat(), followup_id))
            
            affected = conn.total_changes
            conn.commit()
            conn.close()
            
            if affected > 0:
                self.logger.info(f"Rescheduled follow-up {followup_id} to {new_datetime}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error rescheduling follow-up {followup_id}: {e}")
            return False
    
    def cancel_followup(self, followup_id: int, reason: str = "Cancelled by user") -> bool:
        """Cancel a follow-up."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                UPDATE followups 
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'scheduled'
            """, (followup_id,))
            
            affected = conn.total_changes
            conn.commit()
            conn.close()
            
            if affected > 0:
                self.logger.info(f"Cancelled follow-up {followup_id}: {reason}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling follow-up {followup_id}: {e}")
            return False
    
    def update_campaign_settings(self, campaign_id: str, settings: Dict) -> bool:
        """Update campaign follow-up settings."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            update_fields = []
            values = []
            
            if 'followup_enabled' in settings:
                update_fields.append("followup_enabled = ?")
                values.append(1 if settings['followup_enabled'] else 0)
            
            if 'followup_delay_days' in settings:
                update_fields.append("followup_delay_days = ?")
                values.append(settings['followup_delay_days'])
            
            if 'max_followups' in settings:
                update_fields.append("max_followups = ?")
                values.append(settings['max_followups'])
            
            if update_fields:
                query = f"UPDATE campaigns SET {', '.join(update_fields)} WHERE id = ?"
                values.append(campaign_id)
                conn.execute(query, values)
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating campaign settings: {e}")
            return False
    
    def get_campaigns(self) -> List[Dict]:
        """Get all campaigns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
        
        columns = [desc[0] for desc in cursor.description]
        campaigns = []
        
        for row in cursor.fetchall():
            campaign = dict(zip(columns, row))
            # Get follow-up stats
            stats_cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_followups,
                    SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM followups WHERE campaign_id = ?
            """, (campaign['id'],))
            
            stats = stats_cursor.fetchone()
            campaign.update({
                'total_followups': stats[0] or 0,
                'scheduled_followups': stats[1] or 0,
                'sent_followups': stats[2] or 0,
                'cancelled_followups': stats[3] or 0
            })
            campaigns.append(campaign)
        
        conn.close()
        return campaigns
    
    def get_analytics(self) -> Dict:
        """Get follow-up analytics."""
        conn = sqlite3.connect(self.db_path)
        
        # Overall stats
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_followups,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN scheduled_at < datetime('now') AND status = 'scheduled' THEN 1 ELSE 0 END) as overdue
            FROM followups
        """)
        
        stats = cursor.fetchone()
        
        # Campaign breakdown
        cursor = conn.execute("""
            SELECT c.name, COUNT(f.id) as followup_count
            FROM campaigns c
            LEFT JOIN followups f ON c.id = f.campaign_id
            GROUP BY c.id, c.name
            ORDER BY followup_count DESC
            LIMIT 10
        """)
        
        campaign_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_followups': stats[0] or 0,
            'scheduled_followups': stats[1] or 0,
            'sent_followups': stats[2] or 0,
            'cancelled_followups': stats[3] or 0,
            'overdue_followups': stats[4] or 0,
            'campaigns': [{'name': name, 'followup_count': count} for name, count in campaign_stats]
        }
    
    def process_overdue_followups(self) -> int:
        """Process overdue follow-ups (mock implementation)."""
        overdue_followups = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT id, contact_email, original_email, sequence_number
            FROM followups 
            WHERE status = 'scheduled' AND scheduled_at < datetime('now')
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            followup_id, contact_email, original_email, sequence_number = row
            # In a real implementation, this would trigger email sending
            conn.execute("""
                UPDATE followups 
                SET status = 'sent', sent_at = datetime('now')
                WHERE id = ?
            """, (followup_id,))
            overdue_followups.append(followup_id)
        
        conn.commit()
        conn.close()
        
        return len(overdue_followups)


# Global instance for the Streamlit app
_manager = None

def get_followup_manager() -> FollowUpManager:
    """Get the global follow-up manager instance."""
    global _manager
    if _manager is None:
        _manager = FollowUpManager()
    return _manager
