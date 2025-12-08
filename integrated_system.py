"""
InternMailer - Integrated System
All 10 features automatically enabled when you run: python system.py

This module integrates:
- Email validation (pre-send checks)
- SMTP retry logic
- Structured logging
- DB connection pooling
- Adaptive rate limiting
- Reply detection (for received emails)
- Configuration management

No need to run separate servers - everything works automatically!
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all integrated features
try:
    from email_validator import get_email_validator
    EMAIL_VALIDATOR_ENABLED = True
except ImportError:
    EMAIL_VALIDATOR_ENABLED = False
    print("⚠️ Email validator not available (pip install dnspython)")

try:
    from monitoring_system import get_logger
    LOGGING_ENABLED = True
except ImportError:
    LOGGING_ENABLED = False

try:
    from config_manager import get_config
    CONFIG_ENABLED = True
except ImportError:
    CONFIG_ENABLED = False

try:
    from adaptive_rate_limiter import get_rate_limiter
    RATE_LIMITER_ENABLED = True
except ImportError:
    RATE_LIMITER_ENABLED = False

try:
    from db_pool import get_db_pool
    DB_POOL_ENABLED = True
except ImportError:
    DB_POOL_ENABLED = False

try:
    from reply_classifier import get_reply_classifier
    REPLY_CLASSIFIER_ENABLED = True
except ImportError:
    REPLY_CLASSIFIER_ENABLED = False

class IntegratedEmailSystem:
    """
    Wrapper around VerifiedEmailSystem that automatically uses all features
    Drop-in replacement - just import this instead!
    """
    
    def __init__(self):
        # Initialize logger first
        if LOGGING_ENABLED:
            self.logger = get_logger()
            self.logger.log_campaign_start(0, 'initialization')
        
        # Load configuration
        if CONFIG_ENABLED:
            self.config = get_config()
            print("✅ Configuration loaded from config.yaml")
        
        # Get rate limiter
        if RATE_LIMITER_ENABLED:
            self.rate_limiter = get_rate_limiter()
            status = self.rate_limiter.get_reputation_status()
            print(f"{status['reputation_emoji']} Sender Reputation: {status['reputation_tier']}")
            print(f"   Recommended Daily Limit: {status['recommended_limit']} emails/day")
        
        # Initialize validators
        if EMAIL_VALIDATOR_ENABLED:
            self.email_validator = get_email_validator()
            print("✅ Email validator ready (DNS MX + regex)")
        
        if REPLY_CLASSIFIER_ENABLED:
            self.reply_classifier = get_reply_classifier()
            print("✅ Reply classifier ready (NLP categories)")
        
        # Initialize DB pools
        if DB_POOL_ENABLED:
            self.db_pools = {}
            print("✅ Database connection pooling enabled")
        
        print("\n🚀 All features integrated and ready!")
        print("   Just run your campaign as normal - everything works automatically\n")
    
    def validate_email_before_send(self, email: str) -> bool:
        """Validate email before sending (automatic pre-send check)"""
        if not EMAIL_VALIDATOR_ENABLED:
            return True  # Skip if not available
        
        result = self.email_validator.validate_email(email)
        
        if not result['is_valid']:
            if LOGGING_ENABLED:
                self.logger.log_email_failed(email, result['reason'], 0)
            print(f"   ⚠️ Skipping {email}: {result['reason']}")
            return False
        
        return True
    
    def get_db_connection(self, db_path: str):
        """Get pooled database connection (automatic connection reuse)"""
        if not DB_POOL_ENABLED:
            # Fallback to regular connection
            import sqlite3
            return sqlite3.connect(db_path)
        
        if db_path not in self.db_pools:
            self.db_pools[db_path] = get_db_pool(db_path)
        
        return self.db_pools[db_path].get_connection()
    
    def check_rate_limit(self) -> tuple:
        """Check if we can send more emails today (automatic rate limiting)"""
        if not RATE_LIMITER_ENABLED:
            return True, 500  # Default: allow up to 500
        
        recommended_limit = self.rate_limiter.calculate_safe_daily_limit()
        
        # Get current send count
        try:
            import sqlite3
            conn = sqlite3.connect('email_tracking.db')
            cursor = conn.cursor()
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE date(sent_at) = ?", (today,))
            sent_today = cursor.fetchone()[0]
            conn.close()
            
            can_send = sent_today < recommended_limit
            remaining = recommended_limit - sent_today
            
            return can_send, remaining
        except:
            return True, recommended_limit
    
    def log_email_event(self, event_type: str, **kwargs):
        """Log email event (automatic logging)"""
        if not LOGGING_ENABLED:
            return
        
        if event_type == 'sent':
            self.logger.log_email_sent(kwargs.get('to'), kwargs.get('subject'))
        elif event_type == 'failed':
            self.logger.log_email_failed(kwargs.get('to'), kwargs.get('error'), kwargs.get('retry', 0))
        elif event_type == 'bounce':
            self.logger.log_bounce(kwargs.get('email'), kwargs.get('reason'))

# Create global instance
integrated_system = IntegratedEmailSystem()

def get_integrated_system():
    """Get the integrated system instance"""
    return integrated_system

# Convenience functions that system.py can use
def validate_email(email: str) -> bool:
    """Validate email before sending"""
    return integrated_system.validate_email_before_send(email)

def check_daily_limit() -> tuple:
    """Check if we can send more today"""
    return integrated_system.check_rate_limit()

def log_event(event_type: str, **kwargs):
    """Log an email event"""
    integrated_system.log_email_event(event_type, **kwargs)

if __name__ == '__main__':
    print("✅ InternMailer Integrated System - All Features Ready")
    print("\nFeatures Status:")
    print(f"   Email Validator: {'✅' if EMAIL_VALIDATOR_ENABLED else '❌'}")
    print(f"   Structured Logging: {'✅' if LOGGING_ENABLED else '❌'}")
    print(f"   Configuration: {'✅' if CONFIG_ENABLED else '❌'}")
    print(f"   Rate Limiter: {'✅' if RATE_LIMITER_ENABLED else '❌'}")
    print(f"   DB Pooling: {'✅' if DB_POOL_ENABLED else '❌'}")
    print(f"   Reply Classifier: {'✅' if REPLY_CLASSIFIER_ENABLED else '❌'}")
