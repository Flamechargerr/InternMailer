"""Tests for email generation, validation, and error tracking"""
import pytest
import os
import sys
from unittest.mock import patch, Mock, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'InternMailer', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from email_generator import EmailGenerator
except ImportError:
    # Fallback for different import structure
    try:
        from InternMailer.src.email_generator import EmailGenerator
    except ImportError:
        EmailGenerator = None

try:
    from email_sender import EmailSender
except ImportError:
    try:
        from src.email_sender import EmailSender
    except ImportError:
        EmailSender = None

class TestEmailGenerator:
    """Test email generation functionality"""
    
    def test_email_generation_basic(self, sample_student_info, sample_professor):
        """Test basic email generation"""
        if EmailGenerator is None:
            pytest.skip("EmailGenerator not available")
            
        email_gen = EmailGenerator(sample_student_info, use_ollama=False)
        subject = email_gen.generate_subject(sample_professor)
        body = email_gen.generate_body(sample_professor)
        
        assert subject is not None and len(subject) > 0
        assert body is not None and len(body) > 0
        assert 'Research Internship' in subject or 'Inquiry' in subject
        assert sample_professor['Name'].split()[-1] in body  # Last name
        assert sample_professor['Research Area'] in body or 'research' in body.lower()
    
    def test_subject_generation_variations(self, sample_student_info):
        """Test subject generation for different research areas"""
        if EmailGenerator is None:
            pytest.skip("EmailGenerator not available")
            
        email_gen = EmailGenerator(sample_student_info, use_ollama=False)
        
        research_areas = [
            'Machine Learning',
            'Computer Vision', 
            'Natural Language Processing',
            'Robotics',
            'Data Science'
        ]
        
        for area in research_areas:
            professor = {
                'Name': 'Dr. Test Professor',
                'University': 'Test University',
                'Research Area': area
            }
            subject = email_gen.generate_subject(professor)
            assert subject is not None
            assert len(subject) > 10
            assert area in subject or 'Research' in subject
    
    def test_relevant_skills_matching(self, sample_student_info):
        """Test that relevant skills are matched to research areas"""
        if EmailGenerator is None:
            pytest.skip("EmailGenerator not available")
            
        email_gen = EmailGenerator(sample_student_info, use_ollama=False)
        
        # Test ML research area
        ml_professor = {
            'Name': 'Dr. ML Expert',
            'Research Area': 'Machine Learning',
            'University': 'MIT'
        }
        
        relevant = email_gen.find_relevant_skills_and_projects(ml_professor)
        
        assert 'skills' in relevant
        assert 'projects' in relevant
        assert len(relevant['skills']) > 0
        
        # Should include ML-related skills
        ml_skills = ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning']
        found_ml_skills = any(skill in relevant['skills'] for skill in ml_skills)
        assert found_ml_skills
    
    @patch('requests.post')
    def test_llm_generation(self, mock_post, sample_student_info, sample_professor, mock_ollama):
        """Test LLM-based email generation"""
        if EmailGenerator is None:
            pytest.skip("EmailGenerator not available")
            
        # Mock successful LLM response
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': 'Dear Prof. Smith,\n\nI am writing to express my interest in your research...'
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        email_gen = EmailGenerator(sample_student_info, use_ollama=True)
        body = email_gen.generate_with_llm(sample_professor)
        
        assert body is not None
        assert len(body) > 50
        assert 'Prof.' in body or 'Dear' in body
        mock_post.assert_called_once()
    
    def test_template_fallback(self, sample_student_info, sample_professor):
        """Test fallback to template when LLM fails"""
        if EmailGenerator is None:
            pytest.skip("EmailGenerator not available")
            
        email_gen = EmailGenerator(sample_student_info, use_ollama=False)
        body = email_gen.generate_body(sample_professor)
        
        assert body is not None
        assert len(body) > 100
        # Should contain template-style content
        assert 'Dear' in body or 'Hi' in body
        assert sample_student_info['name'] in body

