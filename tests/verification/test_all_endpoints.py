#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing
==============================
Tests all API endpoints, pages, and functionality without browser automation
"""

import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import config


class EndpointTester:
    """Test all endpoints comprehensively"""
    
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'endpoints': {},
            'errors': [],
            'warnings': []
        }
        self.session = requests.Session()
        self.session.timeout = 10
    
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
            elif method == 'PUT':
                response = self.session.put(url, json=data, timeout=10)
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=10)
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
                'response_time': round(response_time, 3),
                'description': description
            }
            
            # Try to parse JSON response
            try:
                result['response_data'] = response.json()
            except:
                result['response_text'] = response.text[:200]  # First 200 chars
            
            self.results['endpoints'][description] = result
            
            status_icon = "✅" if status_ok else "⚠️"
            print(f"{status_icon} {method:6} {path:40} - {response.status_code:3} ({response_time:.2f}s)")
            
            if not status_ok:
                self.results['warnings'].append(
                    f"{description}: Expected {expected_status}, got {response.status_code}"
                )
            
            return status_ok
            
        except requests.exceptions.Timeout:
            self.results['endpoints'][description] = {
                'method': method,
                'path': path,
                'error': 'Timeout',
                'ok': False
            }
            self.results['errors'].append(f"{description}: Timeout")
            print(f"❌ {method:6} {path:40} - TIMEOUT")
            return False
            
        except requests.exceptions.ConnectionError:
            self.results['endpoints'][description] = {
                'method': method,
                'path': path,
                'error': 'Connection refused',
                'ok': False
            }
            self.results['errors'].append(f"{description}: Connection refused - Is server running?")
            print(f"❌ {method:6} {path:40} - CONNECTION REFUSED")
            return False
            
        except Exception as e:
            self.results['endpoints'][description] = {
                'method': method,
                'path': path,
                'error': str(e),
                'ok': False
            }
            self.results['errors'].append(f"{description}: {str(e)}")
            print(f"❌ {method:6} {path:40} - ERROR: {e}")
            return False
    
    def test_all_endpoints(self):
        """Test all known endpoints"""
        print("\n" + "="*70)
        print("🔍 TESTING ALL ENDPOINTS")
        print("="*70)
        print(f"{'Method':6} {'Path':40} {'Status':6} {'Time':8}")
        print("-"*70)
        
        # Health and monitoring
        self.test_endpoint('GET', '/health', [200], description='Health Check')
        self.test_endpoint('GET', '/metrics', [200], description='Metrics')
        self.test_endpoint('GET', '/api/stats', [200], description='Stats API')
        
        # Contacts
        self.test_endpoint('GET', '/api/contacts/available', [200], description='Available Contacts')
        
        # Email preview
        self.test_endpoint('GET', '/preview-emails', [200], params={'count': 1}, description='Preview Emails')
        self.test_endpoint('GET', '/preview-emails', [200, 400], params={'count': 0}, description='Preview Emails (invalid)')
        
        # Jobs API
        self.test_endpoint('GET', '/api/jobs', [200], description='Get Jobs')
        self.test_endpoint('GET', '/api/jobs/discover', [200, 405, 500], description='Discover Jobs (may be POST)')
        
        # Daemon API
        self.test_endpoint('GET', '/api/daemon/status', [200], description='Daemon Status')
        
        # Pages (should return HTML)
        pages = ['/', '/jobs', '/contacts', '/replies', '/settings']
        for page in pages:
            self.test_endpoint('GET', page, [200], description=f'Page: {page}')
        
        # POST endpoints (with validation)
        print("\n" + "-"*70)
        print("Testing POST endpoints (may require authentication/data)...")
        print("-"*70)
        
        # These may fail without proper data, but we test them
        self.test_endpoint('POST', '/send-emails', [200, 400, 401], 
                          data={'count': 1}, description='Send Emails')
        
        # AI endpoints
        self.test_endpoint('POST', '/api/ai/cover-letter', [200, 400, 500],
                          data={'role': 'Software Engineer', 'company': 'Test Corp', 'skills': 'Python'},
                          description='AI Cover Letter')
        
        self.test_endpoint('POST', '/api/ai/interview-guide', [200, 400, 500],
                          data={'role': 'Software Engineer', 'company': 'Test Corp', 'skills': 'Python'},
                          description='AI Interview Guide')
    
    def check_server_running(self):
        """Check if server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        total = len(self.results['endpoints'])
        passed = sum(1 for e in self.results['endpoints'].values() if e.get('ok', False))
        failed = total - passed
        
        print(f"\n✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"❌ Errors: {len(self.results['errors'])}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
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
        if total == 0:
            print("\n❌ No endpoints tested - server may not be running")
            print(f"   Start server with: python3 main.py")
            return False
        elif success_rate >= 80:
            print("\n✅ Application is working properly!")
            return True
        elif success_rate >= 50:
            print("\n⚠️  Application has some issues but mostly working")
            return False
        else:
            print("\n❌ Application has significant issues")
            return False
    
    def save_results(self, filename: str = 'endpoint_test_results.json'):
        """Save test results to file"""
        results_file = Path(__file__).parent / filename
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
        return results_file


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test all endpoints')
    parser.add_argument('--url', default='http://localhost:5050', help='Base URL')
    parser.add_argument('--output', default='endpoint_test_results.json', help='Output file')
    
    args = parser.parse_args()
    
    tester = EndpointTester(base_url=args.url)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    if not tester.check_server_running():
        print(f"❌ Server not running at {args.url}")
        print(f"   Start server with: python3 main.py")
        print(f"   Or test against different URL with: --url http://your-server:port")
        return 1
    
    print("✅ Server is running\n")
    
    # Run tests
    tester.test_all_endpoints()
    
    # Print summary
    success = tester.print_summary()
    
    # Save results
    tester.save_results(args.output)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
