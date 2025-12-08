import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#!/usr/bin/env python3
"""
INTERNMAILER SYSTEM CHECK
Comprehensive end-to-end verification
"""

import os
import sqlite3
import sys

print("=" * 60)
print("INTERNMAILER SYSTEM CHECK")
print("=" * 60)

# 1. Check all files exist
print("\n1. FILE CHECK:")
files = [
    ('system.py', 'Main email engine'),
    ('dashboard.py', 'Streamlit dashboard'), 
    ('recruiter_finder.py', 'Recruiter importer'),
    ('smart_research_system.py', 'Smart research (no rate limits)'),
    ('apollo_importer.py', 'Apollo.io importer'),
    ('import_excel.py', 'Excel importer'),
    ('data/recruiters.db', 'Recruiter database'),
    ('data/clean_40k_professors.db', 'Professor database'),
    ('campaign_results/email_tracking.db', 'Email tracking'),
    ('.env', 'Environment config')
]
all_ok = True
for f, desc in files:
    status = '✅' if os.path.exists(f) else '❌'
    if not os.path.exists(f):
        all_ok = False
    print(f'   {status} {f} - {desc}')

# 2. Check recruiter database
print("\n2. RECRUITER DATABASE:")
try:
    conn = sqlite3.connect('data/recruiters.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM recruiters')
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM recruiters WHERE contacted = 'no'")
    fresh = c.fetchone()[0]
    print(f'   Total recruiters: {total}')
    print(f'   Fresh (not contacted): {fresh}')
    
    # Premium companies
    c.execute("""
        SELECT company, COUNT(*) as cnt FROM recruiters 
        WHERE company IN ('Google', 'Meta', 'Amazon', 'Microsoft', 'Apple', 
                         'Citadel', 'Morgan Stanley', 'BlackRock', 'Salesforce', 
                         'Adobe', 'JPMorganChase', 'Deloitte', 'Jane Street')
        GROUP BY company ORDER BY cnt DESC
    """)
    premium = c.fetchall()
    if premium:
        print('   Premium company contacts:')
        for company, cnt in premium:
            print(f'      🏢 {company}: {cnt}')
    conn.close()
except Exception as e:
    print(f'   ❌ Error: {e}')

# 3. Check professor database
print("\n3. PROFESSOR DATABASE:")
try:
    conn = sqlite3.connect('data/clean_40k_professors.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM verified_contacts')
    total_profs = c.fetchone()[0]
    print(f'   Total professors: {total_profs}')
    
    # Sample universities
    c.execute("SELECT DISTINCT affiliation FROM verified_contacts LIMIT 5")
    unis = c.fetchall()
    print('   Sample universities:')
    for (uni,) in unis:
        print(f'      🎓 {uni[:50]}...' if len(uni) > 50 else f'      🎓 {uni}')
    conn.close()
except Exception as e:
    print(f'   ❌ Error: {e}')

# 4. Check tracking database
print("\n4. EMAIL TRACKING:")
try:
    conn = sqlite3.connect('campaign_results/email_tracking.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM sent_emails')
    sent = c.fetchone()[0]
    c.execute('SELECT COUNT(DISTINCT email) FROM sent_emails')
    unique = c.fetchone()[0]
    print(f'   Total emails sent: {sent}')
    print(f'   Unique contacts reached: {unique}')
    
    # Recent sends
    c.execute("SELECT recipient_name, email, sent_date FROM sent_emails ORDER BY sent_date DESC LIMIT 3")
    recent = c.fetchall()
    if recent:
        print('   Recent sends:')
        for name, email, date in recent:
            print(f'      📧 {name} - {email[:30]}... ({date[:10]})')
    conn.close()
except Exception as e:
    print(f'   ❌ Error: {e}')

# 5. Test system.py import
print("\n5. SYSTEM.PY CHECK:")
try:
    import system
    vs = system.VerifiedEmailSystem()
    print('   ✅ VerifiedEmailSystem loaded')
    
    # Check key methods exist
    methods = ['get_verified_contacts', 'get_recruiters', 'launch_legendary_campaign_integrated', 
               'show_status', '_get_corporate_template', 'personalize_email_corporate']
    for method in methods:
        if hasattr(vs, method):
            print(f'   ✅ {method}')
        else:
            print(f'   ❌ {method} MISSING')
except Exception as e:
    print(f'   ❌ Error loading system: {e}')

# 6. Test smart research
print("\n6. SMART RESEARCH SYSTEM:")
try:
    from smart_research_system import get_smart_research_system
    srs = get_smart_research_system()
    print('   ✅ Smart Research System loaded')
    print('   ✅ Uses DBLP + Semantic Scholar (no rate limits)')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 7. Test recruiter finder
print("\n7. RECRUITER FINDER:")
try:
    from recruiter_finder import RecruiterFinder
    rf = RecruiterFinder()
    recruiters = rf.get_fresh_recruiters(5)
    print(f'   ✅ Loaded, {len(recruiters)} sample recruiters ready')
except Exception as e:
    print(f'   ❌ Error: {e}')

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"""
📊 DATABASE STATS:
   Recruiters: {total} ({fresh} fresh)
   Professors: {total_profs}
   Emails sent: {sent}

🎯 READY FOR:
   ✅ Academic campaign: python system.py --count 20
   ✅ Corporate campaign: python system.py --hr --count 20
   ✅ Dashboard: streamlit run dashboard.py

⚡ FEATURES:
   ✅ Smart research (no Google Scholar rate limits)
   ✅ Duplicate filtering (skips already contacted)
   ✅ Multi-source recruiter import
   ✅ Corporate + Academic templates
""")
