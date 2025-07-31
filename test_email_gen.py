import sys
import os
sys.path.append('src')

# Sample professor data
prof_data = {
    'name': 'Dr. John Smith',
    'affiliation': 'Stanford University', 
    'email': 'jsmith@stanford.edu'
}

prof_profile = {
    'lab_description': 'machine learning research',
    'keywords': ['machine learning', 'deep learning']
}

recent_paper = {
    'title': 'Advances in Neural Networks',
    'venue': 'ICML',
    'year': 2024
}

# Create fallback email template
fallback_template = """SUBJECT: Research Internship Opportunity - Winter '25-'26

BODY:
Dear Prof. [ProfName],

I hope this email finds you well. I am writing to express my strong interest in pursuing a research internship in your lab during the Winter '25-'26 semester.

I am a Data Science Engineering student at Manipal Institute of Technology, graduating in 2027. I have been following your work in [LabDesc] and am particularly impressed by your recent publication "[RecentTitle]" published in [Venue] ([Year]).

Your research aligns perfectly with my interests in [MyDomains]. My background includes experience in [CV_Summary], which I believe would be valuable for your ongoing research projects.

I am eager to contribute to your lab's work and learn from your expertise. I have attached my CV for your review and would be grateful for the opportunity to discuss potential research opportunities.

Thank you for your time and consideration.

Best regards,
Anamay Tripathy
Manipal Institute of Technology
"""

# Fill template with data
filled_email = fallback_template.replace('[ProfName]', prof_data.get('name', 'Professor'))
filled_email = filled_email.replace('[Affiliation]', prof_data.get('affiliation', 'University'))
filled_email = filled_email.replace('[LabDesc]', prof_profile.get('lab_description', 'research'))
filled_email = filled_email.replace('[RecentTitle]', recent_paper.get('title', 'Recent Research'))
filled_email = filled_email.replace('[Venue]', recent_paper.get('venue', 'Academic Conference'))
filled_email = filled_email.replace('[Year]', str(recent_paper.get('year', 2024)))
keywords = prof_profile.get('keywords', ['machine learning', 'data science'])
filled_email = filled_email.replace('[ProfKeyword1]', keywords[0] if len(keywords) > 0 else 'machine learning')
filled_email = filled_email.replace('[ProfKeyword2]', keywords[1] if len(keywords) > 1 else 'data science')
filled_email = filled_email.replace('[MyDomains]', 'Machine Learning, Data Science, Python Development')
filled_email = filled_email.replace('[CV_Summary]', 'Python development, machine learning projects, and data analysis')
filled_email = filled_email.replace('[MatchScore]', '0.85')
filled_email = filled_email.replace('[Your Discipline]', 'Data Science Engineering')
filled_email = filled_email.replace('[Your University]', 'Manipal Institute of Technology')
filled_email = filled_email.replace('[Grad Year]', '2027')

print('=== SAMPLE EMAIL THAT WOULD BE SENT TO PROFESSORS ===')
print(f'TO: {prof_data["email"]}')
print()
print(filled_email)
