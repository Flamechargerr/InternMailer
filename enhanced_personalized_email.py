#!/usr/bin/env python3
"""
Enhanced Personalized Email Generator
Generates highly personalized emails based on professor's specific research, papers, and contributions
"""

import sys
import os
sys.path.append('src')
from jinja2 import Template
from azure_ai_client import generate_with_azure_ai

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta charset="UTF-8">
    <title>Research Internship Inquiry</title>
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Times New Roman', Times, serif; line-height: 1.5; color: #000000;">
    
    <div style="max-width: 700px; margin: 30px auto; background: #ffffff; padding: 40px 45px; border: 1px solid #e0e0e0;">
        
        <div style="text-align: center; margin-bottom: 25px; border-bottom: 2px solid #000000; padding-bottom: 15px;">
            <h1 style="margin: 0; font-size: 18px; font-weight: bold; color: #000000; letter-spacing: 1px;">
                RESEARCH INTERNSHIP INQUIRY
            </h1>
        </div>
        
        <p style="margin: 0 0 20px 0; font-size: 16px; color: #000000;">
            Dear Prof. {{ professor_last_name }},
        </p>

        <p style="margin: 0 0 20px 0; font-size: 16px; color: #000000; text-align: justify;">
            I hope this message finds you well.
        </p>
        
        <p style="margin: 0 0 30px 0; font-size: 16px; color: #000000; text-align: justify;">
            My name is <strong>Anamay Tripathy</strong>, a third-year B.Tech student in Data Science & Engineering at <strong>MIT Manipal, India</strong>. I am writing to express my sincere interest in joining your research group as a research intern.
        </p>

        <!-- Specific Research Interest -->
        <div style="margin-bottom: 25px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 5px;">
                Why Your Specific Research Resonates with Me
            </h2>
            
            <p style="margin: 0 0 15px 0; font-size: 16px; color: #000000; text-align: justify;">
                {{ specific_research_interest }}
            </p>
            
            {% if notable_papers %}
            <p style="margin: 0 0 15px 0; font-size: 16px; color: #000000; text-align: justify;">
                {{ paper_discussion }}
            </p>
            {% endif %}
        </div>

        <!-- Technical Alignment -->
        <div style="margin-bottom: 25px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 5px;">
                Technical Background & Research Alignment
            </h2>
            
            <p style="margin: 0 0 15px 0; font-size: 16px; color: #000000; text-align: justify;">
                {{ technical_alignment }}
            </p>
            
            <ul style="margin: 0 0 15px 0; padding-left: 0; list-style: none; font-size: 16px; color: #000000;">
                <li style="margin-bottom: 12px;">
                    <strong>Technical Head</strong>, <em>YaanBarpe</em> (Govt. of Karnataka-incubated startup)<br>
                    <span style="font-style: italic; padding-left: 15px; color: #444;">Leading AI-driven system architecture and sustainable technology solutions.</span>
                </li>
                <li style="margin-bottom: 12px;">
                    <strong>Data Analyst Intern</strong>, <em>Intellect Design Arena</em>, Mumbai<br>
                    <span style="font-style: italic; padding-left: 15px; color: #444;">Built ML pipelines and scalable APIs, achieving 22% engagement increase.</span>
                </li>
                <li style="margin-bottom: 12px;">
                    <strong>Relevant Projects</strong>: {{ relevant_projects }}
                </li>
            </ul>
        </div>

        <!-- Research Contribution Potential -->
        <div style="margin-bottom: 25px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 5px;">
                Potential Research Contributions
            </h2>
            
            <p style="margin: 0 0 15px 0; font-size: 16px; color: #000000; text-align: justify;">
                {{ research_contribution_ideas }}
            </p>
        </div>

        <p style="margin: 0 0 15px 0; font-size: 16px; color: #000000; text-align: justify;">
            I am available for internships in <strong>Winter 2025</strong> or <strong>Summer 2026</strong>, and welcome <strong>remote or on-site</strong>, <strong>funded or volunteer</strong> opportunities. I've attached my <strong>CV</strong> and would be grateful for the opportunity to discuss how my background and interests align with your ongoing projects.
        </p>

        <p style="margin: 0 0 25px 0; font-size: 16px; color: #000000;">
            Thank you for your time and consideration.
        </p>

        <!-- Contact Information -->
        <div style="margin-bottom: 25px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 5px;">
                Contact Information
            </h2>
            
            <p style="margin: 0; font-size: 16px; color: #000000; line-height: 1.4;">
                📧 <a href="mailto:tripathy.anamay23@gmail.com" style="color: #000000; text-decoration: underline;">tripathy.anamay23@gmail.com</a><br>
                📞 <a href="tel:+919877454747" style="color: #000000; text-decoration: underline;">+91-9877454747</a><br>
                🌐 <a href="https://anamay.vercel.app" style="color: #000000; text-decoration: underline;">anamay.vercel.app</a> | 
                <a href="https://github.com/Flamechargerr" style="color: #000000; text-decoration: underline;">github.com/Flamechargerr</a>
            </p>
        </div>

        <!-- Signature -->
        <div style="margin-top: 30px; border-top: 1px solid #000000; padding-top: 20px;">
            <p style="margin: 0 0 8px 0; font-size: 16px; color: #000000;">
                Warm regards,
            </p>
            <p style="margin: 0 0 3px 0; font-size: 16px; color: #000000; font-weight: bold;">
                Anamay Tripathy
            </p>
            <p style="margin: 0; font-size: 16px; color: #000000; font-style: italic;">
                B.Tech Data Science & Engineering, MIT Manipal
            </p>
        </div>
    </div>
