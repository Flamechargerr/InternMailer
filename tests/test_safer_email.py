import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test the safer email generation with research area descriptions
"""
from ai_research_validator import get_research_validator
validator = get_research_validator()

print("="*60)
print("TESTING SAFER EMAIL GENERATION")
print("="*60)

# Test 1: Srdjan Capkun (Security researcher at ETH)
print("\n1. Testing Srdjan Capkun at ETH...")
result = validator.generate_validated_email('Srdjan Capkun', 'capkun@inf.ethz.ch', 'ETH Zurich')
print(f"   Status: {result.get('validation_status')}")
print(f"   Research Area: {result.get('research_area', 'N/A')}")
print(f"   Papers Found: {result.get('papers_found', 'N/A')}")
print("\n   Email excerpt:")
body_lines = result.get('body', '').split('\n')
# Show the personalized paragraph
for i, line in enumerate(body_lines):
    if 'following your work' in line.lower() or 'been following' in line.lower():
        print(f"   {body_lines[i]}")
        if i+1 < len(body_lines):
            print(f"   {body_lines[i+1]}")
        break

# Test 2: Yulan He (NLP researcher)
print("\n2. Testing Yulan He at Warwick...")
result = validator.generate_validated_email('Yulan He', 'yulan.he@warwick.ac.uk', 'University of Warwick')
print(f"   Status: {result.get('validation_status')}")
print(f"   Research Area: {result.get('research_area', 'N/A')}")
print(f"   Papers Found: {result.get('papers_found', 'N/A')}")

# Test 3: Elena Glassman (HCI researcher)
print("\n3. Testing Elena Glassman at Harvard...")
result = validator.generate_validated_email('Elena Glassman', 'glassman@seas.harvard.edu', 'Harvard University')
print(f"   Status: {result.get('validation_status')}")
print(f"   Research Area: {result.get('research_area', 'N/A')}")
print(f"   Papers Found: {result.get('papers_found', 'N/A')}")

print("\n" + "="*60)
print("SAFER APPROACH: No specific paper titles cited!")
print("Research areas derived from their actual papers.")
print("="*60)
