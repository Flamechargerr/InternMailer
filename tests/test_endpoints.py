
import sys
import os
import requests
import time
import subprocess
from threading import Thread

# Import Flask app
sys.path.insert(0, os.getcwd())
try:
    from web.web_dashboard import app
except Exception as e:
    print(f"❌ Failed to import web_dashboard: {e}")
    sys.exit(1)

print("🔍 Validating Web Dashboard Endpoints...")

def test_endpoints():
    """Test that all critical endpoints are registered"""
    print("   Test: Checking imports and app initialization... ✅")
    
    # We can't easily start the server and test it in this script without blocking or complexity.
    # But we can verify that the app object has the expected routes registered.
    
    required_routes = [
        '/api/ai/cover-letter',
        '/api/ai/interview-guide',
        '/api/ai/analyze-resume',
        '/api/jobs',
        '/api/jobs/discover',
        '/api/daemon/start'
    ]
    
    registered_routes = [rule.rule for rule in app.url_map.iter_rules()]
    
    missing = []
    for route in required_routes:
        if route not in registered_routes:
            missing.append(route)
            
    if missing:
        print(f"❌ Missing endpoints: {missing}")
        assert False, f"Missing endpoints: {missing}"
        
    print(f"✅ All {len(required_routes)} critical endpoints are registered.")
    print("✅ Web Dashboard restoration successful!")
    assert True

if __name__ == "__main__":
    test_endpoints()
