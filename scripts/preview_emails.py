import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Preview contacts and sample emails before sending
"""
import system
vs = system.VerifiedEmailSystem()

# Get 10 professors who haven't been contacted
profs = vs.get_verified_contacts(10, min_confidence=95)
print('='*70)
print('PROFESSORS TO EMAIL (10):')
print('='*70)
for i, p in enumerate(profs, 1):
    print(f"{i}. {p[0]} - {p[1]} ({p[2]})")

print()

# Get 10 recruiters
recs = vs.get_recruiters(10)
print('='*70)
print('RECRUITERS TO EMAIL (10):')
print('='*70)
for i, r in enumerate(recs, 1):
    if isinstance(r, dict):
        name = r.get('name', 'Unknown')
        email = r.get('email', '')
        company = r.get('company', '')
        print(f"{i}. {name} - {email} ({company})")
    else:
        print(f"{i}. {r[0]} - {r[1]} ({r[2]})")

print()
print('='*70)
print('SAMPLE CORPORATE EMAIL:')
print('='*70)

if recs:
    r = recs[0]
    if isinstance(r, dict):
        contact = (r.get('name', 'Unknown'), r.get('email', ''), r.get('company', ''), 95, 'A+')
    else:
        contact = r
    
    template = vs._get_corporate_template()
    subj, body = vs.personalize_email_corporate(template, contact)
    print(f"Subject: {subj}")
    print()
    print(body)

print()
print('='*70)
print('SAMPLE ACADEMIC EMAIL:')
print('='*70)

if profs:
    # Simulate academic email generation
    from smart_research_system import get_smart_research_system
    p = profs[0]
    name, email, affiliation = p[0], p[1], p[2]
    
    try:
        smart_research = get_smart_research_system()
        research_data = smart_research.research_professor(name, email, affiliation)
        research_area = research_data.get('research_area', 'Computer Science')
    except:
        research_data = {'research_area': 'Computer Science', 'research_mention': 'your research', 'research_focus': 'advancing the field'}
        research_area = 'Computer Science'
    
    print(f"To: Professor {name}")
    print(f"Subject: Research Internship Inquiry – Genuine Interest in Your {research_area.title()} Work")
    print()
    print("(Email body would be generated with deep research personalization)")
