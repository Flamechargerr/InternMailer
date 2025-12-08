"""
COMPREHENSIVE EMAIL SYSTEM AUDIT
Cross-verifies all databases and logs for synchronization
"""
import sqlite3
import os
from datetime import datetime, date
from collections import defaultdict

print("=" * 60)
print("🔍 COMPREHENSIVE EMAIL SYSTEM AUDIT")
print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

today_str = "2025-12-08"
email_records = defaultdict(list)  # email -> [source1, source2, ...]

# === 1. Check campaign_results/email_tracking.db ===
db1_path = 'campaign_results/email_tracking.db'
if os.path.exists(db1_path):
    print(f"\n📁 SOURCE 1: {db1_path}")
    db = sqlite3.connect(db1_path)
    cur = db.cursor()
    
    # sent_emails table
    cur.execute("SELECT COUNT(*) FROM sent_emails")
    total = cur.fetchone()[0]
    print(f"  sent_emails total: {total}")
    
    cur.execute("SELECT email, sent_date FROM sent_emails")
    for row in cur.fetchall():
        email, sent_date = row
        if sent_date and today_str in str(sent_date):
            email_records[email].append('email_tracking.db/sent_emails')

# === 2. Check campaign_results/advanced_tracking.db ===
db2_path = 'campaign_results/advanced_tracking.db'
if os.path.exists(db2_path):
    print(f"\n📁 SOURCE 2: {db2_path}")
    db = sqlite3.connect(db2_path)
    cur = db.cursor()
    
    # email_tracking table
    cur.execute("SELECT COUNT(*) FROM email_tracking")
    total = cur.fetchone()[0]
    print(f"  email_tracking total: {total}")
    
    # Get columns
    cur.execute("PRAGMA table_info(email_tracking)")
    cols = [c[1] for c in cur.fetchall()]
    print(f"  columns: {cols}")
    
    # Find date column and email column
    date_col = next((c for c in cols if 'date' in c.lower() or 'time' in c.lower() or 'sent' in c.lower()), None)
    email_col = next((c for c in cols if 'email' in c.lower() or 'recipient' in c.lower()), None)
    
    if date_col and email_col:
        cur.execute(f"SELECT {email_col}, {date_col} FROM email_tracking")
        for row in cur.fetchall():
            email, sent_date = row
            if sent_date and today_str in str(sent_date):
                email_records[email].append('advanced_tracking.db/email_tracking')

# === 3. Check root email_tracking.db ===
db3_path = 'email_tracking.db'
if os.path.exists(db3_path):
    print(f"\n📁 SOURCE 3: {db3_path}")
    db = sqlite3.connect(db3_path)
    cur = db.cursor()
    
    cur.execute("SELECT COUNT(*) FROM sent_emails")
    total = cur.fetchone()[0]
    print(f"  sent_emails total: {total}")
    
    # Get columns
    cur.execute("PRAGMA table_info(sent_emails)")
    cols = [c[1] for c in cur.fetchall()]
    print(f"  columns: {cols}")
    
    date_col = next((c for c in cols if 'date' in c.lower() or 'time' in c.lower() or 'sent' in c.lower()), None)
    email_col = next((c for c in cols if 'email' in c.lower() or 'recipient' in c.lower()), None)
    
    if date_col and email_col:
        cur.execute(f"SELECT {email_col}, {date_col} FROM sent_emails")
        for row in cur.fetchall():
            email, sent_date = row
            if sent_date and today_str in str(sent_date):
                email_records[email].append('email_tracking.db/sent_emails')

# === 4. Check Jarvis log ===
jarvis_log = 'campaign_results/jarvis_log.txt'
jarvis_today = 0
if os.path.exists(jarvis_log):
    print(f"\n📁 SOURCE 4: {jarvis_log}")
    with open(jarvis_log, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        today_lines = [l for l in lines if today_str in l]
        print(f"  Log entries today: {len(today_lines)}")
        
        # Count email sends mentioned
        send_lines = [l for l in today_lines if 'email' in l.lower() and ('sent' in l.lower() or 'send' in l.lower())]
        jarvis_today = len(send_lines)
        print(f"  Email-related entries: {jarvis_today}")

# === 5. Check turbo/ultra campaign logs ===
for log_name in ['turbo_campaign.log', 'ultra_campaign.log', 'campaign.log']:
    log_path = f'campaign_results/{log_name}'
    if os.path.exists(log_path):
        print(f"\n📁 SOURCE 5: {log_path}")
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            today_mentions = content.count(today_str)
            print(f"  Today mentions: {today_mentions}")

# === SUMMARY ===
print("\n" + "=" * 60)
print("📊 AUDIT SUMMARY")
print("=" * 60)

unique_emails_today = len(email_records)
print(f"\n✉️  UNIQUE EMAILS SENT TODAY: {unique_emails_today}")

# Check for duplicates (same email in multiple DBs)
duplicated = {e: sources for e, sources in email_records.items() if len(sources) > 1}
if duplicated:
    print(f"\n⚠️  DUPLICATED ACROSS DATABASES: {len(duplicated)} emails")
    print("  (These are tracked in multiple DBs but represent single sends)")

print(f"\n📈 GMAIL LIMIT STATUS:")
print(f"   Daily Limit: 500")
print(f"   Sent Today:  {unique_emails_today}")
print(f"   Remaining:   {500 - unique_emails_today}")

if unique_emails_today >= 500:
    print("\n🚨 WARNING: At or over Gmail daily limit!")
elif unique_emails_today >= 400:
    print("\n⚠️  CAUTION: Approaching Gmail daily limit")
else:
    print("\n✅ Within safe sending limits")

# Show sample of today's emails
if email_records:
    print(f"\n📧 Sample of today's recipients (first 5):")
    for i, (email, sources) in enumerate(list(email_records.items())[:5]):
        print(f"   {i+1}. {email}")
        
print("\n" + "=" * 60)
