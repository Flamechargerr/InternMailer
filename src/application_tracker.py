"""
Application Status Tracking System for InternMailer
Tracks application lifecycle, status updates, and follow-ups
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

class ApplicationStatus(Enum):
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

@dataclass
class ApplicationUpdate:
    application_id: str
    status: ApplicationStatus
    timestamp: datetime
    notes: str
    source: str  # 'manual', 'email_parser', 'web_scraper'
    metadata: Dict

class ApplicationTracker:
    def __init__(self, db_path: str = "data/internmailer.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize application tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Application status history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                notes TEXT,
                source TEXT,
                metadata TEXT,
                FOREIGN KEY (application_id) REFERENCES applications (id)
            )
        """)
        
        # Follow-up reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS follow_up_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT NOT NULL,
                reminder_date TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                message TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL,
                FOREIGN KEY (application_id) REFERENCES applications (id)
            )
        """)
        
        # Application metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_applications INTEGER DEFAULT 0,
                tier1_applications INTEGER DEFAULT 0,
                tier2_applications INTEGER DEFAULT 0,
                tier3_applications INTEGER DEFAULT 0,
                responses_received INTEGER DEFAULT 0,
                interviews_scheduled INTEGER DEFAULT 0,
                offers_received INTEGER DEFAULT 0,
                rejection_rate REAL DEFAULT 0.0,
                response_rate REAL DEFAULT 0.0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def update_application_status(self, application_id: str, status: ApplicationStatus, 
                                notes: str = "", source: str = "manual", 
                                metadata: Dict = None) -> bool:
        """Update application status and log the change"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert status update
            cursor.execute("""
                INSERT INTO application_status_history 
                (application_id, status, timestamp, notes, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                status.value,
                datetime.now().isoformat(),
                notes,
                source,
                json.dumps(metadata or {})
            ))
            
            # Update current status in applications table
            cursor.execute("""
                UPDATE applications 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status.value, datetime.now().isoformat(), application_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated application {application_id} status to {status.value}")
            
            # Schedule follow-up reminders based on status
            self._schedule_follow_ups(application_id, status)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating application status: {e}")
            return False
    
    def get_application_status(self, application_id: str) -> Optional[ApplicationStatus]:
        """Get current status of an application"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status FROM applications WHERE id = ?
            """, (application_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return ApplicationStatus(result[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting application status: {e}")
            return None
    
    def get_status_history(self, application_id: str) -> List[Dict]:
        """Get complete status history for an application"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, timestamp, notes, source, metadata
                FROM application_status_history
                WHERE application_id = ?
                ORDER BY timestamp DESC
            """, (application_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'status': row[0],
                    'timestamp': row[1],
                    'notes': row[2],
                    'source': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {}
                })
            
            conn.close()
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting status history: {e}")
            return []
    
    def _schedule_follow_ups(self, application_id: str, status: ApplicationStatus):
        """Schedule automatic follow-up reminders based on status"""
        follow_up_schedule = {
            ApplicationStatus.APPLIED: {
                'days': 7,
                'type': 'first_follow_up',
                'message': 'Send polite follow-up email to check application status'
            },
            ApplicationStatus.UNDER_REVIEW: {
                'days': 10,
                'type': 'review_follow_up',
                'message': 'Follow up on review status'
            },
            ApplicationStatus.INTERVIEW_SCHEDULED: {
                'days': 1,
                'type': 'interview_prep',
                'message': 'Prepare for upcoming interview'
            },
            ApplicationStatus.INTERVIEW_COMPLETED: {
                'days': 5,
                'type': 'post_interview_follow_up',
                'message': 'Send thank you note and follow up on decision'
            }
        }
        
        if status in follow_up_schedule:
            schedule_info = follow_up_schedule[status]
            reminder_date = datetime.now() + timedelta(days=schedule_info['days'])
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO follow_up_reminders
                    (application_id, reminder_date, reminder_type, message, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    application_id,
                    reminder_date.isoformat(),
                    schedule_info['type'],
                    schedule_info['message'],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                self.logger.error(f"Error scheduling follow-up: {e}")
    
    def get_pending_follow_ups(self) -> List[Dict]:
        """Get all pending follow-up reminders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.id, r.application_id, r.reminder_date, r.reminder_type, 
                       r.message, a.job_title, a.company
                FROM follow_up_reminders r
                JOIN applications a ON r.application_id = a.id
                WHERE r.completed = FALSE AND r.reminder_date <= ?
                ORDER BY r.reminder_date ASC
            """, (datetime.now().isoformat(),))
            
            reminders = []
            for row in cursor.fetchall():
                reminders.append({
                    'reminder_id': row[0],
                    'application_id': row[1],
                    'reminder_date': row[2],
                    'reminder_type': row[3],
                    'message': row[4],
                    'job_title': row[5],
                    'company': row[6]
                })
            
            conn.close()
            return reminders
            
        except Exception as e:
            self.logger.error(f"Error getting pending follow-ups: {e}")
            return []
    
    def mark_follow_up_completed(self, reminder_id: int) -> bool:
        """Mark a follow-up reminder as completed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE follow_up_reminders
                SET completed = TRUE
                WHERE id = ?
            """, (reminder_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking follow-up completed: {e}")
            return False
    
    def get_application_metrics(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get application metrics for a date range"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).isoformat()
            if not end_date:
                end_date = datetime.now().isoformat()
            
            # Get application counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM applications
                WHERE created_at BETWEEN ? AND ?
                GROUP BY status
            """, (start_date, end_date))
            
            status_counts = dict(cursor.fetchall())
            
            # Get prestige tier distribution
            cursor.execute("""
                SELECT prestige_tier, COUNT(*) as count
                FROM applications
                WHERE created_at BETWEEN ? AND ?
                GROUP BY prestige_tier
            """, (start_date, end_date))
            
            tier_counts = dict(cursor.fetchall())
            
            # Calculate rates
            total_applications = sum(status_counts.values())
            responses = status_counts.get('under_review', 0) + status_counts.get('interview_scheduled', 0) + \
                       status_counts.get('interview_completed', 0) + status_counts.get('offer_received', 0) + \
                       status_counts.get('rejected', 0)
            
            response_rate = (responses / total_applications * 100) if total_applications > 0 else 0
            rejection_rate = (status_counts.get('rejected', 0) / total_applications * 100) if total_applications > 0 else 0
            
            conn.close()
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'totals': {
                    'total_applications': total_applications,
                    'responses_received': responses,
                    'interviews_scheduled': status_counts.get('interview_scheduled', 0),
                    'offers_received': status_counts.get('offer_received', 0),
                    'rejections': status_counts.get('rejected', 0)
                },
                'rates': {
                    'response_rate': round(response_rate, 2),
                    'rejection_rate': round(rejection_rate, 2),
                    'interview_rate': round((status_counts.get('interview_scheduled', 0) / total_applications * 100) if total_applications > 0 else 0, 2),
                    'offer_rate': round((status_counts.get('offer_received', 0) / total_applications * 100) if total_applications > 0 else 0, 2)
                },
                'by_status': status_counts,
                'by_tier': tier_counts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting application metrics: {e}")
            return {}
    
    def update_metrics_daily(self):
        """Update daily metrics snapshot"""
        try:
            metrics = self.get_application_metrics()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO application_metrics
                (date, total_applications, tier1_applications, tier2_applications, 
                 tier3_applications, responses_received, interviews_scheduled, 
                 offers_received, rejection_rate, response_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().date().isoformat(),
                metrics['totals']['total_applications'],
                metrics['by_tier'].get('Tier 1', 0),
                metrics['by_tier'].get('Tier 2', 0),
                metrics['by_tier'].get('Tier 3', 0),
                metrics['totals']['responses_received'],
                metrics['totals']['interviews_scheduled'],
                metrics['totals']['offers_received'],
                metrics['rates']['rejection_rate'],
                metrics['rates']['response_rate']
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info("Daily metrics updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating daily metrics: {e}")
    
    def get_applications_by_status(self, status: ApplicationStatus) -> List[Dict]:
        """Get all applications with a specific status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, job_title, company, location, apply_link, 
                       created_at, prestige_tier, match_score
                FROM applications
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status.value,))
            
            applications = []
            for row in cursor.fetchall():
                applications.append({
                    'id': row[0],
                    'job_title': row[1],
                    'company': row[2],
                    'location': row[3],
                    'apply_link': row[4],
                    'created_at': row[5],
                    'prestige_tier': row[6],
                    'match_score': row[7],
                    'status': status.value
                })
            
            conn.close()
            return applications
            
        except Exception as e:
            self.logger.error(f"Error getting applications by status: {e}")
            return []

if __name__ == "__main__":
    # Test the application tracker
    tracker = ApplicationTracker()
    
    # Test status update
    test_app_id = "test_app_123"
    tracker.update_application_status(
        test_app_id, 
        ApplicationStatus.APPLIED,
        "Application submitted via company portal",
        "manual"
    )
    
    # Get status
    current_status = tracker.get_application_status(test_app_id)
    print(f"Current status: {current_status}")
    
    # Get metrics
    metrics = tracker.get_application_metrics()
    print(f"Application metrics: {json.dumps(metrics, indent=2)}")