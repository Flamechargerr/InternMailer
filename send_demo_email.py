#!/usr/bin/env python3
"""
Send Demo Email - Enhanced Ultra-Personalized System
Send a real sample email to demonstrate the full personalization capabilities
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import sys
from datetime import datetime
import csv
import os
from typing import List, Dict

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import modules, create simplified versions if they don't exist
try:
    from research_alignment_analyzer import ResearchAlignmentAnalyzer
    from research_publication_finder import ResearchPublicationFinder
    from enhanced_research_area_inference import EnhancedResearchAreaInference
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    print("⚠️  Some modules not available, using simplified demo version")

# Load environment variables and confirm if .env was found
dotenv_loaded = load_dotenv()

if dotenv_loaded:
    print("✅ .env file found and loaded successfully.")
else:
    print("❌ .env file not found. Please ensure it's in the correct directory.")

def load_html_template(template_path):
    """Load HTML template from file"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Return a simplified template if the main one doesn't exist
        return get_simplified_template()

def get_simplified_template():
    """Return a more detailed HTML template based on user's preferred layout"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Research Internship Inquiry - {{ professor.research_area }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f4; }
        .container { background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .header { text-align: center; margin-bottom: 25px; border-bottom: 2px solid #005a9c; padding-bottom: 15px; }
        .header h1 { font-size: 24px; color: #003d6b; margin: 0; }
        .header p { color: #555; margin-top: 5px; font-size: 16px; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 18px; font-weight: bold; color: #005a9c; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 15px; }
        .highlight-box { background-color: #eaf2f8; border-left: 5px solid #005a9c; padding: 15px 20px; margin: 20px 0; border-radius: 5px; }
        .publication-item { background: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .publication-header { font-weight: bold; color: #2c3e50; margin-bottom: 8px; }
        .publication-venue { color: #7f8c8d; font-style: italic; margin-bottom: 8px; }
        .publication-summary { color: #34495e; margin-bottom: 12px; line-height: 1.5; }
        .research-alignment { background: #eaf2f8; border-left: 4px solid #3498db; color: #333; padding: 12px 15px; border-radius: 6px; margin-top: 10px; font-size: 14px; line-height: 1.4; }
        .research-alignment strong { display: block; margin-bottom: 5px; font-size: 15px; color: #005a9c; }
        .contact-info { background-color: #f9f9f9; padding: 20px; border-radius: 8px; text-align: center; margin-top: 20px; }
        .contact-info a { color: #005a9c; text-decoration: none; margin: 0 10px; }
        .contact-info a:hover { text-decoration: underline; }
        .skills-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; }
        .skill-category { margin-bottom: 10px; }
        .skill-category strong { display: block; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RESEARCH INTERNSHIP INQUIRY</h1>
            <p>{{ professor.research_area }} Research Opportunity</p>
        </div>

        <p>Dear Prof. {{ professor.last_name }},</p>

        <div class="highlight-box">
            <strong>🎯 Research Alignment with {{ professor.research_area.lower() }}:</strong>
            <p>{{ professor.research_alignment }}</p>
        </div>

        <p>I am Anamay Tripathy, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in a research internship opportunity with your esteemed group, particularly in the areas of {{ professor.research_area.lower() }} and its intersection with artificial intelligence applications.</p>

        <div class="section">
            <h2 class="section-title">🎓 Academic Background</h2>
            <p><strong>Degree:</strong> B.Tech in Data Science Engineering (2023–2027)</p>
            <p><strong>Institution:</strong> MIT Manipal, India</p>
            <p><strong>CGPA:</strong> 7.6 / 10</p>
            <p><strong>Relevant Coursework:</strong> {{ professor.relevant_coursework | join(', ') }}</p>
        </div>

        <div class="section">
            <h2 class="section-title">💼 Professional Experience</h2>
            <div>
                <strong>Technical Head – YaanBarpe (Current)</strong><br>
                Leading technical development and product strategy for a Karnataka Government-incubated startup focused on sustainable solutions. Responsible for system architecture, team coordination, and strategic technology decisions.
            </div>
            <div style="margin-top: 15px;">
                <strong>Data Analyst Intern – Intellect Design Arena, Mumbai (3 months)</strong><br>
                Automated KPI dashboard systems using Python and SQL, resulting in 12+ hours weekly time savings. Developed and deployed REST APIs that improved user engagement metrics by 22%. Conducted statistical analysis on large datasets to derive actionable business insights.
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🚀 Selected Research-Oriented Projects</h2>
            {% for project in professor.highlighted_projects %}
            <div class="project-item">
                <strong>{{ project.name }}</strong><br>
                {{ project.description }}
            </div>
            {% endfor %}
        </div>

        <div class="section">
            <h2 class="section-title">�️ Technical Competencies</h2>
            <div class="skills-grid">
                <div class="skill-category"><strong>Programming:</strong> Python, JavaScript, Java, C++, SQL</div>
                <div class="skill-category"><strong>Web Technologies:</strong> React.js, Node.js, Next.js, RESTful APIs</div>
                <div class="skill-category"><strong>Cloud & DevOps:</strong> AWS, GCP, Docker, Git, Linux/Unix</div>
                <div class="skill-category"><strong>Data Science:</strong> {{ professor.skills_emphasis }}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">� Recent Research Publications</h2>
            <div class="publications-section">
                {{ professor.recent_publications_html | safe }}
            </div>
        </div>

        <p>I am seeking a research internship opportunity—whether remote or on-site, funded or voluntary—to contribute to your ongoing research while gaining invaluable experience that will inform my planned graduate studies in {{ professor.research_area.lower() }} and related fields.</p>

        <p>I would be honored to discuss how my technical background, research interests, and enthusiasm for {{ professor.research_area.lower() }} can contribute to your laboratory's ongoing work. I would welcome the opportunity to provide any additional information or documentation that would be helpful.</p>

        <p>Thank you for considering my application. I look forward to the possibility of contributing to your research endeavors.</p>

        <p>Sincerely,<br>
        <strong>Anamay Tripathy</strong><br>
        B.Tech Data Science Engineering<br>
        MIT Manipal, India</p>

        <div class="contact-info">
            <a href="mailto:tripathy.anamay23@gmail.com">Email</a> | 
            <a href="https://anamay.vercel.app" target="_blank">Portfolio</a> | 
            <a href="https://www.linkedin.com/in/anamay-tripathy" target="_blank">LinkedIn</a> | 
            <a href="https://github.com/Flamechargerr" target="_blank">GitHub</a>
        </div>
    </div>
</body>
</html>
    """

