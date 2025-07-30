#!/usr/bin/env python3
"""
Enhanced Personalized Email Generator
Generates highly personalized emails using Azure AI (GPT-4o) with advanced prompting
Pure AI-powered personalization without external scraping or APIs
"""

import sys
import os
import logging
sys.path.append('src')
from jinja2 import Template
from azure_ai_client import generate_with_azure_ai, get_azure_ai_client
from llama_client import generate_with_llama, get_llama_client
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_backup_email_content() -> str:
    """
    Generate backup email content when both AI systems fail.
    Returns empty string - we use detailed backup sections instead.
    """
    logger.info("🔄 Using detailed backup template sections (AI systems unavailable)")
    return ""

def get_research_specific_backup(research_area: str, professor_name: str, university: str) -> dict:
    """
    Generate research-area specific backup content that's actually tailored to the professor's work.
    This replaces generic templates with targeted content based on research domain.
    """
    research_area_lower = research_area.lower()
    
    # AI Ethics and Robotics (like Professor Kuipers)
    if any(term in research_area_lower for term in ['ethics', 'robotics', 'ai ethics', 'robot ethics']):
        return {
            'specific_research_interest': f"""
Your pioneering work in AI ethics and robotics particularly resonates with me because it addresses one of the most critical challenges facing our field today. As AI systems become increasingly integrated into society, your research on foundational domains of knowledge - especially ethics as a core domain for robots and AI agents - represents exactly the kind of forward-thinking approach I want to contribute to. Your focus on enabling AI systems to act as responsible members of human society aligns perfectly with my belief that technical excellence must be paired with ethical responsibility. I am especially drawn to how your work bridges the gap between abstract ethical principles and concrete implementations in robotic systems.
            """,
            
            'technical_alignment': f"""
My technical background in AI systems development, combined with my philosophical interest in responsible technology, positions me well to contribute to your ethics-focused robotics research. Through my leadership role at YaanBarpe, I've grappled with real-world ethical considerations in AI deployment, while my data science training provides the technical foundation to implement ethical reasoning systems. My experience building scalable AI architectures could support your work on foundational knowledge domains, particularly in developing computational frameworks that can represent and reason about ethical principles in robotic decision-making systems.
            """,
            
            'research_contribution_ideas': f"""
I could contribute to your research by developing computational frameworks for ethical reasoning in robotic systems, building on my experience with decision-making algorithms and knowledge representation. My background in scalable system architecture would be valuable for implementing your foundational domains approach, particularly in creating robust frameworks that can handle the complexity of ethical reasoning in real-time robotic applications. Additionally, I could help develop empirical methodologies to evaluate the effectiveness of ethical reasoning systems, drawing on my data analysis experience to create metrics and benchmarks for measuring ethical behavior in AI agents.
            """
        }
    
    # Machine Learning / AI Vision
    elif any(term in research_area_lower for term in ['machine learning', 'computer vision', 'deep learning', 'neural networks']):
        return {
            'specific_research_interest': f"""
Your research in {research_area} particularly excites me because it represents the cutting edge of AI systems that can understand and interact with the visual world. The intersection of theoretical ML advances with practical computer vision applications aligns perfectly with my interests in both algorithmic innovation and real-world problem solving. Your work demonstrates how rigorous mathematical foundations can be translated into systems that meaningfully impact how machines perceive and understand visual information, which is exactly the kind of research I want to contribute to during my career.
            """,
            
            'technical_alignment': f"""
My hands-on experience building ML pipelines and computer vision systems at Intellect Design Arena, combined with my theoretical foundation in data science, positions me well to contribute to your {research_area} research. I've worked extensively with neural network architectures and optimization algorithms, and my experience scaling ML systems in production environments could support your work on developing robust vision systems. My background in both the mathematical foundations and practical implementation challenges of ML makes me well-suited to advance your research objectives.
            """,
            
            'research_contribution_ideas': f"""
I could contribute by developing and optimizing neural network architectures for your vision research, leveraging my experience with ML pipeline development and performance optimization. My background in scalable system design would be valuable for implementing efficient training and inference frameworks for large-scale vision models. Additionally, I could help develop novel evaluation methodologies and benchmarking systems for vision algorithms, drawing on my data analysis expertise to create comprehensive assessment frameworks that measure both accuracy and computational efficiency.
            """
        }
    
    # Systems/Distributed Computing
    elif any(term in research_area_lower for term in ['systems', 'distributed', 'networks', 'security', 'databases']):
        return {
            'specific_research_interest': f"""
Your work in {research_area} particularly resonates with me because it tackles the fundamental challenges of building reliable, scalable computing infrastructure that underpins all modern applications. The complexity of designing systems that can handle massive scale while maintaining reliability and security aligns with my passion for solving complex technical challenges. Your research approach, which balances theoretical rigor with practical considerations, represents exactly the kind of systems thinking I want to develop further in my career.
            """,
            
            'technical_alignment': f"""
My experience as Technical Head at YaanBarpe, where I've architected scalable AI systems and dealt with real-world deployment challenges, directly aligns with your {research_area} research. I've worked extensively with distributed architectures, performance optimization, and system reliability - challenges that are central to your work. My combination of hands-on system building experience and theoretical computer science background positions me well to contribute to research that requires both deep technical knowledge and practical implementation skills.
            """,
            
            'research_contribution_ideas': f"""
I could contribute to your systems research by developing and implementing novel distributed algorithms and system architectures, leveraging my experience with scalable system design and performance optimization. My background in both theoretical analysis and practical system building would be valuable for prototyping and evaluating new system approaches. Additionally, I could help develop comprehensive benchmarking and evaluation frameworks for distributed systems, drawing on my data analysis expertise to create metrics that capture both performance and reliability characteristics.
            """
        }
    
    # Natural Language Processing
    elif any(term in research_area_lower for term in ['nlp', 'natural language', 'language model', 'text']):
        return {
            'specific_research_interest': f"""
Your research in {research_area} particularly fascinates me because it addresses the fundamental challenge of enabling machines to understand and generate human language meaningfully. The intersection of computational linguistics, machine learning, and cognitive science in your work represents exactly the kind of interdisciplinary approach I'm passionate about. Your focus on developing systems that can truly comprehend language, rather than just process it statistically, aligns with my interest in building AI systems that can engage with human knowledge and reasoning in sophisticated ways.
            """,
            
            'technical_alignment': f"""
My background in machine learning and data science, particularly my experience with large-scale text processing and analysis systems, aligns well with your {research_area} research. Through my work at Intellect Design Arena, I've developed ML pipelines for processing and analyzing textual data, while my theoretical foundation in algorithms and statistics provides the mathematical background necessary for advancing NLP research. My experience with both the engineering challenges and theoretical aspects of language processing positions me well to contribute to your research group.
            """,
            
            'research_contribution_ideas': f"""
I could contribute to your NLP research by developing and optimizing language processing algorithms and neural architectures, leveraging my experience with ML systems and performance optimization. My background in data analysis would be valuable for developing novel evaluation methodologies and linguistic analysis frameworks. Additionally, I could help build scalable infrastructure for training and deploying large language models, drawing on my systems experience to address the computational challenges inherent in modern NLP research.
            """
        }
    
    # Generic fallback (but still better than the old generic version)
    else:
        return {
            'specific_research_interest': f"""
Your research in {research_area} at {university} particularly excites me because it represents cutting-edge work that pushes the boundaries of our field. The innovative approaches you've developed demonstrate a deep understanding of both theoretical foundations and practical applications, which strongly resonates with my own interests in bridging academic research with real-world impact. Your work addresses fundamental questions in {research_area} while maintaining relevance to current technological challenges, which is exactly the kind of research environment where I believe I can make meaningful contributions and grow as a researcher.
            """,
            
            'technical_alignment': f"""
My technical background in data science and machine learning, developed through my roles at YaanBarpe and Intellect Design Arena, aligns well with the computational and analytical demands of your {research_area} research. My experience with scalable system architecture, algorithm implementation, and data analysis provides a strong foundation for contributing to research projects that require both theoretical understanding and practical implementation skills. The combination of my academic training and industry experience offers a unique perspective that I believe would be valuable for advancing your research objectives.
            """,
            
            'research_contribution_ideas': f"""
I could contribute to your {research_area} research by applying my experience in machine learning algorithm development and system optimization to advance your current projects. My background in data analysis and computational methods would be valuable for developing novel approaches to research challenges in your field. Additionally, my experience with scalable system implementation could help translate theoretical advances into practical, deployable solutions that demonstrate the real-world impact of your research.
            """
        }

