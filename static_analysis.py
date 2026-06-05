#!/usr/bin/env python3
"""
Static Analysis - Comprehensive Code Check
==========================================
Checks all endpoints, imports, functions, and code structure without running server
"""

import sys
import ast
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Set
import json

# Add project root
sys.path.insert(0, str(Path(__file__).parent))


class StaticAnalyzer:
    """Static code analyzer"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            'endpoints': {},
            'imports': {},
            'functions': {},
            'errors': [],
            'warnings': [],
            'info': []
        }
    
    def analyze_web_dashboard(self):
        """Analyze web dashboard file"""
        print("\n" + "="*70)
        print("🔍 ANALYZING WEB DASHBOARD")
        print("="*70)
        
        dashboard_path = Path(__file__).parent / 'web' / 'web_dashboard.py'
        
        # Parse AST
        try:
            with open(dashboard_path, 'r') as f:
                tree = ast.parse(f.read(), filename=str(dashboard_path))
        except Exception as e:
            self.results['errors'].append(f"Cannot parse web_dashboard.py: {e}")
            return
        
        # Find all routes
        routes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for route decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == 'route':
                                # Extract route info
                                route_path = None
                                methods = ['GET']  # Default
                                
                                if decorator.args:
                                    route_path = self._extract_string(decorator.args[0])
                                
                                if len(decorator.keywords) > 0:
                                    for kw in decorator.keywords:
                                        if kw.arg == 'methods':
                                            if isinstance(kw.value, ast.List):
                                                methods = [self._extract_string(e) for e in kw.value.elts]
                                
                                routes.append({
                                    'path': route_path or '/',
                                    'methods': methods,
                                    'function': node.name,
                                    'line': node.lineno
                                })
        
        print(f"\n✅ Found {len(routes)} routes:")
        for route in routes:
            methods_str = ', '.join(route['methods'])
            print(f"   {methods_str:15} {route['path']:40} -> {route['function']}")
            self.results['endpoints'][route['path']] = {
                'methods': route['methods'],
                'function': route['function'],
                'line': route['line']
            }
        
        return routes
    
    def _extract_string(self, node):
        """Extract string value from AST node"""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant):
            return node.value
        return None
    
    def test_imports(self):
        """Test all imports"""
        print("\n" + "="*70)
        print("📦 TESTING IMPORTS")
        print("="*70)
        
        modules_to_test = [
            'web.web_dashboard',
            'core.email_system',
            'core.job_discovery',
            'core.job_pipeline',
            'core.database_manager',
            'utils.config',
            'utils.security',
            'middleware.rate_limit',
            'middleware.health_check',
            'middleware.csrf',
        ]
        
        for module_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                print(f"✅ {module_name}")
                self.results['imports'][module_name] = {'ok': True}
            except ImportError as e:
                print(f"❌ {module_name} - {e}")
                self.results['imports'][module_name] = {'ok': False, 'error': str(e)}
                self.results['errors'].append(f"Import error: {module_name} - {e}")
            except Exception as e:
                print(f"⚠️  {module_name} - {e}")
                self.results['imports'][module_name] = {'ok': False, 'error': str(e)}
                self.results['warnings'].append(f"Import warning: {module_name} - {e}")
    
    def test_web_app(self):
        """Test web app initialization"""
        print("\n" + "="*70)
        print("🌐 TESTING WEB APP")
        print("="*70)
        
        try:
            from web.web_dashboard import app
            
            # Check app exists
            print(f"✅ Flask app created: {type(app).__name__}")
            
            # Get all routes
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append({
                    'path': rule.rule,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    'endpoint': rule.endpoint
                })
            
            print(f"\n✅ Found {len(routes)} registered routes:")
            for route in sorted(routes, key=lambda x: x['path']):
                methods_str = ', '.join(route['methods'])
                print(f"   {methods_str:20} {route['path']}")
            
            # Check critical routes exist
            critical_routes = [
                '/',
                '/health',
                '/metrics',
                '/api/stats',
                '/api/contacts/available',
            ]
            
            route_paths = {r['path'] for r in routes}
            missing = [r for r in critical_routes if r not in route_paths]
            
            if missing:
                self.results['warnings'].append(f"Missing critical routes: {missing}")
                print(f"\n⚠️  Missing critical routes: {missing}")
            else:
                print("\n✅ All critical routes registered")
            
            self.results['info'].append(f"Total routes: {len(routes)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing web app: {e}")
            self.results['errors'].append(f"Web app test: {str(e)}")
            return False
    
    def test_functions(self):
        """Test critical functions"""
        print("\n" + "="*70)
        print("🔧 TESTING FUNCTIONS")
        print("="*70)
        
        functions_to_test = [
            ('web.web_dashboard', 'get_campaign_stats'),
            ('web.web_dashboard', 'get_contacts'),
            ('web.web_dashboard', 'get_replies'),
            ('web.web_dashboard', 'get_jobs'),
            ('utils.security', 'InputValidator'),
            ('utils.security', 'SecretMasker'),
        ]
        
        for module_name, func_name in functions_to_test:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    if callable(func):
                        print(f"✅ {module_name}.{func_name} - callable")
                        self.results['functions'][f"{module_name}.{func_name}"] = {'ok': True}
                    else:
                        print(f"⚠️  {module_name}.{func_name} - not callable")
                        self.results['functions'][f"{module_name}.{func_name}"] = {'ok': False}
                else:
                    print(f"⚠️  {module_name}.{func_name} - not found")
                    self.results['functions'][f"{module_name}.{func_name}"] = {'ok': False}
            except Exception as e:
                print(f"❌ {module_name}.{func_name} - {e}")
                self.results['functions'][f"{module_name}.{func_name}"] = {'ok': False, 'error': str(e)}
    
    def check_security(self):
        """Check security features"""
        print("\n" + "="*70)
        print("🔒 CHECKING SECURITY")
        print("="*70)
        
        checks = []
        
        # Check rate limiting
        try:
            from web.web_dashboard import rate_limiter
            print("✅ Rate limiter configured")
            checks.append(True)
        except:
            print("⚠️  Rate limiter not found")
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
            print("⚠️  CSRF check failed")
            checks.append(False)
        
        # Check input validation
        try:
            from utils.security import InputValidator
            validator = InputValidator()
            # Test validation
            assert validator.validate_email("test@example.com") == True
            assert validator.validate_email("invalid") == False
            print("✅ Input validation working")
            checks.append(True)
        except Exception as e:
            print(f"⚠️  Input validation check failed: {e}")
            checks.append(False)
        
        # Check secret masking
        try:
            from utils.security import SecretMasker
            masked = SecretMasker.mask_string("secret123")
            assert masked != "secret123"
            assert len(masked) == len("secret123")
            print("✅ Secret masking working")
            checks.append(True)
        except Exception as e:
            print(f"⚠️  Secret masking check failed: {e}")
            checks.append(False)
        
        security_score = sum(checks) / len(checks) * 100
        print(f"\n📊 Security Score: {security_score:.0f}%")
        
        return security_score >= 75
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*70)
        print("📊 ANALYSIS SUMMARY")
        print("="*70)
        
        endpoint_count = len(self.results['endpoints'])
        import_ok = sum(1 for i in self.results['imports'].values() if i.get('ok', False))
        import_total = len(self.results['imports'])
        func_ok = sum(1 for f in self.results['functions'].values() if f.get('ok', False))
        func_total = len(self.results['functions'])
        
        print(f"\n✅ Endpoints found: {endpoint_count}")
        print(f"✅ Imports: {import_ok}/{import_total} passed")
        print(f"✅ Functions: {func_ok}/{func_total} passed")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"❌ Errors: {len(self.results['errors'])}")
        
        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in self.results['warnings'][:10]:
                print(f"   - {warning}")
        
        if self.results['errors']:
            print("\n❌ ERRORS:")
            for error in self.results['errors'][:10]:
                print(f"   - {error}")
        
        print("="*70)
        
        # Overall assessment
        if len(self.results['errors']) == 0 and endpoint_count > 0:
            print("\n✅ Application structure is valid!")
            return True
        elif len(self.results['errors']) < 3:
            print("\n⚠️  Application has minor issues")
            return False
        else:
            print("\n❌ Application has significant issues")
            return False
    
    def save_results(self, filename: str = 'static_analysis_results.json'):
        """Save results"""
        results_file = Path(__file__).parent / filename
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
        return results_file
    
    def run_all(self):
        """Run all analyses"""
        print("="*70)
        print("🔍 COMPREHENSIVE STATIC ANALYSIS")
        print("="*70)
        
        self.analyze_web_dashboard()
        self.test_imports()
        self.test_web_app()
        self.test_functions()
        self.check_security()
        
        success = self.print_summary()
        self.save_results()
        
        return success


def main():
    """Main entry point"""
    analyzer = StaticAnalyzer()
    success = analyzer.run_all()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
