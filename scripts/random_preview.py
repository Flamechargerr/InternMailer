"""
Generate a random professor email preview - ASCII only output
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress logging
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("=" * 70)
print("RANDOM PROFESSOR EMAIL PREVIEW")
print("=" * 70)

from ai_research_validator import get_research_validator
from system import VerifiedEmailSystem

validator = get_research_validator()
vs = VerifiedEmailSystem()

print("\nGetting random professor...")
contacts = vs.get_verified_contacts(max_contacts=5)

if contacts:
    import random
    prof = random.choice(contacts)
    name, email, affiliation, conf, grade = prof
    
    print("\n" + "-" * 70)
    print("PROFESSOR INFO:")
    print("-" * 70)
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"University: {affiliation}")
    print(f"Grade: {grade} | Confidence: {conf}%")
    
    print("\nGenerating AI-personalized email...")
    result = validator.generate_validated_email(name, email, affiliation)
    
    print("\n" + "-" * 70)
    print(f"Status: {result.get('validation_status', 'UNKNOWN')}")
    print(f"Research Area: {result.get('research_area', 'Unknown')}")
    print("-" * 70)
    
    print("\n" + "=" * 70)
    print("SUBJECT:")
    print("=" * 70)
    print(result.get('subject', 'No subject'))
    
    print("\n" + "=" * 70)
    print("EMAIL BODY:")
    print("=" * 70)
    print(result.get('body', 'No body'))
    print("=" * 70)
else:
    print("No professors found")
