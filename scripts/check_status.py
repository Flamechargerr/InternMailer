import sqlite3
import os
from datetime import datetime, date

print("=== COMPREHENSIVE EMAIL STATUS CHECK ===\n")
print(f"Current Date: {date.today()}\n")

# Check ALL tracking databases
dbs_to_check = [
    'campaign_results/email_tracking.db',
    'campaign_results/advanced_tracking.db',
    'email_tracking.db',
    'data/sent_emails.db'
]

total_today = 0

for db_path in dbs_to_check:
    if os.path.exists(db_path):
        print(f"\n📁 {db_path}")
        db = sqlite3.connect(db_path)
        cur = db.cursor()
        
        # Get all tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cur.fetchall()]
        
        for table in tables:
            if 'sqlite' in table.lower():
                continue
                
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            
            if count > 0:
                print(f"  {table}: {count} rows")
                
                # Check for date columns and count today
                cur.execute(f"PRAGMA table_info({table})")
                cols = [c[1] for c in cur.fetchall()]
                
                for col in cols:
                    if any(x in col.lower() for x in ['date', 'time', 'sent', 'created']):
                        try:
                            # Try both date formats
                            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE '2025-12-08%'")
                            today_count = cur.fetchone()[0]
                            if today_count > 0:
                                print(f"    -> TODAY (Dec 8): {today_count}")
                                total_today += today_count
                        except:
                            pass

# Check turbo_sender log file
log_files = ['campaign_results/turbo_campaign.log', 'campaign_results/ultra_campaign.log']
for log_file in log_files:
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            today_lines = [l for l in lines if '2025-12-08' in l]
            if today_lines:
                print(f"\n📄 {log_file}: {len(today_lines)} entries today")

print(f"\n{'='*50}")
print(f"TOTAL EMAILS SENT TODAY: {total_today}")
print(f"GMAIL DAILY LIMIT: 500")
print(f"REMAINING: {500 - total_today}")
print(f"{'='*50}")