def get_demo_research_data(research_area):
    """Get demo research-specific data"""
    if research_area == "Machine Learning":
        return {
            'research_title': 'Machine Learning and Artificial Intelligence',
            'research_alignment': 'My expertise in machine learning algorithms, deep learning frameworks, and AI applications directly aligns with your research in Machine Learning. My projects demonstrate practical implementation of ML models achieving 89% prediction accuracy through advanced neural network architectures and ensemble learning techniques.',
            'highlighted_projects': [
                {
                    'name': 'VARtificial Intelligence - Machine Learning Sports Prediction System',
                    'description': 'Implemented a sophisticated prediction model using XGBoost and Pyodide, incorporating real-time player statistics, historical performance data, and game dynamics analysis. The system achieves 89% prediction accuracy through advanced feature engineering and ensemble learning techniques.'
                }
            ],
            'relevant_coursework': ['Machine Learning', 'Deep Learning', 'Neural Networks', 'Python Programming'],
            'skills_emphasis': 'Python, TensorFlow, PyTorch, Scikit-learn, XGBoost, Statistical Analysis, Data Visualization, Predictive Modeling'
        }
    elif research_area == "Cybersecurity":
        return {
            'research_title': 'Cybersecurity and Information Security',
            'research_alignment': 'My technical background in system architecture and data security, combined with my experience in handling sensitive data during my internship at Intellect Design Arena, aligns well with your cybersecurity research. My projects demonstrate practical implementation of secure systems and privacy-preserving technologies.',
            'highlighted_projects': [
                {
                    'name': 'Secure Data Analytics Platform',
                    'description': 'Developed a secure data processing system with encryption and access control mechanisms, ensuring data privacy while maintaining analytical capabilities. Implemented using Python and modern cryptographic libraries.'
                }
            ],
            'relevant_coursework': ['Information Security', 'Cryptography', 'Network Security', 'Python Programming'],
            'skills_emphasis': 'Python, Cybersecurity, Data Protection, System Architecture, Cloud Security (AWS, GCP), Statistical Analysis'
        }
    else:  # Data Science
        return {
            'research_title': 'Data Science and Analytics',
            'research_alignment': 'My B.Tech in Data Science Engineering and practical experience in statistical analysis directly align with your data science research. My internship experience in developing automated KPI dashboard systems and conducting statistical analysis on large datasets provides a strong foundation for contributing to your research.',
            'highlighted_projects': [
                {
                    'name': 'Automated Analytics Dashboard System',
                    'description': 'Developed comprehensive data analytics platform using Python and SQL, resulting in 12+ hours weekly time savings. Implemented statistical analysis, data visualization, and predictive modeling capabilities.'
                }
            ],
            'relevant_coursework': ['Data Science', 'Statistical Analysis', 'Data Mining', 'Python Programming'],
            'skills_emphasis': 'Python, Statistical Analysis, Data Visualization, SQL, Machine Learning, Predictive Modeling, Business Intelligence'
        }

