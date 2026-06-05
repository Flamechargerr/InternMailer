#!/usr/bin/env python3
"""
Tests for rate limiting and email tracking functionality.

**Validates: Requirements 2.6, 2.7**

This test suite verifies:
- Rate limiting between emails (min delay)
- Daily email limits
- Email tracking in database
- Accurate sent/failed counts
"""

import unittest
import sqlite3
import time
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.email_system import RateLimiter, EmailSystem


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def test_min_delay_enforcement(self):
        """Test that minimum delay between emails is enforced"""
        # **Validates: Requirements 2.6**
        min_delay = 0.5  # 500ms
        limiter = RateLimiter(min_delay=min_delay, max_daily=100)
        
        # First send should be immediate
        start = time.time()
        limiter.wait_if_needed()
        first_wait = time.time() - start
        self.assertLess(first_wait, 0.1, "First send should not wait")
        
        # Second send should wait at least min_delay
        start = time.time()
        limiter.wait_if_needed()
        second_wait = time.time() - start
        self.assertGreaterEqual(second_wait, min_delay, 
                                f"Should wait at least {min_delay}s between sends")
        self.assertLess(second_wait, min_delay + 0.2,
                       f"Should not wait much more than {min_delay}s")
    
    def test_daily_limit_enforcement(self):
        """Test that daily email limit is enforced"""
        # **Validates: Requirements 2.6**
        max_daily = 5
        limiter = RateLimiter(min_delay=0.01, max_daily=max_daily)
        
        # Should allow sends up to limit
        for i in range(max_daily):
            can_send, message = limiter.can_send()
            self.assertTrue(can_send, f"Should allow send {i+1}/{max_daily}")
            limiter.record_sent()
        
        # Should block after limit
        can_send, message = limiter.can_send()
        self.assertFalse(can_send, "Should block after daily limit")
        self.assertIn("limit", message.lower(), "Message should mention limit")
    
    def test_daily_reset(self):
        """Test that daily counter resets at midnight"""
        # **Validates: Requirements 2.6**
        limiter = RateLimiter(min_delay=0.01, max_daily=5)
        
        # Send up to limit
        for _ in range(5):
            limiter.record_sent()
        
        # Should be at limit
        can_send, _ = limiter.can_send()
        self.assertFalse(can_send, "Should be at limit")
        
        # Simulate midnight reset by setting reset time to past
        limiter.daily_reset_time = time.time() - 1
        
        # Should allow sends again
        can_send, _ = limiter.can_send()
        self.assertTrue(can_send, "Should allow sends after reset")
        self.assertEqual(limiter.daily_sent, 0, "Counter should reset to 0")
    
    def test_rate_limiter_status(self):
        """Test rate limiter status reporting"""
        # **Validates: Requirements 2.6**
        max_daily = 10
        limiter = RateLimiter(min_delay=0.1, max_daily=max_daily)
        
        # Send some emails
        for _ in range(3):
            limiter.record_sent()
        
        status = limiter.get_status()
        
        self.assertEqual(status['daily_sent'], 3)
        self.assertEqual(status['daily_limit'], max_daily)
        self.assertEqual(status['remaining_today'], max_daily - 3)
        self.assertEqual(status['min_delay'], 0.1)
        self.assertIn('next_reset', status)
    
    def test_jitter_in_delay(self):
        """Test that jitter is added to prevent predictable timing"""
        # **Validates: Requirements 2.6**
        min_delay = 0.2
        limiter = RateLimiter(min_delay=min_delay, max_daily=100)
        
        # Collect multiple wait times
        wait_times = []
        for _ in range(5):
            start = time.time()
            limiter.wait_if_needed()
            wait_time = time.time() - start
            wait_times.append(wait_time)
        
        # Check that wait times vary (jitter is present)
        # Skip first wait (should be ~0)
        actual_waits = wait_times[1:]
        
        # All should be >= min_delay
        for wait in actual_waits:
            self.assertGreaterEqual(wait, min_delay, 
                                   "All waits should be at least min_delay")
        
        # Should have some variation (not all exactly the same)
        # Allow for timing precision issues
        unique_waits = len(set(round(w, 2) for w in actual_waits))
        self.assertGreater(unique_waits, 1, 
                          "Wait times should vary due to jitter")


