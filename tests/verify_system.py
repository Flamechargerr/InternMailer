import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# InternMailer - End-to-End Verification Script

import sys
sys.path.insert(0, '.')

print("🔍 InternMailer System Verification\n")
print("="*50)

# Test 1: Integrated System
print("\n1️⃣ Testing Integrated System...")
try:
    from integrated_system import get_integrated_system
    system = get_integrated_system()
    print("   ✅ Integrated system loaded successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Email Validator
print("\n2️⃣ Testing Email Validator...")
try:
    from email_validator import get_email_validator
    validator = get_email_validator()
    result = validator.validate_email("test@mit.edu")
    print(f"   ✅ Email validation working")
    print(f"      Valid: {result['is_valid']}, Confidence: {result['confidence']:.0%}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Reply Classifier
print("\n3️⃣ Testing Reply Classifier...")
try:
    from reply_classifier import get_reply_classifier
    classifier = get_reply_classifier()
    result = classifier.classify_reply("I'm interested!", "Re: Opportunity")
    print(f"   ✅ Reply classifier working")
    print(f"      Category: {result['category'].value}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Configuration
print("\n4️⃣ Testing Configuration Manager...")
try:
    from config_manager import get_config
    config = get_config()
    limit = config.get('campaign.daily_limit')
    print(f"   ✅ Config manager working")
    print(f"      Daily limit: {limit}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Rate Limiter
print("\n5️⃣ Testing Adaptive Rate Limiter...")
try:
    from adaptive_rate_limiter import get_rate_limiter
    limiter = get_rate_limiter()
    status = limiter.get_reputation_status()
    print(f"   ✅ Rate limiter working")
    print(f"      Reputation: {status['reputation_tier']}")
    print(f"      Recommended limit: {status['recommended_limit']}/day")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: DB Pool
print("\n6️⃣ Testing Database Pooling...")
try:
    from db_pool import get_db_pool
    pool = get_db_pool('email_tracking.db')
    print(f"   ✅ DB pooling working")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("\n🎉 END-TO-END VERIFICATION COMPLETE!")
print("\nTo run actual campaign:")
print("  python system.py --count 10 --template research")