def generate_publications_html(publications, research_area):
    """Generate HTML for publications with alignment explanations"""
    if not publications:
        return "<p>No recent publications found.</p>"
    
    html_parts = []
    
    # Sample alignment explanations based on research area
    alignment_templates = {
        "Machine Learning": [
            "This research directly aligns with my core expertise in machine learning algorithms and deep learning frameworks. The predictive modeling approaches discussed connect perfectly with my VARtificial Intelligence project, where I achieved 89% prediction accuracy using advanced ML techniques.",
            "The neural network methodologies presented resonate with my coursework in Neural Networks and practical experience with TensorFlow and PyTorch. My technical proficiency in ensemble learning techniques makes me well-equipped to contribute to this research area.",
            "This machine learning research aligns with my academic focus in Data Science Engineering and my hands-on experience in developing sophisticated prediction models with advanced feature engineering techniques."
        ],
        "Cybersecurity": [
            "This security research aligns with my growing interest in cybersecurity applications and data privacy protection. The data protection aspects connect with my experience in handling sensitive data during my internship at Intellect Design Arena.",
            "This systems security research complements my technical background in system architecture and development from my role as Technical Head at YaanBarpe. My technical skills in cloud computing (AWS, GCP) provide a strong foundation for contributing to this research.",
            "The analytical components of this research align with my strong background in statistical analysis and data processing, particularly relevant to my work on automated KPI dashboard systems."
        ],
        "Data Science": [
            "This data analysis research directly aligns with my B.Tech in Data Science Engineering and practical experience in statistical analysis. The methodologies discussed connect perfectly with my professional experience at Intellect Design Arena.",
            "This research resonates with my experience in developing automated KPI dashboard systems that saved 12+ hours weekly. My technical proficiency in statistical analysis, data visualization, and predictive modeling makes me well-equipped to contribute.",
            "The statistical approaches presented align with my coursework and professional experience in statistical analysis, particularly relevant to my work on large-scale data processing and analytics."
        ]
    }
    
    alignments = alignment_templates.get(research_area, alignment_templates["Machine Learning"])
    
    for i, pub in enumerate(publications):
        title = pub.get('title', 'Untitled')
        year = pub.get('year', 'N/A')
        venue = pub.get('venue', 'Unknown Venue')
        summary = pub.get('summary', 'No summary available.')
        
        # Use corresponding alignment or cycle through available ones
        alignment = alignments[i % len(alignments)]
        
        # Truncate summary if too long
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        html_parts.append(f"""
        <div class="publication-item">
            <div class="publication-header">
                <strong>{i+1}. {title}</strong> ({year})
            </div>
            <div class="publication-venue">
                <em>Venue:</em> {venue}
            </div>
            <div class="publication-summary">
                <em>Summary:</em> {summary}
            </div>
            <div class="research-alignment">
                <strong>🎯 Research Alignment:</strong> {alignment}
            </div>
        </div>
        """)
    
    return "".join(html_parts)

