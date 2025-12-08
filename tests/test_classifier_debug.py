import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reply_classifier import get_reply_classifier

c = get_reply_classifier()

test1 = "Thanks for reaching out! I'm interested in discussing this further."
test2 = "Thank you, but I'm not interested at this time."

r1 = c.classify_reply(test1)
r2 = c.classify_reply(test2)

print(f"Test 1: '{test1}'")
print(f"  Category: {r1['category'].value}")
print(f"  Keywords: {r1['matched_keywords']}")
print()
print(f"Test 2: '{test2}'")  
print(f"  Category: {r2['category'].value}")
print(f"  Keywords: {r2['matched_keywords']}")
