"""
Email Notification System for InternMailer
Sends daily reports and follow-up reminders to tripathy.anamay23@gmail.com
"""

import smtplib
import json
import logging
from datetime import datetime
from typing import Dict, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path
import tempfile

class EmailNotifier:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
        # Email configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('SENDER_EMAIL', 'internmailer.bot@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.recipient_email = "tripathy.anamay23@gmail.com"
        
    def _load_config(self, config_path: str) -> Dict:
        """Load email configuration"""
        try:
            import yaml
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.warning(f"Could not load config: {e}")
            return {}
    
    def send_daily_report(self, report_data: Dict) -> bool:
        """
        Send daily internship report email
        
        Args:
            report_data: Daily report in JSON format
            
        Returns:
            bool: Success status
        """
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"Daily Internship Update – Summer 2026 UG Roles ({report_data.get('date', datetime.now().date())})"
            
            # Generate HTML content
            html_content = self._generate_html_report(report_data)
            
            # Generate plain text content
            text_content = self._generate_text_report(report_data)
            
            # Attach both versions
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Attach JSON report
            json_attachment = self._create_json_attachment(report_data)
            msg.attach(json_attachment)
            
            # Send email
            return self._send_email(msg)
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return False
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML email content"""
        summary = report_data.get('summary', {})
        opportunities = report_data.get('opportunities_ranked', [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .tier-badge {{ padding: 3px 8px; border-radius: 3px; color: white; font-size: 12px; }}
                .tier1 {{ background-color: #e74c3c; }}
                .tier2 {{ background-color: #f39c12; }}
                .tier3 {{ background-color: #27ae60; }}
                .opportunity {{ border: 1px solid #bdc3c7; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .company {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
                .title {{ font-size: 16px; color: #34495e; margin: 5px 0; }}
                .details {{ color: #7f8c8d; font-size: 14px; }}
                .scores {{ margin: 10px 0; }}
                .score {{ display: inline-block; margin-right: 15px; }}
                .links {{ margin: 10px 0; }}
                .btn {{ background-color: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; }}
                .contact {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Daily Internship Update</h1>
                <p>Summer 2026 Undergraduate Roles | {report_data.get('date')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Daily Summary</h2>
                <p><strong>Total Opportunities Found:</strong> {summary.get('total_found', 0)}</p>
                <p><strong>Shortlisted:</strong> {summary.get('shortlisted', 0)}</p>
                <p><strong>Manual Review Required:</strong> {summary.get('manual_required', 0)}</p>
                
                <h3>🏆 By Prestige Tier</h3>
                <p>
                    <span class="tier-badge tier1">Tier 1: {summary.get('tiers', {}).get('Tier 1', 0)}</span>
                    <span class="tier-badge tier2">Tier 2: {summary.get('tiers', {}).get('Tier 2', 0)}</span>
                    <span class="tier-badge tier3">Tier 3: {summary.get('tiers', {}).get('Tier 3', 0)}</span>
                </p>
            </div>
        """
        
        if opportunities:
            html += "<h2>🎯 Top Ranked Opportunities</h2>"
            
            for i, opp in enumerate(opportunities[:10], 1):
                tier_class = opp.get('prestige_tier', 'Unknown').lower().replace(' ', '')
                
                html += f"""
                <div class="opportunity">
                    <div class="company">{i}. {opp.get('company', 'Unknown Company')}</div>
                    <div class="title">{opp.get('job_title', 'Unknown Position')}</div>
                    <div class="details">📍 {opp.get('location', 'Location TBD')}</div>
                    
                    <div class="scores">
                        <span class="score">🎯 Match: {opp.get('match_score', 0):.2f}</span>
                        <span class="score">⭐ Prestige: {opp.get('prestige_score', 0):.2f}</span>
                        <span class="tier-badge {tier_class}">{opp.get('prestige_tier', 'Unknown')}</span>
                    </div>
                """
                
                if opp.get('contact_email'):
                    html += f"""
                    <div class="contact">
                        📧 Contact: <a href="mailto:{opp.get('contact_email')}">{opp.get('contact_email')}</a>
                    </div>
                    """
                
                html += f"""
                    <div class="links">
                        <a href="{opp.get('apply_link', '#')}" class="btn">Apply Now</a>
                    </div>
                </div>
                """
        else:
            html += "<p>No new opportunities found today.</p>"
        
        html += f"""
            <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                <h3>📋 Next Steps</h3>
                <ol>
                    <li>Review the ranked opportunities above</li>
                    <li>Click "Apply Now" for positions of interest</li>
                    <li>Use provided contact emails for direct outreach</li>
                    <li>Tailored resumes and cover letters are attached</li>
                </ol>
                
                <p><em>This report was generated automatically by InternMailer on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_report(self, report_data: Dict) -> str:
        """Generate plain text email content"""
        summary = report_data.get('summary', {})
        opportunities = report_data.get('opportunities_ranked', [])
        
        text = f"""