def send_demo_email():
    """Send demonstration emails for a list of professors"""
    print("📧 SENDING MULTI-PROFESSOR DEMO EMAILS - Enhanced Ultra-Personalized System")
    print("=" * 60)
    print("Demonstrating full personalization with real professor data")
    print("=" * 60)
    
    # Read real professors from CSV file
    professors_list = []
    csv_file_path = "FINAL_MASTER_EMAIL_DATABASE.csv"
    
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Use professors with more complete names for better matching
                name = row.get('name', '').strip()
                if name and len(name) > 5 and not name.startswith("Prof."):  # Skip fictional names
                    professors_list.append({
                        "name": name,
                        "last_name": name.split()[-1] if name else "",
                        "email": "tripathy.anamay23@gmail.com",  # Send to your email for demo
                        "research_area": "Machine Learning"  # Default area, will be personalized
                    })
                    
                    # Limit to 3 professors for demo
                    if len(professors_list) >= 3:
                        break
                        
        print(f"✅ Loaded {len(professors_list)} real professors from CSV file")
    else:
        print("⚠️ CSV file not found, using fictional professors")
        # Sample list of 5 professors with different research areas
        professors_list = [
            {
                "name": "Prof. Sarah Johnson",
                "last_name": "Johnson", 
                "email": "tripathy.anamay23@gmail.com",
                "research_area": "Machine Learning"
            },
            {
                "name": "Prof. Michael Chen",
                "last_name": "Chen",
                "email": "tripathy.anamay23@gmail.com",
                "research_area": "Cybersecurity"
            },
            {
                "name": "Prof. David Rodriguez",
                "last_name": "Rodriguez",
                "email": "tripathy.anamay23@gmail.com",
                "research_area": "Data Science"
            }
        ]
    
    # Process each professor
    for i, demo_professor in enumerate(professors_list, 1):
        print(f"\n🎓 [{i}/{len(professors_list)}] Creating personalized email for: {demo_professor['name']} ({demo_professor['research_area']})")
        
        # Get research-specific content
        research_data = get_demo_research_data(demo_professor['research_area'])
        
        # Fetch real publications for the professor
        try:
            from research_publication_finder import ResearchPublicationFinder
            finder = ResearchPublicationFinder()
            # Use the correct method name and parameters
            real_publications = finder.get_professor_publications(demo_professor['name'])
            
            # Limit to maximum 3 publications even if more are found
            if real_publications and len(real_publications) > 0:
                demo_publications = real_publications[:3]  # Take only first 3 publications
                print(f"✅ Found {len(real_publications)} real publications for {demo_professor['name']}, using first {len(demo_publications)}")
            else:
                print(f"⚠️ No real publications found for {demo_professor['name']}, using demo data")
                # Demo publications with realistic data (fallback)
                demo_publications = [
                    {
                        "title": "Deep Learning Approaches for Predictive Analytics in Healthcare",
                        "year": 2024,
                        "venue": "IEEE Transactions on Medical Imaging",
                        "summary": "This paper presents novel deep learning techniques for predicting patient outcomes using electronic health records and medical imaging data. The proposed ensemble learning approach achieves high accuracy in clinical prediction tasks while maintaining interpretability for healthcare professionals."
                    },
                    {
                        "title": "Federated Learning for Privacy-Preserving Machine Learning in Healthcare",
                        "year": 2024,
                        "venue": "Nature Machine Intelligence",
                        "summary": "We propose a federated learning framework that enables collaborative machine learning across healthcare institutions while preserving patient privacy. The system uses differential privacy and secure aggregation to ensure data confidentiality while improving model performance."
                    },
                    {
                        "title": "Explainable AI for Clinical Decision Support Systems",
                        "year": 2023,
                        "venue": "Journal of Medical Internet Research",
                        "summary": "This work addresses the need for interpretable machine learning models in clinical settings. We develop explainable AI techniques that provide clear reasoning for medical predictions, enabling healthcare professionals to understand and trust AI-assisted diagnoses."
                    }
                ]
                
                if demo_professor['research_area'] == "Cybersecurity":
                    demo_publications = [
                        {
                            "title": "Advanced Threat Detection Using Machine Learning",
                            "year": 2024,
                            "venue": "IEEE Security & Privacy",
                            "summary": "This paper presents a novel approach to threat detection using advanced machine learning techniques. The proposed system can identify and classify security threats with high accuracy while minimizing false positives."
                        },
                        {
                            "title": "Secure Multi-Party Computation for Privacy-Preserving Data Analysis",
                            "year": 2023,
                            "venue": "ACM Conference on Computer and Communications Security",
                            "summary": "We propose a secure multi-party computation framework that enables collaborative data analysis while preserving the privacy of individual datasets. The system uses advanced cryptographic techniques to ensure data confidentiality."
                        },
                        {
                            "title": "Blockchain-Based Security Framework for IoT Networks",
                            "year": 2024,
                            "venue": "IEEE Internet of Things Journal",
                            "summary": "This work addresses the security challenges in IoT networks by proposing a blockchain-based framework. The system ensures data integrity and device authentication in large-scale IoT deployments."
                        }
                    ]
                elif demo_professor['research_area'] == "Data Science":
                    demo_publications = [
                        {
                            "title": "Big Data Analytics for Business Intelligence",
                            "year": 2024,
                            "venue": "Journal of Big Data",
                            "summary": "This paper explores the application of big data analytics in deriving business intelligence. We present a framework for processing large datasets to extract actionable insights for strategic decision-making."
                        },
                        {
                            "title": "Predictive Modeling Techniques for Financial Markets",
                            "year": 2023,
                            "venue": "International Journal of Data Science and Analytics",
                            "summary": "We investigate various predictive modeling techniques for financial market analysis. The proposed models can forecast market trends with high accuracy, providing valuable insights for investment strategies."
                        },
                        {
                            "title": "Data Visualization Strategies for Complex Datasets",
                            "year": 2024,
                            "venue": "IEEE Transactions on Visualization and Computer Graphics",
                            "summary": "This work presents innovative data visualization strategies for complex datasets. Our techniques enable users to effectively explore and understand large-scale data through interactive visual representations."
                        }
                    ]
        except ImportError:
            print("⚠️ ResearchPublicationFinder module not found, using demo publications")
            # Use the same demo publications as above
            demo_publications = [
                {
                    "title": "Deep Learning Approaches for Predictive Analytics in Healthcare",
                    "year": 2024,
                    "venue": "IEEE Transactions on Medical Imaging",
                    "summary": "This paper presents novel deep learning techniques for predicting patient outcomes using electronic health records and medical imaging data. The proposed ensemble learning approach achieves high accuracy in clinical prediction tasks while maintaining interpretability for healthcare professionals."
                },
                {
                    "title": "Federated Learning for Privacy-Preserving Machine Learning in Healthcare",
                    "year": 2024,
                    "venue": "Nature Machine Intelligence",
                    "summary": "We propose a federated learning framework that enables collaborative machine learning across healthcare institutions while preserving patient privacy. The system uses differential privacy and secure aggregation to ensure data confidentiality while improving model performance."
                },
                {
                    "title": "Explainable AI for Clinical Decision Support Systems",
                    "year": 2023,
                    "venue": "Journal of Medical Internet Research",
                    "summary": "This work addresses the need for interpretable machine learning models in clinical settings. We develop explainable AI techniques that provide clear reasoning for medical predictions, enabling healthcare professionals to understand and trust AI-assisted diagnoses."
                }
            ]
            
            if demo_professor['research_area'] == "Cybersecurity":
                demo_publications = [
                    {
                        "title": "Advanced Threat Detection Using Machine Learning",
                        "year": 2024,
                        "venue": "IEEE Security & Privacy",
                        "summary": "This paper presents a novel approach to threat detection using advanced machine learning techniques. The proposed system can identify and classify security threats with high accuracy while minimizing false positives."
                    },
                    {
                        "title": "Secure Multi-Party Computation for Privacy-Preserving Data Analysis",
                        "year": 2023,
                        "venue": "ACM Conference on Computer and Communications Security",
                        "summary": "We propose a secure multi-party computation framework that enables collaborative data analysis while preserving the privacy of individual datasets. The system uses advanced cryptographic techniques to ensure data confidentiality."
                    },
                    {
                        "title": "Blockchain-Based Security Framework for IoT Networks",
                        "year": 2024,
                        "venue": "IEEE Internet of Things Journal",
                        "summary": "This work addresses the security challenges in IoT networks by proposing a blockchain-based framework. The system ensures data integrity and device authentication in large-scale IoT deployments."
                    }
                ]
            elif demo_professor['research_area'] == "Data Science":
                demo_publications = [
                    {
                        "title": "Big Data Analytics for Business Intelligence",
                        "year": 2024,
                        "venue": "Journal of Big Data",
                        "summary": "This paper explores the application of big data analytics in deriving business intelligence. We present a framework for processing large datasets to extract actionable insights for strategic decision-making."
                    },
                    {
                        "title": "Predictive Modeling Techniques for Financial Markets",
                        "year": 2023,
                        "venue": "International Journal of Data Science and Analytics",
                        "summary": "We investigate various predictive modeling techniques for financial market analysis. The proposed models can forecast market trends with high accuracy, providing valuable insights for investment strategies."
                    },
                    {
                        "title": "Data Visualization Strategies for Complex Datasets",
                        "year": 2024,
                        "venue": "IEEE Transactions on Visualization and Computer Graphics",
                        "summary": "This work presents innovative data visualization strategies for complex datasets. Our techniques enable users to effectively explore and understand large-scale data through interactive visual representations."
                    }
                ]
        
        # Generate publications HTML with alignment explanations
        publications_html = generate_publications_html(demo_publications, demo_professor['research_area'])
        
        # Create complete professor data
        professor_data = {
            'last_name': demo_professor['last_name'],
            'research_area': demo_professor['research_area'],
            'research_title': research_data['research_title'],
            'research_alignment': research_data['research_alignment'],
            'highlighted_projects': research_data['highlighted_projects'],
            'relevant_coursework': research_data['relevant_coursework'],
            'skills_emphasis': research_data['skills_emphasis'],
            'recent_publications': demo_publications,
            'recent_publications_html': publications_html
        }
        
        # Load and render template
        template_content = get_simplified_template()
        
        # Simple template rendering (replace Jinja2 syntax manually for demo)
        html_content = template_content.replace('{{ professor.research_area }}', professor_data['research_area'])
        html_content = html_content.replace('{{ professor.research_area.lower() }}', professor_data['research_area'].lower())
        html_content = html_content.replace('{{ professor.last_name }}', professor_data['last_name'])
        html_content = html_content.replace('{{ professor.research_alignment }}', professor_data['research_alignment'])
        html_content = html_content.replace('{{ professor.relevant_coursework | join(\', \') }}', ', '.join(professor_data['relevant_coursework']))
        html_content = html_content.replace('{{ professor.skills_emphasis }}', professor_data['skills_emphasis'])
        html_content = html_content.replace('{{ professor.recent_publications_html | safe }}', professor_data['recent_publications_html'])
        
        # Add projects manually
        projects_html = ""
        for project in professor_data['highlighted_projects']:
            projects_html += f'<div class="project-item"><strong>{project["name"]}</strong><br>{project["description"]}</div>'
        
        # Replace the entire projects block
        start_tag = '{% for project in professor.highlighted_projects %}'
        end_tag = '{% endfor %}'
        start_index = html_content.find(start_tag)
        end_index = html_content.find(end_tag)

        if start_index != -1 and end_index != -1:
            # Extract the block and replace it with the generated HTML
            block_to_replace = html_content[start_index : end_index + len(end_tag)]
            html_content = html_content.replace(block_to_replace, projects_html)
        
        # Email configuration for each professor
        recipient_email = demo_professor["email"]
        subject = f"DEMO: Research Internship Inquiry - {demo_professor['research_area']} (Enhanced Personalization)"
        
        print(f"📧 Sending demo email to: {recipient_email}")
        print(f"📋 Subject: {subject}")
        print(f"🎯 Research Area: {demo_professor['research_area']}")
        print(f"📄 Publications: {len(demo_publications)} with alignment explanations")
        
        # Send email
        try:
            # Get email credentials
            sender_email = os.getenv('GMAIL_USER')
            sender_password = os.getenv('GMAIL_APP_PASSWORD')
            
            if not sender_email or not sender_password:
                print("❌ Email credentials not found in .env file")
                print("Please ensure GMAIL_USER and GMAIL_APP_PASSWORD are set")
                
                # Save HTML for manual review
                demo_filename = f"demo_email_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(demo_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"📄 Demo email saved as: {demo_filename}")
                print("You can open this file in a browser to see how the email looks!")
                return
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add CV attachment if available
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cv_path_from_env = os.getenv('RESUME_PATH')
            cv_paths = []
            if cv_path_from_env:
                # Create an absolute path to the resume to ensure it's found
                absolute_cv_path = os.path.join(script_dir, cv_path_from_env)
                cv_paths.append(absolute_cv_path)
            # Add fallback paths
            cv_paths.extend(['resumes/Anamay_Tripathy_Resume.pdf', 'Anamay_Tripathy_Resume.pdf', 'resume.pdf'])
            
            cv_attached = False
            for cv_path in cv_paths:
                if os.path.exists(cv_path):
                    with open(cv_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{os.path.basename(cv_path)}"'
                    )
                    msg.attach(part)
                    print(f"📎 CV attachment added: {os.path.basename(cv_path)}")
                    cv_attached = True
                    break
            
            if not cv_attached:
                print("⚠️  CV not found, sending without attachment")
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print("✅ Demo email sent successfully!")
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            print("Saving demo email as HTML file for manual review...")
            
            # Save HTML for manual review
            demo_filename = f"demo_email_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(demo_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 Demo email saved as: {demo_filename}")
            print("You can open this file in a browser to see how the email looks!")

    print("\n" + "=" * 60)
    print("All demo emails sent! Check your inbox.")
    print("=" * 60)

if __name__ == "__main__":
    send_demo_email()
