#!/usr/bin/env python3
"""
Comprehensive Browser-Based Testing
===================================
Tests all endpoints, buttons, and functionality using Playwright
"""

import os
import sys
import time
import json
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install")

import requests
from flask import Flask

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import config


class BrowserTestSuite:
    """Comprehensive browser-based test suite"""
    
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.results: Dict[str, Any] = {
            'endpoints': {},
            'pages': {},
            'buttons': {},
            'forms': {},
            'errors': []
        }
        self.server_process: Optional[subprocess.Popen] = None
        self.server_started = False
    
    def start_server(self):
        """Start the Flask server"""
        if self.server_started:
            return
        
        print("🚀 Starting Flask server...")
        try:
            # Start server in background
            env = os.environ.copy()
            env['FLASK_ENV'] = 'testing'
            env['DEBUG'] = 'false'
            
            self.server_process = subprocess.Popen(
                [sys.executable, '-m', 'flask', 'run', '--port', '5050', '--host', '0.0.0.0'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent
            )
            
            # Wait for server to start
            max_attempts = 30
            for i in range(max_attempts):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ Server started successfully")
                        self.server_started = True
                        time.sleep(2)  # Give it a moment to fully initialize
                        return
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            raise Exception("Server failed to start within 30 seconds")
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            # Try alternative method
            print("🔄 Trying alternative server start method...")
            self._start_server_alternative()
    
    def _start_server_alternative(self):
        """Alternative server start method"""
        def run_server():
            from web.web_dashboard import app
            app.run(host='0.0.0.0', port=5050, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server
        max_attempts = 30
        for i in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Server started successfully (alternative method)")
                    self.server_started = True
                    time.sleep(2)
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        raise Exception("Server failed to start")
    
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
            except Exception as e:
                print(f"⚠️  Error stopping server: {e}")
                try:
                    self.server_process.kill()
                except:
                    pass
    
    def test_endpoints(self):
        """Test all API endpoints"""
        print("\n" + "="*70)
        print("🔍 TESTING API ENDPOINTS")
        print("="*70)
        
        endpoints = [
            ('GET', '/health', None, 200),
            ('GET', '/metrics', None, 200),
            ('GET', '/api/stats', None, 200),
            ('GET', '/api/contacts/available', None, 200),
            ('GET', '/preview-emails?count=1', None, 200),
        ]
        
        for method, path, data, expected_status in endpoints:
            try:
                url = f"{self.base_url}{path}"
                if method == 'GET':
                    response = requests.get(url, timeout=5)
                elif method == 'POST':
                    response = requests.post(url, json=data, timeout=5)
                else:
                    continue
                
                status_ok = response.status_code == expected_status
                self.results['endpoints'][path] = {
                    'status': response.status_code,
                    'expected': expected_status,
                    'ok': status_ok,
                    'response_time': response.elapsed.total_seconds()
                }
                
                status_icon = "✅" if status_ok else "❌"
                print(f"{status_icon} {method} {path} - {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                
                if not status_ok:
                    self.results['errors'].append(f"{method} {path}: Expected {expected_status}, got {response.status_code}")
                    
            except Exception as e:
                self.results['endpoints'][path] = {
                    'error': str(e),
                    'ok': False
                }
                self.results['errors'].append(f"{method} {path}: {str(e)}")
                print(f"❌ {method} {path} - ERROR: {e}")
    
    def test_pages(self, page: Page):
        """Test all pages load correctly"""
        print("\n" + "="*70)
        print("🌐 TESTING PAGES")
        print("="*70)
        
        pages = [
            '/',
            '/jobs',
            '/contacts',
            '/replies',
            '/settings',
        ]
        
        for path in pages:
            try:
                url = f"{self.base_url}{path}"
                response = page.goto(url, wait_until='networkidle', timeout=10000)
                
                status_ok = response.status == 200
                title = page.title()
                
                self.results['pages'][path] = {
                    'status': response.status,
                    'title': title,
                    'ok': status_ok
                }
                
                status_icon = "✅" if status_ok else "❌"
                print(f"{status_icon} {path} - Status: {response.status}, Title: {title}")
                
                if not status_ok:
                    self.results['errors'].append(f"Page {path}: Status {response.status}")
                    
            except Exception as e:
                self.results['pages'][path] = {
                    'error': str(e),
                    'ok': False
                }
                self.results['errors'].append(f"Page {path}: {str(e)}")
                print(f"❌ {path} - ERROR: {e}")
    
    def test_buttons(self, page: Page):
        """Test all buttons on the pages"""
        print("\n" + "="*70)
        print("🔘 TESTING BUTTONS")
        print("="*70)
        
        # Test dashboard buttons
        try:
            page.goto(f"{self.base_url}/", wait_until='networkidle', timeout=10000)
            time.sleep(1)
            
            buttons = page.locator('button, a.button, input[type="button"], input[type="submit"]')
            button_count = buttons.count()
            
            print(f"Found {button_count} buttons on dashboard")
            
            for i in range(min(button_count, 20)):  # Test first 20 buttons
                try:
                    button = buttons.nth(i)
                    text = button.text_content() or button.get_attribute('value') or button.get_attribute('aria-label') or f"Button {i}"
                    is_visible = button.is_visible()
                    is_enabled = button.is_enabled()
                    
                    if is_visible and is_enabled:
                        # Try to click (but don't wait for navigation)
                        try:
                            button.click(timeout=2000)
                            time.sleep(0.5)
                            self.results['buttons'][f"dashboard_button_{i}"] = {
                                'text': text[:50],
                                'clickable': True,
                                'ok': True
                            }
                            print(f"✅ Button {i}: '{text[:30]}' - Clickable")
                        except Exception as e:
                            self.results['buttons'][f"dashboard_button_{i}"] = {
                                'text': text[:50],
                                'clickable': False,
                                'error': str(e),
                                'ok': False
                            }
                            print(f"⚠️  Button {i}: '{text[:30]}' - Not clickable: {e}")
                    else:
                        self.results['buttons'][f"dashboard_button_{i}"] = {
                            'text': text[:50],
                            'visible': is_visible,
                            'enabled': is_enabled,
                            'ok': False
                        }
                        print(f"⚠️  Button {i}: '{text[:30]}' - Not visible/enabled")
                        
                except Exception as e:
                    print(f"⚠️  Error testing button {i}: {e}")
                    
        except Exception as e:
            self.results['errors'].append(f"Button testing: {str(e)}")
            print(f"❌ Error testing buttons: {e}")
    
    def test_forms(self, page: Page):
        """Test form submissions"""
        print("\n" + "="*70)
        print("📝 TESTING FORMS")
        print("="*70)
        
        # Test API endpoints that accept POST
        forms_to_test = [
            {
                'name': 'Preview Emails',
                'method': 'GET',
                'url': '/preview-emails',
                'params': {'count': 1}
            },
        ]
        
        for form in forms_to_test:
            try:
                url = f"{self.base_url}{form['url']}"
                if form['method'] == 'GET':
                    response = requests.get(url, params=form.get('params'), timeout=5)
                elif form['method'] == 'POST':
                    response = requests.post(url, json=form.get('data'), timeout=5)
                else:
                    continue
                
                status_ok = response.status_code < 400
                self.results['forms'][form['name']] = {
                    'status': response.status_code,
                    'ok': status_ok
                }
                
                status_icon = "✅" if status_ok else "❌"
                print(f"{status_icon} {form['name']} - {response.status_code}")
                
            except Exception as e:
                self.results['forms'][form['name']] = {
                    'error': str(e),
                    'ok': False
                }
                print(f"❌ {form['name']} - ERROR: {e}")
    
    def test_api_endpoints_comprehensive(self):
        """Comprehensive API endpoint testing"""
        print("\n" + "="*70)
        print("🔌 COMPREHENSIVE API TESTING")
        print("="*70)
        
        # Test all known endpoints
        api_tests = [
            # Health and metrics
            ('GET', '/health', None, None, [200]),
            ('GET', '/metrics', None, None, [200]),
            ('GET', '/api/stats', None, None, [200]),
            
            # Contacts
            ('GET', '/api/contacts/available', None, None, [200]),
            
            # Email preview
            ('GET', '/preview-emails', {'count': 1}, None, [200]),
            ('GET', '/preview-emails', {'count': 0}, None, [400, 200]),  # May fail
            
            # Jobs (if available)
            ('GET', '/api/jobs', None, None, [200]),
            ('GET', '/api/jobs/discover', None, None, [200, 405]),  # May be POST only
            
            # Daemon
            ('GET', '/api/daemon/status', None, None, [200]),
        ]
        
        for method, path, params, data, allowed_statuses in api_tests:
            try:
                url = f"{self.base_url}{path}"
                
                if method == 'GET':
                    response = requests.get(url, params=params, timeout=5)
                elif method == 'POST':
                    response = requests.post(url, json=data, params=params, timeout=5)
                else:
                    continue
                
                status_ok = response.status_code in allowed_statuses
                
                endpoint_key = f"{method} {path}"
                self.results['endpoints'][endpoint_key] = {
                    'status': response.status_code,
                    'allowed': allowed_statuses,
                    'ok': status_ok,
                    'response_time': response.elapsed.total_seconds()
                }
                
                status_icon = "✅" if status_ok else "⚠️"
                print(f"{status_icon} {method} {path} - {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                
                if not status_ok:
                    self.results['errors'].append(
                        f"{method} {path}: Got {response.status_code}, expected {allowed_statuses}"
                    )
                    
            except Exception as e:
                endpoint_key = f"{method} {path}"
                self.results['endpoints'][endpoint_key] = {
                    'error': str(e),
                    'ok': False
                }
                self.results['errors'].append(f"{method} {path}: {str(e)}")
                print(f"❌ {method} {path} - ERROR: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Playwright not available. Running API tests only...")
            self.start_server()
            try:
                self.test_endpoints()
                self.test_api_endpoints_comprehensive()
            finally:
                self.stop_server()
            return
        
        print("\n" + "="*70)
        print("🧪 COMPREHENSIVE BROWSER TEST SUITE")
        print("="*70)
        
        self.start_server()
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Set longer timeout
                page.set_default_timeout(30000)
                
                # Run all tests
                self.test_endpoints()
                self.test_api_endpoints_comprehensive()
                self.test_pages(page)
                self.test_buttons(page)
                self.test_forms(page)
                
                browser.close()
                
        except Exception as e:
            print(f"❌ Browser test error: {e}")
            self.results['errors'].append(f"Browser test: {str(e)}")
        finally:
            self.stop_server()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        # Count successes
        endpoint_count = len(self.results['endpoints'])
        endpoint_ok = sum(1 for e in self.results['endpoints'].values() if e.get('ok', False))
        
        page_count = len(self.results['pages'])
        page_ok = sum(1 for p in self.results['pages'].values() if p.get('ok', False))
        
        button_count = len(self.results['buttons'])
        button_ok = sum(1 for b in self.results['buttons'].values() if b.get('ok', False))
        
        form_count = len(self.results['forms'])
        form_ok = sum(1 for f in self.results['forms'].values() if f.get('ok', False))
        
        print(f"\n✅ Endpoints: {endpoint_ok}/{endpoint_count} passed")
        print(f"✅ Pages: {page_ok}/{page_count} passed")
        print(f"✅ Buttons: {button_ok}/{button_count} passed")
        print(f"✅ Forms: {form_ok}/{form_count} passed")
        print(f"❌ Errors: {len(self.results['errors'])}")
        
        if self.results['errors']:
            print("\n❌ ERRORS FOUND:")
            for error in self.results['errors'][:10]:  # Show first 10
                print(f"   - {error}")
            if len(self.results['errors']) > 10:
                print(f"   ... and {len(self.results['errors']) - 10} more")
        
        # Overall status
        total_tests = endpoint_count + page_count + button_count + form_count
        total_passed = endpoint_ok + page_ok + button_ok + form_ok
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests})")
            
            if success_rate >= 90:
                print("✅ Application is working properly!")
            elif success_rate >= 70:
                print("⚠️  Application has some issues but mostly working")
            else:
                print("❌ Application has significant issues")
        
        print("="*70)
        
        return len(self.results['errors']) == 0 and total_passed > 0


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive browser-based testing')
    parser.add_argument('--url', default='http://localhost:5050', help='Base URL to test')
    parser.add_argument('--no-server', action='store_true', help='Assume server is already running')
    
    args = parser.parse_args()
    
    suite = BrowserTestSuite(base_url=args.url)
    
    if args.no_server:
        suite.server_started = True
    
    suite.run_all_tests()
    success = suite.print_summary()
    
    # Save results to file
    results_file = Path(__file__).parent.parent / 'test_results.json'
    with open(results_file, 'w') as f:
        json.dump(suite.results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {results_file}")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