</body>
</html>
'''

def generate_deeply_personalized_email(professor_data):
    """
    Generate a deeply personalized email based on professor's specific research, papers, and work.
    
    Args:
        professor_data (dict): Contains professor info including:
            - name: Full name
            - university: Institution
            - research_area: Primary research area
            - notable_papers: List of key papers/publications
            - current_projects: Current research projects
            - specific_interests: Specific research interests
            - homepage_text: Text scraped from homepage (if available)
    """
    
    # Extract professor details
    full_name = professor_data.get('name', professor_data.get('Name', ''))
    last_name = full_name.split()[-1] if full_name else 'Professor'
    research_area = professor_data.get('research_area', professor_data.get('Research Area', ''))
    university = professor_data.get('university', professor_data.get('University', ''))
    notable_papers = professor_data.get('notable_papers', [])
    current_projects = professor_data.get('current_projects', [])
    homepage_text = professor_data.get('homepage_text', '')
    
    # Generate highly specific research interest discussion
    specific_research_prompt = f"""
    Write a compelling and specific paragraph explaining why I (as a student) am deeply interested in your research in {research_area} at {university}. 
    
    Context about the professor's work:
    - Research area: {research_area}
    - University: {university}
    - Homepage content: {homepage_text[:500] if homepage_text else 'Not available'}
    
    Write in FIRST PERSON addressing the professor directly as "your work" or "your research". Focus on:
    1. Specific aspects of their research approach that inspire me
    2. How their work advances the field in ways that excite me
    3. Real-world impact of their contributions that motivates me
    4. Why their methodology/focus is particularly innovative to me
    
    Use phrases like "I am inspired by your work on..." or "Your approach to... resonates with me because..."
    Keep it under 150 words and be specific, not generic.
    """
    
    specific_research_interest = generate_with_azure_ai(specific_research_prompt)
    
    # Generate paper discussion if papers are available
    paper_discussion = ""
    if notable_papers:
        paper_prompt = f"""
        Write a thoughtful discussion about how your research contributions have influenced me, specifically mentioning your work in {research_area}. 
        
        Key papers/work to reference: {', '.join(notable_papers[:3])}
        
        Write in FIRST PERSON addressing the professor directly. Use phrases like:
        - "Your work on [paper] has shown me..."
        - "I was particularly impressed by your approach in..."
        - "Your research in [area] demonstrates..."
        
        Discuss:
        1. How your specific research contributions have influenced the field
        2. What makes your approach unique or groundbreaking in my view
        3. How your work connects to current challenges I'm interested in
        
        Write from my perspective as a student who has studied your work. Keep it under 100 words and be specific, not generic.
        """
        paper_discussion = generate_with_azure_ai(paper_prompt)
    
    # Generate technical alignment based on their specific research
    technical_alignment_prompt = f"""
    Write a paragraph explaining how my background as a Data Science & Engineering student would align with and contribute to your research in {research_area} at {university}.
    
    My background:
    - B.Tech Data Science & Engineering, MIT Manipal
    - Experience: Python, Machine Learning, JavaScript, React, TensorFlow, PyTorch
    - Projects: CrimeConnect (case management), VARtificial Intelligence (ML prediction)
    - Role: Technical Head at government-incubated startup
    - Internship: Data Analyst at Intellect Design Arena
    
    Write in FIRST PERSON addressing the professor. Use phrases like "My experience with..." and "I believe my skills in... would contribute to your research..."
    
    Focus on:
    1. Specific technical skills that match your research needs
    2. How my project experience relates to your work
    3. Potential contributions I could make to your research
    
    Be specific to {research_area} and avoid generic statements. Keep under 120 words.
    """
    
    technical_alignment = generate_with_azure_ai(technical_alignment_prompt)
    
    # Generate research contribution ideas
    contribution_prompt = f"""
    Suggest 2-3 specific ways I could contribute to your research in {research_area} at {university} as a Data Science & Engineering intern.
    
    Consider:
    - Current trends and challenges in {research_area}
    - How data science/ML techniques could enhance your research
    - Specific methodologies or tools that could be valuable
    - Implementation or analysis tasks that would be meaningful
    
    Write in FIRST PERSON as potential contributions I could make to your research. Use phrases like "I could contribute by..." or "I would be excited to help with..."
    Be specific and actionable. Keep under 100 words.
    """
    
    research_contribution_ideas = generate_with_azure_ai(contribution_prompt)
    
    # Determine relevant projects based on research area
    relevant_projects = "CrimeConnect (distributed case management system), VARtificial Intelligence (ML prediction platform)"
    if "machine learning" in research_area.lower() or "ai" in research_area.lower():
        relevant_projects = "VARtificial Intelligence (89% accuracy ML prediction system), CrimeConnect (data-driven case management)"
    elif "systems" in research_area.lower() or "distributed" in research_area.lower():
        relevant_projects = "CrimeConnect (scalable case management architecture), distributed ML pipeline development"
    elif "security" in research_area.lower():
        relevant_projects = "CrimeConnect (secure case management system), HackOps (cybersecurity gamification platform)"
    
    # Render the template
    template = Template(HTML_TEMPLATE)
    return template.render(
        professor_last_name=last_name,
        specific_research_interest=specific_research_interest,
        notable_papers=notable_papers,
        paper_discussion=paper_discussion,
        technical_alignment=technical_alignment,
        research_contribution_ideas=research_contribution_ideas,
        relevant_projects=relevant_projects
    )

# Example usage with detailed professor data
if __name__ == "__main__":
    sample_professor = {
        'name': 'Barbara Liskov',
        'university': 'MIT',
        'research_area': 'distributed systems and programming languages',
        'notable_papers': [
            'A History of CLU Programming Language',
            'Practical Uses of Synchronized Clocks in Distributed Systems',
            'Byzantine Fault Tolerance'
        ],
        'current_projects': [
            'Distributed system reliability',
            'Programming language design for concurrency'
        ],
        'homepage_text': 'Research focuses on distributed systems, fault tolerance, and programming language design. Known for pioneering work in data abstraction and Byzantine fault tolerance. Current work includes reliable distributed computing and programming language support for distributed systems.'
    }
    
    print("🔧 Generating deeply personalized email...")
    print("=" * 60)
    
    personalized_email = generate_deeply_personalized_email(sample_professor)
    
    # Save to file
    output_file = "deeply_personalized_email.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Subject: Research Internship Inquiry – Anamay Tripathy re: {sample_professor['research_area']}\n\n")
        f.write(personalized_email)
    
    print(f"✅ Deeply personalized email generated and saved to: {output_file}")
    print("\nEmail preview (first 500 chars):")
    print("-" * 50)
    print(personalized_email[:500] + "...")
    print("-" * 50)
