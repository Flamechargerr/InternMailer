import smtplib
from email.message import EmailMessage
import os

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

class EmailSender:
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = to_email
            msg.set_content(content)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.user, self.password)
                server.send_message(msg)
                print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

# Usage example
if __name__ == "__main__":
    sender = EmailSender(GMAIL_USER, GMAIL_APP_PASSWORD)
    sender.send_email('example@domain.com', 'Test Subject', 'This is a test email.')