class TestEmailTracking(unittest.TestCase):
    """Test email tracking in database"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.tracking_db = os.path.join(self.temp_dir, 'test_tracking.db')
        
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.EMAIL_ADDRESS = 'test@example.com'
        self.mock_config.EMAIL_PASSWORD = 'test_password'
        self.mock_config.CONTACTS_DB_PATH = os.path.join(self.temp_dir, 'contacts.db')
        self.mock_config.DATABASE_PATH = self.tracking_db
        self.mock_config.RATE_LIMIT_DELAY = 0.01
        self.mock_config.MAX_EMAILS_PER_DAY = 100
        self.mock_config.MAX_CONCURRENT_EMAILS = 5
        self.mock_config.AUTO_APPROVE_SENDS = True
        self.mock_config.EMAIL_STRICT_TEMPLATE = False
        self.mock_config.EMAIL_SKIP_ACADEMIC = False
        self.mock_config.COMPANY_CONTACTS_CSV = os.path.join(self.temp_dir, 'contacts.csv')
        self.mock_config.JOBS_DB_PATH = os.path.join(self.temp_dir, 'jobs.db')
        self.mock_config.DEFAULT_ROLE_TITLE = 'Software Engineer'
        self.mock_config.STRICT_TEMPLATE_KEYWORDS_EXTRA = ''
        
        # Patch config
        self.config_patcher = patch('core.email_system.config', self.mock_config)
        self.config_patcher.start()
        
        # Patch get_profile
        self.profile_patcher = patch('core.email_system.get_profile')
        mock_get_profile = self.profile_patcher.start()
        mock_get_profile.return_value = {
            'name': 'Test User',
            'email': 'test@example.com',
            'title': 'Software Engineer',
            'location': 'Test City',
            'skills': ['Python', 'SQL'],
            'experience_highlights': ['Built systems'],
            'project_highlights': ['Created tools']
        }
        
        # Patch credential validation to avoid actual SMTP connection
        self.validate_patcher = patch.object(EmailSystem, '_validate_credentials')
        mock_validate = self.validate_patcher.start()
        mock_validate.return_value = True
        
        # Patch SMTP connection pool to avoid actual SMTP connections
        self.pool_patcher = patch('core.email_system.SMTPConnectionPool')
        mock_pool_class = self.pool_patcher.start()
        mock_pool = Mock()
        mock_pool.pool_size = 5
        mock_pool.connections = Mock()
        mock_pool.connections.qsize.return_value = 5
        mock_pool_class.return_value = mock_pool
    
    def tearDown(self):
        """Clean up test database"""
        self.config_patcher.stop()
        self.profile_patcher.stop()
        self.validate_patcher.stop()
        self.pool_patcher.stop()
        
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_tracking_db_initialization(self):
        """Test that tracking database is initialized correctly"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        # Check that database exists
        self.assertTrue(os.path.exists(self.tracking_db))
        
        # Check that tables exist
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            self.assertIn('sent_emails', tables)
            self.assertIn('rate_limit_log', tables)
            self.assertIn('campaign_stats', tables)
    
    def test_track_sent_email(self):
        """Test tracking a successfully sent email"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        metadata = {
            'provider': 'test_provider',
            'confidence': 0.95,
            'ai_used': True
        }
        
        system.track_email(
            email='recipient@example.com',
            name='Test Recipient',
            company='Test Company',
            position='Software Engineer',
            metadata=metadata,
            subject='Test Subject',
            status='sent'
        )
        
        # Verify email was tracked
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute(
                "SELECT * FROM sent_emails WHERE email = ?",
                ('recipient@example.com',)
            )
            row = cursor.fetchone()
            
            self.assertIsNotNone(row, "Email should be tracked")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            email_data = dict(zip(columns, row))
            
            self.assertEqual(email_data['email'], 'recipient@example.com')
            self.assertEqual(email_data['name'], 'Test Recipient')
            self.assertEqual(email_data['company'], 'Test Company')
            self.assertEqual(email_data['position'], 'Software Engineer')
            self.assertEqual(email_data['subject'], 'Test Subject')
            self.assertEqual(email_data['status'], 'sent')
            self.assertEqual(email_data['provider_used'], 'test_provider')
            self.assertAlmostEqual(email_data['ai_confidence'], 0.95, places=2)
    
    def test_track_failed_email(self):
        """Test tracking a failed email with error message"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        metadata = {'provider': 'fallback', 'confidence': 0.0}
        
        system.track_email(
            email='failed@example.com',
            name='Failed Recipient',
            company='Test Company',
            position='Engineer',
            metadata=metadata,
            subject='Test Subject',
            status='failed',
            error_message='SMTP connection error'
        )
        
        # Verify failed email was tracked
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute(
                "SELECT status, error_message FROM sent_emails WHERE email = ?",
                ('failed@example.com',)
            )
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'failed')
            self.assertEqual(row[1], 'SMTP connection error')
    
    def test_update_existing_email_tracking(self):
        """Test updating an existing email record (retry scenario)"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        metadata = {'provider': 'test', 'confidence': 0.8}
        
        # Track initial attempt
        system.track_email(
            email='retry@example.com',
            name='Retry User',
            company='Test Co',
            position='Dev',
            metadata=metadata,
            subject='Test',
            status='failed',
            error_message='First attempt failed',
            retry_count=0
        )
        
        # Track retry
        system.track_email(
            email='retry@example.com',
            name='Retry User',
            company='Test Co',
            position='Dev',
            metadata=metadata,
            subject='Test',
            status='sent',
            error_message=None,
            retry_count=1
        )
        
        # Verify only one record exists with updated status
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute(
                "SELECT status, retry_count, error_message FROM sent_emails WHERE email = ?",
                ('retry@example.com',)
            )
            rows = cursor.fetchall()
            
            self.assertEqual(len(rows), 1, "Should have only one record")
            self.assertEqual(rows[0][0], 'sent', "Status should be updated")
            self.assertEqual(rows[0][1], 1, "Retry count should be updated")
            self.assertIsNone(rows[0][2], "Error message should be cleared")
    
    def test_get_daily_sent_count(self):
        """Test getting accurate daily sent count"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        metadata = {'provider': 'test', 'confidence': 0.8}
        
        # Track multiple emails
        for i in range(5):
            system.track_email(
                email=f'user{i}@example.com',
                name=f'User {i}',
                company='Test Co',
                position='Dev',
                metadata=metadata,
                subject='Test',
                status='sent'
            )
        
        # Track one failed email
        system.track_email(
            email='failed@example.com',
            name='Failed User',
            company='Test Co',
            position='Dev',
            metadata=metadata,
            subject='Test',
            status='failed'
        )
        
        # Get daily count (should only count sent, not failed)
        count = system.get_daily_sent_count()
        self.assertEqual(count, 5, "Should count only successfully sent emails")
    
    def test_rate_limit_logging(self):
        """Test that rate limit decisions are logged"""
        # **Validates: Requirements 2.6, 2.7**
        system = EmailSystem()
        
        # Log some rate limit decisions
        system.log_rate_limit('send_email', True, 'OK (5/100 today)')
        system.log_rate_limit('send_email', True, 'OK (6/100 today)')
        system.log_rate_limit('send_email', False, 'Daily limit reached')
        
        # Verify logs exist
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute(
                "SELECT action, was_allowed, reason FROM rate_limit_log ORDER BY id"
            )
            logs = cursor.fetchall()
            
            self.assertEqual(len(logs), 3)
            self.assertEqual(logs[0][1], 1)  # was_allowed = True
            self.assertEqual(logs[1][1], 1)  # was_allowed = True
            self.assertEqual(logs[2][1], 0)  # was_allowed = False
            self.assertIn('limit', logs[2][2].lower())
    
    def test_campaign_stats_tracking(self):
        """Test that campaign statistics are tracked correctly"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        # Simulate campaign activity
        system.stats['sent'] = 10
        system.stats['failed'] = 2
        system.stats['skipped'] = 1
        system.stats['ai_generated'] = 8
        system.stats['fallback_used'] = 2
        system.stats['auth_errors'] = 1
        system.stats['connection_errors'] = 1
        system.stats['rate_limit_hits'] = 0
        system.stats['daily_limit_exceeded'] = 0
        
        # Update campaign stats
        system.update_campaign_stats()
        
        # Verify stats were saved
        today = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(self.tracking_db) as conn:
            cursor = conn.execute(
                "SELECT * FROM campaign_stats WHERE campaign_date = ?",
                (today,)
            )
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            columns = [desc[0] for desc in cursor.description]
            stats = dict(zip(columns, row))
            
            self.assertEqual(stats['total_sent'], 10)
            self.assertEqual(stats['total_failed'], 2)
            self.assertEqual(stats['total_skipped'], 1)
            self.assertEqual(stats['ai_generated'], 8)
            self.assertEqual(stats['fallback_used'], 2)
            self.assertEqual(stats['auth_errors'], 1)
            self.assertEqual(stats['connection_errors'], 1)


class TestRateLimitingIntegration(unittest.TestCase):
    """Integration tests for rate limiting with email system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.tracking_db = os.path.join(self.temp_dir, 'test_tracking.db')
        
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.EMAIL_ADDRESS = 'test@example.com'
        self.mock_config.EMAIL_PASSWORD = 'test_password'
        self.mock_config.CONTACTS_DB_PATH = os.path.join(self.temp_dir, 'contacts.db')
        self.mock_config.DATABASE_PATH = self.tracking_db
        self.mock_config.RATE_LIMIT_DELAY = 0.1
        self.mock_config.MAX_EMAILS_PER_DAY = 5  # Low limit for testing
        self.mock_config.MAX_CONCURRENT_EMAILS = 5
        self.mock_config.AUTO_APPROVE_SENDS = True
        self.mock_config.EMAIL_STRICT_TEMPLATE = False
        self.mock_config.EMAIL_SKIP_ACADEMIC = False
        self.mock_config.COMPANY_CONTACTS_CSV = os.path.join(self.temp_dir, 'contacts.csv')
        self.mock_config.JOBS_DB_PATH = os.path.join(self.temp_dir, 'jobs.db')
        self.mock_config.DEFAULT_ROLE_TITLE = 'Software Engineer'
        self.mock_config.STRICT_TEMPLATE_KEYWORDS_EXTRA = ''
        
        # Patch config
        self.config_patcher = patch('core.email_system.config', self.mock_config)
        self.config_patcher.start()
        
        # Patch get_profile
        self.profile_patcher = patch('core.email_system.get_profile')
        mock_get_profile = self.profile_patcher.start()
        mock_get_profile.return_value = {
            'name': 'Test User',
            'email': 'test@example.com',
            'title': 'Software Engineer',
            'location': 'Test City',
            'skills': ['Python', 'SQL'],
            'experience_highlights': ['Built systems'],
            'project_highlights': ['Created tools']
        }
        
        # Patch credential validation
        self.validate_patcher = patch.object(EmailSystem, '_validate_credentials')
        mock_validate = self.validate_patcher.start()
        mock_validate.return_value = True
        
        # Patch SMTP connection pool to avoid actual SMTP connections
        self.pool_patcher = patch('core.email_system.SMTPConnectionPool')
        mock_pool_class = self.pool_patcher.start()
        mock_pool = Mock()
        mock_pool.pool_size = 5
        mock_pool.connections = Mock()
        mock_pool.connections.qsize.return_value = 5
        mock_pool_class.return_value = mock_pool
    
    def tearDown(self):
        """Clean up"""
        self.config_patcher.stop()
        self.profile_patcher.stop()
        self.validate_patcher.stop()
        self.pool_patcher.stop()
        
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_rate_limit_blocks_after_daily_limit(self):
        """Test that rate limiter blocks sends after daily limit"""
        # **Validates: Requirements 2.6**
        system = EmailSystem()
        
        # Simulate reaching daily limit
        for _ in range(5):
            system.rate_limiter.record_sent()
        
        # Try to send another email
        can_send, remaining = system.can_send_today()
        
        self.assertFalse(can_send, "Should not allow send after daily limit")
        self.assertEqual(remaining, 0, "Should have 0 remaining")
    
    def test_rate_limit_allows_before_daily_limit(self):
        """Test that rate limiter allows sends before daily limit"""
        # **Validates: Requirements 2.6**
        system = EmailSystem()
        
        # Send a few emails
        for _ in range(3):
            system.rate_limiter.record_sent()
        
        # Should still allow more
        can_send, remaining = system.can_send_today()
        
        self.assertTrue(can_send, "Should allow send before daily limit")
        self.assertEqual(remaining, 2, "Should have 2 remaining")
    
    def test_accurate_sent_count_tracking(self):
        """Test that sent counts are accurate across multiple operations"""
        # **Validates: Requirements 2.7**
        system = EmailSystem()
        
        metadata = {'provider': 'test', 'confidence': 0.8}
        
        # Track multiple successful sends
        for i in range(3):
            system.track_email(
                email=f'user{i}@example.com',
                name=f'User {i}',
                company='Test Co',
                position='Dev',
                metadata=metadata,
                subject='Test',
                status='sent'
            )
            system.rate_limiter.record_sent()
        
        # Verify counts match
        db_count = system.get_daily_sent_count()
        limiter_count = system.rate_limiter.daily_sent
        
        self.assertEqual(db_count, 3, "Database should show 3 sent")
        self.assertEqual(limiter_count, 3, "Rate limiter should show 3 sent")
        self.assertEqual(db_count, limiter_count, "Counts should match")


if __name__ == '__main__':
    unittest.main()
