"""
PREVIEW AI-PERSONALIZED EMAIL
Shows exactly what email will be sent before the campaign
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_research_validator import get_research_validator
from system import VerifiedEmailSystem

print("=" * 70)
print("📧 AI-PERSONALIZED EMAIL PREVIEW")
print("=" * 70)

# Get validator and system
validator = get_research_validator()
vs = VerifiedEmailSystem()

# Get a sample professor
print("\n📋 Getting sample professor...")
contacts = vs.get_verified_contacts(max_contacts=1)

if contacts:
    name, email, affiliation, conf, grade = contacts[0]
    
    print(f"\n👤 PROFESSOR INFO:")
    print(f"   Name: {name}")
    print(f"   Email: {email}")
    print(f"   University: {affiliation}")
    
    print(f"\n🤖 Generating AI-personalized email...")
    print("   Using: Gemini + Ollama + Groq (round-robin)")
    
    # Generate email
    result = validator.generate_validated_email(name, email, affiliation)
    
    print(f"\n✅ Validation Status: {result.get('validation_status', 'UNKNOWN')}")
    print(f"🎯 Research Area: {result.get('research_area', 'Unknown')}")
    print(f"📊 Confidence: {result.get('confidence', 0):.0%}")
    
    print("\n" + "=" * 70)
    print("📨 SUBJECT LINE:")
    print("=" * 70)
    print(result.get('subject', 'No subject'))
    
    print("\n" + "=" * 70)
    print("📝 EMAIL BODY:")
    print("=" * 70)
    body = result.get('body', 'No body generated')
    print(body)
    
    # Validation check
    print("\n" + "=" * 70)
    print("🔍 QUALITY CHECKS:")
    print("=" * 70)
    
    # Check for repetition
    words = body.lower().split()
    repetition_found = False
    for i in range(len(words) - 4):
        phrase = ' '.join(words[i:i+5])
        if body.lower().count(phrase) >= 2:
            print(f"   ⚠️ Repetition: '{phrase[:50]}...'")
            repetition_found = True
            break
    
    if not repetition_found:
        print("   ✅ No phrase repetition detected")
    
    # Check YaanBarpe
    if "cultural tourism" in body.lower() or "tulu nadu" in body.lower():
        print("   ✅ YaanBarpe description is CORRECT (cultural tourism)")
    elif "waste management" in body.lower():
        print("   ❌ YaanBarpe description is WRONG (waste management)")
    
    print("=" * 70)
else:
    print("❌ No professors found for preview")
