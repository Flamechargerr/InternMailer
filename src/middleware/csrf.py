"""
CSRF Protection - Cross-Site Request Forgery protection
Secure form submissions and API requests
"""

import secrets
import hmac
import hashlib
from typing import Optional, Callable, Any
from functools import wraps
from flask import Flask, request, session, g, current_app
from flask_wtf.csrf import CSRFProtect

from utils.logger import get_logger


class CSRFProtection:
    """
    Custom CSRF protection for Flask applications
    """
    
    def __init__(self, app: Flask = None, secret_key: Optional[str] = None):
        """
        Initialize CSRF protection
        
        Args:
            app: Flask application (optional)
            secret_key: Secret key for CSRF tokens (optional, uses app.secret_key)
        """
        self.secret_key = secret_key
        self.logger = get_logger('csrf')
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CSRF protection with Flask app"""
        self.secret_key = app.secret_key
        
        # Add before request handler
        app.before_request(self._validate_csrf)
        
        # Add CSRF token to context
        app.context_processor(self._csrf_context)
        
        self.logger.info("CSRF protection initialized")
    
    def _csrf_context(self) -> dict:
        """Add CSRF token to template context"""
        return {
            'csrf_token': self.generate_token(),
            'csrf_token_input': self.generate_token_input()
        }
    
    def generate_token(self) -> str:
        """Generate CSRF token"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    def generate_token_input(self) -> str:
        """Generate HTML input field for CSRF token"""
        token = self.generate_token()
        return f'<input type="hidden" name="csrf_token" value="{token}">'
    
    def _validate_csrf(self):
        """Validate CSRF token on each request"""
        # Skip if exempt flag is set
        if getattr(g, 'csrf_exempt', False):
            return
        
        # Skip validation for safe methods
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return
        
        # Skip validation for API endpoints (they use different auth)
        if request.path.startswith('/api/'):
            return
        
        # Skip validation for dashboard action endpoints
        exempt_paths = ['/send-emails', '/preview-emails', '/api/daemon/start', '/api/daemon/stop']
        if request.path in exempt_paths:
            return
        
        # Get token from request
        token = self._get_token_from_request()
        
        if not token:
            self.logger.warning(f"CSRF token missing for {request.path}")
            from flask import abort
            abort(403, description="CSRF token missing")
        
        # Validate token
        if not self._validate_token(token):
            self.logger.warning(f"CSRF token invalid for {request.path}")
            from flask import abort
            abort(403, description="CSRF token invalid")
    
    def _get_token_from_request(self) -> Optional[str]:
        """Get CSRF token from request"""
        # Check form data
        token = request.form.get('csrf_token')
        if token:
            return token
        
        # Check JSON body
        if request.is_json:
            data = request.get_json()
            if data and 'csrf_token' in data:
                return data['csrf_token']
        
        # Check headers
        token = request.headers.get('X-CSRF-Token')
        if token:
            return token
        
        return None
    
    def _validate_token(self, token: str) -> bool:
        """Validate CSRF token"""
        stored_token = session.get('csrf_token')
        
        if not stored_token:
            return False
        
        # Use constant-time comparison
        return hmac.compare_digest(token, stored_token)
    
    def exempt(self, view_func: Callable) -> Callable:
        """
        Decorator to exempt view from CSRF validation
        
        Usage:
            @csrf.exempt
            @app.route('/api/webhook')
            def webhook():
                pass
        """
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            g.csrf_exempt = True
            return view_func(*args, **kwargs)
        
        return wrapper


def csrf_protect(secret_key: Optional[str] = None):
    """
    Decorator for CSRF protection on individual routes
    
    Usage:
        @app.route('/api/send', methods=['POST'])
        @csrf_protect()
        def send_email():
            pass
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # Skip if exempt
            if getattr(g, 'csrf_exempt', False):
                return view_func(*args, **kwargs)
            
            # Validate CSRF token
            token = request.form.get('csrf_token') or \
                   (request.get_json().get('csrf_token') if request.is_json else None)
            
            if not token:
                from flask import abort, jsonify
                response = jsonify({'error': 'CSRF token required'})
                response.status_code = 403
                return response
            
            stored_token = session.get('csrf_token')
            
            if not stored_token or not hmac.compare_digest(token, stored_token):
                from flask import abort, jsonify
                response = jsonify({'error': 'Invalid CSRF token'})
                response.status_code = 403
                return response
            
            return view_func(*args, **kwargs)
        
        return wrapper
    return decorator


def init_csrf(app: Flask, secret_key: Optional[str] = None) -> CSRFProtection:
    """
    Initialize CSRF protection for Flask app
    
    Args:
        app: Flask application
        secret_key: Optional secret key
        
    Returns:
        CSRFProtection instance
    """
    csrf = CSRFProtection(app, secret_key)
    return csrf
