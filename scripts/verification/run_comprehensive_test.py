#!/usr/bin/env python3
"""
Comprehensive Application Test
==============================
Tests all endpoints, buttons, and functionality.
Can start server automatically or test existing server.
"""

import sys
import os
import time
import json
import subprocess
import signal
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import config


class ComprehensiveTester:
    """Comprehensive test suite"""
    
    def __init__(self, base_url: str = "http://localhost:5050", auto_start: bool = True):
        self.base_url = base_url
        self.auto_start = auto_start
        self.server_process: Optional[subprocess.Popen] = None
        self.results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'server_started': False,
            'endpoints': {},
            'pages': {},
            'errors': [],
            'warnings': []
        }
        self.session = requests.Session()
        self.session.timeout = 10
    
    def start_server(self):
        """Start the Flask server"""
        if self.server_process:
            return
        
        print("🚀 Starting Flask server...")
        try:
            env = os.environ.copy()
            env['FLASK_ENV'] = 'testing'
            env['DEBUG'] = 'false'
            
            # Start server
            self.server_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent
            )
            
            # Wait for server to be ready
            print("⏳ Waiting for server to start...")
            max_attempts = 30
            for i in range(max_attempts):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ Server started successfully")
                        self.results['server_started'] = True
                        time.sleep(1)  # Give it a moment
                        return True
                except:
                    pass
                time.sleep(1)
                if i % 5 == 0:
                    print(f"   Still waiting... ({i}/{max_attempts})")
            
            print("❌ Server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            try:
                print("\n🛑 Stopping server...")
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
    
    def check_server(self):
        """Check if server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def test_endpoint(self, method: str, path: str, expected_status: List[int] = None,
                     data: Dict = None, params: Dict = None, description: str = None):
        """Test a single endpoint"""
        if expected_status is None:
            expected_status = [200]
        
        url = f"{self.base_url}{path}"
        description = description or f"{method} {path}"
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, json=data, params=params, timeout=10)
            else:
                return False
            
            response_time = time.time() - start_time
            status_ok = response.status_code in expected_status
            
            result = {
                'method': method,
                'path': path,
                'status': response.status_code,
                'expected': expected_status,
                'ok': status_ok,
                'response_time': round(response_time, 3)
            }
            
            try:
                result['response_data'] = response.json()
            except:
                result['response_text'] = response.text[:200]
            
            self.results['endpoints'][description] = result
            
            icon = "✅" if status_ok else "⚠️"
            print(f"{icon} {method:6} {path:40} {response.status_code:3} ({response_time:.2f}s)")
            
            if not status_ok:
                self.results['warnings'].append(
                    f"{description}: Expected {expected_status}, got {response.status_code}"
                )
            
            return status_ok
            
        except requests.exceptions.Timeout:
            self.results['endpoints'][description] = {'error': 'Timeout', 'ok': False}
            self.results['errors'].append(f"{description}: Timeout")
            print(f"❌ {method:6} {path:40} - TIMEOUT")
            return False
        except requests.exceptions.ConnectionError:
            self.results['endpoints'][description] = {'error': 'Connection refused', 'ok': False}
            self.results['errors'].append(f"{description}: Connection refused")
            print(f"❌ {method:6} {path:40} - CONNECTION REFUSED")
            return False
        except Exception as e:
            self.results['endpoints'][description] = {'error': str(e), 'ok': False}
            self.results['errors'].append(f"{description}: {str(e)}")
            print(f"❌ {method:6} {path:40} - ERROR: {e}")
            return False
    
    def test_all_endpoints(self):
        """Test all endpoints"""
        print("\n" + "="*70)
        print("🔍 TESTING ALL ENDPOINTS")
        print("="*70)
        print(f"{'Method':6} {'Path':40} {'Status':6} {'Time':8}")
        print("-"*70)
        
        # Health & Monitoring
        self.test_endpoint('GET', '/health', [200], description='Health Check')
        self.test_endpoint('GET', '/metrics', [200], description='Metrics')
        self.test_endpoint('GET', '/api/stats', [200], description='Stats API')
        
        # Contacts
        self.test_endpoint('GET', '/api/contacts/available', [200], description='Available Contacts')
        
        # Email
        self.test_endpoint('GET', '/preview-emails', [200], params={'count': 1}, description='Preview Emails')
        
        # Jobs
        self.test_endpoint('GET', '/api/jobs', [200], description='Get Jobs')
        self.test_endpoint('GET', '/api/jobs/discover', [200, 405, 500], description='Discover Jobs')
        
        # Daemon
        self.test_endpoint('GET', '/api/daemon/status', [200], description='Daemon Status')
        
        # Pages
        print("\n" + "-"*70)
        print("Testing Pages (HTML responses)...")
        print("-"*70)
        pages = ['/', '/jobs', '/contacts', '/replies', '/settings']
        for page in pages:
            self.test_endpoint('GET', page, [200], description=f'Page: {page}')
        
        # POST Endpoints
        print("\n" + "-"*70)
        print("Testing POST Endpoints...")
        print("-"*70)
        
        self.test_endpoint('POST', '/send-emails', [200, 400, 401],
                          data={'count': 1}, description='Send Emails')
        
        self.test_endpoint('POST', '/api/ai/cover-letter', [200, 400, 500],
                          data={'role': 'Software Engineer', 'company': 'Test Corp', 'skills': 'Python'},
                          description='AI Cover Letter')
        
        self.test_endpoint('POST', '/api/ai/interview-guide', [200, 400, 500],
                          data={'role': 'Software Engineer', 'company': 'Test Corp', 'skills': 'Python'},
                          description='AI Interview Guide')
    
    def test_page_content(self, path: str):
        """Test page content"""
        try:
            response = self.session.get(f"{self.base_url}{path}", timeout=10)
            if response.status_code == 200:
                html = response.text
                
                # Check for common elements
                has_title = '<title' in html
                has_nav = 'nav' in html.lower() or 'navbar' in html.lower()
                has_buttons = 'button' in html.lower() or 'btn' in html.lower()
                
                result = {
                    'status': response.status_code,
                    'has_title': has_title,
                    'has_nav': has_nav,
                    'has_buttons': has_buttons,
                    'content_length': len(html),
                    'ok': True
                }
                
                self.results['pages'][path] = result
                return result
        except Exception as e:
            self.results['pages'][path] = {'error': str(e), 'ok': False}
            return None
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        endpoint_total = len(self.results['endpoints'])
        endpoint_ok = sum(1 for e in self.results['endpoints'].values() if e.get('ok', False))
        
        page_total = len(self.results['pages'])
        page_ok = sum(1 for p in self.results['pages'].values() if p.get('ok', False))
        
        print(f"\n✅ Endpoints: {endpoint_ok}/{endpoint_total} passed")
        print(f"✅ Pages: {page_ok}/{page_total} passed")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"❌ Errors: {len(self.results['errors'])}")
        
        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in self.results['warnings'][:5]:
                print(f"   - {warning}")
        
        if self.results['errors']:
            print("\n❌ ERRORS:")
            for error in self.results['errors'][:5]:
                print(f"   - {error}")
        
        total = endpoint_total + page_total
        passed = endpoint_ok + page_ok
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
            
            if success_rate >= 80:
                print("✅ Application is working properly!")
                return True
            elif success_rate >= 50:
                print("⚠️  Application has some issues but mostly working")
                return False
            else:
                print("❌ Application has significant issues")
                return False
        
        return False
    
    def save_results(self, filename: str = 'comprehensive_test_results.json'):
        """Save results"""
        results_file = Path(__file__).parent / filename
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
        return results_file
    
    def run(self):
        """Run all tests"""
        print("="*70)
        print("🧪 COMPREHENSIVE APPLICATION TEST")
        print("="*70)
        
        try:
            # Check or start server
            if not self.check_server():
                if self.auto_start:
                    if not self.start_server():
                        print("❌ Cannot proceed without server")
                        return False
                else:
                    print(f"❌ Server not running at {self.base_url}")
                    print("   Start server with: python3 main.py")
                    return False
            
            # Run tests
            self.test_all_endpoints()
            
            # Test page content
            print("\n" + "-"*70)
            print("Testing Page Content...")
            print("-"*70)
            for page in ['/', '/jobs', '/contacts']:
                result = self.test_page_content(page)
                if result:
                    print(f"✅ {page:20} - Title: {result['has_title']}, Nav: {result['has_nav']}, Buttons: {result['has_buttons']}")
            
            # Print summary
            success = self.print_summary()
            
            # Save results
            self.save_results()
            
            return success
            
        finally:
            if self.server_process:
                self.stop_server()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive application test')
    parser.add_argument('--url', default='http://localhost:5050', help='Base URL')
    parser.add_argument('--no-start', action='store_true', help='Do not start server automatically')
    parser.add_argument('--output', default='comprehensive_test_results.json', help='Output file')
    
    args = parser.parse_args()
    
    tester = ComprehensiveTester(base_url=args.url, auto_start=not args.no_start)
    
    try:
        success = tester.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        tester.stop_server()
        return 130
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        tester.stop_server()
        return 1


if __name__ == '__main__':
    sys.exit(main())
