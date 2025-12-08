import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3

conn = sqlite3.connect('data/recruiters.db')
cursor = conn.cursor()

# Count verified vs total
cursor.execute('SELECT COUNT(*) FROM recruiters')
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM recruiters WHERE verified = 'yes'")
verified = cursor.fetchone()[0]

print(f'TOTAL RECRUITERS IN DATABASE: {total}')
print(f'VERIFIED FROM WEB: {verified}')
print()
print('='*60)
print('VERIFIED RECRUITERS (Official Emails):')
print('='*60)
cursor.execute("SELECT full_name, email, company, title FROM recruiters WHERE verified = 'yes' ORDER BY company")
for r in cursor.fetchall():
    print(f'{r[2]:20} | {r[0]:35} | {r[1]}')

conn.close()
