import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email_with_cv(professor_data, recipient_email):
    """Sends an email with the academic email template."""
    
    professor_name = professor_data.get("name", "Professor")
    research_area = professor_data.get("research_area", "Research")
    
    subject = f"Research Collaboration Inquiry - {research_area}"
    body = f"Dear {professor_name},\n\nI hope this message finds you well."
    
    # Simulated email sending logic
    print(f"Sending email to {recipient_email}...")
    print("Subject:", subject)
    print("Body:", body)

    # Use SMTP library to send the email (example placeholders below)
    # smtp_server = "smtp.example.com"
    # sender_email = "your_email@example.com"
    # password = "your_password"
    # 
    # msg = MIMEMultipart()
    # msg['From'] = sender_email
    # msg['To'] = recipient_email
    # msg['Subject'] = subject
    # msg.attach(MIMEText(body, 'plain'))
    
    # Notes: Actual implementation would involve authenticating with a real SMTP server.
    # server = smtplib.SMTP(smtp_server, 587)
    # server.starttls()
    # server.login(sender_email, password)
    # server.send_message(msg)
    # server.quit()

    print("Email sent!")

