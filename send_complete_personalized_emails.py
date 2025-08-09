#!/usr/bin/env python3
"""
Send Complete Personalized Emails with Full Content
==================================================

This creates emails with complete, properly formatted content including:
✅ All sections filled out completely
✅ Research publications with alignments  
✅ CV attachment
✅ Professional formatting
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ultra_accurate_research_finder import UltraAccurateResearchFinder, Publication
from enhanced_research_area_inference import EnhancedResearchAreaInference
from send_html_template_emails_with_cv import send_html_email_with_cv

def create_complete_personalized_email(professor_name, research_area):
    """Create complete personalized email with all content filled"""
    
    # Get research area details
    inference = EnhancedResearchAreaInference()
    area_details = inference.get_research_area_details(research_area)
    
    # Create sample publications for demonstration
    sample_publications = [
        Publication(
            title="Deep Learning Approaches for Predictive Analytics in Healthcare",
            authors=["Research Team"],
            year=2024,
            venue="IEEE Transactions on Medical Imaging",
            abstract="This paper presents novel deep learning techniques for predicting patient outcomes using electronic health records and medical imaging data. The proposed ensemble learning approach achieves high accuracy in clinical prediction tasks.",
            citations=87,
            source="Research Database",
            confidence_score=0.95
        ),
        Publication(
            title="Federated Learning for Privacy-Preserving Machine Learning in Healthcare", 
            authors=["ML Research Group"],
            year=2024,
            venue="Nature Machine Intelligence",
            abstract="We propose a federated learning framework that enables collaborative machine learning across healthcare institutions while preserving patient privacy. The system uses differential privacy and secure aggregation techniques.",
            citations=124,
            source="Research Database",
            confidence_score=0.93
        ),
        Publication(
            title="Explainable AI for Clinical Decision Support Systems",
            authors=["AI Lab Team"],
            year=2023,
            venue="Journal of Medical Internet Research", 
            abstract="This work addresses the need for interpretable machine learning models in clinical settings. We develop explainable AI techniques that provide clear reasoning for medical predictions, enabling healthcare professionals to make informed decisions.",
            citations=156,
            source="Research Database",
            confidence_score=0.91
        )
    ]
    
    # Create complete HTML email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .email-container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: bold;
            }}
            .header h2 {{
                margin: 10px 0 0 0;
                font-size: 18px;
                opacity: 0.9;
                font-weight: normal;
            }}
            .content {{
                padding: 30px;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .section h3 {{
                color: #2c3e50;
                font-size: 18px;
                margin-bottom: 15px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 5px;
            }}
            .research-alignment {{
                background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%);
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                font-style: italic;
                color: #2c3e50;
            }}
            .publication {{
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
            }}
            .publication h4 {{
                color: #2c3e50;
                margin: 0 0 10px 0;
                font-size: 16px;
            }}
            .publication-meta {{
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
            }}
            .publication-alignment {{
                background: #e8f4fd;
                border-left: 3px solid #667eea;
                padding: 15px;
                margin-top: 15px;
                border-radius: 3px;
                font-style: italic;
                color: #2c3e50;
            }}
            .skills-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }}
            .skill-category {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                border-left: 3px solid #667eea;
            }}
            .contact-info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-top: 25px;
            }}
            .contact-info h3 {{
                margin-top: 0;
                color: #2c3e50;
            }}
            .contact-links {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 15px;
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 8px;
            }}
            .signature {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>RESEARCH INTERNSHIP INQUIRY</h1>
                <h2>{area_details['title']} Research Opportunity</h2>
            </div>
            
            <div class="content">
                <div class="section">
                    <p><strong>Dear Prof. {professor_name},</strong></p>
                    
                    <h3>🎯 Research Alignment with {research_area}</h3>
                    <div class="research-alignment">
                        {area_details['research_alignment']}
                    </div>
                    
                    <p>I am Anamay Tripathy, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in a research internship opportunity with your esteemed group, particularly in the areas of <strong>{research_area}</strong> and its intersection with artificial intelligence applications.</p>
                    
                    <p>Your pioneering contributions to {research_area} and computational systems have been a significant inspiration for my academic journey. I am particularly drawn to the intersection of theoretical concepts and practical applications, and I am eager to contribute meaningfully to your ongoing research while deepening my understanding under your guidance.</p>
                </div>

                <div class="section">
                    <h3>🎓 Academic Background</h3>
                    <p><strong>Degree:</strong> B.Tech in Data Science Engineering (2023–2027)<br>
                    <strong>Institution:</strong> MIT Manipal, India<br>
                    <strong>CGPA:</strong> 7.6 / 10</p>
                    
                    <p><strong>Relevant Coursework:</strong> {', '.join(area_details['relevant_coursework'])}</p>
                </div>

                <div class="section">
                    <h3>💼 Professional Experience</h3>
                    <p><strong>Technical Head – YaanBarpe (Current)</strong><br>
                    Leading technical development and product strategy for a Karnataka Government-incubated startup focused on sustainable solutions. Responsible for system architecture, team coordination, and strategic technology decisions.</p>
                    
                    <p><strong>Data Analyst Intern – Intellect Design Arena, Mumbai (3 months)</strong></p>
                    <ul>
                        <li>Automated KPI dashboard systems using Python and SQL, resulting in 12+ hours weekly time savings</li>
                        <li>Developed and deployed REST APIs that improved user engagement metrics by 22%</li>
                        <li>Conducted statistical analysis on large datasets to derive actionable business insights</li>
                    </ul>
                </div>

                <div class="section">
                    <h3>🚀 Selected Research-Oriented Projects</h3>
                    <p><strong>{area_details['highlighted_projects'][0]}</strong><br>
                    Implemented a sophisticated prediction model using XGBoost and Pyodide, incorporating real-time player statistics, historical performance data, and game dynamics analysis. The system achieves 89% prediction accuracy through advanced feature engineering and ensemble learning techniques.</p>
                    
                    <p><strong>Advanced Data Analytics Platform</strong><br>
                    Developed innovative solutions using cutting-edge technologies and methodologies. Implemented robust systems with focus on performance, scalability, and user experience.</p>
                </div>

                <div class="section">
                    <h3>🛠️ Technical Competencies</h3>
                    <div class="skills-grid">
                        <div class="skill-category">
                            <strong>Programming Languages</strong><br>
                            Python, JavaScript, Java, C++, SQL
                        </div>
                        <div class="skill-category">
                            <strong>{area_details['title']}</strong><br>
                            {', '.join(area_details['skills_emphasis'])}
                        </div>
                        <div class="skill-category">
                            <strong>Web Technologies</strong><br>
                            React.js, Node.js, MongoDB, Next.js, RESTful APIs
                        </div>
                        <div class="skill-category">
                            <strong>Cloud & DevOps</strong><br>
                            AWS, GCP, Docker, Git, Linux/Unix
                        </div>
                        <div class="skill-category">
                            <strong>Data Science & Analytics</strong><br>
                            Statistical Analysis, Data Visualization, Predictive Modeling
                        </div>
                        <div class="skill-category">
                            <strong>Development Tools</strong><br>
                            Supabase, Firebase, Jupyter Notebooks, VS Code
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h3>📄 Recent Research Publications</h3>
    """
    
    # Add publications
    for i, pub in enumerate(sample_publications, 1):
        # Create specific research alignment for each publication
        if "healthcare" in pub.title.lower() or "medical" in pub.title.lower():
            alignment = "This research directly aligns with my core expertise in machine learning algorithms and deep learning frameworks. The predictive modeling approaches discussed connect perfectly with my VARtificial Intelligence project, where I achieved 89% prediction accuracy using advanced ML techniques."
        elif "federated" in pub.title.lower() or "privacy" in pub.title.lower():
            alignment = "The neural network methodologies presented resonate with my coursework in Neural Networks and practical experience with TensorFlow and PyTorch. My technical proficiency in ensemble learning techniques makes me well-equipped to contribute to this research area."
        else:
            alignment = "This machine learning research aligns with my academic focus in Data Science Engineering and my hands-on experience in developing sophisticated prediction models with advanced feature engineering techniques."
        
        html_content += f"""
                    <div class="publication">
                        <h4>{i}. {pub.title} ({pub.year})</h4>
                        <div class="publication-meta">
                            <strong>Venue:</strong> {pub.venue}<br>
                            <strong>Citations:</strong> {pub.citations}<br>
                            <strong>Summary:</strong> {pub.abstract[:200]}...
                        </div>
                        <div class="publication-alignment">
                            🎯 <strong>Research Alignment:</strong> {alignment}
                        </div>
                    </div>
        """
    
    html_content += f"""
                </div>

                <div class="section">
                    <h3>🔬 Research Interests and Alignment</h3>
                    <p>I am particularly fascinated by the intersection of {research_area} algorithms and real-world applications, especially in the context of predictive modeling and automated decision-making systems. My academic coursework in deep learning and practical experience in implementing ML models has prepared me to contribute meaningfully to research in these areas.</p>
                    
                    <p>I am seeking a research internship opportunity—whether remote or on-site, funded or voluntary—to contribute to your ongoing research while gaining invaluable experience that will inform my planned graduate studies in {research_area} and related fields.</p>
                    
                    <p>I would be honored to discuss how my technical background, research interests, and enthusiasm for {research_area} can contribute to your laboratory's ongoing work. I have attached my detailed curriculum vitae for your review, and I would welcome the opportunity to provide any additional information or documentation that would be helpful.</p>
                    
                    <p>Thank you very much for your time and consideration. I look forward to the possibility of contributing to your research group.</p>
                </div>

                <div class="contact-info">
                    <h3>📞 Contact Information</h3>
                    <div class="contact-links">
                        <div><strong>Email:</strong> tripathy.anamay23@gmail.com</div>
                        <div><strong>Phone:</strong> +91-9877454747</div>
                        <div><strong>Portfolio:</strong> anamay.vercel.app</div>
                        <div><strong>LinkedIn:</strong> linkedin.com/in/anamay-tripathy</div>
                        <div><strong>GitHub:</strong> github.com/Flamechargerr</div>
                    </div>
                </div>

                <div class="signature">
                    <p>Sincerely,<br><br>
                    <strong>Anamay Tripathy</strong><br>
                    B.Tech Data Science Engineering<br>
                    MIT Manipal, India</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_complete_demo_email():
    """Send a complete, properly formatted demonstration email"""
    
    print("📧 SENDING COMPLETE PERSONALIZED EMAIL DEMONSTRATION")
    print("=" * 80)
    print("✅ Features:")
    print("   • Complete content in all sections")
    print("   • Professional HTML formatting")
    print("   • Research publications with alignments")
    print("   • CV attachment")
    print("   • Proper email structure")
    print("=" * 80)
    
    target_email = "tripathy.anamay23@gmail.com"
    
    # Create complete personalized email
    html_content = create_complete_personalized_email("Tyagi", "machine learning")
    subject = "Research Internship Inquiry - Your work in machine learning"
    
    # Send email with CV
    success = send_html_email_with_cv(
        target_email,
        subject, 
        html_content,
        "Complete Personalized Email Demo"
    )
    
    print(f"\n📊 RESULTS:")
    if success:
        print(f"✅ Complete email sent successfully to {target_email}")
        print("📧 Email contains:")
        print("   • All sections properly filled out")
        print("   • 3 research publications with alignments")
        print("   • Professional formatting")
        print("   • CV attachment (PDF)")
        print("   • Complete technical competencies")
        print("   • Full contact information")
    else:
        print("⚠️ Email saved locally (check SMTP config)")
    
    print("\n" + "=" * 80)
    print("🎉 COMPLETE EMAIL DEMONSTRATION FINISHED!")
    print("✅ Check your inbox for the fully formatted email")
    print("=" * 80)

if __name__ == "__main__":
    send_complete_demo_email()
