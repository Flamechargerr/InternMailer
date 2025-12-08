"""
InternMailer - Adaptive Rate Limit System
Auto-adjust daily sending limits based on sender reputation
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict

class AdaptiveRateLimiter:
    """
    Dynamically adjust daily sending limits based on:
    - Bounce rate
    - Campaign age (days since first send)
    - Historical success rate
    """
    
    def __init__(self, db_path='campaign_results/advanced_tracking.db'):
        self.db_path = db_path
    
    def get_bounce_rate(self) -> float:
        """Calculate current bounce rate percentage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get bounces in last 30 days
            cursor.execute('''
                SELECT COUNT(*) FROM email_tracking 
                WHERE bounced = 1 AND date(sent_date) > date('now', '-30 days')
            ''')
            bounces = cursor.fetchone()[0] or 0
            
            # Get total sent in last 30 days
            cursor.execute('''
                SELECT COUNT(*) FROM email_tracking 
                WHERE date(sent_date) > date('now', '-30 days')
            ''')
            total = cursor.fetchone()[0] or 1
            
            conn.close()
            
            return (bounces / total * 100) if total > 0 else 0.0
        except:
            return 0.0
    
    def get_campaign_age_days(self) -> int:
        """Get number of days since first email sent"""
        try:
            conn = sqlite3.connect('email_tracking.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT MIN(date(sent_at)) FROM sent_emails")
            first_send_date = cursor.fetchone()[0]
            
            conn.close()
            
            if first_send_date:
                first = datetime.strptime(first_send_date, '%Y-%m-%d')
                age = (datetime.now() - first).days
                return max(age, 1)  # Minimum 1 day
            
            return 1
        except:
            return 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate (non-bounced emails) percentage"""
        bounce_rate = self.get_bounce_rate()
        return 100.0 - bounce_rate
    
    def calculate_safe_daily_limit(self) -> int:
        """
        Calculate recommended daily sending limit based on reputation
        
        Returns:
            Recommended daily limit (10 to 500)
        """
        bounce_rate = self.get_bounce_rate()
        campaign_age = self.get_campaign_age_days()
        success_rate = self.get_success_rate()
        
        # Base limit on campaign age (warmup progression)
        if campaign_age <= 3:
            base_limit = 20
        elif campaign_age <= 7:
            base_limit = 50
        elif campaign_age <= 14:
            base_limit = 100
        elif campaign_age <= 30:
            base_limit = 200
        else:
            base_limit = 500  # Mature campaign
        
        # Adjust based on bounce rate
        if bounce_rate < 1.0:
            # Excellent reputation - can send more
            multiplier = 1.5
        elif bounce_rate < 2.0:
            # Good reputation
            multiplier = 1.2
        elif bounce_rate < 3.0:
            # Acceptable
            multiplier = 1.0
        elif bounce_rate < 5.0:
            # Warning - reduce sends
            multiplier = 0.7
        else:
            # High bounce rate - aggressive reduction
            multiplier = 0.3
        
        # Calculate final limit
        recommended_limit = int(base_limit * multiplier)
        
        # Clamp between 10 and 500
        recommended_limit = max(10, min(500, recommended_limit))
        
        return recommended_limit
    
    def get_reputation_status(self) -> Dict:
        """
        Get comprehensive reputation status
        
        Returns:
            {
                'bounce_rate': float,
                'success_rate': float,
                'campaign_age_days': int,
                'recommended_limit': int,
                'reputation_tier': str,
                'status_message': str
            }
        """
        bounce_rate = self.get_bounce_rate()
        success_rate = self.get_success_rate()
        campaign_age = self.get_campaign_age_days()
        recommended_limit = self.calculate_safe_daily_limit()
        
        # Determine reputation tier
        if bounce_rate < 1.0 and campaign_age > 30:
            tier = "EXCELLENT"
            emoji = "🌟"
            message = "Perfect sender reputation! Maximum sending capacity unlocked."
        elif bounce_rate < 2.0 and campaign_age > 14:
            tier = "GOOD"
            emoji = "✅"
            message = "Strong sender reputation. Can increase volume safely."
        elif bounce_rate < 3.0:
            tier = "ACCEPTABLE"
            emoji = "👍"
            message = "Maintaining healthy sender reputation."
        elif bounce_rate < 5.0:
            tier = "WARNING"
            emoji = "⚠️"
            message = "Bounce rate elevated. Reduce volume and improve targeting."
        else:
            tier = "CRITICAL"
            emoji = "🚨"
            message = "High bounce rate detected! Immediate action required."
        
        return {
            'bounce_rate': round(bounce_rate, 2),
            'success_rate': round(success_rate, 2),
            'campaign_age_days': campaign_age,
            'recommended_limit': recommended_limit,
            'reputation_tier': tier,
            'reputation_emoji': emoji,
            'status_message': message
        }

# Singleton instance
_rate_limiter_instance = None

def get_rate_limiter() -> AdaptiveRateLimiter:
    """Get singleton rate limiter"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = AdaptiveRateLimiter()
    return _rate_limiter_instance

# Example usage
if __name__ == '__main__':
    limiter = get_rate_limiter()
    status = limiter.get_reputation_status()
    
    print(f"{status['reputation_emoji']} Sender Reputation: {status['reputation_tier']}\n")
    print(f"Bounce Rate: {status['bounce_rate']}%")
    print(f"Success Rate: {status['success_rate']}%")
    print(f"Campaign Age: {status['campaign_age_days']} days")
    print(f"Recommended Daily Limit: {status['recommended_limit']} emails/day")
    print(f"\n{status['status_message']}")
