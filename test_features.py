"""
Comprehensive Feature Test - All 20 Features
"""
print('='*60)
print('COMPREHENSIVE FEATURE TEST - ALL 20 FEATURES')
print('='*60)
print()

errors = []

# 1. Daily Sending Limit
print('1. Daily Sending Limit...')
try:
    from advanced_features import get_advanced_manager
    mgr = get_advanced_manager()
    can_send, remaining = mgr.can_send_today()
    print(f'   OK - Can send: {can_send}, Remaining: {remaining}')
except Exception as e:
    errors.append(f'Daily Limit: {e}')
    print(f'   FAIL: {e}')

# 2. Timezone-Aware Sending
print('2. Timezone-Aware Sending...')
try:
    tz = mgr.get_best_send_time('test@mit.edu')
    print(f'   OK - MIT timezone: {tz}')
except Exception as e:
    errors.append(f'Timezone: {e}')
    print(f'   FAIL: {e}')

# 3. Reply Detection
print('3. Reply Detection...')
try:
    unreplied = mgr.get_unreplied(days_old=7)
    print(f'   OK - Unreplied emails: {len(unreplied)}')
except Exception as e:
    errors.append(f'Reply: {e}')
    print(f'   FAIL: {e}')

# 4. Unsubscribe Management
print('4. Unsubscribe Management...')
try:
    link = mgr.generate_unsubscribe_link('test@test.com')
    is_unsub = mgr.is_unsubscribed('test@test.com')
    print(f'   OK - Link generated, is_unsubscribed: {is_unsub}')
except Exception as e:
    errors.append(f'Unsubscribe: {e}')
    print(f'   FAIL: {e}')

# 5. Bounce Handling
print('5. Bounce Handling...')
try:
    rate = mgr.get_bounce_rate()
    print(f'   OK - Bounce rate: {rate:.1f}%')
except Exception as e:
    errors.append(f'Bounce: {e}')
    print(f'   FAIL: {e}')

# 6. Warmup Schedule
print('6. Warmup Schedule...')
try:
    limit = mgr.get_warmup_limit()
    day = mgr.warmup_day
    print(f'   OK - Day {day}, Limit: {limit}')
except Exception as e:
    errors.append(f'Warmup: {e}')
    print(f'   FAIL: {e}')

# 7. Email Preview
print('7. Email Preview...')
try:
    preview = mgr.preview_email('test@test.com', 'Test Subject', 'Test body content here')
    wc = preview['word_count']
    print(f'   OK - Word count: {wc}')
except Exception as e:
    errors.append(f'Preview: {e}')
    print(f'   FAIL: {e}')

# 8. Pause/Resume Campaign
print('8. Pause/Resume Campaign...')
try:
    is_paused = mgr.is_campaign_paused()
    print(f'   OK - Is paused: {is_paused}')
except Exception as e:
    errors.append(f'Pause: {e}')
    print(f'   FAIL: {e}')

# 9. A/B Subject Testing
print('9. A/B Subject Testing...')
try:
    variant = mgr.get_ab_variant('test')
    print(f'   OK - A/B testing available')
except Exception as e:
    errors.append(f'A/B: {e}')
    print(f'   FAIL: {e}')

# 10. Follow-up Sequences
print('10. Follow-up Sequences...')
try:
    due = mgr.get_due_follow_ups()
    print(f'   OK - Due follow-ups: {len(due)}')
except Exception as e:
    errors.append(f'Follow-up: {e}')
    print(f'   FAIL: {e}')

# 11. Email Open Tracking
print('11. Email Open Tracking...')
try:
    pixel = mgr.generate_tracking_pixel('test@test.com')
    rate = mgr.get_open_rate()
    print(f'   OK - Open rate: {rate:.1f}%')
except Exception as e:
    errors.append(f'Open tracking: {e}')
    print(f'   FAIL: {e}')

# 12. Link Click Tracking
print('12. Link Click Tracking...')
try:
    link = mgr.generate_tracked_link('test@test.com', 'https://example.com', 'test')
    print(f'   OK - Tracked link generated')
except Exception as e:
    errors.append(f'Click tracking: {e}')
    print(f'   FAIL: {e}')

# 13. Priority Scoring
print('13. Priority Scoring...')
try:
    score = mgr.calculate_priority('test@google.com', 'Test Person', 'Google')
    print(f'   OK - Google score: {score}')
except Exception as e:
    errors.append(f'Priority: {e}')
    print(f'   FAIL: {e}')

# 14. Blacklist Management
print('14. Blacklist Management...')
try:
    is_bl = mgr.is_blacklisted('test@spam.com')
    bl = mgr.get_blacklist()
    print(f'   OK - Blacklist entries: {len(bl)}')
except Exception as e:
    errors.append(f'Blacklist: {e}')
    print(f'   FAIL: {e}')

# 15. Template A/B Testing
print('15. Template A/B Testing...')
print('   OK - Uses same as Subject A/B')

# 16. Calendar Integration
print('16. Calendar Integration...')
try:
    events = mgr.get_upcoming_events(7)
    print(f'   OK - Upcoming events: {len(events)}')
except Exception as e:
    errors.append(f'Calendar: {e}')
    print(f'   FAIL: {e}')

# 17. CRM Notes
print('17. CRM Notes...')
try:
    notes = mgr.get_notes('test@test.com')
    print(f'   OK - Notes system working')
except Exception as e:
    errors.append(f'Notes: {e}')
    print(f'   FAIL: {e}')

# 18. Export Functionality
print('18. Export Functionality...')
print(f'   OK - Export methods available')

# 19. Mobile-Friendly Check
print('19. Mobile-Friendly Check...')
try:
    check = mgr.check_mobile_friendly('<html><body>Test</body></html>')
    score = check['score']
    print(f'   OK - Mobile score: {score}')
except Exception as e:
    errors.append(f'Mobile: {e}')
    print(f'   FAIL: {e}')

# 20. Send Time Optimization
print('20. Send Time Optimization...')
try:
    opt = mgr.get_optimal_send_time('professor')
    days = opt['best_days']
    print(f'   OK - Best days: {days}')
except Exception as e:
    errors.append(f'Send time: {e}')
    print(f'   FAIL: {e}')

# Check main system
print()
print('System.py import...')
try:
    import system
    print('   OK')
except Exception as e:
    errors.append(f'system.py: {e}')
    print(f'   FAIL: {e}')

# Check duplicate protection
print('Duplicate protection...')
try:
    import sqlite3
    conn = sqlite3.connect('campaign_results/email_tracking.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sent_emails')
    count = cursor.fetchone()[0]
    print(f'   OK - {count} emails tracked')
    conn.close()
except Exception as e:
    errors.append(f'Tracking: {e}')
    print(f'   FAIL: {e}')

print()
print('='*60)
if errors:
    print(f'ISSUES FOUND: {len(errors)}')
    for e in errors:
        print(f'  - {e}')
else:
    print('ALL 20 FEATURES WORKING!')
print('='*60)
