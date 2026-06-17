"""
Health Check and Monitoring - System health and monitoring endpoints
Provides health checks and system status information
"""

import os
import sys
import time
import psutil
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from functools import wraps

from flask import jsonify
from core.database_manager import (
    get_email_tracking_db,
    get_inbox_monitor_db,
    get_daemon_status_db,
    get_job_discovery_db,
)
from utils.logger import get_logger


class HealthChecker:
    """
    Health check system for monitoring application status
    """
    
    def __init__(self):
        self.logger = get_logger('health_checker')
        self.checks: Dict[str, Callable] = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check('database', self._check_database)
        self.register_check('disk_space', self._check_disk_space)
        self.register_check('memory', self._check_memory)
        self.register_check('cpu', self._check_cpu)
        self.register_check('dependencies', self._check_dependencies)
        self.register_check('configuration', self._check_configuration)
    
    def register_check(self, name: str, check_func: Callable):
        """
        Register a custom health check
        
        Args:
            name: Name of the health check
            check_func: Function that returns check result
        """
        self.checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """
        Run a specific health check
        
        Args:
            name: Name of the check to run
            
        Returns:
            Check result with status and details
        """
        if name not in self.checks:
            return {
                'status': 'unknown',
                'message': f"Check '{name}' not registered"
            }
        
        try:
            result = self.checks[name]()
            return {
                'status': 'pass',
                'timestamp': datetime.now().isoformat(),
                **result
            }
        except Exception as e:
            self.logger.error(f"Health check '{name}' failed: {str(e)}", exc_info=True)
            return {
                'status': 'fail',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all registered health checks
        
        Returns:
            Overall health status
        """
        results = {}
        overall_status = 'pass'
        has_warnings = False
        
        for name in self.checks:
            results[name] = self.run_check(name)
            status = results[name]['status']
            
            if status == 'fail':
                overall_status = 'fail'
            elif status == 'warn':
                has_warnings = True
        
        # Only downgrade to warn if not already failed
        if overall_status != 'fail' and has_warnings:
            overall_status = 'warn'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and integrity"""
        results = {
            'email_tracking': {'status': 'unknown'},
            'inbox_monitor': {'status': 'unknown'},
            'daemon_status': {'status': 'unknown'},
            'job_discovery': {'status': 'unknown'}
        }
        
        # Check email tracking database
        try:
            db = get_email_tracking_db()
            stats = db.get_stats()
            results['email_tracking'] = {
                'status': 'pass',
                'size_mb': round(stats['size_mb'], 2),
                'tables': len(stats['tables'])
            }
        except Exception as e:
            results['email_tracking'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        # Check inbox monitor database
        try:
            db = get_inbox_monitor_db()
            stats = db.get_stats()
            results['inbox_monitor'] = {
                'status': 'pass',
                'size_mb': round(stats['size_mb'], 2),
                'tables': len(stats['tables'])
            }
        except Exception as e:
            results['inbox_monitor'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        # Check daemon status database
        try:
            db = get_daemon_status_db()
            stats = db.get_stats()
            results['daemon_status'] = {
                'status': 'pass',
                'size_mb': round(stats['size_mb'], 2),
                'tables': len(stats['tables'])
            }
        except Exception as e:
            results['daemon_status'] = {
                'status': 'fail',
                'error': str(e)
            }

        # Check job discovery database
        try:
            db = get_job_discovery_db()
            stats = db.get_stats()
            results['job_discovery'] = {
                'status': 'pass',
                'size_mb': round(stats['size_mb'], 2),
                'tables': len(stats['tables'])
            }
        except Exception as e:
            results['job_discovery'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        return results
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            
            free_gb = disk.free / (1024 ** 3)
            total_gb = disk.total / (1024 ** 3)
            used_percent = (disk.used / disk.total) * 100
            
            status = 'pass' if used_percent < 90 else 'warn'
            if used_percent > 95:
                status = 'fail'
            
            return {
                'status': status,
                'total_gb': round(total_gb, 2),
                'used_gb': round(disk.used / (1024 ** 3), 2),
                'free_gb': round(free_gb, 2),
                'used_percent': round(used_percent, 2)
            }
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            mem = psutil.virtual_memory()
            
            status = 'pass' if mem.percent < 80 else 'warn'
            if mem.percent > 90:
                status = 'fail'
            
            return {
                'status': status,
                'total_mb': round(mem.total / (1024 ** 2), 2),
                'used_mb': round(mem.used / (1024 ** 2), 2),
                'free_mb': round(mem.available / (1024 ** 2), 2),
                'used_percent': mem.percent
            }
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }
    
    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            status = 'pass' if cpu_percent < 70 else 'warn'
            if cpu_percent > 90:
                status = 'fail'
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count()
            }
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies"""
        results = {
            'python_version': {
                'status': 'pass',
                'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            },
            'packages': {}
        }
        
        # Check required packages (package_name: import_name)
        required_packages = {
            'flask': 'flask',
            'requests': 'requests',
            'beautifulsoup4': 'bs4',
            'dnspython': 'dns',
            'schedule': 'schedule'
        }
        
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                results['packages'][package_name] = {
                    'status': 'pass',
                    'version': 'installed'
                }
            except ImportError:
                results['packages'][package_name] = {
                    'status': 'fail',
                    'version': 'not installed'
                }
        
        # Check optional packages
        optional_packages = ['smtplib', 'imaplib']
        for package in optional_packages:
            try:
                __import__(package)
                results['packages'][package] = {
                    'status': 'pass',
                    'version': 'available'
                }
            except ImportError:
                results['packages'][package] = {
                    'status': 'warn',
                    'version': 'not available'
                }
        
        # Check if all required packages are present
        all_pass = all(
            results['packages'][pkg]['status'] == 'pass'
            for pkg in required_packages
        )
        
        results['overall_status'] = 'pass' if all_pass else 'fail'
        
        return results
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check required configuration"""
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'GMAIL_USER',
            'GMAIL_APP_PASSWORD'
        ]
        
        optional_vars = [
            'GROQ_API_KEY',
            'OPENROUTER_API_KEY',
            'GITHUB_TOKEN'
        ]
        
        results = {
            'required': {},
            'optional': {}
        }
        
        # Check required variables
        all_required_present = True
        for var in required_vars:
            value = os.getenv(var)
            present = bool(value and value != 'your.email@gmail.com' and value != 'your_app_password')
            
            results['required'][var] = {
                'status': 'pass' if present else 'fail',
                'configured': present
            }
            
            if not present:
                all_required_present = False
        
        # Check optional variables
        for var in optional_vars:
            value = os.getenv(var)
            present = bool(value)
            
            results['optional'][var] = {
                'status': 'pass' if present else 'warn',
                'configured': present
            }
        
        return {
            'status': 'pass' if all_required_present else 'fail',
            'required': results['required'],
            'optional': results['optional']
        }


class MetricsCollector:
    """
    Collect and expose application metrics
    """
    
    def __init__(self):
        self.logger = get_logger('metrics')
        self._metrics: Dict[str, Any] = {}
        self._start_time = time.time()
    
    def increment(self, name: str, value: int = 1):
        """Increment a counter metric"""
        if name not in self._metrics:
            self._metrics[name] = {'type': 'counter', 'value': 0}
        
        if self._metrics[name]['type'] == 'counter':
            self._metrics[name]['value'] += value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        if name not in self._metrics:
            self._metrics[name] = {'type': 'gauge', 'value': value}
        else:
            if self._metrics[name]['type'] == 'gauge':
                self._metrics[name]['value'] = value
    
    def record_timing(self, name: str, duration_ms: float):
        """Record a timing metric"""
        if name not in self._metrics:
            self._metrics[name] = {
                'type': 'histogram',
                'values': []
            }
        
        if self._metrics[name]['type'] == 'histogram':
            self._metrics[name]['values'].append(duration_ms)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        uptime = time.time() - self._start_time
        
        result = {
            'uptime_seconds': round(uptime, 2),
            'metrics': {}
        }
        
        for name, data in self._metrics.items():
            if data['type'] == 'counter':
                result['metrics'][name] = {
                    'type': 'counter',
                    'value': data['value']
                }
            elif data['type'] == 'gauge':
                result['metrics'][name] = {
                    'type': 'gauge',
                    'value': data['value']
                }
            elif data['type'] == 'histogram':
                values = data['values']
                result['metrics'][name] = {
                    'type': 'histogram',
                    'count': len(values),
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'avg': sum(values) / len(values) if values else 0
                }
        
        return result


# Global instances
_health_checker = None
_metrics_collector = None


def get_health_checker() -> HealthChecker:
    """Get singleton health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def require_healthy(f):
    """
    Decorator to require healthy status for endpoint
    
    Usage:
        @app.route('/api/sensitive')
        @require_healthy
        def sensitive_operation():
            pass
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        checker = get_health_checker()
        health = checker.run_all_checks()
        
        if health['status'] != 'pass':
            from flask import jsonify
            response = jsonify({
                'error': 'System unhealthy',
                'health': health
            })
            response.status_code = 503
            return response
        
        return f(*args, **kwargs)
    
    return wrapper
