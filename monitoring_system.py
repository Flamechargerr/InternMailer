"""
InternMailer - Monitoring & Logging System
Structured JSON logging with alert triggers
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
import os

class StructuredLogger:
    """
    JSON-based structured logging for better debugging and monitoring
    """
    
    def __init__(self, log_file='campaign_logs/application.log', level=logging.INFO):
        self.logger = logging.getLogger('InternMailer')
        self.logger.setLevel(level)
        
        # Create logs directory
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler - JSON format
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter('%(message)s'))
        
        # Console handler - human readable
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)  # Only warnings/errors to console
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # Alert thresholds
        self.bounce_rate_threshold = 3.0  # %
        self.daily_limit_threshold = 450
        self.error_count_threshold = 10  # errors in 1 hour
    
    def _create_log_entry(self, event_type: str, data: Dict[str, Any], level: str = 'info') -> str:
        """Create structured JSON log entry"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'event_type': event_type,
            'data': data
        }
        return json.dumps(entry)
    
    def log_email_sent(self, to: str, subject: str, template: str = ''):
        """Log successful email send"""
        entry = self._create_log_entry('email_sent', {
            'to': to,
            'subject': subject,
            'template': template
        })
        self.logger.info(entry)
    
    def log_email_failed(self, to: str, error: str, retry_count: int = 0):
        """Log failed email send"""
        entry = self._create_log_entry('email_failed', {
            'to': to,
            'error': str(error),
            'retry_count': retry_count
        }, level='error')
        self.logger.error(entry)
        
        # Alert if too many failures
        if retry_count >= 3:
            self.trigger_alert('smtp_failure', f"Failed to send to {to} after {retry_count} retries")
    
    def log_bounce(self, email: str, reason: str):
        """Log email bounce"""
        entry = self._create_log_entry('bounce', {
            'email': email,
            'reason': reason
        }, level='warning')
        self.logger.warning(entry)
    
    def log_reply_received(self, from_email: str, category: str, sentiment: float):
        """Log categorized reply"""
        entry = self._create_log_entry('reply_received', {
            'from': from_email,
            'category': category,
            'sentiment': sentiment
        })
        self.logger.info(entry)
    
    def log_campaign_start(self, count: int, mode: str):
        """Log campaign start"""
        entry = self._create_log_entry('campaign_start', {
            'email_count': count,
            'mode': mode
        })
        self.logger.info(entry)
    
    def log_campaign_complete(self, sent: int, failed: int, duration_seconds: float):
        """Log campaign completion"""
        success_rate = (sent / (sent + failed) * 100) if (sent + failed) > 0 else 0
        
        entry = self._create_log_entry('campaign_complete', {
            'emails_sent': sent,
            'emails_failed': failed,
            'success_rate': success_rate,
            'duration_seconds': duration_seconds
        })
        self.logger.info(entry)
        
        # Alert if success rate too low
        if success_rate < 90 and sent + failed > 10:
            self.trigger_alert('low_success_rate', f"Success rate: {success_rate:.1f}%")
    
    def log_daily_limit_reached(self, current_count: int, limit: int):
        """Log daily limit reached"""
        entry = self._create_log_entry('daily_limit_reached', {
            'current_count': current_count,
            'limit': limit
        }, level='warning')
        self.logger.warning(entry)
        
        self.trigger_alert('daily_limit', f"Reached daily limit: {current_count}/{limit}")
    
    def trigger_alert(self, alert_type: str, message: str):
        """Trigger monitoring alert"""
        entry = self._create_log_entry('alert', {
            'alert_type': alert_type,
            'message': message
        }, level='critical')
        self.logger.critical(entry)
        
        # In production, this would integrate with:
        # - Email notifications
        # - Slack/Discord webhooks
        # - PagerDuty/monitoring tools
        print(f"🚨 ALERT [{alert_type}]: {message}")
    
    def get_recent_logs(self, count: int = 100) -> List[Dict]:
        """Get recent log entries (for dashboard)"""
        # Would parse log file in production
        return []

# Singleton instance
_logger_instance = None

def get_logger():
    """Get singleton logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger()
    return _logger_instance
