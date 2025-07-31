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


# Function to send a dry-run email

def send_dry_run_email(recipient_email="tripathy.anamay23@gmail.com"):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = "[DRY RUN] Internship Inquiry Email Test"

    # Corporate internship email content
    body = """
    Dear Hiring Manager,

    I hope this message finds you well. My name is Anamay Tripathy, a Data Science & Engineering student at Manipal Institute of Technology.

    I am reaching out to explore potential internship opportunities where I can apply my skills in Machine Learning, Data Analysis, and AI-driven systems.

    A brief overview of my qualifications:
    - Led the AI-driven system architecture at YaanBarpe.
    - Developed ML pipelines at Intellect Design Arena, enhancing user engagement by 22%.
    - Created VARtificial Intelligence, achieving 89% accuracy in predictions.
    - Proficient in Python, Docker, AWS, and more.

    I am eager to contribute to innovative work and support your team with my expertise. You can find more details on my portfolio (https://anamay.vercel.app) and GitHub (https://github.com/Flamechargerr).

    Thank you for considering my application.

    Best regards,

    Anamay Tripathy
    Email: tripathy.anamay23@gmail.com | Phone: +91-9877454747
    """
    msg.attach(MIMEText(body, 'plain'))

    # Attach CV
    filename = r"C:\Users\anama\OneDrive\Desktop\internmailing\Anamay_Tripathy_CV.txt"
    attachment = open(filename, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= " + filename)

    msg.attach(part)

    # Send the mail
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, recipient_email, text)
        server.quit()
        print(f"[SUCCESS] Test email sent to {recipient_email}.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")


if __name__ == "__main__":
    send_dry_run_email()
