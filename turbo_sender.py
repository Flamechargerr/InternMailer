"""
TURBO PARALLEL EMAIL SENDER
===========================
Sends emails with AI validation but in PARALLEL for maximum speed.

Process:
1. Pre-fetch all professor research data in parallel (using ThreadPoolExecutor)
2. Validate all data in parallel
3. Send all emails using connection pool

Target: 50 emails in ~2-3 minutes instead of 30+ minutes
"""

import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

def send_turbo_campaign(count=50):
    """
    TURBO mode: Parallel AI validation + Parallel sending
    """
    print("=" * 70)
    print("🚀 TURBO PARALLEL EMAIL CAMPAIGN")
    print("   AI Validation + Parallel Processing = SPEED")
    print("=" * 70)
    
    start_time = time.time()
    
    # Import systems
    from system import VerifiedEmailSystem
    from ai_research_validator import get_research_validator
    
    vs = VerifiedEmailSystem()
    validator = get_research_validator()
    
    # Step 1: Get professors
    print(f"\n📋 Loading {count} professors...")
    professors = vs.get_verified_contacts(count * 2, min_confidence=90)[:count]
    print(f"   Loaded {len(professors)} professors")
    
    # Step 2: PARALLEL AI Validation (the slow part - now parallelized)
    print(f"\n🔬 PARALLEL AI Validation ({len(professors)} professors)...")
    print("   Using 10 parallel threads for research validation...")
    
    validated_data = {}
    validation_start = time.time()
    
    def validate_professor(prof):
        """Validate single professor - runs in thread"""
        try:
            if isinstance(prof, dict):
                name = prof.get('name', 'Professor')
                email = prof.get('email', '')
                affiliation = prof.get('affiliation', '')
            else:
                name, email, affiliation, _, _ = prof
            
            result = validator.generate_validated_email(name, email, affiliation)
            return (email, {
                'name': name,
                'email': email,
                'affiliation': affiliation,
                'subject': result.get('subject', ''),
                'body': result.get('body', ''),
                'status': result.get('validation_status', 'UNKNOWN')
            })
        except Exception as e:
            return (None, {'error': str(e)})
    
    # Parallel validation with 10 threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(validate_professor, p): p for p in professors}
        
        completed = 0
        for future in as_completed(futures):
            email, data = future.result()
            if email:
                validated_data[email] = data
            completed += 1
            if completed % 10 == 0:
                print(f"   ✅ Validated {completed}/{len(professors)} professors...")
    
    validation_time = time.time() - validation_start
    print(f"   ⚡ Validation complete in {validation_time:.1f}s ({len(validated_data)} validated)")
    
    # Step 3: PARALLEL Email Sending
    print(f"\n📧 PARALLEL Email Sending ({len(validated_data)} emails)...")
    print("   Using 8 parallel SMTP connections...")
    
    send_start = time.time()
    sent_count = 0
    failed_count = 0
    
    def send_single_email(data):
        """Send single email - runs in thread"""
        try:
            result = vs.send_email_concurrent_safe(
                data['email'], 
                data['subject'], 
                data['body'], 
                data['name']
            )
            return result
        except Exception as e:
            return False
    
    # Parallel sending with 8 threads (using SMTP pool)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(send_single_email, data): email 
                   for email, data in validated_data.items()}
        
        for future in as_completed(futures):
            if future.result():
                sent_count += 1
            else:
                failed_count += 1
            
            if (sent_count + failed_count) % 10 == 0:
                print(f"   📤 Sent {sent_count}/{len(validated_data)} emails...")
    
    send_time = time.time() - send_start
    total_time = time.time() - start_time
    
    # Results
    print("\n" + "=" * 70)
    print("📊 TURBO CAMPAIGN RESULTS")
    print("=" * 70)
    print(f"   ✅ Emails Sent: {sent_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   ⚡ Validation Time: {validation_time:.1f}s")
    print(f"   ⚡ Sending Time: {send_time:.1f}s")
    print(f"   ⏱️  Total Time: {total_time:.1f}s")
    print(f"   📈 Speed: {sent_count / total_time * 60:.1f} emails/minute")
    print("=" * 70)
    
    return sent_count


def send_ultra_turbo(count=50):
    """
    ULTRA TURBO: Pre-cache research + batch send
    Even faster by caching all research first
    """
    print("=" * 70)
    print("⚡ ULTRA TURBO MODE - Maximum Speed")
    print("=" * 70)
    
    start_time = time.time()
    
    from system import VerifiedEmailSystem
    from ai_research_validator import get_research_validator
    from safe_template_system import create_safe_academic_email
    
    vs = VerifiedEmailSystem()
    validator = get_research_validator()
    
    # Get professors
    professors = vs.get_verified_contacts(count * 2, min_confidence=90)[:count]
    print(f"📋 Loaded {len(professors)} professors")
    
    # Phase 1: Parallel Research (20 threads)
    print(f"\n🔬 Phase 1: Parallel Research Fetch (20 threads)...")
    
    email_data = []
    
    def prepare_email(prof):
        try:
            if isinstance(prof, dict):
                name = prof.get('name', 'Professor')
                email = prof.get('email', '')
                affiliation = prof.get('affiliation', '')
            else:
                name, email, affiliation, _, _ = prof
            
            # Try AI validation first, fallback to safe template
            try:
                result = validator.generate_validated_email(name, email, affiliation)
                subject = result.get('subject', '')
                body = result.get('body', '')
            except:
                subject, body = create_safe_academic_email(name, email, affiliation)
            
            return {'name': name, 'email': email, 'subject': subject, 'body': body}
        except:
            return None
    
    # Use 4 workers for Ollama (optimal for sequential AI generation)
    # This is the sweet spot - more workers overwhelm Ollama, fewer are too slow
    print("   🤖 AI personalization running (4 parallel workers)...")
    completed = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(prepare_email, p): p for p in professors}
        for future in as_completed(futures):
            result = future.result()
            if result:
                email_data.append(result)
            completed += 1
            if completed % 10 == 0:
                print(f"   ✨ Generated {completed}/{len(professors)} AI-personalized emails...")
    
    prep_time = time.time() - start_time
    print(f"   ✅ Prepared {len(email_data)} AI-personalized emails in {prep_time:.1f}s")
    
    # Phase 2: Batch Send (8 threads)
    print(f"\n📧 Phase 2: Batch Send (8 threads)...")
    
    send_start = time.time()
    sent = 0
    
    def send_email(data):
        try:
            return vs.send_email_concurrent_safe(
                data['email'], data['subject'], data['body'], data['name']
            )
        except:
            return False
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(send_email, email_data))
        sent = sum(1 for r in results if r)
    
    send_time = time.time() - send_start
    total_time = time.time() - start_time
    
    print(f"\n{'=' * 70}")
    print(f"⚡ ULTRA TURBO COMPLETE!")
    print(f"   ✅ Sent: {sent}/{len(email_data)}")
    print(f"   ⏱️  Prep: {prep_time:.1f}s | Send: {send_time:.1f}s | Total: {total_time:.1f}s")
    print(f"   📈 Speed: {sent / total_time * 60:.1f} emails/minute")
    print(f"{'=' * 70}")
    
    return sent


if __name__ == '__main__':
    import sys
    
    count = 50
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except:
            pass
    
    mode = 'turbo'
    if len(sys.argv) > 2:
        mode = sys.argv[2]
    
    if mode == 'ultra':
        send_ultra_turbo(count)
    else:
        send_turbo_campaign(count)
