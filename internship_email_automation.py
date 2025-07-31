import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import csv
from email.mime.base import MIMEBase
from email import encoders
import time

load_dotenv()

smtp_server = 'smtp.gmail.com'
smtp_port = 587
login_email = os.getenv('GMAIL_USER')
login_password = os.getenv('GMAIL_APP_PASSWORD')

cv_path = 'C:/Users/anama/OneDrive/Desktop/internmailing/resumes/CV_Anamay_Modern.pdf'

contacted_path = 'contacted_companies.csv'
contacted = set()
if os.path.exists(contacted_path):
    with open(contacted_path, 'r') as file:
        contacted = set(line.strip() for line in file)

with open('hr_contacts_from_spreadsheet.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    company_data = list(reader)

with open('enhanced_personalized_template.html', 'r', encoding='utf-8') as file:
    email_template = file.read()

def fill_template(template, name, title, company, location):
    specific_role = 'Software Development, Data Analysis'
    return template.format(
        Name=name,
        Job_Title=title,
        Company_Name=company,
        Location=location,
        Preferred_Role_Type=specific_role
    )

def send_personalized_email(email, content):
    message = MIMEMultipart()
    message['From'] = login_email
    message['To'] = email
    message['Subject'] = 'Summer Internship Inquiry'
    message.attach(MIMEText(content, 'html'))

    with open(cv_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= CV_Anamay_Modern.pdf')
    message.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(login_email, login_password)
            server.send_message(message)
        print(f'Email sent to {email}')
        return True
    except Exception as e:
        print(f'Failed to send email to {email}: {e}')
        return False

sent_count = 0
for contact in company_data:
    company_name = contact['Company Name']
    if company_name in contacted:
        continue

    email = contact['Linkedin URL']  # Assuming email as LinkedIn URL temporarily
    name = contact.get('Name', 'HR Team')
    title = contact.get('Job Title', 'HR Professional')
    location = contact.get('Location', 'Location')

    filled_content = fill_template(email_template, name, title, company_name, location)
    if send_personalized_email(email, filled_content):
        with open(contacted_path, 'a') as file:
            file.write(company_name + '\n')
        sent_count += 1

    if sent_count >= 50:
        break

    time.sleep(2)

print(f'{sent_count} emails successfully sent.')