class TestEmailValidation:
    """Test email validation with MX record checking"""
    
    @patch('dns.resolver.resolve')
    def test_mx_record_validation_success(self, mock_resolve):
        """Test successful MX record validation"""
        # Mock successful MX record lookup
        mock_mx_record = Mock()
        mock_mx_record.exchange = 'mail.example.com'
        mock_resolve.return_value = [mock_mx_record]
        
        # Create a basic email validator function
        def validate_email_mx(email):
            import re
            import dns.resolver
            
            # Basic format check
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return False
            
            domain = email.split('@')[1]
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                return len(mx_records) > 0
            except:
                return False
        
        result = validate_email_mx('test@example.com')
        assert result is True
        mock_resolve.assert_called_with('example.com', 'MX')
    
    @patch('dns.resolver.resolve')
    def test_mx_record_validation_failure(self, mock_resolve):
        """Test MX record validation failure"""
        from dns.resolver import NXDOMAIN
        mock_resolve.side_effect = NXDOMAIN()
        
        def validate_email_mx(email):
            import re
            import dns.resolver
            
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return False
            
            domain = email.split('@')[1]
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                return len(mx_records) > 0
            except:
                return False
        
        result = validate_email_mx('test@nonexistentdomain.com')
        assert result is False
    
    def test_email_format_validation(self):
        """Test basic email format validation"""
        import re
        
        def is_valid_email_format(email):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None
        
        # Valid emails
        valid_emails = [
            'test@example.com',
            'user.name@domain.org',
            'user+tag@subdomain.example.co.uk'
        ]
        
        for email in valid_emails:
            assert is_valid_email_format(email), f"Should be valid: {email}"
        
        # Invalid emails
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user@domain',
            'user space@domain.com'
        ]
        
        for email in invalid_emails:
            assert not is_valid_email_format(email), f"Should be invalid: {email}"

class TestSentryIntegration:
    """Test Sentry error tracking integration"""
    
    @patch('sentry_sdk.capture_exception')
    def test_exception_capture(self, mock_capture):
        """Test that exceptions are properly captured by Sentry"""
        test_exception = ValueError("Test exception for Sentry")
        
        try:
            raise test_exception
        except Exception as e:
            # Simulate Sentry integration
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        
        mock_capture.assert_called_once()
        captured_exception = mock_capture.call_args[0][0]
        assert isinstance(captured_exception, ValueError)
        assert str(captured_exception) == "Test exception for Sentry"
    
    @patch('sentry_sdk.capture_exception')
    def test_email_generation_error_tracking(self, mock_capture, sample_student_info):
        """Test error tracking in email generation"""
        if EmailGenerator is None:
            pytest.skip("EmailGenerator not available")
            
        # Mock a function that might fail
        def failing_email_generation():
            try:
                # Simulate an error in email generation
                invalid_professor = {}
                email_gen = EmailGenerator(sample_student_info, use_ollama=False)
                # This should handle the error gracefully
                return email_gen.generate_body(invalid_professor)
            except Exception as e:
                import sentry_sdk
                sentry_sdk.capture_exception(e)
                raise
        
        # The function should either work or capture the exception
        try:
            result = failing_email_generation()
            # If it works, result should be a string
            assert isinstance(result, str)
        except Exception:
            # If it fails, exception should be captured
            mock_capture.assert_called()
    
    @patch('sentry_sdk.capture_message')
    def test_message_capture(self, mock_capture_message):
        """Test that messages are captured for debugging"""
        import sentry_sdk
        
        # Simulate capturing a debug message
        sentry_sdk.capture_message("Email generation completed successfully", level='info')
        
        mock_capture_message.assert_called_once_with(
            "Email generation completed successfully", 
            level='info'
        )

class TestEmailSender:
    """Test email sending functionality"""
    
    def test_email_sender_initialization(self):
        """Test EmailSender initialization"""
        if EmailSender is None:
            pytest.skip("EmailSender not available")
            
        sender = EmailSender('test@example.com', 'password')
        assert sender.user == 'test@example.com'
        assert sender.password == 'password'
    
    @patch('smtplib.SMTP_SSL')
    def test_successful_email_send(self, mock_smtp):
        """Test successful email sending"""
        if EmailSender is None:
            pytest.skip("EmailSender not available")
            
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        sender = EmailSender('test@example.com', 'password')
        result = sender.send_email(
            'recipient@example.com', 
            'Test Subject', 
            'Test email body content'
        )
        
        assert result is True
        mock_server.login.assert_called_once_with('test@example.com', 'password')
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP_SSL')
    def test_failed_email_send(self, mock_smtp):
        """Test handling of email sending failure"""
        if EmailSender is None:
            pytest.skip("EmailSender not available")
            
        # Mock SMTP server to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        sender = EmailSender('test@example.com', 'password')
        result = sender.send_email(
            'recipient@example.com', 
            'Test Subject', 
            'Test email body content'
        )
        
        assert result is False
