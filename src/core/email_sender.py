"""SMTP email sender with pooling."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

class EmailSender:
    def __init__(self, host="smtp.gmail.com", port=587, user="", password=""):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.pool = []
    
    def send(self, to: str, subject: str, body: str, html: str = None) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = to
        msg.attach(MIMEText(body, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, [to], msg.as_string())
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def send_batch(self, recipients: List[str], subject: str, body: str) -> List[bool]:
        return [self.send(r, subject, body) for r in recipients]
