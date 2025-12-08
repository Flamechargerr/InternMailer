"""
Unit tests for EmailNotifier module
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_notifier import EmailNotifier
from datetime import datetime

class TestEmailNotifier(unittest.TestCase):
    def setUp(self):
        self.notifier = EmailNotifier()
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        sample_data = {
            'date': '2024-12-04',
            'summary': {
                'total_found': 5,
                'shortlisted': 3,
                'manual_required': 3,
                'tiers': {'Tier 1': 1, 'Tier 2': 1, 'Tier 3': 1}
            },
            'opportunities_ranked': [
                {
                    'company': 'Google',
                    'job_title': 'ML Intern',
                    'location': 'Mountain View, CA',
                    'match_score': 0.95,
                    'prestige_tier': 'Tier 1',
                    'prestige_score': 1.0,
                    'apply_link': 'https://careers.google.com/jobs/123',
                    'contact_email': 'recruiter@google.com'
                }
            ]
        }
        
        html = self.notifier._generate_html_report(sample_data)
        
        # Check that HTML contains expected elements
        self.assertIn('Daily Internship Update', html)
        self.assertIn('Google', html)
        self.assertIn('ML Intern', html)
        self.assertIn('Mountain View, CA', html)
        self.assertIn('0.95', html)
        self.assertIn('Tier 1', html)
        self.assertIn('recruiter@google.com', html)
    
    def test_generate_text_report(self):
        """Test plain text report generation"""
        sample_data = {
            'date': '2024-12-04',
            'summary': {
                'total_found': 5,
                'shortlisted': 3,
                'manual_required': 3,
                'tiers': {'Tier 1': 1, 'Tier 2': 1, 'Tier 3': 1}
            },
            'opportunities_ranked': [
                {
                    'company': 'Google',
                    'job_title': 'ML Intern',
                    'location': 'Mountain View, CA',
                    'match_score': 0.95,
                    'prestige_tier': 'Tier 1',
                    'prestige_score': 1.0,
                    'apply_link': 'https://careers.google.com/jobs/123'
                }
            ]
        }
        
        text = self.notifier._generate_text_report(sample_data)
        
        # Check that text contains expected elements
        self.assertIn('DAILY INTERNSHIP UPDATE', text)
        self.assertIn('Google', text)
        self.assertIn('ML Intern', text)
        self.assertIn('Mountain View, CA', text)
        self.assertIn('0.95', text)
        self.assertIn('Tier 1', text)
    
    def test_generate_follow_up_html(self):
        """Test follow-up HTML generation"""
        reminders = [
            {
                'company': 'Google',
                'job_title': 'ML Intern',
                'message': 'Send follow-up email',
                'reminder_date': '2024-12-04'
            }
        ]
        
        html = self.notifier._generate_follow_up_html(reminders)
        
        self.assertIn('Follow-up Reminders', html)
        self.assertIn('Google', html)
        self.assertIn('ML Intern', html)
        self.assertIn('Send follow-up email', html)
    
    def test_generate_follow_up_text(self):
        """Test follow-up text generation"""
        reminders = [
            {
                'company': 'Google',
                'job_title': 'ML Intern',
                'message': 'Send follow-up email',
                'reminder_date': '2024-12-04'
            }
        ]
        
        text = self.notifier._generate_follow_up_text(reminders)
        
        self.assertIn('FOLLOW-UP REMINDERS', text)
        self.assertIn('Google', text)
        self.assertIn('ML Intern', text)
        self.assertIn('Send follow-up email', text)
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Create a simple message
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart()
        msg['From'] = 'test@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Email'
        msg.attach(MIMEText('Test message', 'plain'))
        
        # Test sending
        result = self.notifier._send_email(msg)
        
        # Verify SMTP calls
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
        
        self.assertTrue(result)
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure"""
        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception('SMTP Error')
        
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        
        result = self.notifier._send_email(msg)
        self.assertFalse(result)
    
    def test_create_json_attachment(self):
        """Test JSON attachment creation"""
        sample_data = {
            'date': '2024-12-04',
            'summary': {'total_found': 5}
        }
        
        attachment = self.notifier._create_json_attachment(sample_data)
        
        # Check that attachment was created
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.get_content_type(), 'application/json')
    
    @patch.object(EmailNotifier, '_send_email')
    def test_send_daily_report(self, mock_send):
        """Test daily report sending"""
        mock_send.return_value = True
        
        sample_data = {
            'date': '2024-12-04',
            'summary': {'total_found': 5},
            'opportunities_ranked': [],
            'application_logs': [],
            'materials': []
        }
        
        result = self.notifier.send_daily_report(sample_data)
        
        self.assertTrue(result)
        mock_send.assert_called_once()
    
    @patch.object(EmailNotifier, '_send_email')
    def test_send_follow_up_reminders(self, mock_send):
        """Test follow-up reminders sending"""
        mock_send.return_value = True
        
        reminders = [
            {
                'company': 'Google',
                'job_title': 'ML Intern',
                'message': 'Follow up required',
                'reminder_date': '2024-12-04'
            }
        ]
        
        result = self.notifier.send_follow_up_reminders(reminders)
        
        self.assertTrue(result)
        mock_send.assert_called_once()
    
    def test_send_follow_up_reminders_empty(self):
        """Test sending empty follow-up reminders"""
        result = self.notifier.send_follow_up_reminders([])
        self.assertTrue(result)  # Should return True for empty list

if __name__ == '__main__':
    unittest.main()