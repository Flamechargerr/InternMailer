"""Quick demo - sends 2 test emails to inbox"""
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

EMAIL = 'tripathy.anamay23@gmail.com'
PASSWORD = 'xctf elgn llfo aohf'

# Get 2 European professors
conn = sqlite3.connect('data/clean_40k_professors.db')
cursor = conn.cursor()
cursor.execute("SELECT name, email, affiliation FROM verified_contacts WHERE affiliation LIKE '%Imperial%' OR affiliation LIKE '%Cambridge%' LIMIT 2")
profs = cursor.fetchall()
conn.close()

for i, (name, prof_email, affiliation) in enumerate(profs, 1):
    # Sample enhanced email
    email_html = f"""<p>Dear Professor {name},</p>

<p>I am writing to express my strong interest in joining your research group at {affiliation}. I have been following your work with great enthusiasm, particularly your recent research in computer systems and distributed computing. Your innovative approaches to addressing fundamental challenges in scalable systems design have inspired me, and I believe your methodologies could significantly advance the field of data-driven computational research.</p>

<p>What particularly draws me to your work is the potential for applying machine learning techniques to optimize system performance and resource allocation. My experience leading ML-based projects at YaanBarpe, where we achieved a 34% efficiency improvement in waste management systems through predictive modeling, has given me practical insights into deploying ML at scale. Similarly, my work at Intellect Design Arena optimizing financial transaction processing for 2.3M+ daily transactions has prepared me to contribute meaningfully to research involving high-throughput distributed systems. I believe my background in both theoretical ML and production-scale deployment could bring a unique perspective to exploring how AI-driven optimization can enhance system efficiency in your research domain.</p>

<p>My technical background includes:</p>

<ul>
    <li><strong>Research Leadership:</strong> Technical Head at YaanBarpe, leading ML-powered waste management (34% efficiency improvement)</li>
    <li><strong>Industry Experience:</strong> Optimized financial data processing at Intellect Design Arena (2.3M+ transactions/day, 67% faster)</li>
    <li><strong>Skills:</strong> Python, PyTorch, TensorFlow, SQL, distributed systems, ML pipelines</li>
</ul>

<p>I am eager to contribute to your research. I have attached my CV for your review.</p>

<p>Thank you for considering my application.</p>

<p>Sincerely,<br><br>
<strong>Anamay Tripathy</strong><br>
B.Tech Data Science Engineering<br>
MIT Manipal, India<br>
<a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a><br>
<a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
+91-9877454747</p>
"""
    
    # Send
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL
    msg['To'] = EMAIL  # Send to your inbox
    msg['Subject'] = f"Research Inquiry - Computer Systems Research ({affiliation})"
    
    html_part = MIMEText(email_html, 'html', 'utf-8')
    msg.attach(html_part)
    
    cv_path = Path('resumes/CV_Anamay_Modern.pdf')
    if cv_path.exists():
        with open(cv_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="Anamay_Tripathy_CV.pdf"')
        msg.attach(part)
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    server.quit()
    
    print(f"✅ Demo email {i} sent - Professor {name} ({affiliation})")

print("\n🎉 Both demo emails sent to your inbox!")
print("Check tripathy.anamay23@gmail.com")