DAILY INTERNSHIP UPDATE - Summer 2026 UG Roles
Date: {report_data.get('date')}

{'='*50}
DAILY SUMMARY
{'='*50}

Total Opportunities Found: {summary.get('total_found', 0)}
Shortlisted: {summary.get('shortlisted', 0)}
Manual Review Required: {summary.get('manual_required', 0)}

By Prestige Tier:
- Tier 1: {summary.get('tiers', {}).get('Tier 1', 0)}
- Tier 2: {summary.get('tiers', {}).get('Tier 2', 0)}
- Tier 3: {summary.get('tiers', {}).get('Tier 3', 0)}

"""
        
        if opportunities:
            text += f"""
{'='*50}
TOP RANKED OPPORTUNITIES
{'='*50}

"""
            
            for i, opp in enumerate(opportunities[:10], 1):
                text += f"""
{i}. {opp.get('company', 'Unknown Company')}
   Position: {opp.get('job_title', 'Unknown Position')}
   Location: {opp.get('location', 'Location TBD')}
   Match Score: {opp.get('match_score', 0):.2f}
   Prestige: {opp.get('prestige_tier', 'Unknown')} ({opp.get('prestige_score', 0):.2f})
   Apply: {opp.get('apply_link', 'Link not available')}
"""
                
                if opp.get('contact_email'):
                    text += f"   Contact: {opp.get('contact_email')}\n"
                
                text += "\n"
        else:
            text += "\nNo new opportunities found today.\n"
        
        text += f"""
{'='*50}
NEXT STEPS
{'='*50}

1. Review the ranked opportunities above
2. Click apply links for positions of interest
3. Use provided contact emails for direct outreach
4. Tailored resumes and cover letters are in the attached JSON

