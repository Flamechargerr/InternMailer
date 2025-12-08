"""
DATABASE SYNC CHECK
Identifies which databases are out of sync
"""
import sqlite3
import os

print("=" * 60)
print("🔄 DATABASE SYNCHRONIZATION CHECK")
print("=" * 60)

# Get all emails from each database
emails_by_db = {}

# DB 1: campaign_results/email_tracking.db
db1_path = 'campaign_results/email_tracking.db'
if os.path.exists(db1_path):
    db = sqlite3.connect(db1_path)
    cur = db.cursor()
    cur.execute("SELECT email FROM sent_emails")
    emails_by_db['campaign_results/email_tracking.db'] = set(r[0] for r in cur.fetchall())
    print(f"\n{db1_path}: {len(emails_by_db['campaign_results/email_tracking.db'])} emails")

# DB 2: email_tracking.db (root)
db2_path = 'email_tracking.db'
if os.path.exists(db2_path):
    db = sqlite3.connect(db2_path)
    cur = db.cursor()
    cur.execute("SELECT email FROM sent_emails")
    emails_by_db['email_tracking.db'] = set(r[0] for r in cur.fetchall())
    print(f"{db2_path}: {len(emails_by_db['email_tracking.db'])} emails")

# DB 3: campaign_results/advanced_tracking.db
db3_path = 'campaign_results/advanced_tracking.db'
if os.path.exists(db3_path):
    db = sqlite3.connect(db3_path)
    cur = db.cursor()
    # Get email column
    cur.execute("PRAGMA table_info(email_tracking)")
    cols = [c[1] for c in cur.fetchall()]
    email_col = next((c for c in cols if 'email' in c.lower() or 'recipient' in c.lower()), None)
    if email_col:
        cur.execute(f"SELECT {email_col} FROM email_tracking")
        emails_by_db['advanced_tracking.db'] = set(r[0] for r in cur.fetchall() if r[0])
        print(f"{db3_path}: {len(emails_by_db['advanced_tracking.db'])} emails")

# Find sync issues
print("\n" + "=" * 60)
print("🔍 SYNC ANALYSIS")
print("=" * 60)

if len(emails_by_db) >= 2:
    db_names = list(emails_by_db.keys())
    for i, db1 in enumerate(db_names):
        for db2 in db_names[i+1:]:
            set1 = emails_by_db[db1]
            set2 = emails_by_db[db2]
            
            only_in_1 = set1 - set2
            only_in_2 = set2 - set1
            common = set1 & set2
            
            print(f"\n{db1} vs {db2}:")
            print(f"  Common: {len(common)}")
            print(f"  Only in {db1}: {len(only_in_1)}")
            print(f"  Only in {db2}: {len(only_in_2)}")
            
            if only_in_1:
                print(f"    Missing from {db2}: {list(only_in_1)[:3]}...")
            if only_in_2:
                print(f"    Missing from {db1}: {list(only_in_2)[:3]}...")

# Check which DBs are used by which scripts
print("\n" + "=" * 60)
print("📝 SCRIPT-TO-DB MAPPING")
print("=" * 60)

script_db_mapping = {
    'turbo_sender.py': 'email_tracking.db (root)',
    'system.py': 'campaign_results/email_tracking.db',
    'jarvis_mode.py': 'Uses system.py -> campaign_results/',
}

for script, db in script_db_mapping.items():
    print(f"  {script} -> {db}")

print("\n⚠️  ISSUE: Different scripts use different databases!")
print("   This causes sync problems.")
