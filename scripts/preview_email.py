"""
Generate a preview email to show the user the current template
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_research_validator import get_research_validator
from system import VerifiedEmailSystem

print("=" * 70)
print("📧 EMAIL TEMPLATE PREVIEW")
print("=" * 70)

# Get a sample professor from the database
vs = VerifiedEmailSystem()
contacts = vs.get_verified_contacts(max_contacts=1)

if contacts:
    name, email, affiliation, conf, grade = contacts[0]
    print(f"\n👤 Sample Professor: {name}")
    print(f"📧 Email: {email}")
    print(f"🏫 University: {affiliation}")
    
    # Generate email using the validator
    validator = get_research_validator()
    result = validator.generate_validated_email(name, email, affiliation)
    
    print(f"\n📋 Validation Status: {result.get('validation_status', 'UNKNOWN')}")
    print(f"🎯 Confidence: {result.get('confidence', 0):.0%}")
    
    print("\n" + "=" * 70)
    print("📨 SUBJECT:")
    print("=" * 70)
    print(result.get('subject', 'No subject'))
    
    print("\n" + "=" * 70)
    print("📝 BODY:")
    print("=" * 70)
    print(result.get('body', 'No body'))
    
else:
    print("❌ No contacts available for preview")

print("\n" + "=" * 70)