This report was generated automatically by InternMailer
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return text
    
    def _create_json_attachment(self, report_data: Dict) -> MIMEBase:
        """Create JSON attachment with full report data"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f, indent=2, default=str)
            temp_path = f.name
        
        # Create attachment
        with open(temp_path, 'rb') as f:
            attachment = MIMEBase('application', 'json')
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="internship_report_{report_data.get(\'date\', datetime.now().date())}.json"'
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return attachment
    
    def send_follow_up_reminders(self, reminders: List[Dict]) -> bool:
        """Send follow-up reminder email"""
        try:
            if not reminders:
                return True
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"📅 Follow-up Reminders - {len(reminders)} Action Items"
            
            # Generate content
            html_content = self._generate_follow_up_html(reminders)
            text_content = self._generate_follow_up_text(reminders)
            
            # Attach content
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            return self._send_email(msg)
            
        except Exception as e:
            self.logger.error(f"Error sending follow-up reminders: {e}")
            return False
    
    def _generate_follow_up_html(self, reminders: List[Dict]) -> str:
        """Generate HTML for follow-up reminders"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #e67e22; color: white; padding: 20px; border-radius: 5px; }}
                .reminder {{ border: 1px solid #bdc3c7; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .urgent {{ border-left: 5px solid #e74c3c; }}
                .company {{ font-size: 16px; font-weight: bold; color: #2c3e50; }}
                .action {{ color: #e67e22; font-weight: bold; }}
                .date {{ color: #7f8c8d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📅 Follow-up Reminders</h1>
                <p>{len(reminders)} action items require your attention</p>
            </div>
        """
        
        for reminder in reminders:
            html += f"""
            <div class="reminder urgent">
                <div class="company">{reminder.get('company', 'Unknown Company')}</div>
                <div>{reminder.get('job_title', 'Unknown Position')}</div>
                <div class="action">Action: {reminder.get('message', 'Follow up required')}</div>
                <div class="date">Due: {reminder.get('reminder_date', 'Today')}</div>
            </div>
            """
        
        html += """
            <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                <p><strong>💡 Tips:</strong></p>
                <ul>
                    <li>Keep follow-ups professional and concise</li>
                    <li>Reference your previous application</li>
                    <li>Express continued interest in the role</li>
                    <li>Ask for timeline updates</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_follow_up_text(self, reminders: List[Dict]) -> str:
        """Generate plain text for follow-up reminders"""
        text = f"""
FOLLOW-UP REMINDERS
{len(reminders)} action items require your attention

{'='*50}
"""
        
        for i, reminder in enumerate(reminders, 1):
            text += f"""
{i}. {reminder.get('company', 'Unknown Company')}
   Position: {reminder.get('job_title', 'Unknown Position')}
   Action: {reminder.get('message', 'Follow up required')}
   Due: {reminder.get('reminder_date', 'Today')}

"""
        
        text += """
TIPS:
- Keep follow-ups professional and concise
- Reference your previous application
- Express continued interest in the role
- Ask for timeline updates
"""
        
        return text
    
    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS
            
            # Login
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {self.recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = "🧪 InternMailer Test Email"
            
            body = """
            This is a test email from InternMailer.
            
            If you receive this, the email configuration is working correctly.
            
            System Status: ✅ Operational
            Timestamp: {}
            """
            
            msg.attach(MIMEText(body.format(datetime.now()), 'plain'))
            
            return self._send_email(msg)
            
        except Exception as e:
            self.logger.error(f"Error sending test email: {e}")
            return False
    
    def send_error_notification(self, error_details: Dict) -> bool:
        """Send error notification email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = "🚨 InternMailer Error Alert"
            
            body = f"""
            An error occurred in the InternMailer system:
            
            Error: {error_details.get('error', 'Unknown error')}
            Component: {error_details.get('component', 'Unknown')}
            Timestamp: {error_details.get('timestamp', datetime.now())}
            
            Details:
            {json.dumps(error_details, indent=2)}
            
            Please check the system logs for more information.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            return self._send_email(msg)
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False

if __name__ == "__main__":
    # Test the email notifier
    notifier = EmailNotifier()
    
    # Test daily report
    sample_report = {
        'date': datetime.now().date().isoformat(),
        'summary': {
            'total_found': 5,
            'shortlisted': 3,
            'auto_applied': 0,
            'manual_required': 3,
            'tiers': {'Tier 1': 1, 'Tier 2': 1, 'Tier 3': 1}
        },
        'opportunities_ranked': [
            {
                'job_title': 'Machine Learning Intern',
                'company': 'Google',
                'location': 'Mountain View, CA',
                'apply_link': 'https://careers.google.com/jobs/123',
                'contact_email': 'recruiter@google.com',
                'match_score': 0.95,
                'prestige_tier': 'Tier 1',
                'prestige_score': 1.0
            }
        ],
        'application_logs': [],
        'materials': []
    }
    
    print("Email notifier created successfully")
    print("Ready to send daily reports to tripathy.anamay23@gmail.com")