import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Configuration for sending email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "tripathy.anamay23@gmail.com"
EMAIL_PASS = "qzxw bjqs wgqk wqtt"  # App password from auto_campaign.py


def create_enhanced_corporate_email(name, title, company, linkedin):
    """Creates an enhanced corporate internship email"""
    subject = f"Internship Inquiry – Anamay Tripathy re: Data Science & AI Opportunities"
    
    email_body = f"""
INTERNSHIP INQUIRY

Dear {name},

I am Anamay Tripathy, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in internship opportunities at {company}, particularly in areas leveraging Machine Learning, Data Analysis, and AI-driven systems.

Your work as {title} at {company} and the company's commitment to innovation in technology have been a significant inspiration for my career journey. I am particularly drawn to {company}'s approach to technological solutions, and I am eager to contribute meaningfully to your team while gaining valuable industry experience.

Academic Background

Degree: B.Tech in Data Science Engineering (2023–2027)
Institution: MIT Manipal, India
CGPA: 7.6 / 10
Relevant Coursework: Data Structures & Algorithms, Machine Learning, Database Management Systems, Computer Networks, Software Engineering, Statistical Analysis

Professional Experience

Technical Head – YaanBarpe (Current)
Leading technical development and product strategy for a Karnataka Government-incubated startup focused on sustainable solutions. Responsible for system architecture, team coordination, and strategic technology decisions.

Data Analyst Intern – Intellect Design Arena, Mumbai (3 months)
• Automated KPI dashboard systems using Python and SQL, resulting in 12+ hours weekly time savings
• Developed and deployed REST APIs that improved user engagement metrics by 22%
• Conducted statistical analysis on large datasets to derive actionable business insights

Selected Projects

CrimeConnect: Data-Driven Case Management Platform
Developed a comprehensive case management system using the MERN stack and Supabase, incorporating AI-powered analytics for pattern recognition. The system achieved a 40% reduction in case processing time through automated workflow optimization.

VARtificial Intelligence: Machine Learning Prediction System
Implemented a sophisticated prediction model using XGBoost and Pyodide, incorporating real-time data analysis. The system achieves 89% prediction accuracy through advanced feature engineering and ensemble learning techniques.

HackOps: Cybersecurity Gamification Platform
Designed and implemented a comprehensive cybersecurity training platform featuring 25+ security challenges. The platform improved user cyber-awareness by 35% through gamified learning methodologies.

Technical Competencies

Programming Languages: Python, JavaScript, Java, SQL
ML/AI: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy
Cloud & Systems: Docker, Kubernetes, AWS, System Architecture
Data: Data Analysis, Feature Engineering, Data Visualization
Development Tools: Git, Supabase, Firebase, VS Code

I am seeking an internship opportunity—whether remote or on-site—to contribute to {company}'s innovative work while gaining valuable industry experience. I am particularly interested in roles that combine my technical skills with practical business applications.

I would be honored to discuss how my technical background and enthusiasm for data science can contribute to {company}'s ongoing projects. I have attached my detailed curriculum vitae for your review.

Thank you very much for your time and consideration. I look forward to the possibility of contributing to your team.

Contact Information

Email: tripathy.anamay23@gmail.com
Phone: +91-9877454747
Portfolio: anamay.vercel.app
LinkedIn: linkedin.com/in/anamay-tripathy
GitHub: github.com/Flamechargerr

Sincerely,

Anamay Tripathy
B.Tech Data Science Engineering
MIT Manipal, India
    """
    
    return subject, email_body


def send_enhanced_dry_run_email(recipient_email="tripathy.anamay23@gmail.com"):
    """Send enhanced dry run email with PDF CV"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = "[DRY RUN] Enhanced Corporate Internship Inquiry"

    # Create sample email content
    subject, body = create_enhanced_corporate_email(
        "Hiring Manager", 
        "Talent Acquisition Lead", 
        "Your Company", 
        "linkedin.com/sample"
    )
    
    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF CV (use existing PDF if available, otherwise text)
    cv_paths = [
        r"C:\Users\anama\OneDrive\Desktop\internmailing\resumes\CV_Anamay_Modern.pdf",
        r"C:\Users\anama\OneDrive\Desktop\internmailing\Anamay_Tripathy_CV.pdf",
        r"C:\Users\anama\OneDrive\Desktop\internmailing\Anamay_Tripathy_CV.txt"
    ]
    
    cv_attached = False
    for cv_path in cv_paths:
        if os.path.exists(cv_path):
            try:
                with open(cv_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    
                    filename = os.path.basename(cv_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
                    cv_attached = True
                    print(f"Attached CV: {filename}")
                    break
            except Exception as e:
                print(f"Failed to attach {cv_path}: {e}")
                continue
    
    if not cv_attached:
        print("Warning: No CV file could be attached")

    # Send the mail
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, recipient_email, text)
        server.quit()
        print(f"[SUCCESS] Enhanced test email sent to {recipient_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")


if __name__ == "__main__":
    send_enhanced_dry_run_email()
