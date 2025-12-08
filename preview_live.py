
"""
Script to preview one AI-personalized Professor email and one detailed HR email.
"""
import sys
import ai_generator

print("="*60)
print("EXPERIENCING PERSONALIZATION ENGINE")
print("="*60)

# ----------------------------------------------------
# 1. PROFESSOR EMAIL (AI POWERED)
# ----------------------------------------------------
prof_name = "Professor Feifei Li"
university = "Stanford University"
research_area = "Computer Vision and Deep Learning"
paper_title = "ImageNet: A Large-Scale Hierarchical Image Database"

print("\n[SCENARIO 1] Academic Outreach (AI Engine Active)")
print(f"Target: {prof_name} ({university})")
print(f"Area: {research_area}")
print("Generating Smart Connection...")

# Call the AI Engine
try:
    ai_hook = ai_generator.generate_smart_connection(prof_name, research_area, paper_title, university)
except Exception as e:
    ai_hook = f"Error: {e}"

# Construct Body
prof_body = f"""Dear Professor {prof_name.split()[-1]},

I hope this message finds you well. My name is Anamay Tripathy, and I am currently in my third year of a B.Tech in Data Science at MIT Manipal, India, with a CGPA of 7.6.

I am writing to express my strong interest in contributing to your research group through a research internship. My core interests lie in {research_area.lower()}.

{ai_hook}

A brief overview of my experience:
I am currently interning at Intellect Design Arena, Mumbai, working in data analytics (processing 2.3M daily transactions).
I serve as the Technical Head at YaanBarpe (Govt Startup), where I lead the product’s technical development.

I have hands-on experience with Python, TensorFlow, PyTorch.

Due to financial constraints, I am particularly exploring fully funded or remote research opportunities.

Warm regards,
Anamay Tripathy
"""

print("-"*20 + " PREVIEW " + "-"*20)
print(prof_body)
print("-"*50)


# ----------------------------------------------------
# 2. HR EMAIL (CORPORATE MODE)
# ----------------------------------------------------
# Simulating the exact logic from system.py's corporate template for a top company
recruiter_name = "Google University Recruiting"
company = "Google"

print("\n\n[SCENARIO 2] Corporate Outreach (High-Value Target)")
print(f"Target: {recruiter_name} @ {company}")

# Simulated corporate hook logic from system.py (abbreviated for preview)
hr_body = f"""Dear {recruiter_name},

I hope you're having a productive week. My name is Anamay, a Data Science undergrad (3rd Year) at MIT Manipal.

I've been following Google's recent work in multimodal AI agents, and I'm writing to express my interest in internship opportunities for Winter 2025/Summer 2026.

Why I think I'd be a good fit:
1. Intellect Design Arena Internship: I built data pipelines processing 2.3M daily transactions (optimized reporting by 67%).
2. YaanBarpe (Govt Incubated Startup): As Technical Head, I engineered an ML-based waste classification system from scratch.
3. Hackathons: Winner of 3 national hackathons in AI/Web3.

I thrive in fast-paced environments where engineering meets product. I'm attaching my resume and would value the chance to discuss how I can contribute to your engineering teams.

Best regards,
Anamay Tripathy
B.Tech Data Science | MIT Manipal
+91 98774 54747
"""

print("-"*20 + " PREVIEW " + "-"*20)
print(hr_body)
print("="*60)
