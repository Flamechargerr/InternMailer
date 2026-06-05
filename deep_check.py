#!/usr/bin/env python3
"""
Deep Comprehensive Check
========================
Thoroughly checks every aspect of the codebase
"""

import sys
import os
import ast
import importlib
import inspect
import traceback
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import json

sys.path.insert(0, str(Path(__file__).parent))


class DeepChecker:
    """Deep comprehensive checker"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            'syntax_errors': [],
            'import_errors': [],
            'function_errors': [],
            'endpoint_errors': [],
            'database_errors': [],
            'security_issues': [],
            'missing_dependencies': [],
            'configuration_issues': [],
            'warnings': [],
            'info': []
        }
        self.checked_files: Set[str] = set()
    
    def check_all(self):
        """Run all checks"""
        print("="*70)
        print("🔍 DEEP COMPREHENSIVE CHECK")
        print("="*70)
        
        self.check_syntax()
        self.check_imports()
        self.check_functions()
        self.check_endpoints()
        self.check_database_operations()
        self.check_security()
        self.check_dependencies()
        self.check_configuration()
        self.check_error_handling()
        
        return self.print_summary()
    
    def check_syntax(self):
        """Check Python syntax in all files"""
        print("\n" + "="*70)
        print("📝 CHECKING SYNTAX")
        print("="*70)
        
        core_files = [
            'web/web_dashboard.py',
            'core/email_system.py',
            'core/job_discovery.py',
            'core/job_pipeline.py',
            'core/database_manager.py',
            'core/inbox_monitor.py',
            'core/followup_scheduler.py',
            'core/reply_classifier.py',
            'core/unified_ai_provider.py',
            'core/anti_templating_engine.py',
            'utils/config.py',
            'utils/security.py',
            'utils/profile.py',
            'utils/validators.py',
            'middleware/rate_limit.py',
            'middleware/csrf.py',
            'middleware/health_check.py',
        ]
        
        for file_path in core_files:
            full_path = Path(__file__).parent / file_path
            if not full_path.exists():
                self.results['syntax_errors'].append(f"{file_path}: File not found")
                continue
            
            try:
                with open(full_path, 'r') as f:
                    code = f.read()
                
                # Parse AST
                ast.parse(code, filename=str(full_path))
                print(f"✅ {file_path}")
                self.checked_files.add(str(full_path))
            except SyntaxError as e:
                error_msg = f"{file_path}:{e.lineno}: {e.msg}"
                self.results['syntax_errors'].append(error_msg)
                print(f"❌ {file_path}:{e.lineno} - {e.msg}")
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                self.results['syntax_errors'].append(error_msg)
                print(f"⚠️  {file_path} - {str(e)}")
    
    def check_imports(self):
        """Check all imports"""
        print("\n" + "="*70)
        print("📦 CHECKING IMPORTS")
        print("="*70)
        
        modules = [
            'web.web_dashboard',
            'core.email_system',
            'core.job_discovery',
            'core.job_pipeline',
            'core.database_manager',
            'core.inbox_monitor',
            'core.followup_scheduler',
            'core.reply_classifier',
            'core.unified_ai_provider',
            'core.anti_templating_engine',
            'core.job_apply',
            'core.lead_discovery',
            'utils.config',
            'utils.security',
            'utils.profile',
            'utils.validators',
            'utils.logger',
            'utils.exceptions',
            'middleware.rate_limit',
            'middleware.csrf',
            'middleware.health_check',
        ]
        
        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                print(f"✅ {module_name}")
            except ImportError as e:
                error_msg = f"{module_name}: {str(e)}"
                self.results['import_errors'].append(error_msg)
                print(f"❌ {module_name} - {str(e)}")
            except Exception as e:
                error_msg = f"{module_name}: {str(e)}"
                self.results['import_errors'].append(error_msg)
                print(f"⚠️  {module_name} - {str(e)}")
    
    def check_functions(self):
        """Check critical functions"""
        print("\n" + "="*70)
        print("🔧 CHECKING FUNCTIONS")
        print("="*70)
        
        functions_to_check = [
            ('web.web_dashboard', 'get_campaign_stats'),
            ('web.web_dashboard', 'get_contacts'),
            ('web.web_dashboard', 'get_replies'),
            ('web.web_dashboard', 'get_jobs'),
            ('web.web_dashboard', 'get_job_stats'),
            ('web.web_dashboard', 'get_current_config'),
            ('core.email_system', 'EmailSystem'),
            ('core.job_discovery', 'JobDiscovery'),
            ('core.database_manager', 'DatabaseManager'),
            ('utils.security', 'InputValidator'),
            ('utils.security', 'SecretMasker'),
        ]
        
        for module_name, func_name in functions_to_check:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, func_name):
                    obj = getattr(module, func_name)
                    if callable(obj) or inspect.isclass(obj):
                        # Try to get signature
                        try:
                            sig = inspect.signature(obj)
                            print(f"✅ {module_name}.{func_name} - callable")
                        except:
                            print(f"✅ {module_name}.{func_name} - callable (no signature)")
                    else:
                        error_msg = f"{module_name}.{func_name} is not callable"
                        self.results['function_errors'].append(error_msg)
                        print(f"⚠️  {module_name}.{func_name} - not callable")
                else:
                    error_msg = f"{module_name}.{func_name} not found"
                    self.results['function_errors'].append(error_msg)
                    print(f"❌ {module_name}.{func_name} - not found")
            except Exception as e:
                error_msg = f"{module_name}.{func_name}: {str(e)}"
                self.results['function_errors'].append(error_msg)
                print(f"❌ {module_name}.{func_name} - {str(e)}")
    
    def check_endpoints(self):
        """Check all endpoints"""
        print("\n" + "="*70)
        print("🌐 CHECKING ENDPOINTS")
        print("="*70)
        
        try:
            from web.web_dashboard import app
            
            routes = list(app.url_map.iter_rules())
            print(f"✅ Found {len(routes)} routes")
            
            # Check each route has a handler
            for rule in routes:
                endpoint = rule.endpoint
                try:
                    view_func = app.view_functions.get(endpoint)
                    if view_func is None:
                        error_msg = f"Route {rule.rule}: No view function for endpoint {endpoint}"
                        self.results['endpoint_errors'].append(error_msg)
                        print(f"❌ {rule.rule} - No handler")
                    else:
                        # Check if function is callable
                        if not callable(view_func):
                            error_msg = f"Route {rule.rule}: Handler not callable"
                            self.results['endpoint_errors'].append(error_msg)
                            print(f"❌ {rule.rule} - Handler not callable")
                except Exception as e:
                    error_msg = f"Route {rule.rule}: {str(e)}"
                    self.results['endpoint_errors'].append(error_msg)
                    print(f"⚠️  {rule.rule} - {str(e)}")
            
            # Check critical endpoints exist
            critical = ['/', '/health', '/metrics', '/api/stats']
            route_paths = {r.rule for r in routes}
            missing = [r for r in critical if r not in route_paths]
            
            if missing:
                self.results['endpoint_errors'].extend([f"Missing critical route: {r}" for r in missing])
                print(f"❌ Missing critical routes: {missing}")
            else:
                print("✅ All critical routes exist")
                
        except Exception as e:
            error_msg = f"Endpoint check failed: {str(e)}"
            self.results['endpoint_errors'].append(error_msg)
            print(f"❌ Endpoint check failed: {str(e)}")
            traceback.print_exc()
    
    def check_database_operations(self):
        """Check database operations"""
        print("\n" + "="*70)
        print("💾 CHECKING DATABASE OPERATIONS")
        print("="*70)
        
        try:
            from core.database_manager import DatabaseManager
            from utils.config import config
            
            # Check database manager
            db = DatabaseManager(config.DATABASE_PATH)
            print("✅ DatabaseManager initialized")
            
            # Check methods exist
            methods = ['insert', 'update', 'delete', 'fetch_one', 'fetch_all', 'get_connection']
            for method in methods:
                if hasattr(db, method):
                    print(f"✅ DatabaseManager.{method} exists")
                else:
                    error_msg = f"DatabaseManager.{method} missing"
                    self.results['database_errors'].append(error_msg)
                    print(f"❌ DatabaseManager.{method} missing")
            
            # Check SQL injection prevention
            db_file = Path(__file__).parent / 'core' / 'database_manager.py'
            if db_file.exists():
                with open(db_file, 'r') as f:
                    content = f.read()
                    if 'sanitize_sql_identifier' in content:
                        print("✅ SQL injection prevention found")
                    else:
                        self.results['security_issues'].append("SQL injection prevention may be missing")
                        print("⚠️  SQL injection prevention check needed")
            
        except Exception as e:
            error_msg = f"Database check failed: {str(e)}"
            self.results['database_errors'].append(error_msg)
            print(f"❌ Database check failed: {str(e)}")
    
    def check_security(self):
        """Check security features"""
        print("\n" + "="*70)
        print("🔒 CHECKING SECURITY")
        print("="*70)
        
        checks = []
        
        # Check rate limiting
        try:
            from web.web_dashboard import rate_limiter
            if rate_limiter:
                print("✅ Rate limiter configured")
                checks.append(True)
            else:
                checks.append(False)
        except:
            checks.append(False)
        
        # Check CSRF
        try:
            from web.web_dashboard import csrf
            if csrf:
                print("✅ CSRF protection enabled")
                checks.append(True)
            else:
                print("⚠️  CSRF protection disabled")
                checks.append(False)
        except:
            checks.append(False)
        
        # Check input validation
        try:
            from utils.security import InputValidator
            validator = InputValidator()
            assert validator.validate_email("test@example.com") == True
            assert validator.validate_email("invalid") == False
            print("✅ Input validation working")
            checks.append(True)
        except Exception as e:
            print(f"⚠️  Input validation: {str(e)}")
            checks.append(False)
        
        # Check secret masking
        try:
            from utils.security import SecretMasker
            masked = SecretMasker.mask_string("secret123")
            assert masked != "secret123"
            print("✅ Secret masking working")
            checks.append(True)
        except Exception as e:
            print(f"⚠️  Secret masking: {str(e)}")
            checks.append(False)
        
        # Check SQL injection prevention
        try:
            from utils.security import sanitize_sql_identifier
            # Should raise error for invalid input
            try:
                sanitize_sql_identifier("DROP TABLE users;")
                self.results['security_issues'].append("SQL injection prevention not working")
                print("❌ SQL injection prevention not working")
                checks.append(False)
            except ValueError:
                print("✅ SQL injection prevention working")
                checks.append(True)
        except Exception as e:
            print(f"⚠️  SQL injection check: {str(e)}")
            checks.append(False)
        
        security_score = sum(checks) / len(checks) * 100 if checks else 0
        print(f"\n📊 Security Score: {security_score:.0f}%")
        
        if security_score < 80:
            self.results['security_issues'].append(f"Security score below threshold: {security_score}%")
    
    def check_dependencies(self):
        """Check required dependencies"""
        print("\n" + "="*70)
        print("📚 CHECKING DEPENDENCIES")
        print("="*70)
        
        required = {
            'flask': 'flask',
            'requests': 'requests',
            'beautifulsoup4': 'bs4',
            'pyyaml': 'yaml',
            'python-dotenv': 'dotenv',
            'dnspython': 'dns',
            'schedule': 'schedule',
            'psutil': 'psutil',
            'flask-cors': 'flask_cors',
            'cryptography': 'cryptography',
        }
        
        optional = {
            'playwright': 'playwright',
            'gunicorn': 'gunicorn',
            'gevent': 'gevent',
        }
        
        missing_required = []
        missing_optional = []
        
        for package, import_name in required.items():
            try:
                __import__(import_name)
                print(f"✅ {package}")
            except ImportError:
                missing_required.append(package)
                self.results['missing_dependencies'].append(f"Required: {package}")
                print(f"❌ {package} - MISSING")
        
        for package, import_name in optional.items():
            try:
                __import__(import_name)
                print(f"✅ {package} (optional)")
            except ImportError:
                missing_optional.append(package)
                print(f"⚠️  {package} - optional, not installed")
        
        if missing_required:
            print(f"\n❌ Missing required dependencies: {missing_required}")
        else:
            print("\n✅ All required dependencies installed")
    
    def check_configuration(self):
        """Check configuration"""
        print("\n" + "="*70)
        print("⚙️  CHECKING CONFIGURATION")
        print("="*70)
        
        try:
            from utils.config import config
            
            # Check required config
            required = ['GMAIL_USER', 'GMAIL_APP_PASSWORD']
            missing = []
            for key in required:
                value = getattr(config, key, None)
                if not value:
                    missing.append(key)
                    self.results['configuration_issues'].append(f"Missing: {key}")
            
            if missing:
                print(f"⚠️  Missing config: {missing}")
            else:
                print("✅ Required configuration present")
            
            # Check optional but important
            optional = ['GROQ_API_KEY', 'JOB_SOURCES_PATH', 'COMPANY_CONTACTS_CSV']
            for key in optional:
                value = getattr(config, key, None)
                if value:
                    print(f"✅ {key} configured")
                else:
                    print(f"⚠️  {key} not configured (optional)")
            
        except Exception as e:
            error_msg = f"Configuration check failed: {str(e)}"
            self.results['configuration_issues'].append(error_msg)
            print(f"❌ Configuration check failed: {str(e)}")
    
    def check_error_handling(self):
        """Check error handling"""
        print("\n" + "="*70)
        print("🛡️  CHECKING ERROR HANDLING")
        print("="*70)
        
        # Check web dashboard error handling
        dashboard_file = Path(__file__).parent / 'web' / 'web_dashboard.py'
        if dashboard_file.exists():
            with open(dashboard_file, 'r') as f:
                content = f.read()
                
            # Count try-except blocks
            try_count = content.count('try:')
            except_count = content.count('except')
            
            if try_count > 0 and except_count > 0:
                print(f"✅ Error handling found ({try_count} try blocks)")
            else:
                self.results['warnings'].append("Limited error handling in web_dashboard.py")
                print("⚠️  Limited error handling")
        
        # Check database error handling
        db_file = Path(__file__).parent / 'core' / 'database_manager.py'
        if db_file.exists():
            with open(db_file, 'r') as f:
                content = f.read()
            
            if 'try:' in content and 'except' in content:
                print("✅ Database error handling found")
            else:
                self.results['warnings'].append("Database error handling may be insufficient")
                print("⚠️  Database error handling check needed")
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE SUMMARY")
        print("="*70)
        
        total_errors = (
            len(self.results['syntax_errors']) +
            len(self.results['import_errors']) +
            len(self.results['function_errors']) +
            len(self.results['endpoint_errors']) +
            len(self.results['database_errors']) +
            len(self.results['security_issues']) +
            len(self.results['missing_dependencies']) +
            len(self.results['configuration_issues'])
        )
        
        print(f"\n📝 Syntax Errors: {len(self.results['syntax_errors'])}")
        print(f"📦 Import Errors: {len(self.results['import_errors'])}")
        print(f"🔧 Function Errors: {len(self.results['function_errors'])}")
        print(f"🌐 Endpoint Errors: {len(self.results['endpoint_errors'])}")
        print(f"💾 Database Errors: {len(self.results['database_errors'])}")
        print(f"🔒 Security Issues: {len(self.results['security_issues'])}")
        print(f"📚 Missing Dependencies: {len(self.results['missing_dependencies'])}")
        print(f"⚙️  Configuration Issues: {len(self.results['configuration_issues'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"\n❌ Total Issues: {total_errors}")
        
        # Show errors
        if self.results['syntax_errors']:
            print("\n❌ SYNTAX ERRORS:")
            for error in self.results['syntax_errors'][:10]:
                print(f"   - {error}")
        
        if self.results['import_errors']:
            print("\n❌ IMPORT ERRORS:")
            for error in self.results['import_errors'][:10]:
                print(f"   - {error}")
        
        if self.results['function_errors']:
            print("\n❌ FUNCTION ERRORS:")
            for error in self.results['function_errors'][:10]:
                print(f"   - {error}")
        
        if self.results['endpoint_errors']:
            print("\n❌ ENDPOINT ERRORS:")
            for error in self.results['endpoint_errors'][:10]:
                print(f"   - {error}")
        
        if self.results['security_issues']:
            print("\n🔒 SECURITY ISSUES:")
            for issue in self.results['security_issues'][:10]:
                print(f"   - {issue}")
        
        if self.results['missing_dependencies']:
            print("\n📚 MISSING DEPENDENCIES:")
            for dep in self.results['missing_dependencies'][:10]:
                print(f"   - {dep}")
        
        print("="*70)
        
        if total_errors == 0:
            print("\n✅ ALL CHECKS PASSED - APPLICATION IS READY!")
            return True
        elif total_errors < 5:
            print("\n⚠️  MINOR ISSUES FOUND - MOSTLY READY")
            return False
        else:
            print("\n❌ SIGNIFICANT ISSUES FOUND - NEEDS ATTENTION")
            return False
    
    def save_results(self, filename: str = 'deep_check_results.json'):
        """Save results"""
        results_file = Path(__file__).parent / filename
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
        return results_file


def main():
    """Main entry point"""
    checker = DeepChecker()
    success = checker.check_all()
    checker.save_results()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
