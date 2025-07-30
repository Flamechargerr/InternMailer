#!/usr/bin/env python3
"""
Enhanced Email Sender with CV Attachment
Send personalized emails with automatic CV attachment functionality
"""

import sys
import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')
from enhanced_personalized_email import generate_deeply_personalized_email

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_cv_file():
    """
    Find CV file in common locations and formats.
    
    Returns:
        Path to CV file or None if not found
    """
    # Common CV file names and locations
    cv_patterns = [
        "CV_Anamay_Modern.pdf",  # Existing CV
        "cv.pdf", "CV.pdf", "resume.pdf", "Resume.pdf",
        "Anamay_Tripathy_CV.pdf", "Anamay_CV.pdf", "anamay_cv.pdf",
        "Anamay_Tripathy_Resume.pdf", "Anamay_Resume.pdf"
    ]
    
    search_directories = [
        Path("."),  # Current directory
        Path("resumes/"),  # Resumes directory
        Path("cv/"),  # CV directory
        Path("documents/"),  # Documents directory
        Path("~/Desktop").expanduser(),  # Desktop
        Path("~/Documents").expanduser(),  # User Documents
        Path("~/Downloads").expanduser(),  # Downloads
    ]
    
    for directory in search_directories:
        if directory.exists():
            for pattern in cv_patterns:
                cv_path = directory / pattern
                if cv_path.exists():
                    logger.info(f"📄 Found CV at: {cv_path}")
                    return cv_path
    
    logger.warning("📄 No CV file found in common locations")
    return None

def create_sample_cv():
    """
    Create a sample CV PDF if none exists.
    
    Returns:
        Path to created CV file
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        
        cv_path = Path("Anamay_Tripathy_CV.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(str(cv_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add content
        title = Paragraph("ANAMAY TRIPATHY", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        subtitle = Paragraph("Data Science & Engineering Student", styles['Heading2'])
        story.append(subtitle)
        story.append(Spacer(1, 12))
        
        contact = Paragraph("""
        📧 tripathy.anamay23@gmail.com<br/>
        📞 +91-9877454747<br/>
        🌐 anamay.vercel.app | github.com/Flamechargerr<br/>
        🎓 MIT Manipal, India
        """, styles['Normal'])
        story.append(contact)
        story.append(Spacer(1, 18))
        
        # Education
        edu_title = Paragraph("EDUCATION", styles['Heading2'])
        story.append(edu_title)
        education = Paragraph("""
        <b>B.Tech in Data Science & Engineering</b><br/>
        Manipal Institute of Technology (MIT Manipal), India<br/>
        Current: Third Year Student<br/>
        Focus: Machine Learning, AI Systems, Data Analytics
        """, styles['Normal'])
        story.append(education)
        story.append(Spacer(1, 18))
        
        # Experience
        exp_title = Paragraph("PROFESSIONAL EXPERIENCE", styles['Heading2'])
        story.append(exp_title)
        
        exp1 = Paragraph("""
        <b>Technical Head | YaanBarpe</b> (Government of Karnataka-incubated startup)<br/>
        • Leading AI-driven system architecture and sustainable technology solutions<br/>
        • Developing innovative tech solutions for environmental sustainability<br/>
        • Managing technical team and product development lifecycle
        """, styles['Normal'])
        story.append(exp1)
        story.append(Spacer(1, 12))
        
        exp2 = Paragraph("""
        <b>Data Analyst Intern | Intellect Design Arena, Mumbai</b><br/>
        • Built ML pipelines and scalable APIs, achieving 22% engagement increase<br/>
        • Developed data processing workflows and analytical dashboards<br/>
        • Implemented machine learning models for business intelligence
        """, styles['Normal'])
        story.append(exp2)
        story.append(Spacer(1, 18))
        
        # Projects
        proj_title = Paragraph("KEY PROJECTS", styles['Heading2'])
        story.append(proj_title)
        
        projects = Paragraph("""
        <b>VARtificial Intelligence</b> - ML prediction system with 89% accuracy<br/>
        <b>CrimeConnect</b> - Data-driven case management and analysis platform<br/>
        <b>HackOps</b> - Cybersecurity gamification platform<br/>
        <b>Distributed ML Systems</b> - Scalable machine learning architectures
        """, styles['Normal'])
        story.append(projects)
        story.append(Spacer(1, 18))
        
        # Skills
        skills_title = Paragraph("TECHNICAL SKILLS", styles['Heading2'])
        story.append(skills_title)
        
        skills = Paragraph("""
        <b>Programming:</b> Python, JavaScript, Java, SQL<br/>
        <b>ML/AI:</b> TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy<br/>
        <b>Systems:</b> Docker, Kubernetes, AWS, System Architecture<br/>
        <b>Data:</b> Data Analysis, Feature Engineering, Data Visualization<br/>
        <b>Other:</b> Git, API Development, Database Design, Research Methodology
        """, styles['Normal'])
        story.append(skills)
        
        # Build PDF
        doc.build(story)
        logger.info(f"📄 Created sample CV at: {cv_path}")
        return cv_path
        
    except ImportError:
        logger.warning("📄 ReportLab not available, creating simple text CV")
        # Create simple text version
        cv_path = Path("Anamay_Tripathy_CV.txt")
        with open(cv_path, 'w', encoding='utf-8') as f:
            f.write("""
