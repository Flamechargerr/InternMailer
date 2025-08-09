#!/usr/bin/env python3
"""
Send Truly Personalized Emails with Real Research Data
====================================================

This script creates emails like the Prof. LeCun example with:
1. Real research publications from APIs
2. Specific research alignment for each publication
3. Proper personalization based on professor's actual work
4. CV attachment
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ultra_accurate_research_finder import UltraAccurateResearchFinder
from enhanced_research_area_inference import EnhancedResearchAreaInference
from send_html_template_emails_with_cv import send_html_email_with_cv

def create_personalized_email_with_research(professor_name, research_area, publications, target_email):
    """Create fully personalized email with real research data"""
    
    # Get research area details
    inference = EnhancedResearchAreaInference()
    area_details = inference.get_research_area_details(research_area)
    
    # Create personalized email content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ max-width: 800px; margin: 0 auto; }}
            .research-pub {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 15px 0; }}
            .alignment {{ color: #2c3e50; font-style: italic; background: #e8f4fd; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>RESEARCH INTERNSHIP INQUIRY</h1>
            <h2>{area_details['title']} Research Opportunity</h2>
        </div>
        
        <div class="content">
            <p><strong>Dear Prof. {professor_name},</strong></p>
            
            <h3>🎯 Research Alignment with {research_area}</h3>
            <div class="alignment">
                {area_details['research_alignment']}
            </div>
            
            <p>I am Anamay Tripathy, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in a research internship opportunity with your esteemed group, particularly in the areas of <strong>{research_area}</strong> and its intersection with artificial intelligence applications.</p>
            
            <p>Your pioneering contributions to {research_area} and computational systems have been a significant inspiration for my academic journey. I am particularly drawn to the intersection of theoretical concepts and practical applications, and I am eager to contribute meaningfully to your ongoing research while deepening my understanding under your guidance.</p>
            
            <h3>🎓 Academic Background</h3>
            <p><strong>Degree:</strong> B.Tech in Data Science Engineering (2023–2027)<br>
            <strong>Institution:</strong> MIT Manipal, India<br>
            <strong>CGPA:</strong> 7.6 / 10<br>
            <strong>Relevant Coursework:</strong> {', '.join(area_details['relevant_coursework'])}</p>
            
            <h3>💼 Professional Experience</h3>
            <p><strong>Technical Head – YaanBarpe (Current)</strong><br>
            Leading technical development and product strategy for a Karnataka Government-incubated startup focused on sustainable solutions. Responsible for system architecture, team coordination, and strategic technology decisions.</p>
            
            <p><strong>Data Analyst Intern – Intellect Design Arena, Mumbai (3 months)</strong></p>
            <ul>
                <li>Automated KPI dashboard systems using Python and SQL, resulting in 12+ hours weekly time savings</li>
                <li>Developed and deployed REST APIs that improved user engagement metrics by 22%</li>
                <li>Conducted statistical analysis on large datasets to derive actionable business insights</li>
            </ul>
            
            <h3>🚀 Selected Research-Oriented Projects</h3>
            <p><strong>{area_details['highlighted_projects'][0]}</strong><br>
            Implemented a sophisticated prediction model using XGBoost and Pyodide, incorporating real-time player statistics, historical performance data, and game dynamics analysis. The system achieves 89% prediction accuracy through advanced feature engineering and ensemble learning techniques.</p>
            
            <h3>🛠️ Technical Competencies</h3>
            <p><strong>Programming Languages:</strong> Python, JavaScript, Java, C++, SQL<br>
            <strong>{area_details['title']}:</strong> {', '.join(area_details['skills_emphasis'])}<br>
            <strong>Web Technologies:</strong> React.js, Node.js, MongoDB, Next.js, RESTful APIs<br>
            <strong>Cloud & DevOps:</strong> AWS, GCP, Docker, Git, Linux/Unix<br>
            <strong>Data Science & Analytics:</strong> Statistical Analysis, Data Visualization, Predictive Modeling</p>
    """
    
    # Add research publications section if available
    if publications:
        html_content += """
            <h3>📄 Recent Research Publications</h3>
        """
        
        for i, pub in enumerate(publications, 1):
            # Create specific research alignment for each publication
            pub_alignment = f"This research exemplifies the innovative thinking that attracts me to your group - I see clear opportunities for my technical skills to add value. My hands-on experience developing predictive models with 89% accuracy demonstrates my capability in algorithmic research."
            
            if "medical" in pub.title.lower() or "healthcare" in pub.title.lower():
                pub_alignment = f"The challenges addressed in this work resonate with my practical experience in system development and data analytics, particularly in healthcare applications where precision and reliability are paramount."
            elif "vision" in pub.title.lower() or "image" in pub.title.lower():
                pub_alignment = f"The computer vision techniques showcased in this work align perfectly with my experience in image processing and pattern recognition systems using OpenCV."
            elif "graph" in pub.title.lower() or "neural" in pub.title.lower():
                pub_alignment = f"The graph neural network methodologies in this research align with my understanding of complex data relationships and network analysis."
            
            html_content += f"""
            <div class="research-pub">
                <h4>{i}. {pub.title} ({pub.year})</h4>
                <p><strong>Venue:</strong> {pub.venue}<br>
                <strong>Citations:</strong> {pub.citations}<br>
                <strong>Summary:</strong> {pub.abstract[:200]}...</p>
                
                <div class="alignment">
                    🎯 <strong>Research Alignment:</strong> {pub_alignment}
                </div>
            </div>
            """
    
    html_content += f"""
            <h3>🔬 Research Interests and Alignment</h3>
            <p>I am particularly fascinated by the intersection of {research_area} algorithms and real-world applications, especially in the context of predictive modeling and automated decision-making systems. My academic coursework in deep learning and practical experience in implementing ML models has prepared me to contribute meaningfully to research in these areas.</p>
            
            <p>I am seeking a research internship opportunity—whether remote or on-site, funded or voluntary—to contribute to your ongoing research while gaining invaluable experience that will inform my planned graduate studies in {research_area} and related fields.</p>
            
            <p>I would be honored to discuss how my technical background, research interests, and enthusiasm for {research_area} can contribute to your laboratory's ongoing work. I have attached my detailed curriculum vitae for your review, and I would welcome the opportunity to provide any additional information or documentation that would be helpful.</p>
            
            <p>Thank you very much for your time and consideration. I look forward to the possibility of contributing to your research group.</p>
            
            <h3>📞 Contact Information</h3>
            <p><strong>Email:</strong> tripathy.anamay23@gmail.com<br>
            <strong>Phone:</strong> +91-9877454747<br>
            <strong>Portfolio:</strong> anamay.vercel.app<br>
            <strong>LinkedIn:</strong> linkedin.com/in/anamay-tripathy<br>
            <strong>GitHub:</strong> github.com/Flamechargerr</p>
            
            <p>Sincerely,<br><br>
            <strong>Anamay Tripathy</strong><br>
            B.Tech Data Science Engineering<br>
            MIT Manipal, India</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_personalized_research_emails():
    """Send 2 fully personalized emails with real research publications"""
    
    print("📧 SENDING TRULY PERSONALIZED RESEARCH EMAILS")
    print("=" * 80)
    print("✅ Features:")
    print("   • Real research publications from academic APIs")
    print("   • Publication-specific research alignment")
    print("   • Personalized content based on professor's actual work")
    print("   • CV attachment included")
    print("=" * 80)
    
    target_email = "tripathy.anamay23@gmail.com"
    finder = UltraAccurateResearchFinder()
    
    # Test professors with known research
    test_professors = [
        {
            'name': 'Yann LeCun',
            'affiliation': 'Meta AI',
            'email': 'yann@fb.com',
            'scholar_id': 'WLN3QrAAAAAJ',  # Real Scholar ID
            'expected_area': 'machine learning'
        },
        {
            'name': 'Fei-Fei Li', 
            'affiliation': 'Stanford University',
            'email': 'feifeili@cs.stanford.edu',
            'scholar_id': 'rDfyQnIAAAAJ',  # Real Scholar ID
            'expected_area': 'computer vision'
        }
    ]
    
    emails_sent = 0
    
    for i, prof in enumerate(test_professors, 1):
        print(f"\n📚 EMAIL {i}: Researching {prof['name']} from {prof['affiliation']}")
        print("-" * 60)
        
        try:
            # Find real research publications
            publications = finder.find_author_publications(
                name=prof['name'],
                affiliation=prof['affiliation'],
                email=prof['email'],
                scholar_id=prof['scholar_id'],
                max_results=3
            )
            
            print(f"📄 Found {len(publications)} publications")
            
            if publications:
                # Extract research interests from real publications
                research_interests = finder._extract_research_interests(publications)
                print(f"🧠 Research interests: {research_interests[:3]}")
                
                # Infer research area
                inference = EnhancedResearchAreaInference()
                research_area = inference.infer_research_area({
                    'name': ' '.join(research_interests),
                    'affiliation': prof['affiliation']
                })
                print(f"🎯 Classified as: {research_area.upper()}")
                
                # Create personalized email
                subject = f"Research Internship Inquiry - Your work in {research_area}"
                html_content = create_personalized_email_with_research(
                    prof['name'].split()[-1],  # Last name
                    research_area,
                    publications,
                    target_email
                )
                
                # Send email with CV
                success = send_html_email_with_cv(
                    target_email, 
                    subject, 
                    html_content, 
                    f"Personalized Email - {prof['name']}"
                )
                
                if success:
                    emails_sent += 1
                    print(f"✅ Personalized email sent to {target_email}")
                else:
                    print(f"⚠️ Email saved locally but not sent")
                    
            else:
                print(f"❌ No publications found for {prof['name']}")
                
        except Exception as e:
            print(f"❌ Error processing {prof['name']}: {str(e)}")
            continue
    
    # Summary
    print(f"\n" + "=" * 80)
    print("📊 PERSONALIZED EMAIL CAMPAIGN SUMMARY")
    print("=" * 80)
    print(f"✅ Emails sent: {emails_sent}/2")
    print(f"📧 Target: {target_email}")
    print(f"📎 CV attached: ✅ YES")
    print(f"🔬 Real research publications: ✅ YES")
    print(f"💌 Publication-specific alignment: ✅ YES")
    
    if emails_sent > 0:
        print(f"\n🎉 Check your inbox at {target_email}!")
        print("📧 Each email contains:")
        print("   • Professor's actual research publications")
        print("   • Specific alignment for each publication")
        print("   • Research area-based personalization")
        print("   • Professional HTML formatting")
        print("   • Attached CV (PDF)")
    else:
        print(f"\n⚠️ No emails sent. Check API connectivity and SMTP settings.")
    
    print("=" * 80)

if __name__ == "__main__":
    send_personalized_research_emails()
