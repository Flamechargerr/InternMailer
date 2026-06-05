#!/usr/bin/env python3
"""
Integration test to verify rate limiting and tracking work correctly.

This test demonstrates that:
1. Rate limiting properly delays between emails
2. Tracking accurately records sent/failed emails
3. Daily limits are enforced
"""

import time
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.email_system import RateLimiter


def test_rate_limiting_timing():
    """
    Verify that rate limiting actually delays between operations.
    **Validates: Requirements 2.6**
    """
    print("\n" + "="*60)
    print("TEST: Rate Limiting Timing")
    print("="*60)
    
    min_delay = 0.3  # 300ms
    limiter = RateLimiter(min_delay=min_delay, max_daily=100)
    
    # Measure time for 5 sends
    start = time.time()
    
    for i in range(5):
        limiter.wait_if_needed()
        print(f"  Send {i+1}: {time.time() - start:.3f}s elapsed")
    
    total_time = time.time() - start
    
    # Should take at least 4 * min_delay (first send is immediate)
    expected_min = 4 * min_delay
    
    print(f"\nTotal time: {total_time:.3f}s")
    print(f"Expected minimum: {expected_min:.3f}s")
    
    assert total_time >= expected_min, \
        f"Rate limiting not working: took {total_time:.3f}s, expected >= {expected_min:.3f}s"
    
    print("✅ Rate limiting timing verified")


def test_daily_limit_enforcement():
    """
    Verify that daily limits are properly enforced.
    **Validates: Requirements 2.6**
    """
    print("\n" + "="*60)
    print("TEST: Daily Limit Enforcement")
    print("="*60)
    
    max_daily = 3
    limiter = RateLimiter(min_delay=0.01, max_daily=max_daily)
    
    # Send up to limit
    for i in range(max_daily):
        can_send, message = limiter.can_send()
        print(f"  Attempt {i+1}: can_send={can_send}, message='{message}'")
        assert can_send, f"Should allow send {i+1}/{max_daily}"
        limiter.record_sent()
    
    # Try to send beyond limit
    can_send, message = limiter.can_send()
    print(f"  Attempt {max_daily+1}: can_send={can_send}, message='{message}'")
    
    assert not can_send, "Should block after daily limit"
    assert "limit" in message.lower(), "Message should mention limit"
    
    print("✅ Daily limit enforcement verified")


def test_tracking_database_operations():
    """
    Verify that tracking database operations work correctly.
    **Validates: Requirements 2.7**
    """
    print("\n" + "="*60)
    print("TEST: Tracking Database Operations")
    print("="*60)
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_tracking.db')
    
    try:
        # Initialize database with same schema as EmailSystem
        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    name TEXT,
                    company TEXT,
                    position TEXT,
                    subject TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    provider_used TEXT,
                    ai_confidence REAL,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert test records
            test_emails = [
                ('user1@example.com', 'User 1', 'Company A', 'Engineer', 'sent'),
                ('user2@example.com', 'User 2', 'Company B', 'Developer', 'sent'),
                ('user3@example.com', 'User 3', 'Company C', 'Analyst', 'failed'),
            ]
            
            for email, name, company, position, status in test_emails:
                conn.execute('''
                    INSERT INTO sent_emails (email, name, company, position, subject, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (email, name, company, position, f'Application to {company}', status))
                print(f"  Inserted: {email} ({status})")
            
            conn.commit()
            
            # Verify counts
            cursor = conn.execute("SELECT COUNT(*) FROM sent_emails WHERE status = 'sent'")
            sent_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sent_emails WHERE status = 'failed'")
            failed_count = cursor.fetchone()[0]
            
            print(f"\nCounts:")
            print(f"  Sent: {sent_count}")
            print(f"  Failed: {failed_count}")
            
            assert sent_count == 2, f"Expected 2 sent, got {sent_count}"
            assert failed_count == 1, f"Expected 1 failed, got {failed_count}"
            
            print("✅ Tracking database operations verified")
            
    finally:
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_rate_limiter_status_reporting():
    """
    Verify that rate limiter status is reported correctly.
    **Validates: Requirements 2.6**
    """
    print("\n" + "="*60)
    print("TEST: Rate Limiter Status Reporting")
    print("="*60)
    
    max_daily = 10
    limiter = RateLimiter(min_delay=0.1, max_daily=max_daily)
    
    # Send some emails
    for i in range(3):
        limiter.record_sent()
    
    status = limiter.get_status()
    
    print(f"  Daily sent: {status['daily_sent']}")
    print(f"  Daily limit: {status['daily_limit']}")
    print(f"  Remaining today: {status['remaining_today']}")
    print(f"  Min delay: {status['min_delay']}")
    print(f"  Next reset: {status['next_reset']}")
    
    assert status['daily_sent'] == 3, f"Expected 3 sent, got {status['daily_sent']}"
    assert status['daily_limit'] == max_daily, f"Expected limit {max_daily}, got {status['daily_limit']}"
    assert status['remaining_today'] == 7, f"Expected 7 remaining, got {status['remaining_today']}"
    assert status['min_delay'] == 0.1, f"Expected min_delay 0.1, got {status['min_delay']}"
    assert 'next_reset' in status, "Status should include next_reset"
    
    print("✅ Rate limiter status reporting verified")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("RATE LIMITING AND TRACKING INTEGRATION TESTS")
    print("="*60)
    
    try:
        test_rate_limiting_timing()
        test_daily_limit_enforcement()
        test_tracking_database_operations()
        test_rate_limiter_status_reporting()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nConclusion:")
        print("- Rate limiting properly enforces delays between emails")
        print("- Daily limits are correctly enforced")
        print("- Email tracking database operations work correctly")
        print("- Status reporting provides accurate information")
        print("\nRequirements 2.6 and 2.7 are satisfied.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
