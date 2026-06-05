"""
Unit tests for email personalization and fallback functionality.
Tests Requirements 2.4 and 2.5.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from core.email_system import EmailSystem
from utils.profile import Profile


class TestEmailPersonalization:
    """Test email personalization with AI and fallback templates."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.DATABASE_PATH = self.db_path
        self.mock_config.CONTACTS_DB_PATH = ":memory:"
        self.mock_config.JOBS_DB_PATH = ":memory:"
        self.mock_config.EMAIL_STRICT_TEMPLATE = False
        self.mock_config.DEFAULT_ROLE_TITLE = "Software Engineering Intern"
        self.mock_config.AUTO_APPROVE_SENDS = True
        self.mock_config.EMAIL_ADDRESS = "test@example.com"
        self.mock_config.EMAIL_PASSWORD = "test_password_1234"
        self.mock_config.SMTP_SERVER = "smtp.gmail.com"
        self.mock_config.SMTP_PORT = 587
        self.mock_config.MAX_CONCURRENT_EMAILS = 5
        self.mock_config.RATE_LIMIT_DELAY = 0.1
        self.mock_config.MAX_EMAILS_PER_DAY = 100
        
        # Mock profile
        self.mock_profile = Mock(spec=Profile)
        self.mock_profile.get = Mock(side_effect=lambda key, default=None: {
            'name': 'Test User',
            'email': 'test@example.com',
            'title': 'Software Engineer',
            'location': 'Test City',
            'experience_highlights': ['Built scalable systems', 'Optimized database queries'],
            'project_highlights': ['Open source contributor', 'Hackathon winner'],
            'skills': ['Python', 'SQL', 'AWS', 'Docker']
        }.get(key, default))
        self.mock_profile.signature_html = Mock(return_value="Test User<br>Software Engineer")
        self.mock_profile.resume_paths = Mock(return_value=[])
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('core.email_system.SMTPConnectionPool')
    @patch.object(EmailSystem, '_validate_credentials', return_value=True)
    def test_uniqueness_seed_generation(self, mock_validate, mock_pool):
        """Test that uniqueness seeds are generated correctly for each recipient."""
        with patch('core.email_system.config', self.mock_config):
            with patch('core.email_system.get_profile', return_value=self.mock_profile):
                email_system = EmailSystem()
                
                # Generate emails for different recipients
                contacts = [
                    ("Alice", "alice@example.com", "CompanyA", "Software Engineer", ""),
                    ("Bob", "bob@example.com", "CompanyB", "Data Scientist", ""),
                    ("Charlie", "charlie@example.com", "CompanyC", "Product Manager", "")
                ]
                
                seeds = []
                for name, email, company, position, job_url in contacts:
                    _, _, metadata = email_system.generate_personalized_email(
                        contact_name=name,
                        email=email,
                        company=company,
                        position=position,
                        use_ai=False,  # Disable AI for consistent testing
                        job_url=job_url
                    )
                    seeds.append(metadata['uniqueness_seed'])
                
                # All seeds should be unique
                assert len(seeds) == len(set(seeds)), "Uniqueness seeds should be unique for different recipients"
                
                # Seeds should be deterministic
                for name, email, company, position, job_url in contacts:
                    _, _, metadata = email_system.generate_personalized_email(
                        contact_name=name,
                        email=email,
                        company=company,
                        position=position,
                        use_ai=False,
                        job_url=job_url
                    )
                    expected_seed = f"{name}_{email}_{company}_{position}_{job_url}"
                    assert metadata['uniqueness_seed'] == expected_seed, "Seeds should be deterministic"
    
    @patch('core.email_system.SMTPConnectionPool')
    @patch.object(EmailSystem, '_validate_credentials', return_value=True)
    def test_fallback_template_variation(self, mock_validate, mock_pool):
        """Test that fallback templates produce different content for different recipients."""
        with patch('core.email_system.config', self.mock_config):
            with patch('core.email_system.get_profile', return_value=self.mock_profile):
                email_system = EmailSystem()
                
                # Generate emails for different recipients
                contacts = [
                    ("Alice", "alice@example.com", "CompanyA", "Software Engineer", ""),
                    ("Bob", "bob@example.com", "CompanyB", "Data Scientist", ""),
                    ("Charlie", "charlie@example.com", "CompanyC", "Product Manager", ""),
                    ("Diana", "diana@example.com", "CompanyD", "DevOps Engineer", "")
                ]
                
                email_bodies = []
                for name, email, company, position, job_url in contacts:
                    _, body, metadata = email_system.generate_personalized_email(
                        contact_name=name,
                        email=email,
                        company=company,
                        position=position,
                        use_ai=False,  # Disable AI to test fallback templates
                        job_url=job_url
                    )
                    email_bodies.append(body)
                    assert metadata['fallback_used'] or metadata['provider'] in ['fallback_template', 'minimal_fallback', 'anti_template']
                
                # Check that emails have variation (not all identical)
                unique_bodies = set(email_bodies)
                assert len(unique_bodies) > 1, "Fallback templates should produce varied content"
    
    @patch('core.email_system.SMTPConnectionPool')
    @patch.object(EmailSystem, '_validate_credentials', return_value=True)
    def test_ai_personalization_with_fallback(self, mock_validate, mock_pool):
        """Test that AI personalization falls back gracefully when AI fails."""
        with patch('core.email_system.config', self.mock_config):
            with patch('core.email_system.get_profile', return_value=self.mock_profile):
                # Mock AI provider that fails
                mock_ai_provider = Mock()
                mock_ai_provider.generate_role_personalization = Mock(side_effect=Exception("AI service unavailable"))
                
                email_system = EmailSystem()
                email_system.ai_provider = mock_ai_provider
                
                # Generate email with AI enabled (should fall back to template)
                subject, body, metadata = email_system.generate_personalized_email(
                    contact_name="Alice",
                    email="alice@example.com",
                    company="CompanyA",
                    position="Software Engineer",
                    use_ai=True,
                    job_url=""
                )
                
                # Should have fallen back to template
                assert metadata['fallback_used'] == True, "Should use fallback when AI fails"
                assert metadata['ai_used'] == False, "AI should not be marked as used when it fails"
                assert subject is not None and len(subject) > 0, "Should generate valid subject"
                assert body is not None and len(body) > 0, "Should generate valid body"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
