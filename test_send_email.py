import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment variables
load_dotenv()

# Configuration for test email
def send_test_email():
    message = Mail(
        from_email=os.getenv('SENDGRID_FROM_EMAIL'),
        to_emails='tripathy.anamay23@gmail.com',
        subject='Test Email for Internship Inquiry',
        html_content='<strong>This is a test email sent for verification before mass emailing.</strong>'
    )
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"Test Email sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending test email: {e}")

send_test_email()
