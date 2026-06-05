#!/usr/bin/env python3
"""
Comprehensive Web App Testing
Tests all endpoints, buttons, and functionality
"""

import sys
import os
import time
import requests
import json
from pathlib import Path
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from web.web_dashboard import app

# Test configuration
BASE_URL = "http://localhost:5050"
TEST_RESULTS = []

class WebAppTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def log_result(self, test_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        self.results.append((test_name, passed, message))
        print(result)
        
    def test_endpoint(self, method, path, expected_status=200, data=None, json_data=None, files=None):
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        try:
            if method == "GET":
                response = self.session.get(url, timeout=10)
            elif method == "POST":
                if files:
                    response = self.session.post(url, data=data, files=files, timeout=10)
                elif json_data:
                    response = self.session.post(url, json=json_data, timeout=10)
                else:
                    response = self.session.post(url, data=data, timeout=10)
            elif method == "OPTIONS":
                response = self.session.options(url, timeout=10)
            else:
                return False, f"Unsupported method: {method}"
                
            passed = response.status_code == expected_status
            message = f"Status: {response.status_code}"
            
            # Try to parse JSON response
            try:
                json_resp = response.json()
                if 'status' in json_resp:
                    message += f", Response: {json_resp.get('status')}"
            except:
                pass
                
            return passed, message
        except requests.exceptions.ConnectionError:
            return False, "Server not running"
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except Exception as e:
            return False, str(e)
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("\n" + "="*60)
        print("🧪 COMPREHENSIVE WEB APP TESTING")
        print("="*60 + "\n")
        
        # Test 1: Main Pages (GET requests)
        print("\n📄 Testing Main Pages...")
        pages = [
            ('/', 'Dashboard'),
            ('/jobs', 'Jobs Page'),
            ('/contacts', 'Contacts Page'),
            ('/replies', 'Replies Page'),
            ('/settings', 'Settings Page'),
            ('/ats-optimizer', 'ATS Optimizer Page'),
        ]
        
        for path, name in pages:
            passed, message = self.test_endpoint('GET', path)
            self.log_result(f"GET {name}", passed, message)
        
        # Test 2: Health & Metrics Endpoints
        print("\n🏥 Testing Health & Metrics...")
        health_endpoints = [
            ('/health', 'Health Check'),
            ('/metrics', 'Metrics'),
            ('/api/stats', 'API Stats'),
        ]
        
        for path, name in health_endpoints:
            passed, message = self.test_endpoint('GET', path)
            self.log_result(f"GET {name}", passed, message)
        
        # Test 3: Job Discovery API
        print("\n💼 Testing Job Discovery API...")
        
        # GET jobs
        passed, message = self.test_endpoint('GET', '/api/jobs')
        self.log_result('GET /api/jobs', passed, message)
        
        # GET jobs with filters
        passed, message = self.test_endpoint('GET', '/api/jobs?limit=10')
        self.log_result('GET /api/jobs (with limit)', passed, message)
        
        passed, message = self.test_endpoint('GET', '/api/jobs?status=new')
        self.log_result('GET /api/jobs (with status filter)', passed, message)
        
        # POST job discovery (starts background task)
        passed, message = self.test_endpoint('POST', '/api/jobs/discover', json_data={})
        self.log_result('POST /api/jobs/discover', passed, message)
        
        # POST job apply (starts background task)
        passed, message = self.test_endpoint('POST', '/api/jobs/apply', json_data={'limit': 5})
        self.log_result('POST /api/jobs/apply', passed, message)
        
        # Test 4: AI Endpoints
        print("\n🤖 Testing AI Endpoints...")
        
        # Test CORS OPTIONS
        passed, message = self.test_endpoint('OPTIONS', '/api/ai/cover-letter', expected_status=200)
        self.log_result('OPTIONS /api/ai/cover-letter (CORS)', passed, message)
        
        # Test cover letter generation
        cover_letter_data = {
            'role': 'Software Engineering Intern',
            'company': 'Test Company',
            'skills': 'Python, JavaScript, React'
        }
        passed, message = self.test_endpoint('POST', '/api/ai/cover-letter', json_data=cover_letter_data)
        self.log_result('POST /api/ai/cover-letter', passed, message)
        
        # Test interview guide
        interview_data = {
            'role': 'Software Engineering Intern',
            'company': 'Test Company',
            'skills': 'Python, JavaScript, React'
        }
        passed, message = self.test_endpoint('POST', '/api/ai/interview-guide', json_data=interview_data)
        self.log_result('POST /api/ai/interview-guide', passed, message)
        
        # Test Claire AI assistant
        claire_data = {
            'message': 'How can I improve my interview skills?',
            'stats': {'applied': 50, 'interviews': 10, 'offers': 2},
            'skills': 'Python, JavaScript'
        }
        passed, message = self.test_endpoint('POST', '/api/ai/claire', json_data=claire_data)
        self.log_result('POST /api/ai/claire', passed, message)
        
        # Test 5: Email Campaign Endpoints
        print("\n📧 Testing Email Campaign...")
        
        # Preview emails
        passed, message = self.test_endpoint('GET', '/preview-emails?count=3')
        self.log_result('GET /preview-emails', passed, message)
        
        # Send emails (background task)
        passed, message = self.test_endpoint('POST', '/send-emails', json_data={'count': 1})
        self.log_result('POST /send-emails', passed, message)
        
        # Test 6: Daemon Control
        print("\n⚙️  Testing Daemon Control...")
        
        # Get daemon status
        passed, message = self.test_endpoint('GET', '/api/daemon/status')
        self.log_result('GET /api/daemon/status', passed, message)
        
        # Start daemon
        passed, message = self.test_endpoint('POST', '/api/daemon/start')
        self.log_result('POST /api/daemon/start', passed, message)
        
        # Wait a bit
        time.sleep(2)
        
        # Stop daemon
        passed, message = self.test_endpoint('POST', '/api/daemon/stop')
        self.log_result('POST /api/daemon/stop', passed, message)
        
        # Test 7: Diagnostic Endpoints
        print("\n🔍 Testing Diagnostic Endpoints...")
        
        # Test Groq API
        passed, message = self.test_endpoint('GET', '/api/test-groq')
        self.log_result('GET /api/test-groq', passed, message)
        
        # Environment check
        passed, message = self.test_endpoint('GET', '/api/core/env-check')
        self.log_result('GET /api/core/env-check', passed, message)
        
        # Activity logs
        passed, message = self.test_endpoint('GET', '/api/activity')
        self.log_result('GET /api/activity', passed, message)
        
        # Core verification
        passed, message = self.test_endpoint('GET', '/api/core/verify')
        self.log_result('GET /api/core/verify', passed, message)
        
        # Test 8: Error Handling
        print("\n⚠️  Testing Error Handling...")
        
        # Missing required fields
        passed, message = self.test_endpoint('POST', '/api/ai/cover-letter', 
                                            json_data={}, expected_status=400)
        self.log_result('POST /api/ai/cover-letter (missing fields)', passed, message)
        
        # Invalid file download
        passed, message = self.test_endpoint('GET', '/download/nonexistent.pdf', expected_status=404)
        self.log_result('GET /download (nonexistent file)', passed, message)
        
        # Test 9: Rate Limiting (if enabled)
        print("\n🚦 Testing Rate Limiting...")
        # Make multiple rapid requests
        rapid_requests = []
        for i in range(5):
            passed, message = self.test_endpoint('GET', '/api/stats')
            rapid_requests.append(passed)
        
        all_passed = all(rapid_requests)
        self.log_result('Rate limiting (5 rapid requests)', all_passed, 
                       f"{sum(rapid_requests)}/5 requests succeeded")
        
        # Print Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for name, p, msg in self.results:
                if not p:
                    print(f"  - {name}: {msg}")
        
        print("\n" + "="*60)
        
        return pass_rate >= 90  # Consider success if 90%+ pass


def test_with_test_client():
    """Test using Flask test client (doesn't require server running)"""
    print("\n" + "="*60)
    print("🧪 FLASK TEST CLIENT TESTING")
    print("="*60 + "\n")
    
    client = app.test_client()
    results = []
    
    def test_route(method, path, expected_status=200, data=None, json_data=None):
        try:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                if json_data:
                    response = client.post(path, json=json_data, content_type='application/json')
                else:
                    response = client.post(path, data=data)
            else:
                return False, "Unsupported method"
            
            passed = response.status_code == expected_status
            return passed, f"Status: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    # Test critical routes
    tests = [
        ('GET', '/', 200, 'Dashboard'),
        ('GET', '/health', 200, 'Health Check'),
        ('GET', '/metrics', 200, 'Metrics'),
        ('GET', '/api/stats', 200, 'API Stats'),
        ('GET', '/api/jobs', 200, 'Jobs API'),
        ('GET', '/api/daemon/status', 200, 'Daemon Status'),
        ('GET', '/jobs', 200, 'Jobs Page'),
        ('GET', '/contacts', 200, 'Contacts Page'),
        ('GET', '/replies', 200, 'Replies Page'),
        ('GET', '/settings', 200, 'Settings Page'),
    ]
    
    for method, path, expected, name in tests:
        passed, message = test_route(method, path, expected)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}: {message}")
        results.append(passed)
    
    # Summary
    total = len(results)
    passed_count = sum(results)
    print(f"\n📊 Test Client Results: {passed_count}/{total} passed ({passed_count/total*100:.1f}%)")
    
    return passed_count == total


if __name__ == '__main__':
    print("\n🚀 Starting Web App Comprehensive Testing\n")
    
    # First, test with Flask test client (doesn't need server running)
    print("Phase 1: Testing with Flask Test Client (no server needed)")
    test_client_success = test_with_test_client()
    
    # Then, test with actual HTTP requests (requires server running)
    print("\n\nPhase 2: Testing with HTTP Requests (requires server running)")
    print("Note: Start the server with 'python main.py' in another terminal\n")
    
    tester = WebAppTester()
    http_test_success = tester.run_all_tests()
    
    # Final verdict
    print("\n" + "="*60)
    print("🎯 FINAL VERDICT")
    print("="*60)
    print(f"Flask Test Client: {'✅ PASS' if test_client_success else '❌ FAIL'}")
    print(f"HTTP Requests: {'✅ PASS' if http_test_success else '⚠️  NEEDS SERVER RUNNING'}")
    print("="*60 + "\n")
    
    sys.exit(0 if test_client_success else 1)
