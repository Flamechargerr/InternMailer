"""
Rate Limiting Middleware - API rate limiting
Protects against abuse and ensures fair usage
"""

import time
import hashlib
import json
from collections import defaultdict
from typing import Dict, List, Optional, Callable, Any, Union
from functools import wraps
from flask import request, jsonify, g

from utils.logger import get_logger
from utils.exceptions import RateLimitError


class RateLimiter:
    """
    In-memory rate limiter for API endpoints
    Supports sliding window and token bucket algorithms
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            requests_per_day: Max requests per day
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        # Track requests: {identifier: [(timestamp, count)]}
        self._requests: Dict[str, List[tuple]] = defaultdict(list)
        
        self.logger = get_logger('rate_limiter')
    
    def _get_identifier(self, request_obj: Any) -> str:
        """Get unique identifier for request"""
        # Use IP address + user agent
        ip = request_obj.remote_addr or 'unknown'
        user_agent = request_obj.headers.get('User-Agent', '')
        
        identifier = f"{ip}:{user_agent}"
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def _clean_old_requests(self, identifier: str, max_age: float):
        """Remove requests older than max_age seconds"""
        current_time = time.time()
        
        requests = self._requests[identifier]
        self._requests[identifier] = [
            (ts, count) for ts, count in requests 
            if current_time - ts <= max_age
        ]
    
    def _get_count_in_window(self, identifier: str, window_seconds: float) -> int:
        """Get count of requests within time window"""
        current_time = time.time()
        
        requests = self._requests[identifier]
        return sum(
            count for ts, count in requests 
            if current_time - ts <= window_seconds
        )
    
    def _record_request(self, identifier: str, count: int = 1):
        """Record a request"""
        current_time = time.time()
        self._requests[identifier].append((current_time, count))
    
    def is_allowed(self, request_obj: Any) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed
        
        Returns:
            Tuple of (is_allowed, rate_info)
        """
        identifier = self._get_identifier(request_obj)
        
        # Clean old requests
        self._clean_old_requests(identifier, 86400)  # 24 hours
        
        # Check rate limits
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        minute_count = sum(
            count for ts, count in self._requests[identifier] 
            if ts >= minute_ago
        )
        
        hour_count = sum(
            count for ts, count in self._requests[identifier] 
            if ts >= hour_ago
        )
        
        day_count = sum(
            count for ts, count in self._requests[identifier] 
            if ts >= day_ago
        )
        
        rate_info: Dict[str, Any] = {
            'minute_count': minute_count,
            'minute_limit': self.requests_per_minute,
            'hour_count': hour_count,
            'hour_limit': self.requests_per_hour,
            'day_count': day_count,
            'day_limit': self.requests_per_day
        }
        
        # Check if any limit exceeded
        if minute_count >= self.requests_per_minute:
            rate_info['limit_type'] = 'minute'
            rate_info['retry_after'] = 60
            return False, rate_info
        
        if hour_count >= self.requests_per_hour:
            rate_info['limit_type'] = 'hour'
            rate_info['retry_after'] = 3600
            return False, rate_info
        
        if day_count >= self.requests_per_day:
            rate_info['limit_type'] = 'day'
            rate_info['retry_after'] = 86400
            return False, rate_info
        
        # Record request
        self._record_request(identifier)
        
        return True, rate_info
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self._requests:
            del self._requests[identifier]


