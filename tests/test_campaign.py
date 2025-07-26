"""Test email campaign system functionality"""
import pytest
import os
import sys
from unittest.mock import patch, Mock
import pandas as pd

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from email_campaign_system import EmailCampaignSystem
except ImportError:
    EmailCampaignSystem = None

class TestEmailCampaignSystem:
    """Test complete email campaign system functionality"""
    
    @pytest.fixture
    def temp_campaign_system(self, temp_csv_file):
        """Create a temporary EmailCampaignSystem for testing"""
        if EmailCampaignSystem is None:
            pytest.skip("EmailCampaignSystem not available")
        return EmailCampaignSystem(temp_csv_file)
    
    def test_campaign_initialization(self, temp_campaign_system):
        """Test proper initialization of email campaign system"""
        if EmailCampaignSystem is None:
            pytest.skip("EmailCampaignSystem not available")
        
        assert temp_campaign_system.csv_path
        assert os.path.exists(temp_campaign_system.csv_path)
        assert isinstance(temp_campaign_system.professors_df, pd.DataFrame)
        assert len(temp_campaign_system.professors_df) > 0
    
    @patch('email_campaign_system.EmailSender')
    @patch('email_campaign_system.TemplateManager')
    def test_load_and_validate_csv_data(self, MockTemplateManager, MockEmailSender, temp_csv_file):
        """Test loading and validating CSV data"""
        if EmailCampaignSystem is None:
            pytest.skip("EmailCampaignSystem not available")
        
        MockTemplateManager.return_value.setup_default_templates.return_value = None
        MockEmailSender.return_value.send_email.return_value = True  # Mock send_email
        
        campaign = EmailCampaignSystem(temp_csv_file)
        df = campaign.load_csv_data()
        
        assert len(df) == 3  # Should have 3 professors
        assert all(col in df.columns for col in ['Name', 'Email', 'University', 'Research Area'])
        assert pd.notna(df['Email']).all()  # No missing emails
        assert df['Email'].str.contains('@').all()  # All have valid format
    
    def test_create_personalized_context(self, temp_campaign_system, sample_student_info, sample_professor):
        """Test creating personalized email context"""
        context = temp_campaign_system.create_personalized_context(sample_professor, sample_student_info)
        
        assert isinstance(context, dict)
        assert 'professor_name' in context
        assert 'student_name' in context
        assert 'research_area' in context
        
        assert context['professor_name'] == sample_professor['Name'].split()[-1]  # Last name
        assert context['student_name'] == sample_student_info['name']
    
    @patch('email_campaign_system.EmailSender.send_email')
    def test_run_campaign_dry_run(self, mock_send_email, temp_campaign_system, sample_student_info):
        """Test running campaign in dry run mode"""
        if EmailCampaignSystem is None:
            pytest.skip("EmailCampaignSystem not available")
        
        mock_send_email.return_value = True  # Simulate successful email sending
        
        # Run campaign in dry run mode
        temp_campaign_system.run_campaign(sample_student_info, dry_run=True)
        
        assert mock_send_email.call_count == 0  # Emails are not actually sent in dry run mode
    
    @patch('email_campaign_system.EmailSender.send_email')
    def test_run_campaign_actual_sending(self, mock_send_email, temp_campaign_system, sample_student_info):
        """Test running campaign with actual sending"""
        if EmailCampaignSystem is None:
            pytest.skip("EmailCampaignSystem not available")
        
        mock_send_email.return_value = True  # Simulate successful email sending
        
        # Run campaign with actual sending
        max_emails = 2
        temp_campaign_system.run_campaign(sample_student_info, dry_run=False, max_emails=max_emails)
        
        assert mock_send_email.call_count == max_emails  # Should send exactly 2 emails
    
    def test_logging_setup(self, temp_campaign_system):
        """Test setup of logging for campaign tracking"""
        import logging
        
        assert hasattr(temp_campaign_system, 'logger')
        logger = temp_campaign_system.logger
        
        assert logger.level == logging.INFO
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
