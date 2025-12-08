import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test multi-source paper fetching
"""
from ai_research_validator import get_research_validator

validator = get_research_validator()

print("="*60)
print("TESTING MULTI-SOURCE FETCHING")
print("="*60)

# Test 1: Direct call to DBLP (simulating fallback)
print("\n1. Testing DBLP direct call (Professor: Srdjan Capkun)...")
try:
    result = validator._fetch_from_dblp('Srdjan Capkun', 'ethz.ch')
    print(f"   Valid: {result.get('valid')}")
    print(f"   Issue: {result.get('issue')}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: Direct call to OpenAlex (Professor: Srdjan Capkun)
print("\n2. Testing OpenAlex direct call (Professor: Srdjan Capkun)...")
try:
    result = validator._fetch_from_openalex('Srdjan Capkun', 'ethz.ch')
    print(f"   Valid: {result.get('valid')}")
    print(f"   Issue: {result.get('issue')}")
    if result.get('papers'):
        print(f"   Papers found: {len(result['papers'])}")
        print(f"   Title example: {result['papers'][0]['title']}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Main method (should use Semantic Scholar as primary)
print("\n3. Testing Main Method (Professor: Srdjan Capkun)...")
try:
    result = validator.fetch_and_validate_papers('Srdjan Capkun', 'capkun@inf.ethz.ch')
    print(f"   Valid: {result.get('valid')}")
    print(f"   Issue: {result.get('issue')}")
    print(f"   Verification Source: {result.get('verification_source', 'Semantic Scholar (Default)')}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