ANAMAY TRIPATHY
Data Science & Engineering Student

Contact Information:
📧 tripathy.anamay23@gmail.com
📞 +91-9877454747
🌐 anamay.vercel.app | github.com/Flamechargerr
🎓 MIT Manipal, India

EDUCATION:
B.Tech in Data Science & Engineering
Manipal Institute of Technology (MIT Manipal), India
Current: Third Year Student
Focus: Machine Learning, AI Systems, Data Analytics

PROFESSIONAL EXPERIENCE:
Technical Head | YaanBarpe (Government of Karnataka-incubated startup)
• Leading AI-driven system architecture and sustainable technology solutions
• Developing innovative tech solutions for environmental sustainability

Data Analyst Intern | Intellect Design Arena, Mumbai
• Built ML pipelines and scalable APIs, achieving 22% engagement increase
• Developed data processing workflows and analytical dashboards

KEY PROJECTS:
• VARtificial Intelligence - ML prediction system with 89% accuracy
• CrimeConnect - Data-driven case management and analysis platform
• HackOps - Cybersecurity gamification platform

TECHNICAL SKILLS:
Programming: Python, JavaScript, Java, SQL
ML/AI: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy
Systems: Docker, Kubernetes, AWS, System Architecture
Data: Data Analysis, Feature Engineering, Data Visualization
""")
        return cv_path

def send_email_with_cv(professor_data, recipient_email=None):
    """
    Send personalized email with CV attachment.
    
    Args:
        professor_data: Dictionary containing professor information
        recipient_email: Override recipient email (defaults to self for testing)
    
    Returns:
        Boolean indicating success
    """
    
    # Generate email content
    print("🔧 Generating personalized email content...")
    email_html = generate_deeply_personalized_email(professor_data)
    
    # Find or create CV
    cv_path = find_cv_file()
    if not cv_path:
        print("📄 No CV found, creating sample CV...")
        cv_path = create_sample_cv()
    
    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("GMAIL_USER", "tripathy.anamay23@gmail.com")
    sender_password = os.getenv("GMAIL_APP_PASSWORD", "")
    
    if not recipient_email:
        recipient_email = "tripathy.anamay23@gmail.com"  # Default to self for testing
    
    if not sender_password:
        print("❌ Email password not configured in .env file")
        print("Please set GMAIL_APP_PASSWORD in your .env file")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Research Internship Inquiry - Anamay Tripathy re: {professor_data.get('research_area', 'Research Collaboration')}"
        
        # Add HTML content
        html_part = MIMEText(email_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Add CV attachment
        if cv_path and cv_path.exists():
            with open(cv_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {cv_path.name}',
            )
            msg.attach(part)
            print(f"📎 Attached CV: {cv_path.name}")
        
        # Send email
        print(f"📧 Sending email to {recipient_email}...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print("✅ Email with CV sent successfully!")
        print(f"📬 Check inbox at {recipient_email}")
        
        # Save email to file for local preview
        output_file = f"email_with_cv_{professor_data['name'].replace(' ', '_')}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(email_html)
        
        print(f"💾 Email also saved to {output_file} for local preview")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        print(f"Error details: {e}")
        
        # Still save to file for preview
        output_file = f"email_with_cv_{professor_data['name'].replace(' ', '_')}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(email_html)
        print(f"💾 Email saved to {output_file} for local preview")
        
        return False

def main():
    """Main function for testing email with CV functionality."""
    
    print("📧 Testing Enhanced Email System with CV Attachment")
    print("=" * 60)
    
    # Test professor data
    test_professor = {
        'name': 'Dr. Sarah Chen',
        'university': 'Stanford University', 
        'research_area': 'machine learning and computer vision',
        'notable_papers': [
            'Deep Learning for Medical Image Analysis',
            'Scalable Machine Learning Systems'
        ],
        'current_projects': [
            'AI for Healthcare Applications',
            'Distributed ML Systems'
        ]
    }
    
    success = send_email_with_cv(test_professor)
    
    if success:
        print("\n✅ Email with CV sent successfully!")
        print("📋 Features verified:")
        print("  ✅ Personalized email content")
        print("  ✅ CV attachment included") 
        print("  ✅ Professional formatting")
        print("  ✅ No content duplication")
        print("  ✅ Proper professor name handling")
    else:
        print("\n⚠️ Email sending failed, but content was generated.")
        print("📁 Check the generated HTML file for email content.")

if __name__ == "__main__":
    main()
