import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import csv

# Get count of contacted
conn = sqlite3.connect('campaign_results/email_tracking.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(DISTINCT email) FROM sent_emails')
count = cursor.fetchone()[0]
print(f'Total unique emails contacted: {count}')

# Check the CSV for more professors
with open('data/proffesor_clean.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    all_profs = list(reader)
print(f'Total professors in CSV: {len(all_profs)}')

# Get contacted emails
cursor.execute('SELECT email FROM sent_emails')
contacted = {r[0] for r in cursor.fetchall()}

# Find fresh ones
fresh = [p for p in all_profs if p.get('Email') not in contacted]
print(f'Fresh (not contacted): {len(fresh)}')

# Show first 10 fresh
print()
print('First 10 fresh professors:')
for p in fresh[:10]:
    print(f"  {p.get('Name')} - {p.get('Email')} ({p.get('University')})")

conn.close()
