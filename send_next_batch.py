import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Send next batch of 60 emails:
- 30 Fresh Professors
- 30 Fresh Recruiters (Verified ones first)
"""
import sqlite3
import csv
import system
import time

print("="*60)
print("PREPARING BATCH OF 60 EMAILS")
print("="*60)

# Initialize system
vs = system.VerifiedEmailSystem()

# 1. Get exclusion list (already contacted)
conn = sqlite3.connect('campaign_results/email_tracking.db')
cursor = conn.cursor()
cursor.execute('SELECT email FROM sent_emails')
contacted = {r[0] for r in cursor.fetchall()}
conn.close()
print(f"Tracking DB contains {len(contacted)} contacted emails.")

# 2. Select 30 Fresh Professors
prof_targets = []
print("\nScanning for fresh professors...")
with open('data/proffesor_clean.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    all_profs = list(reader)

for p in all_profs:
    if len(prof_targets) >= 30:
        break
    email = p.get('Email', '').strip()
    if email and email not in contacted and email not in [t['email'] for t in prof_targets]:
        prof_targets.append({
            'name': p.get('Name', '').strip(),
            'email': email,
            'uni': p.get('University', '').strip(),
            'type': 'professor'
        })

print(f"Selected {len(prof_targets)} fresh professors.")

# 3. Select 30 Fresh Recruiters (Verified first)
rec_targets = []
print("\nScanning for fresh recruiters...")
conn2 = sqlite3.connect('data/recruiters.db')
cursor2 = conn2.cursor()

# Get verified first
cursor2.execute("SELECT full_name, email, company FROM recruiters WHERE verified='yes'")
verified_recs = cursor2.fetchall()

# Get others
cursor2.execute("SELECT full_name, email, company FROM recruiters WHERE verified='no' OR verified IS NULL")
other_recs = cursor2.fetchall()
conn2.close()

# Process verified
for r in verified_recs:
    if len(rec_targets) >= 30:
        break
    email = r[1].strip()
    if email and email not in contacted and email not in [t['email'] for t in rec_targets]:
        rec_targets.append({
            'name': r[0] if r[0] else 'Hiring Team',
            'email': email,
            'company': r[2] if r[2] else 'your company',
            'type': 'corporate'
        })

# Fill rest with others if needed
for r in other_recs:
    if len(rec_targets) >= 30:
        break
    email = r[1].strip()
    if email and email not in contacted and email not in [t['email'] for t in rec_targets]:
        rec_targets.append({
            'name': r[0] if r[0] else 'Hiring Team',
            'email': email,
            'company': r[2] if r[2] else 'your company',
            'type': 'corporate'
        })

print(f"Selected {len(rec_targets)} fresh recruiters.")

# 4. SEND EMAILS
all_targets = prof_targets + rec_targets
print(f"\nReady to send to {len(all_targets)} targets.")
print("="*60)

sent_count = 0
for i, target in enumerate(all_targets, 1):
    print(f"\n[{i}/{len(all_targets)}] Processing: {target['name']} ({target['email']})")
    
    if target['type'] == 'professor':
        # Academic Mode
        try:
            # We use the system's own method to generate content if possible, 
            # but for this script we might need to manually trigger logic if we want specific handling.
            # However, sending directly via send_email_concurrent_safe is safer than full campaign logic for a controlled batch.
            
            # Smart Research Simulation/Call
            try:
                from smart_research_system import get_smart_research_system
                smart_research = get_smart_research_system()
                research_data = smart_research.research_professor(target['name'], target['email'], target['uni'])
                research_area = research_data.get('research_area', 'Computer Science')
            except:
                research_data = {'research_area': 'Computer Science'}
                research_area = 'Computer Science'

            # We'll rely on the system.py's internal fallback/generation if we don't construct the full body here.
            # Actually, system.py generally takes subject/body.
            # Let's generate a High Quality body here using the logic we improved.
            
            # NOTE: To use the improved logic in system.py, we might need to instantiate or call a helper.
            # But the logic is inside launch_legendary_campaign_integrated big loop or personalize_email_corporate.
            # There isn't a standalone "personalize_email_academic" public method easily accessible without some setup.
            # So I will replicate the key part of the improved academic template here to ensure it uses the NEW features.
            
            fullname = target['name']
            university = target['uni']
            
            # New User-Requested Template Logic
            subject = "Research Internship Inquiry – Winter 2025 / Summer 2026"
            
            # Try to get specific hook if available
            connection_part = f"Specifically, your research in {research_area.lower()} aligns deeply with my interests."
            # (Note: In a full system we'd use the deep hooks dictionary here too, but for this script we'll use a strong generic hook if deep lookup isn't easily accessible, 
            # OR we can replicate the deep hook dictionary briefly if space permits. 
            # Given constraints, I'll use a strong dynamic hook based on research area.)
            
            body = f"""Dear Professor {fullname.split()[-1] if ' ' in fullname else fullname},

I hope this message finds you well. My name is Anamay Tripathy, and I am currently in my third year of a B.Tech in Data Science at MIT Manipal, India, with a CGPA of 7.6. Under our institute’s rigorous evaluation system, this reflects a solid academic standing, and I am confident of further improvement in the coming semesters.

I am writing to express my strong interest in contributing to your research group through a remote or on-site research internship, preferably during Winter 2025 or Summer 2026. My core interests lie in {research_area.lower()}, data science, and machine learning, and I am actively preparing to pursue higher studies and research in this area.

{connection_part} I have hands-on experience with Python, TensorFlow, PyTorch, and have built production systems that process real-world data at scale.

A brief overview of my experience:

I am currently interning at Intellect Design Arena, Mumbai, working in data analytics and web development (processing 2.3M daily transactions).

I serve as the Technical Head at YaanBarpe, a startup incubated under the Karnataka Government and E-Cell MIT Manipal, where I lead the product’s technical development (building ML-powered waste classification systems).

Due to financial constraints, I am particularly exploring fully funded or remote research opportunities. I would be deeply grateful for any opportunity—short-term or flexible—to learn, contribute, and grow under your guidance.

My CV is attached for your review. I would be happy to share any additional documents or information if required.

Thank you very much for your time and consideration. I sincerely look forward to the opportunity to connect with you.

Warm regards,
Anamay Tripathy
B.Tech Data Science | MIT Manipal
📧 tripathy.anamay23@gmail.com
📞 +91 98774 54747
🔗 linkedin.com/in/anamay-tripathy | github.com/Flamechargerr"""

            # Send
            vs.send_email_concurrent_safe(target['email'], subject, body, target['name'], 'professor')
            sent_count += 1
            
        except Exception as e:
            print(f"ERROR generating academic email: {e}")

    else:
        # Corporate Mode
        try:
            # Use the improved corporate template
            template = vs._get_corporate_template()
            # Contact tuple: (Name, Email, Company, Confidence, Grade)
            contact_tuple = (target['name'], target['email'], target['company'], 95, 'A+')
            
            subj, body = vs.personalize_email_corporate(template, contact_tuple)
            
            vs.send_email_concurrent_safe(target['email'], subj, body, target['name'], 'corporate')
            sent_count += 1
            
        except Exception as e:
            print(f"ERROR generating corporate email: {e}")
            
    # Small sleep between sends
    time.sleep(2)

print(f"\n\nBatch Complete. Successfully tried to send {sent_count} emails.")
