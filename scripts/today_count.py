"""
ACCURATE TODAY COUNT - Checks ALL databases for Dec 8 emails
"""
import sqlite3
import os

print("=" * 60)
print("📊 ACCURATE TODAY (DEC 8) EMAIL COUNT")
print("=" * 60)

today = "2025-12-08"
total_today = 0

# Check all databases
databases = [
    ('campaign_results/unified_tracking.db', 'sent_emails', 'sent_date'),
    ('email_tracking.db', 'sent_emails', 'date'),
    ('campaign_results/email_tracking.db', 'sent_emails', 'sent_date'),
    ('campaign_results/advanced_tracking.db', 'email_tracking', 'sent_at'),
]

for db_path, table, date_col in databases:
    if os.path.exists(db_path):
        try:
            db = sqlite3.connect(db_path)
            c = db.cursor()
            c.execute(f"SELECT COUNT(*) FROM {table} WHERE {date_col} LIKE '{today}%'")
            count = c.fetchone()[0]
            if count > 0:
                print(f"📁 {db_path}")
                print(f"   Today (Dec 8): {count} emails")
                total_today = max(total_today, count)  # Take the highest (most complete)
            db.close()
        except Exception as e:
            print(f"⚠️  {db_path}: {e}")

print()
print("=" * 60)
print(f"📧 EMAILS SENT TODAY: {total_today}")
print(f"📊 GMAIL LIMIT: 500")
print(f"✅ REMAINING: {500 - total_today}")
print("=" * 60)
