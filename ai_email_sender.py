"""
🆓 FREE AI EMAIL SENDER
Simple standalone script that generates personalized emails using free AI
"""

import sqlite3
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import time
from free_ai_analyzer import FreeAIEmailGenerator

# Email credentials from environment
EMAIL = os.getenv('EMAIL_ADDRESS', 'tripathy.anamay23@gmail.com')
PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # User needs to set this

# Initialize free AI generator
ai_generator = FreeAIEmailGenerator()

def get_european_professors(limit=50):
    """Get European professors from database"""
    db_path = 'data/clean_40k_professors.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, email, affiliation, research_interest 
        FROM verified_contacts 
        LIMIT ?
    """, (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def generate_ai_email(professor_name, university, research_area):
    """Generate personalized email using free AI"""
    ai_result = ai_generator.generate_personalized_email(
        professor_name=professor_name,
        university=university,
        research_area=research_area,
        paper_title=None
    )
    
    # Create email HTML
    email_html = f"""
<p>Dear Professor {professor_name},</p>

<p>{ai_result.personalized_intro}</p>

<p>{ai_result.paper_mention}</p>

<p>My academic background and research experiences have prepared me to contribute meaningfully to your lab:</p>

<ul>
    <li><strong>Research Experience:</strong> As Technical Head at YaanBarpe, I led ML-powered solutions achieving 34% efficiency improvement. I also interned at Intellect Design Arena optimizing financial data processing with Python and Kafka</li>
    <li><strong>Technical Skills:</strong> Python, PyTorch, TensorFlow, SQL, scalable ML pipelines</li>
    <li><strong>Projects:</strong> Predictive modeling, time-series analysis, data-driven systems</li>
</ul>

<p>{ai_result.research_connection}</p>

<p>{ai_result.collaboration_idea}</p>

<p>I have attached my CV for your review. I would welcome the opportunity to discuss my background and potential fit within your group.</p>

<p>Thank you for your time and consideration.</p>

<p>Sincerely,<br><br>
<strong>Anamay Tripathy</strong><br>
B.Tech Data Science Engineering<br>
MIT Manipal, India<br>
<a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a><br>
<a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
+91-9877454747</p>
"""
    
    subject = f"Research Collaboration Inquiry - {research_area}"
    
    return subject, email_html

def send_email(to_email, subject, body_html, professor_name):
    """Send email with attachment"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add HTML body
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Add CV attachment
        cv_path = Path('resumes/CV_Anamay_Modern.pdf')
        if cv_path.exists():
            with open(cv_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="Anamay_Tripathy_CV.pdf"')
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
        
        print(f"✅ Sent to {professor_name} ({to_email})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send to {professor_name}: {e}")
        return False

def main():
    print("🚀 FREE AI-POWERED EMAIL CAMPAIGN")
    print("=" * 60)
    
    # Get password if not set
    global PASSWORD
    if not PASSWORD:
        PASSWORD = input("Enter Gmail app password: ").strip()
    
    # Get professors
    limit = int(input("How many emails to send? (default 10): ").strip() or "10")
    professors = get_european_professors(limit)
    
    print(f"\n📧 Sending {len(professors)} personalized emails...")
    print("-" * 60)
    
    sent = 0
    for name, email, affiliation, research_interest in professors:
        # Generate AI content
        research_area = research_interest if research_interest else "computational research"
        university = affiliation if affiliation else "your institution"
        
        print(f"\n🤖 Generating AI email for {name}...")
        subject, body = generate_ai_email(name, university, research_area)
        
        #Send email
        if send_email(email, subject, body, name):
            sent += 1
        
        # Rate limiting
        time.sleep(3)  # 3 seconds between emails
    
    print("\n" + "=" * 60)
    print(f"✅ Campaign complete! Sent {sent}/{len(professors)} emails")

if __name__ == "__main__":
    main()
