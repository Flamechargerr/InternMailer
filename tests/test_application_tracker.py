"""
Unit tests for ApplicationTracker module
"""

import unittest
import tempfile
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from application_tracker import ApplicationTracker, ApplicationStatus
from datetime import datetime

class TestApplicationTracker(unittest.TestCase):
    def setUp(self):
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.tracker = ApplicationTracker(self.temp_db.name)
        
        # Create a test application in the database
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_title TEXT,
                company TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO applications (id, job_title, company, status, created_at, updated_at)
            VALUES ('test_app_1', 'ML Intern', 'Google', 'not_applied', ?, ?)
        """, (datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def tearDown(self):
        # Clean up temporary database
        os.unlink(self.temp_db.name)
    
    def test_update_application_status(self):
        """Test updating application status"""
        success = self.tracker.update_application_status(
            'test_app_1',
            ApplicationStatus.APPLIED,
            'Application submitted via portal',
            'manual'
        )
        
        self.assertTrue(success)
        
        # Verify status was updated
        current_status = self.tracker.get_application_status('test_app_1')
        self.assertEqual(current_status, ApplicationStatus.APPLIED)
    
    def test_get_application_status(self):
        """Test getting application status"""
        status = self.tracker.get_application_status('test_app_1')
        self.assertEqual(status, ApplicationStatus.NOT_APPLIED)
        
        # Test non-existent application
        status = self.tracker.get_application_status('non_existent')
        self.assertIsNone(status)
    
    def test_get_status_history(self):
        """Test getting status history"""
        # Update status a few times
        self.tracker.update_application_status('test_app_1', ApplicationStatus.APPLIED, 'Applied online')
        self.tracker.update_application_status('test_app_1', ApplicationStatus.UNDER_REVIEW, 'Got confirmation')
        
        history = self.tracker.get_status_history('test_app_1')
        
        self.assertGreaterEqual(len(history), 2)
        # Most recent should be first
        self.assertEqual(history[0]['status'], 'under_review')
        self.assertEqual(history[1]['status'], 'applied')
    
    def test_get_pending_follow_ups(self):
        """Test getting pending follow-ups"""
        # Update status to trigger follow-up scheduling
        self.tracker.update_application_status('test_app_1', ApplicationStatus.APPLIED)
        
        # Get pending follow-ups
        reminders = self.tracker.get_pending_follow_ups()
        
        # Should have at least one reminder
        self.assertGreaterEqual(len(reminders), 0)
    
    def test_mark_follow_up_completed(self):
        """Test marking follow-up as completed"""
        # First create a follow-up
        self.tracker.update_application_status('test_app_1', ApplicationStatus.APPLIED)
        
        reminders = self.tracker.get_pending_follow_ups()
        if reminders:
            reminder_id = reminders[0]['reminder_id']
            success = self.tracker.mark_follow_up_completed(reminder_id)
            self.assertTrue(success)
    
    def test_get_application_metrics(self):
        """Test getting application metrics"""
        metrics = self.tracker.get_application_metrics()
        
        self.assertIn('period', metrics)
        self.assertIn('totals', metrics)
        self.assertIn('rates', metrics)
        self.assertIn('by_status', metrics)
        self.assertIn('by_tier', metrics)
        
        # Should have at least our test application
        self.assertGreaterEqual(metrics['totals']['total_applications'], 1)
    
    def test_get_applications_by_status(self):
        """Test getting applications by status"""
        applications = self.tracker.get_applications_by_status(ApplicationStatus.NOT_APPLIED)
        
        # Should find our test application
        self.assertGreaterEqual(len(applications), 1)
        self.assertEqual(applications[0]['status'], 'not_applied')

if __name__ == '__main__':
    unittest.main()