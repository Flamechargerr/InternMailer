"""
Send 20 emails - 10 professors, 10 recruiters
With proper fresh contact selection
"""
import sqlite3
import csv
import system

# Initialize system
print("Initializing...")
vs = system.VerifiedEmailSystem()

# Get contacted emails
conn = sqlite3.connect('campaign_results/email_tracking.db')
cursor = conn.cursor()
cursor.execute('SELECT email FROM sent_emails')
contacted = {r[0] for r in cursor.fetchall()}
conn.close()

print(f"Already contacted: {len(contacted)} emails")

# Get fresh professors from CSV
print("\n=== SENDING TO 10 FRESH PROFESSORS ===")
with open('data/proffesor_clean.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    all_profs = list(reader)

fresh_profs = [p for p in all_profs if p.get('Email') not in contacted][:10]

prof_sent = 0
for p in fresh_profs:
    name = p.get('Name', '')
    email = p.get('Email', '')
    university = p.get('University', '')
    
    if email in contacted:
        print(f"  SKIP (already contacted): {email}")
        continue
    
    print(f"\nSending to Professor {name} ({email})")
    
    # Generate email using smart research
    try:
        from smart_research_system import get_smart_research_system
        smart_research = get_smart_research_system()
        research_data = smart_research.research_professor(name, email, university)
        research_area = research_data.get('research_area', 'Computer Science')
    except:
        research_data = {'research_area': 'Computer Science', 'research_mention': 'your research'}
        research_area = 'Computer Science'
    
    subject = f"Research Internship Inquiry – Genuine Interest in Your {research_area.title()} Work"
    
    # Use simplified body for now
    body = f"""Dear Professor {name.split()[-1] if ' ' in name else name},

I am writing to inquire about research internship opportunities in your lab at {university}. I have been following your research in {research_area.lower()}, and your contributions to the field represent exactly the kind of rigorous, impactful work I aspire to learn from.

I am Anamay Tripathy, a third-year B.Tech student in Data Science at MIT Manipal, India.

At Intellect Design Arena (Fintech):
I interned on their analytics platform processing 2.3 million daily financial transactions. I built automated reporting pipelines that reduced processing time by 67%.

As Technical Head at YaanBarpe (Karnataka Government Startup):
I led a 4-person team building an ML-powered waste classification system.

Technical Skills: Python (advanced), TensorFlow, PyTorch, Scikit-learn, SQL, Docker, AWS

I would be genuinely grateful for even 15 minutes of your time to discuss whether there might be a place for me in your group.

My resume is attached.

Respectfully,
Anamay Tripathy
B.Tech Data Science, MIT Manipal (2027)
tripathy.anamay23@gmail.com | +91 9877454747
linkedin.com/in/anamay-tripathy"""
    
    result = vs.send_email_concurrent_safe(email, subject, body, name, 'professor')
    if result:
        prof_sent += 1
        contacted.add(email)

print(f"\n✅ Professors sent: {prof_sent}/10")

# Get fresh recruiters
print("\n=== SENDING TO 10 FRESH RECRUITERS ===")
conn2 = sqlite3.connect('data/recruiters.db')
cursor2 = conn2.cursor()
cursor2.execute('SELECT full_name, email, company FROM recruiters LIMIT 20')
all_recs = cursor2.fetchall()
conn2.close()

fresh_recs = [r for r in all_recs if r[1] not in contacted][:10]

rec_sent = 0
for r in fresh_recs:
    name = r[0] or 'Hiring Team'
    email = r[1]
    company = r[2] or 'your company'
    
    if email in contacted:
        print(f"  SKIP (already contacted): {email}")
        continue
    
    print(f"\nSending to {name} at {company} ({email})")
    
    template = vs._get_corporate_template()
    contact_data = (name, email, company, 95, 'A+')
    subject, body = vs.personalize_email_corporate(template, contact_data)
    
    result = vs.send_email_concurrent_safe(email, subject, body, name, 'corporate')
    if result:
        rec_sent += 1
        contacted.add(email)

print(f"\n✅ Recruiters sent: {rec_sent}/10")

print("\n" + "="*60)
print(f"TOTAL SENT: {prof_sent + rec_sent}/20 emails")
print("="*60)
