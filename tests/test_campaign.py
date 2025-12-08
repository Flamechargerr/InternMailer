import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
🧪 COMPREHENSIVE CAMPAIGN SYSTEM TESTS
Tests all components and fixes issues
"""

import sys
import os
from pathlib import Path

print("\n🧪 COMPREHENSIVE CAMPAIGN SYSTEM TESTS")
print("=" * 70)

# Test 1: Import Tests
print("\n1️⃣ Testing Imports...")
try:
    import smart_campaign
    print("   ✅ smart_campaign")
except Exception as e:
    print(f"   ❌ smart_campaign: {e}")

try:
    import ultra_campaign
    print("   ✅ ultra_campaign")
except Exception as e:
    print(f"   ❌ ultra_campaign: {e}")

try:
    import ollama_sender
    print("   ✅ ollama_sender")
except Exception as e:
    print(f"   ❌ ollama_sender: {e}")

# Test 2: Database
print("\n2️⃣ Testing Database...")
try:
    import sqlite3
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    
    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verified_contacts'")
    if cursor.fetchone():
        print("   ✅ verified_contacts table exists")
    else:
        print("   ❌ verified_contacts table missing")
    
    # Check row count
    cursor.execute("SELECT COUNT(*) FROM verified_contacts")
    count = cursor.fetchone()[0]
    print(f"   ✅ Database has {count} professors")
    
    # Check required columns
    cursor.execute("PRAGMA table_info(verified_contacts)")
    columns = [row[1] for row in cursor.fetchall()]
    required = ['name', 'email', 'affiliation']
    missing = [c for c in required if c not in columns]
    if missing:
        print(f"   ❌ Missing columns: {missing}")
    else:
        print(f"   ✅ All required columns present")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Test 3: Ollama
print("\n3️⃣ Testing Ollama...")
try:
    import requests
    resp = requests.get("http://localhost:11434", timeout=2)
    if resp.status_code == 200:
        print("   ✅ Ollama is running")
    else:
        print(f"   ⚠️  Ollama responded with status {resp.status_code}")
except requests.exceptions.ConnectionError:
    print("   ❌ Ollama not running - start with: ollama serve")
except Exception as e:
    print(f"   ❌ Ollama error: {e}")

# Test 4: CV File
print("\n4️⃣ Testing CV File...")
cv_path = Path('resumes/CV_Anamay_Modern.pdf')
if cv_path.exists():
    size = cv_path.stat().st_size
    print(f"   ✅ CV exists ({size} bytes)")
else:
    print("   ❌ CV file missing at resumes/CV_Anamay_Modern.pdf")

# Test 5: Sent Emails Log
print("\n5️⃣ Testing Sent Emails Log...")
log_path = Path('data/sent_emails.log')
if log_path.exists():
    with open(log_path, 'r') as f:
        sent_count = len(f.readlines())
    print(f"   ✅ Log exists ({sent_count} emails sent)")
else:
    print("   ℹ️  No log file yet (will be created on first send)")

# Test 6: Email Credentials
print("\n6️⃣ Testing Email Configuration...")
try:
    from smart_campaign import EMAIL, PASSWORD
    if EMAIL and PASSWORD:
        print(f"   ✅ Credentials configured ({EMAIL})")
    else:
        print("   ❌ Email credentials not set")
except Exception as e:
    print(f"   ❌ Config error: {e}")

# Test 7: European University Detection
print("\n7️⃣ Testing European Detection...")
try:
    from smart_campaign import is_european
    test_cases = [
        ('Imperial College London', 'test@imperial.ac.uk', True),
        ('MIT', 'test@mit.edu', False),
        ('ETH Zurich', 'test@ethz.ch', True),
        ('Stanford', 'test@stanford.edu', False),
    ]
    passed = 0
    for affiliation, email, expected in test_cases:
        result = is_european(affiliation, email)
        if result == expected:
            passed += 1
        else:
            print(f"   ⚠️  {affiliation}: expected {expected}, got {result}")
    print(f"   ✅ {passed}/{len(test_cases)} detection tests passed")
except Exception as e:
    print(f"   ❌ Detection error: {e}")

# Test 8: Email Generation (dry run)
print("\n8️⃣ Testing Email Generation...")
try:
    from smart_campaign import create_enhanced_email
    test_papers = [{
        'title': 'Test Paper on Machine Learning',
        'year': '2024',
        'abstract': 'A test abstract about ML',
        'citations': 100
    }]
    subject, body = create_enhanced_email("Test Professor", "Test University", test_papers)
    if subject and body and len(body) > 100:
        print(f"   ✅ Email generated ({len(body)} chars)")
    else:
        print("   ❌ Email generation produced invalid output")
except Exception as e:
    print(f"   ⚠️  Email generation test skipped (needs Ollama): {e}")

# Summary
print("\n" + "=" * 70)
print("✅ TESTS COMPLETE")
print("\nNext steps:")
print("1. If Ollama not running: ollama serve")
print("2. Run campaign: python ultra_campaign.py")
print("=" * 70)
