import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Preview script for the new Hybrid Academic Template
"""
import system
from smart_research_system import get_smart_research_system

print("="*60)
print("PREVIEWING NEW HYBRID ACADEMIC TEMPLATE")
print("="*60)

# Sample Professor
prof_name = "Professor Francesca Toni"
university = "Imperial College London"
research_area = "Computational Logic and AI"
email = "ft@doc.ic.ac.uk"

# 1. Simulate Smart Research Data
print(f"Simulating research for: {prof_name}")
research_data = {
    'research_area': research_area,
    'research_focus': 'computational argumentation and explainable AI',
    'paper_reference': 'Argumentation for XAI',
    'confidence': 0.9
}

# 2. Key Dynamic Variables
fullname = prof_name
connection_part = f"Specifically, your research in {research_area.lower()} aligns deeply with my interests."
paper_section = f"\n\nI recently read your paper on {research_data['paper_reference']}. The methodology was illuminating - particularly how you approached the problem. It changed how I think about {research_area.lower()} and made me even more eager to learn from your group."

# 3. Generate Body (Using the logic from send_next_batch.py)
subject = "Research Internship Inquiry – Winter 2025 / Summer 2026"

body = f"""Dear Professor {fullname.split()[-1] if ' ' in fullname else fullname},

I hope this message finds you well. My name is Anamay Tripathy, and I am currently in my third year of a B.Tech in Data Science at MIT Manipal, India, with a CGPA of 7.6. Under our institute’s rigorous evaluation system, this reflects a solid academic standing, and I am confident of further improvement in the coming semesters.

I am writing to express my strong interest in contributing to your research group through a remote or on-site research internship, preferably during Winter 2025 or Summer 2026. My core interests lie in {research_area.lower()}, data science, and machine learning, and I am actively preparing to pursue higher studies and research in this area.

Only because I have been following your work on {research_data['research_focus']}. {connection_part}{paper_section}

A brief overview of my experience:

I am currently interning at Intellect Design Arena, Mumbai, working in data analytics and web development (processing 2.3M daily transactions).

I serve as the Technical Head at YaanBarpe, a startup incubated under the Karnataka Government and E-Cell MIT Manipal, where I lead the product’s technical development (building ML-powered waste classification systems).

I have hands-on experience with Python, TensorFlow, PyTorch, and have built production systems that process real-world data at scale.

Due to financial constraints, I am particularly exploring fully funded or remote research opportunities. I would be deeply grateful for any opportunity—short-term or flexible—to learn, contribute, and grow under your guidance.

My CV is attached for your review. I would be happy to share any additional documents or information if required.

Thank you very much for your time and consideration. I sincerely look forward to the opportunity to connect with you.

Warm regards,
Anamay Tripathy
B.Tech Data Science | MIT Manipal
📧 tripathy.anamay23@gmail.com
📞 +91 98774 54747
🔗 linkedin.com/in/anamay-tripathy | github.com/anamay-tripathy"""

print("\n" + "="*20 + " SUBJECT " + "="*20)
print(subject)
print("\n" + "="*20 + " CONTENT " + "="*20)
print(body)
print("="*60)
