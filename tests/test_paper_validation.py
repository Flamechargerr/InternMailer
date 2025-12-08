import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test the improved paper validation
"""
from ai_research_validator import get_research_validator
validator = get_research_validator()

# Test 1: Srdjan Capkun at ETH
print('Testing Srdjan Capkun at ETH...')
result = validator.fetch_and_validate_papers('Srdjan Capkun', 'capkun@inf.ethz.ch')
print(f'  Valid: {result.get("valid")}')
print(f'  Score: {result.get("verification_score", result.get("score", "N/A"))}')
if result.get('papers'):
    print(f'  Paper: {result["papers"][0]["title"][:60]}...')
else:
    print(f'  Issue: {result.get("issue")}')

# Test 2: Yulan He at Warwick
print()
print('Testing Yulan He at Warwick...')
result = validator.fetch_and_validate_papers('Yulan He', 'yulan.he@warwick.ac.uk')
print(f'  Valid: {result.get("valid")}')
print(f'  Score: {result.get("verification_score", result.get("score", "N/A"))}')
if result.get('papers'):
    print(f'  Paper: {result["papers"][0]["title"][:60]}...')
else:
    print(f'  Issue: {result.get("issue")}')

# Test 3: Elena Glassman at Harvard
print()
print('Testing Elena Glassman at Harvard...')
result = validator.fetch_and_validate_papers('Elena Glassman', 'glassman@seas.harvard.edu')
print(f'  Valid: {result.get("valid")}')
print(f'  Score: {result.get("verification_score", result.get("score", "N/A"))}')
if result.get('papers'):
    print(f'  Paper: {result["papers"][0]["title"][:60]}...')
else:
    print(f'  Issue: {result.get("issue")}')

# Test 4: Neil Lawrence at Cambridge
print()
print('Testing Neil Lawrence at Cambridge...')
result = validator.fetch_and_validate_papers('Neil Lawrence', 'ndl21@cam.ac.uk')
print(f'  Valid: {result.get("valid")}')
print(f'  Score: {result.get("verification_score", result.get("score", "N/A"))}')
if result.get('papers'):
    print(f'  Paper: {result["papers"][0]["title"][:60]}...')
else:
    print(f'  Issue: {result.get("issue")}')
