"""
Verified Recruiter Emails - Scraped from official sources
"""
import sqlite3
from datetime import datetime

# Connect to recruiters database
conn = sqlite3.connect('data/recruiters.db')
cursor = conn.cursor()

# Verified emails from web search - GENUINE, NOT PREDICTED
verified_recruiters = [
    # TCS
    ("TCS Careers", "careers@tcs.com", "TCS", "General Recruitment"),
    ("TCS Xplore Support", "xplore.support@tcs.com", "TCS", "Campus Program"),
    ("TCS CBO Campus", "CBOCampus.support1@tcs.com", "TCS", "Campus Business Operations"),
    ("TCS Talent Acquisition", "head.talentacquistion@tcs.com", "TCS", "Talent Acquisition Head"),
    ("TCS Freshers Recruitment", "freshers.recruitment@tcs.com", "TCS", "Freshers Hiring"),
    ("TCS Remote Internship", "rio.support@tcs.com", "TCS", "Remote Internship Program"),
    ("TCS BPS Hiring", "tcsbps.support@tcs.com", "TCS", "BPS Hiring"),
    
    # Infosys
    ("Infosys HR", "askus@infosys.com", "Infosys", "General HR"),
    ("Infosys Campus", "Infosys_LPCampus@infosys.com", "Infosys", "Campus Recruitment"),
    ("Infosys InStep Team", "InStep_team@infosys.com", "Infosys", "International Internship"),
    ("Infosys Intern", "Intern@Infosys.com", "Infosys", "Internship Program"),
    ("Infosys InStep APAC", "inStep_apac@infosys.com", "Infosys", "Asia Pacific Internships"),
    ("Infosys Talent Acquisition", "Talent.Acquisition@infosys.com", "Infosys", "Talent Acquisition"),
    ("Infosys Recruitment Help", "Infy_REC_Helpdesk@infosys.com", "Infosys", "Recruitment Support"),
    
    # Wipro
    ("Wipro Recruitment Help", "helpdesk.recruitment@wipro.com", "Wipro", "Recruitment Queries"),
    ("Wipro Campus Hiring", "manager.campus@wipro.com", "Wipro", "Campus Hiring Manager"),
    
    # Goldman Sachs
    ("Goldman Sachs Engineering Campus", "enggcampushiringprog@gs.com", "Goldman Sachs", "Engineering Campus Hiring"),
    ("Goldman Sachs HCM Asia", "GS-HCM-Help-Asia@hk.email.gs.com", "Goldman Sachs", "HR Asia"),
    
    # Amazon
    ("Amazon Future Engineer India", "afe-in@amazon.com", "Amazon", "Future Engineer Program"),
]

# Check existing columns
cursor.execute("PRAGMA table_info(recruiters)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Existing columns: {columns}")

# Add recruiters
added = 0
skipped = 0

for r in verified_recruiters:
    name, email, company, title = r
    
    # Check if already exists
    cursor.execute("SELECT 1 FROM recruiters WHERE email = ?", (email,))
    if cursor.fetchone():
        print(f"  SKIP (exists): {email}")
        skipped += 1
        continue
    
    # Insert based on available columns
    try:
        cursor.execute("""
            INSERT INTO recruiters (full_name, email, company, title, source, imported_at, verified)
            VALUES (?, ?, ?, ?, 'verified_web', ?, 'yes')
        """, (name, email, company, title, datetime.now().isoformat()))
        added += 1
        print(f"  ADDED: {name} - {email} ({company})")
    except Exception as e:
        print(f"  ERROR: {email} - {e}")

conn.commit()
conn.close()

print()
print(f"="*60)
print(f"VERIFIED RECRUITERS ADDED: {added}")
print(f"SKIPPED (already exists): {skipped}")
print(f"="*60)
