import sqlite3
conn = sqlite3.connect('campaign_results/email_tracking.db')
c = conn.cursor()
c.execute('SELECT recipient_name, email, contact_type, sent_date FROM sent_emails ORDER BY sent_date DESC LIMIT 10')
results = c.fetchall()
print('LATEST EMAILS SENT:')
print('=' * 60)
for name, email, ctype, date in results:
    icon = '🏢' if ctype == 'corporate' else '🎓'
    print(f'{icon} {date[:16]} - {name} ({email})')
c.execute('SELECT COUNT(*) FROM sent_emails')
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM sent_emails WHERE contact_type = 'corporate'")
corp = c.fetchone()[0]
print()
print(f'Total emails: {total}')
print(f'Corporate: {corp}')
print(f'Academic: {total - corp}')
conn.close()
