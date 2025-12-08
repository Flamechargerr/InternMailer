"""
InternMailer - Free Email Validator
No API costs - Uses regex + DNS MX record validation
"""

import re
import dns.resolver
from typing import Tuple, Dict
import sqlite3
from datetime import datetime, timedelta

class FreeEmailValidator:
    """
    Free email validation without external APIs
    - Regex pattern matching
    - DNS MX record verification
    - Disposable email domain detection
    - Cache results to avoid repeated DNS queries
    """
    
    def __init__(self, cache_db='campaign_results/email_validation_cache.db'):
        self.cache_db = cache_db
        self._setup_cache()
        
        # Common disposable email domains (free list)
        self.disposable_domains = {
            'guerrillamail.com', 'mailinator.com', 'tempmail.com', '10minutemail.com',
            'throwaway.email', 'temp-mail.org', 'trashmail.com', 'fakeinbox.com',
            'sharklasers.com', 'yopmail.com', 'mintemail.com', 'maildrop.cc'
        }
        
        # Common role-based emails to avoid
        self.role_based = {
            'admin', 'info', 'support', 'noreply', 'no-reply', 'sales',
            'contact', 'help', 'webmaster', 'postmaster', 'abuse'
        }
    
    def _setup_cache(self):
        """Create cache database for validation results"""
        import os
        os.makedirs(os.path.dirname(self.cache_db), exist_ok=True)
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_cache (
                email TEXT PRIMARY KEY,
                is_valid INTEGER,
                reason TEXT,
                has_mx INTEGER,
                is_disposable INTEGER,
                checked_date TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _check_cache(self, email: str) -> Dict:
        """Check if email was validated recently (cache for 30 days)"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_valid, reason, has_mx, is_disposable, checked_date
            FROM validation_cache
            WHERE email = ? AND date(checked_date) > date('now', '-30 days')
        ''', (email.lower(),))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'email': email,
                'is_valid': bool(result[0]),
                'reason': result[1],
                'has_mx': bool(result[2]),
                'is_disposable': bool(result[3]),
                'cached': True
            }
        return None
    
    def _save_to_cache(self, email: str, result: Dict):
        """Save validation result to cache"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO validation_cache
            (email, is_valid, reason, has_mx, is_disposable, checked_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            email.lower(),
            int(result['is_valid']),
            result['reason'],
            int(result['has_mx']),
            int(result['is_disposable']),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def validate_format(self, email: str) -> Tuple[bool, str]:
        """Validate email format using regex"""
        # RFC 5322 compliant regex (simplified)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check length
        if len(email) > 254:
            return False, "Email too long"
        
        local, domain = email.rsplit('@', 1)
        
        # Check local part
        if len(local) > 64:
            return False, "Local part too long"
        
        # Check for role-based emails
        if local.lower() in self.role_based:
            return False, f"Role-based email ({local})"
        
        return True, "Format valid"
    
    def check_mx_records(self, domain: str) -> Tuple[bool, str]:
        """Check if domain has valid MX records (free DNS query)"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                return True, f"Valid MX records ({len(mx_records)} found)"
            return False, "No MX records found"
        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except dns.resolver.NoAnswer:
            return False, "No MX records"
        except dns.resolver.Timeout:
            return False, "DNS timeout"
        except Exception as e:
            return False, f"DNS error: {str(e)}"
    
    def is_disposable_email(self, domain: str) -> bool:
        """Check if domain is a known disposable email provider"""
        return domain.lower() in self.disposable_domains
    
    def validate_email(self, email: str) -> Dict:
        """
        Complete email validation
        Returns: {
            'email': str,
            'is_valid': bool,
            'reason': str,
            'has_mx': bool,
            'is_disposable': bool,
            'confidence': float  # 0.0 to 1.0
        }
        """
        # Check cache first
        cached = self._check_cache(email)
        if cached:
            return cached
        
        result = {
            'email': email,
            'is_valid': False,
            'reason': '',
            'has_mx': False,
            'is_disposable': False,
            'confidence': 0.0,
            'cached': False
        }
        
        # Step 1: Format validation
        format_valid, format_reason = self.validate_format(email)
        if not format_valid:
            result['reason'] = format_reason
            self._save_to_cache(email, result)
            return result
        
        # Extract domain
        domain = email.rsplit('@', 1)[1]
        
        # Step 2: Check if disposable
        if self.is_disposable_email(domain):
            result['is_disposable'] = True
            result['reason'] = "Disposable email domain"
            result['confidence'] = 0.1
            self._save_to_cache(email, result)
            return result
        
        # Step 3: MX record validation
        has_mx, mx_reason = self.check_mx_records(domain)
        result['has_mx'] = has_mx
        
        if not has_mx:
            result['reason'] = mx_reason
            result['confidence'] = 0.2
            self._save_to_cache(email, result)
            return result
        
        # Email passed all checks
        result['is_valid'] = True
        result['reason'] = "Valid email (format + MX verified)"
        result['confidence'] = 0.9
        self._save_to_cache(email, result)
        
        return result
    
    def validate_bulk(self, emails: list) -> Dict[str, Dict]:
        """Validate multiple emails efficiently"""
        results = {}
        for email in emails:
            results[email] = self.validate_email(email)
        return results
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics from cache"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM validation_cache")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM validation_cache WHERE is_valid = 1")
        valid = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM validation_cache WHERE is_disposable = 1")
        disposable = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_checked': total,
            'valid': valid,
            'invalid': total - valid,
            'disposable': disposable,
            'valid_rate': (valid / total * 100) if total > 0 else 0
        }

# Singleton instance
_validator_instance = None

def get_email_validator():
    """Get singleton email validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = FreeEmailValidator()
    return _validator_instance

# Example usage
if __name__ == '__main__':
    validator = get_email_validator()
    
    # Test cases
    test_emails = [
        'valid.email@university.edu',
        'invalid-email',
        'test@tempmail.com',  # Disposable
        'admin@example.com',  # Role-based
        'user@nonexistent-domain-xyz123.com'
    ]
    
    print("🔍 Email Validation Test Results:\n")
    for email in test_emails:
        result = validator.validate_email(email)
        status = "✅ VALID" if result['is_valid'] else "❌ INVALID"
        print(f"{status} | {email}")
        print(f"   Reason: {result['reason']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   MX Records: {'Yes' if result['has_mx'] else 'No'}")
        print(f"   Disposable: {'Yes' if result['is_disposable'] else 'No'}")
        print()
    
    # Show stats
    stats = validator.get_validation_stats()
    print(f"📊 Validation Statistics:")
    print(f"   Total Checked: {stats['total_checked']}")
    print(f"   Valid: {stats['valid']} ({stats['valid_rate']:.1f}%)")
    print(f"   Invalid: {stats['invalid']}")
    print(f"   Disposable: {stats['disposable']}")