class TokenBucketRateLimiter:
    """
    Token bucket algorithm for smoother rate limiting
    """
    
    def __init__(
        self,
        rate: int = 60,  # tokens per minute
        burst: int = 100  # maximum burst
    ):
        """
        Initialize token bucket
        
        Args:
            rate: Tokens added per second (rate / 60)
            burst: Maximum bucket size
        """
        self.rate = rate / 60.0  # tokens per second
        self.burst = burst
        
        # Track buckets: {identifier: {'tokens': float, 'last_update': float}}
        self._buckets: Dict[str, Dict[str, float]] = {}
        
        self.logger = get_logger('token_bucket_limiter')
    
    def _get_identifier(self, request_obj: Any) -> str:
        """Get unique identifier for request"""
        ip = request_obj.remote_addr or 'unknown'
        path = request_obj.path or '/'
        return f"{ip}:{path}"
    
    def is_allowed(self, request_obj: Any) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed using token bucket
        
        Returns:
            Tuple of (is_allowed, bucket_info)
        """
        identifier = self._get_identifier(request_obj)
        current_time = time.time()
        
        # Get or create bucket
        if identifier not in self._buckets:
            self._buckets[identifier] = {
                'tokens': float(self.burst),
                'last_update': current_time
            }
        
        bucket = self._buckets[identifier]
        
        # Add tokens based on time passed
        time_passed = current_time - bucket['last_update']
        bucket['tokens'] = min(
            bucket['tokens'] + time_passed * self.rate,
            self.burst
        )
        bucket['last_update'] = current_time
        
        # Check if we have enough tokens
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            rate_info: Dict[str, Any] = {
                'tokens_available': bucket['tokens'],
                'burst': self.burst,
                'rate': self.rate * 60  # per minute
            }
            return True, rate_info
        else:
            # Calculate time until next token
            tokens_needed = 1 - bucket['tokens']
            retry_after = tokens_needed / self.rate
            
            rate_info: Dict[str, Any] = {
                'tokens_available': bucket['tokens'],
                'burst': self.burst,
                'rate': self.rate * 60,
                'retry_after': int(retry_after)
            }
            return False, rate_info
    
    def reset(self, identifier: str):
        """Reset bucket for identifier"""
        if identifier in self._buckets:
            del self._buckets[identifier]


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    requests_per_day: int = 10000,
    limiter_type: str = 'sliding'  # 'sliding' or 'token_bucket'
):
    """
    Decorator for rate limiting Flask routes
    
    Usage:
        @app.route('/api/emails', methods=['POST'])
        @rate_limit(requests_per_minute=30)
        def send_emails():
            pass
    """
    def decorator(func):
        # Initialize limiter
        if limiter_type == 'token_bucket':
            limiter = TokenBucketRateLimiter(
                rate=requests_per_minute,
                burst=requests_per_minute * 2
            )
        else:
            limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
                requests_per_day=requests_per_day
            )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if exempt
            if getattr(g, 'rate_limit_exempt', False):
                return func(*args, **kwargs)
            
            # Check rate limit
            is_allowed, rate_info = limiter.is_allowed(request)
            
            if not is_allowed:
                # Add rate limit headers
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': rate_info.get('retry_after', 60),
                    'limits': {
                        'per_minute': requests_per_minute,
                        'per_hour': requests_per_hour,
                        'per_day': requests_per_day
                    }
                })
                
                response.status_code = 429
                response.headers['Retry-After'] = str(rate_info.get('retry_after', 60))
                response.headers['X-RateLimit-Limit'] = str(requests_per_minute)
                
                minute_count = rate_info.get('minute_count', 0)
                remaining = max(0, requests_per_minute - minute_count)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(
                    int(time.time() + 60)
                )
                
                return response
            
            # Add rate limit info headers
            g.rate_info = rate_info
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class IPWhitelist:
    """IP whitelist for bypassing rate limits"""
    
    def __init__(self, whitelist: Optional[List[str]] = None):
        """
        Initialize IP whitelist
        
        Args:
            whitelist: List of whitelisted IP addresses or CIDR ranges
        """
        self.whitelist = set(whitelist or [])
    
    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        # Exact match
        if ip in self.whitelist:
            return True
        
        # CIDR match (simplified)
        for whitelisted_ip in self.whitelist:
            if '/' in whitelisted_ip:
                # CIDR notation
                if self._ip_in_cidr(ip, whitelisted_ip):
                    return True
        
        return False
    
    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """Check if IP is in CIDR range (simplified)"""
        try:
            import ipaddress
            network = ipaddress.ip_network(cidr, strict=False)
            addr = ipaddress.ip_address(ip)
            return addr in network
        except:
            return False


def rate_limit_exempt(func):
    """
    Decorator to exempt route from rate limiting
    
    Usage:
        @app.route('/api/health')
        @rate_limit_exempt
        def health_check():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        g.rate_limit_exempt = True
        return func(*args, **kwargs)
    
    return wrapper