def generate_with_fallback(prompt: str) -> str:
    """
    Generate text using Azure AI first (most reliable), then Llama as fallback.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Generated response text
    """
    # First, try Azure AI (most reliable for personalization)
    azure_client = get_azure_ai_client()
    if azure_client.is_available():
        try:
            logger.info("Attempting generation with Azure AI...")
            result = generate_with_azure_ai(prompt)
            if result and result.strip():
                logger.info("✅ Successfully generated with Azure AI")
                return result
            else:
                logger.warning("Azure AI returned empty response, trying Llama...")
        except Exception as e:
            logger.warning(f"Azure AI generation failed: {e}, trying Llama...")
    else:
        logger.info("Azure AI not available, trying Llama...")
    
    # Second, try Llama
    llama_client = get_llama_client()
    if llama_client.is_available():
        try:
            logger.info("Attempting generation with Llama...")
            result = generate_with_llama(prompt)
            if result and result.strip():
                logger.info("✅ Successfully generated with Llama")
                return result
            else:
                logger.warning("Llama returned empty response, using backup template...")
        except Exception as e:
            logger.warning(f"Llama generation failed: {e}, using backup template...")
    else:
        logger.info("Llama not available, using backup template...")
    
    # Final fallback - use backup template with professor-specific data
    logger.error("Both Azure AI and Llama failed, using backup template")
    return generate_backup_email_content()



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
            I am available for internships in <strong>Winter 2025</strong> or <strong>Summer 2026</strong>, and welcome <strong>remote or on-site</strong>, <strong>funded or volunteer</strong> opportunities. I have attached my detailed CV for your review and would be grateful for the opportunity to discuss how my background and interests align with your ongoing projects.
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
        fetch_real_data (bool): Whether to fetch real research data from APIs
    """
    
    # Extract professor details  
    full_name = professor_data.get('name', professor_data.get('Name', ''))
    last_name = full_name.split()[-1] if full_name else 'Professor'
    research_area = professor_data.get('research_area', professor_data.get('Research Area', ''))
    university = professor_data.get('university', professor_data.get('University', ''))
    homepage_url = professor_data.get('homepage', professor_data.get('Homepage', ''))
    
    # Use provided data - let AI do all the personalization based on basic info
    notable_papers = professor_data.get('notable_papers', [])
    current_projects = professor_data.get('current_projects', [])
    homepage_text = professor_data.get('homepage_text', '')
    
    logging.info(f"Generating AI-personalized email for {full_name} at {university}...")
    
    # Generate highly specific research interest discussion with advanced AI reasoning
    specific_research_prompt = f"""
    Write ONE PARAGRAPH ONLY (100-120 words) from MY perspective as Anamay Tripathy expressing interest in Professor {full_name}'s research.
    
    Context:
    - Professor: {full_name} at {university}
    - Research Area: {research_area}
    - I am: Anamay, Data Science & Engineering student at MIT Manipal
    
    CRITICAL REQUIREMENTS:
    - Write ENTIRELY in FIRST PERSON (I, my, me) throughout
    - Address professor as "you" and "your"
    - NO third-person references like "the professor" or "their work"
    - Be specific about why YOUR work in {research_area} excites ME personally
    - Connect YOUR research to MY career aspirations in AI/data science
    
    Start with: "I am deeply inspired by your work in {research_area}..." or "Your research in {research_area} particularly excites me because..."
    
    Return ONLY the paragraph text, nothing else.
    """
    
    specific_research_interest = generate_with_fallback(specific_research_prompt)
    
    # Generate paper discussion if papers are available
    paper_discussion = ""
    if notable_papers:
        paper_prompt = f"""
        Write ONE PARAGRAPH ONLY (80-100 words) from MY perspective as Anamay Tripathy discussing Professor {full_name}'s specific research contributions.
        
        Key papers/work to reference: {', '.join(notable_papers[:3])}
        
        CRITICAL REQUIREMENTS:
        - Write ENTIRELY in FIRST PERSON (I, my, me) throughout
        - Address professor as "you" and "your"
        - NO third-person references whatsoever
        - Be specific about how YOUR papers have influenced MY understanding
        
        Use phrases like:
        - "Your work on [specific paper] has shown me..."
        - "I was particularly impressed by your approach in..."
        - "Your research demonstrates to me..."
        
        Focus on how YOUR specific contributions have shaped MY perspective on the field.
        
        Return ONLY the paragraph text, nothing else.
        """
        paper_discussion = generate_with_fallback(paper_prompt)
    
    # Generate technical alignment with sophisticated reasoning
    technical_alignment_prompt = f"""
    Write ONE PARAGRAPH ONLY (100-120 words) from MY perspective as Anamay Tripathy explaining technical alignment with Professor {full_name}'s research.
    
    Context:
    - I am: Anamay, B.Tech Data Science & Engineering at MIT Manipal
    - Professor researches: {research_area} at {university}
    - My background: Technical Head at YaanBarpe (startup), Data Analyst at Intellect Design Arena, ML projects
    
    CRITICAL REQUIREMENTS:
    - Write ENTIRELY in FIRST PERSON (I, my, me) throughout
    - Address professor as "you" and "your"
    - NO third-person references like "the student" or "their work"
    - Be specific about how MY skills support YOUR {research_area} work
    
    Include:
    1. How MY ML/systems experience supports YOUR research
    2. MY specific technical skills valuable for YOUR projects
    3. How MY startup experience brings implementation perspective
    4. Why MY theory + hands-on combination is ideal for YOUR work
    
    Start with: "My experience with..." or "I believe my background in..."
    
    Return ONLY the paragraph text, nothing else.
    """
    
    technical_alignment = generate_with_fallback(technical_alignment_prompt)
    
    # Generate sophisticated research contribution ideas
    contribution_prompt = f"""
    You are Anamay Tripathy writing to Professor {full_name}, proposing specific research contributions to their work in {research_area} at {university}.
    
    Based on my technical expertise (ML pipelines, scalable systems, data analysis, AI architecture), suggest 2-3 highly specific ways I could contribute:
    
    Consider current challenges in {research_area} research:
    - Advanced data preprocessing and feature engineering techniques
    - Implementation of state-of-the-art ML algorithms and optimization
    - Development of scalable analysis frameworks and visualization tools  
    - Building robust experimental pipelines and benchmarking systems
    - Applying novel data science methodologies to enhance research outcomes
    
    CRITICAL: Write ONLY in FIRST PERSON from Anamay's perspective. Use "I", "my", "me" throughout.
    Write with specific, actionable contributions. Use phrases like:
    "I could contribute by developing..." "I would be excited to implement..." "My experience enables me to help with..."
    
    Make each contribution concrete and valuable to {research_area} research. 90-100 words.
    """
    
    research_contribution_ideas = generate_with_fallback(contribution_prompt)
    
    # Use research-specific backup template if AI generation failed
    backup_sections = get_research_specific_backup(research_area, full_name, university)
    
    # Replace empty/generic responses with research-specific backup content
    # Check if AI failed by looking for generic backup content
    if (not specific_research_interest or specific_research_interest.strip() == "" or 
        "Thank you for considering" in specific_research_interest or
        "I am deeply inspired by your groundbreaking research work" in specific_research_interest or
        len(specific_research_interest.strip()) < 50):
        specific_research_interest = backup_sections['specific_research_interest'].strip()
        logger.info(f"Using research-specific backup template for {research_area} research interest section")
        
    if (not technical_alignment or technical_alignment.strip() == "" or 
        "Thank you for considering" in technical_alignment or
        "I am deeply inspired by your groundbreaking research work" in technical_alignment or
        len(technical_alignment.strip()) < 50):
        technical_alignment = backup_sections['technical_alignment'].strip()
        logger.info(f"Using research-specific backup template for {research_area} technical alignment section")
        
    if (not research_contribution_ideas or research_contribution_ideas.strip() == "" or 
        "Thank you for considering" in research_contribution_ideas or
        "I am deeply inspired by your groundbreaking research work" in research_contribution_ideas or
        len(research_contribution_ideas.strip()) < 50):
        research_contribution_ideas = backup_sections['research_contribution_ideas'].strip()
        logger.info(f"Using research-specific backup template for {research_area} research contributions section")
    
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
