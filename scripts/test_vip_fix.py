
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_research_validator import get_research_validator
import json

def test_vip_and_caps():
    v = get_research_validator()
    
    # Test Olga (VIP)
    print("Testing Olga (VIP)...")
    res1 = v.generate_validated_email("Olga Russakovsky", "olgarus@cs.princeton.edu", "Princeton University")
    print(f"Olga Subject: {res1['subject']}")
    print(f"Olga Body Preview: {res1['body'][:200]}...")
    if "human-AI" in res1['body']:
         print("CAPS CHECK: 'human-AI' found! ✅")
    else:
         print("CAPS CHECK: 'human-AI' NOT found! ❌")

    # Test Generic with Human-AI input
    print("\nTesting Generic Human-AI...")
    # Mocking papers to force Human-AI detection
    # This is harder to mock without changing code, but we can call _generate_verified_personalized_email directly
    res2 = v._generate_verified_personalized_email(
        "Dr. Test", "Univ Test", 
        [{'title':'Human-AI Interaction study', 'author_confidence':1.0, 'source':'Scholar'}], 
        "Human-AI Interaction"
    )
    print(f"Generic Body Preview: {res2['body'][-500:]}")
    if "human-AI" in res2['body']:
         print("CAPS CHECK (Generic): 'human-AI' found! ✅")
    else:
         print("CAPS CHECK (Generic): 'human-AI' NOT found! ❌")
         print(res2['body'])

if __name__ == "__main__":
    test_vip_and_caps()
