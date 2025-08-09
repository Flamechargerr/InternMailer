#!/usr/bin/env python3
"""
Comprehensive Test Email Sender
Sends test emails for both HR contacts and professors with proper HTML formatting
"""

import smtplib
import os
import csv
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import time

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "tripathy.anamay23@gmail.com"
EMAIL_PASS = "qzxw bjqs wgqk wqtt"

class TestEmailSender:
    def __init__(self):
        self.setup_logging()
        self.load_data()
    
    def setup_logging(self):
        """Setup logging for the email sender"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_email_sender.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_data(self):
        """Load HR contacts and professor data"""
        # Load HR contacts
        self.hr_contacts = []
        try:
            with open('hr_contacts_cleaned.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Name') and row.get('Company Name'):
                        self.hr_contacts.append(row)
            self.logger.info(f"Loaded {len(self.hr_contacts)} HR contacts")
        except Exception as e:
            self.logger.error(f"Error loading HR contacts: {e}")
            self.hr_contacts = []
        
        # Load professor data
        self.professors = []
        try:
            with open('professors_unified_scraped.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('name') and row.get('email'):
                        self.professors.append(row)
            self.logger.info(f"Loaded {len(self.professors)} professors")
        except Exception as e:
            self.logger.error(f"Error loading professors: {e}")
            self.professors = []
    
    def create_hr_email_html(self, hr_contact):
        """Create HTML email for HR contact using professional business template"""
        name = hr_contact.get('Name', '')
        job_title = hr_contact.get('Job Title', '')
        company_name = hr_contact.get('Company Name', '')
        company_niche = hr_contact.get('Company Niche', 'Information Technology & Services')
        location = hr_contact.get('Location', 'Mumbai, India')
        
        # Generate email from LinkedIn URL if available
        linkedin_url = hr_contact.get('Linkedin URL', '')
        email = self.generate_email_from_linkedin(linkedin_url, company_name)
        
        # Professional HR email template with company personalization
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Internship Opportunity - {company_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.5;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 400;
        }}
        .content {{
            padding: 25px;
        }}
        .greeting {{
            font-size: 16px;
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .paragraph {{
            margin-bottom: 15px;
            text-align: justify;
            font-size: 14px;
        }}
        .highlight {{
            background-color: #f8f9fa;
            border-left: 4px solid #2c3e50;
            padding: 12px;
            margin: 15px 0;
        }}
        .signature {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }}
        .contact-info {{
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 5px;
            margin-top: 15px;
            font-size: 13px;
        }}
        .contact-info p {{
            margin: 3px 0;
        }}
        .linkedin-link {{
            color: #0077b5;
            text-decoration: none;
            font-weight: bold;
        }}
        .linkedin-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 15px;
            text-align: center;
            font-size: 11px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>📧 Internship Opportunity</h1>
        </div>
        
        <div class="content">
            <div class="greeting">
                Dear <strong>{name}</strong>,
            </div>
            
            <div class="paragraph">
                I hope this email finds you well. My name is Anamay Tripathy, and I'm reaching out regarding internship opportunities at <strong>{company_name}</strong> for Winter 2025 or Summer 2026.
            </div>
            
            <div class="paragraph">
                I've been following {company_name}'s innovative work in the {company_niche} sector and am particularly impressed by your company's approach to solving industry challenges. {company_name}'s commitment to excellence and dynamic work environment makes it an ideal place where I believe I can contribute meaningfully while gaining invaluable industry experience.
            </div>
            
            <div class="highlight">
                <strong>Why I'm Excited About {company_name}:</strong><br>
                • <strong>Innovation Focus:</strong> {company_name}'s cutting-edge approach to {company_niche} aligns perfectly with my passion for building scalable solutions<br>
                • <strong>Growth Culture:</strong> Your company's dynamic environment and commitment to employee development matches my career aspirations<br>
                • <strong>Industry Impact:</strong> {company_name}'s work in {company_niche} has the potential to transform how businesses operate, which excites me greatly
            </div>
            
            <div class="paragraph">
                My background in technical leadership and proven track record of delivering results (including a 22% improvement in user engagement during my previous internship) positions me well to contribute to {company_name}'s continued success. I believe my fresh perspective, technical skills, and passion for innovation would add immediate value to your team.
            </div>
            
            <div class="paragraph">
                I would be honored to discuss how my technical expertise and enthusiasm for {company_name}'s mission can contribute to your company's growth. I'm available for a call at your convenience and would welcome the opportunity to learn more about potential internship opportunities.
            </div>
            
            <div class="signature">
                <strong>Best regards,</strong><br>
                <strong>Anamay Tripathy</strong><br>
                B.Tech Data Science | MIT Manipal, India<br>
                <a href="https://www.linkedin.com/in/anamay-tripathy" class="linkedin-link">LinkedIn Profile</a>
            </div>
            
            <div class="contact-info">
                <p><strong>📧 Email:</strong> tripathy.anamay23@gmail.com</p>
                <p><strong>📱 Phone:</strong> +91-9877454747</p>
                <p><strong>📍 Location:</strong> Mumbai, India (Willing to relocate)</p>
                <p><strong>📋 CV:</strong> Attached for your review</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Thank you for your time and consideration. I look forward to the possibility of contributing to {company_name}'s success.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content, email
    
    def create_professor_email_html(self, professor):
        """Create HTML email for professor using personalized research template"""
        name = professor.get('name', '')
        university = professor.get('affiliation', '')
        research_area = professor.get('research_area', 'computer vision')
        email = professor.get('email', '')
        
        # Load the academic research template
        try:
            with open('templates/academic_research_template.html', 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Replace template variables with professor-specific content
            html_content = template.replace('{{ professor.last_name }}', name)
            html_content = html_content.replace('{{ professor.research_area }}', research_area)
            html_content = html_content.replace('{{ professor.research_area.lower() }}', research_area.lower())
            
            # Add personalized research interest content
            research_interest_paragraph = f"""
            <p style="margin: 0 0 20px 0; font-size: 16px; color: #000000; text-align: justify;">
                I am particularly fascinated by your work in {research_area.lower()}, especially how it intersects with artificial intelligence and real-world applications. Your research on {research_area.lower()} and its potential to revolutionize how we approach complex computational problems has been incredibly inspiring to my academic journey.
            </p>
            
            <p style="margin: 0 0 20px 0; font-size: 16px; color: #000000; text-align: justify;">
                What particularly draws me to your lab is your innovative approach to {research_area.lower()} and how you're pushing the boundaries of what's possible in this field. I believe my background in machine learning and computer vision, combined with my passion for solving complex problems, would allow me to contribute meaningfully to your ongoing research while learning from your expertise.
            </p>
            """
            
            # Replace the research interests section with more focused content
            html_content = html_content.replace(
                '<h2 style="margin: 0 0 20px 0; font-size: 16px; font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 5px;">\n                Research Interests and Alignment\n            </h2>',
                '<h2 style="margin: 0 0 20px 0; font-size: 16px; font-weight: bold; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 5px;">\n                Why I\'m Excited About Your Research\n            </h2>'
            )
            
            # Add the personalized research interest content
            html_content = html_content.replace(
                '<p style="margin: 0 0 20px 0; font-size: 16px; color: #000000; text-align: justify;">\n                I am particularly fascinated by the intersection of <strong>{{ professor.research_area.lower() }}</strong> and artificial intelligence applications, especially in the context of scalable computing systems and distributed algorithm optimization. My academic coursework and practical experience in machine learning, combined with hands-on experience in building distributed systems, has prepared me to contribute meaningfully to research in these areas.\n            </p>',
                research_interest_paragraph
            )
            
        except FileNotFoundError:
            self.logger.error("Academic research template not found, using fallback")
            # Fallback to improved basic template
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Research Internship Inquiry - {research_area.title()} at {university}</title>
                <style>
                    body {{
                        font-family: 'Georgia', 'Times New Roman', serif;
                        line-height: 1.7;
                        color: #2c3e50;
                        max-width: 650px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .email-container {{
                        background-color: #ffffff;
                        border-radius: 10px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        overflow: hidden;
                        border: 1px solid #e9ecef;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                        color: white;
                        padding: 35px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 26px;
                        font-weight: 400;
                        font-family: 'Georgia', serif;
                    }}
                    .header .subtitle {{
                        margin-top: 10px;
                        font-size: 16px;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 35px;
                    }}
                    .greeting {{
                        font-size: 18px;
                        margin-bottom: 25px;
                        color: #2c3e50;
                        font-weight: 500;
                    }}
                    .paragraph {{
                        margin-bottom: 22px;
                        text-align: justify;
                        font-size: 16px;
                    }}
                    .research-highlight {{
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                        border-left: 5px solid #2c3e50;
                        padding: 20px;
                        margin: 25px 0;
                        border-radius: 0 5px 5px 0;
                    }}
                    .research-highlight h3 {{
                        margin: 0 0 15px 0;
                        color: #2c3e50;
                        font-size: 18px;
                    }}
                    .research-highlight p {{
                        margin: 0;
                        font-style: italic;
                    }}
                    .signature {{
                        margin-top: 35px;
                        padding-top: 25px;
                        border-top: 2px solid #e9ecef;
                    }}
                    .contact-info {{
                        background-color: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        margin-top: 25px;
                        border: 1px solid #e9ecef;
                    }}
                    .contact-info h4 {{
                        margin: 0 0 15px 0;
                        color: #2c3e50;
                        font-size: 16px;
                    }}
                    .contact-info p {{
                        margin: 8px 0;
                        font-size: 14px;
                    }}
                    .linkedin-link {{
                        color: #0077b5;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                    .linkedin-link:hover {{
                        text-decoration: underline;
                    }}
                    .github-link {{
                        color: #333;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                    .github-link:hover {{
                        text-decoration: underline;
                    }}
                    .footer {{
                        background-color: #2c3e50;
                        color: white;
                        padding: 25px;
                        text-align: center;
                        font-size: 13px;
                    }}
                    .footer p {{
                        margin: 5px 0;
                        opacity: 0.9;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🔬 Research Internship Inquiry</h1>
                        <div class="subtitle">{research_area.title()} Research • {university}</div>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">
                            Dear <strong>Dr. {name}</strong>,
                        </div>
                        
                        <div class="paragraph">
                            I hope this email finds you well. My name is Anamay Tripathy, and I'm reaching out to express my strong interest in pursuing a research internship in your {research_area} lab at {university} for the upcoming academic term.
                        </div>
                        
                        <div class="paragraph">
                            I've been following your groundbreaking work in {research_area}, particularly your innovative approaches to solving complex computational challenges. Your research has been incredibly inspiring to my academic journey, and I'm excited about the possibility of contributing to your lab's ongoing work.
                        </div>
                        
                        <div class="research-highlight">
                            <h3>🎯 Why I'm Excited About Your Research</h3>
                            <p>Your work on {research_area} and its applications in artificial intelligence directly aligns with my research interests. I'm particularly fascinated by how your techniques could be adapted for real-world applications and edge computing scenarios. The potential impact of your research on advancing the field is what draws me most to your lab.</p>
                        </div>
                        
                        <div class="paragraph">
                            Currently, I'm working on a government-incubated startup project where I lead technical initiatives involving machine learning and computer vision. This experience has given me hands-on experience with PyTorch, TensorFlow, and various ML libraries, which I believe would be valuable to your research team.
                        </div>
                        
                        <div class="paragraph">
                            I would be honored to contribute to your research while learning from your expertise. I'm particularly excited about the opportunity to work on cutting-edge {research_area} problems and contribute to publications that could advance the field.
                        </div>
                        
                        <div class="paragraph">
                            I would greatly appreciate the opportunity to discuss potential research opportunities in your lab. I'm available for a video call at your convenience and would be happy to share more details about my technical background and research interests.
                        </div>
                        
                        <div class="signature">
                            <strong>Best regards,</strong><br>
                            <strong>Anamay Tripathy</strong><br>
                            Computer Science Student<br>
                            <a href="https://www.linkedin.com/in/anamay-tripathy" class="linkedin-link">LinkedIn Profile</a> • 
                            <a href="https://github.com/anamay-tripathy" class="github-link">GitHub</a>
                        </div>
                        
                        <div class="contact-info">
                            <h4>📧 Contact Information</h4>
                            <p><strong>Email:</strong> tripathy.anamay23@gmail.com</p>
                            <p><strong>Phone:</strong> +91-9877454747</p>
                            <p><strong>University:</strong> MIT Manipal, India</p>
                            <p><strong>Location:</strong> Mumbai, India (Willing to relocate for internship)</p>
                            <p><strong>Available:</strong> Winter 2025 / Summer 2026</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>This email was sent from a professional academic email system.</p>
                        <p>Please feel free to reply directly to this email or schedule a meeting.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return html_content, email
    
    def generate_email_from_linkedin(self, linkedin_url, company_name):
        """Generate email from LinkedIn URL and company name"""
        if not company_name:
            return None
        
        # Clean company name
        company_lower = company_name.lower().strip()
        
        # Remove common suffixes
        suffixes = [' inc', ' inc.', ' corp', ' corp.', ' ltd', ' ltd.', 
                   ' llc', ' llc.', ' co', ' co.', ' company', ' technologies', 
                   ' tech', ' systems', ' solutions', ' services', ' software']
        for suffix in suffixes:
            if company_lower.endswith(suffix):
                company_lower = company_lower[:-len(suffix)].strip()
        
        # Generate domain from clean name
        domain_candidate = ''.join(c for c in company_lower if c.isalnum())
        if domain_candidate:
            return f"hr@{domain_candidate}.com"
        return None
    
    def send_email(self, to_email, subject, html_content, attachment_path=None):
        """Send email with HTML content"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= CV_Anamay_Modern.pdf'
                    )
                    msg.attach(part)
                self.logger.info("📎 CV attachment added")
            
            # Send email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            text = msg.as_string()
            server.sendmail(EMAIL_USER, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_hr_test_email(self, test_email="tripathy.anamay23@gmail.com"):
        """Send test HR email"""
        if not self.hr_contacts:
            self.logger.error("No HR contacts loaded")
            return False
        
        # Use first HR contact for test
        hr_contact = self.hr_contacts[0]
        html_content, generated_email = self.create_hr_email_html(hr_contact)
        
        subject = f"Winter 2025 / Summer 2026 Internship Inquiry - {hr_contact.get('Company Name', 'Test Company')}"
        
        # Send to test email
        success = self.send_email(test_email, subject, html_content, "resumes/CV_Anamay_Modern.pdf")
        
        if success:
            self.logger.info(f"✅ HR test email sent successfully to {test_email}")
            self.logger.info(f"📧 Subject: {subject}")
            self.logger.info(f"👤 HR Contact: {hr_contact.get('Name', 'N/A')}")
            self.logger.info(f"🏢 Company: {hr_contact.get('Company Name', 'N/A')}")
        else:
            self.logger.error("❌ Failed to send HR test email")
        
        return success
    
    def send_professor_test_email(self, test_email="tripathy.anamay23@gmail.com"):
        """Send test professor email"""
        if not self.professors:
            self.logger.error("No professors loaded")
            return False
        
        # Use first professor for test
        professor = self.professors[0]
        html_content, professor_email = self.create_professor_email_html(professor)
        
        subject = f"Research Internship Inquiry - Computer Vision at {professor.get('affiliation', 'Test University')}"
        
        # Send to test email
        success = self.send_email(test_email, subject, html_content, "resumes/CV_Anamay_Modern.pdf")
        
        if success:
            self.logger.info(f"✅ Professor test email sent successfully to {test_email}")
            self.logger.info(f"📧 Subject: {subject}")
            self.logger.info(f"👨‍🏫 Professor: {professor.get('name', 'N/A')}")
            self.logger.info(f"🏫 University: {professor.get('affiliation', 'N/A')}")
        else:
            self.logger.error("❌ Failed to send professor test email")
        
        return success
    
    def send_combined_template_test_email(self, test_email="tripathy.anamay23@gmail.com"):
        """Send a single email containing both HR and professor templates for debugging"""
        try:
            if not self.hr_contacts or not self.professors:
                self.logger.error("❌ No sample data available")
                return False
            
            # Get sample data
            hr_contact = self.hr_contacts[0]
            professor = self.professors[0]
            
            # Create both HTML templates
            hr_html, _ = self.create_hr_email_html(hr_contact)
            professor_html, _ = self.create_professor_email_html(professor)
            
            # Create combined HTML content
            combined_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Template Debug Test - HR + Professor Templates</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .template-section {{ margin-bottom: 40px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .template-title {{ font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px; padding: 10px; background: #007bff; color: white; border-radius: 4px; }}
                    .divider {{ height: 2px; background: linear-gradient(90deg, #007bff, #28a745); margin: 30px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 style="text-align: center; color: #333; margin-bottom: 30px;">🔍 Template Debug Test</h1>
                    <p style="text-align: center; color: #666; margin-bottom: 30px;">This email contains both HR and Professor templates for debugging purposes.</p>
                    
                    <div class="template-section">
                        <div class="template-title">📧 HR Email Template</div>
                        {hr_html}
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div class="template-section">
                        <div class="template-title">🔬 Professor Email Template</div>
                        {professor_html}
                    </div>
                    
                    <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff;">
                        <h3>📋 Debug Information</h3>
                        <p><strong>Test Purpose:</strong> Verify that both templates render correctly in a single email</p>
                        <p><strong>HR Sample Data:</strong> {hr_contact.get('Name', 'N/A')} at {hr_contact.get('Company Name', 'N/A')}</p>
                        <p><strong>Professor Sample Data:</strong> {professor.get('name', 'N/A')} at {professor.get('affiliation', 'N/A')}</p>
                        <p><strong>Sent:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create email message
            subject = "🔍 Template Debug Test - HR + Professor Templates"
            success = self.send_email(test_email, subject, combined_html, "resumes/CV_Anamay_Modern.pdf")
            
            if success:
                self.logger.info(f"✅ Combined template test email sent successfully to {test_email}")
                self.logger.info("📧 Email contains both HR and Professor templates for debugging")
                self.logger.info(f"👤 HR Sample: {hr_contact.get('Name', 'N/A')} at {hr_contact.get('Company Name', 'N/A')}")
                self.logger.info(f"👨‍🏫 Professor Sample: {professor.get('name', 'N/A')} at {professor.get('affiliation', 'N/A')}")
            else:
                self.logger.error("❌ Failed to send combined template test email")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error in combined template test: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive test of both email types"""
        self.logger.info("🚀 Starting comprehensive email test...")
        
        # Test HR email
        self.logger.info("\n" + "="*50)
        self.logger.info("📧 Testing HR Email System")
        self.logger.info("="*50)
        hr_success = self.send_hr_test_email()
        
        # Wait between emails
        time.sleep(2)
        
        # Test professor email
        self.logger.info("\n" + "="*50)
        self.logger.info("🔬 Testing Professor Email System")
        self.logger.info("="*50)
        professor_success = self.send_professor_test_email()
        
        # Summary
        self.logger.info("\n" + "="*50)
        self.logger.info("📊 Test Results Summary")
        self.logger.info("="*50)
        self.logger.info(f"HR Email: {'✅ SUCCESS' if hr_success else '❌ FAILED'}")
        self.logger.info(f"Professor Email: {'✅ SUCCESS' if professor_success else '❌ FAILED'}")
        
        if hr_success and professor_success:
            self.logger.info("🎉 All tests passed! Check your email for the test messages.")
        else:
            self.logger.error("⚠️ Some tests failed. Check the logs for details.")

def main():
    """Main function to run the test email sender"""
    sender = TestEmailSender()
    
    # Send combined template debug test email
    print("🔍 Sending combined template debug test email...")
    success = sender.send_combined_template_test_email()
    
    if success:
        print("✅ Combined template test email sent successfully!")
        print("📧 Check your email at tripathy.anamay23@gmail.com")
        print("🔍 This will help diagnose template rendering issues")
    else:
        print("❌ Failed to send combined template test email")

if __name__ == "__main__":
    main() 