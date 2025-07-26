"""
Pytest configuration and shared fixtures for InternMailer tests
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import sys

# Add src paths to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'InternMailer', 'src'))

@pytest.fixture
def sample_student_info():
    """Sample student information for testing"""
    return {
        'name': 'Anamay Tripathy',
        'email': 'tripathy.anamay23@gmail.com',
        'summary': 'Data Science Engineering student with strong technical skills in full-stack development, machine learning, and data analysis.',
        'skills': ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Web Development', 'React', 'Node.js', 'MongoDB'],
        'projects': ['CrimeConnect', 'VARtificial Intelligence', 'HackOps', 'Flora Fight Frenzy'],
        'courses': ['Machine Learning', 'Data Structures', 'Algorithms', 'Statistics', 'Linear Algebra', 'Database Systems'],
        'domains': ['Machine Learning', 'Web Development', 'Data Science'],
        'experience': ['Data Analyst Web Development Intern at TechCorp', 'Technical Head at CodeClub'],
        'resume_prefix': 'CV_Anamay_Modern'
    }

@pytest.fixture
def sample_professor():
    """Sample professor information for testing"""
    return {
        'Name': 'Dr. Manya Ghobadi',
        'University': 'Massachusetts Institute of Technology (MIT)',
        'Research Area': 'Machine Learning and Networks',
        'Email': 'ghobadi@mit.edu',
        'Homepage': 'http://people.csail.mit.edu/ghobadi'
    }

@pytest.fixture
def sample_professors_list():
    """Sample list of professors for testing"""
    return [
        {
            'Name': 'Dr. John Smith',
            'University': 'Stanford University',
            'Research Area': 'Computer Vision',
            'Email': 'jsmith@stanford.edu'
        },
        {
            'Name': 'Dr. Jane Doe',
            'University': 'MIT',
            'Research Area': 'Natural Language Processing',
            'Email': 'jdoe@mit.edu'
        },
        {
            'Name': 'Dr. Alex Johnson',
            'University': 'Carnegie Mellon University',
            'Research Area': 'Robotics',
            'Email': 'ajohnson@cmu.edu'
        }
    ]

@pytest.fixture
def temp_templates_dir():
    """Create a temporary directory for template testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_dns_resolver():
    """Mock DNS resolver for MX record validation"""
    with patch('dns.resolver.resolve') as mock_resolver:
        # Mock successful MX record lookup
        mock_mx_record = Mock()
        mock_mx_record.exchange = 'mail.example.com'
        mock_resolver.return_value = [mock_mx_record]
        yield mock_resolver

@pytest.fixture
def mock_sentry():
    """Mock Sentry SDK for exception tracking"""
    with patch('sentry_sdk.capture_exception') as mock_capture:
        yield mock_capture

@pytest.fixture
def mock_ollama():
    """Mock Ollama for LLM testing"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': 'Generated email content from LLM'
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        yield mock_post

@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing campaign system"""
    return """Name,Email,University,Research Area
Dr. John Smith,jsmith@stanford.edu,Stanford University,Computer Vision
Dr. Jane Doe,jdoe@mit.edu,MIT,Natural Language Processing
Dr. Alex Johnson,ajohnson@cmu.edu,Carnegie Mellon University,Robotics"""

@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_csv_data)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_email_sender():
    """Mock email sender for testing without actually sending emails"""
    with patch('smtplib.SMTP_SSL') as mock_smtp:
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.login.return_value = None
        mock_server.send_message.return_value = None
        yield mock_server

@pytest.fixture
def sample_resume_text():
    """Sample resume text for parser testing"""
    return """
    Summary
    Data Science Engineering student with strong technical skills

    Education
    B.Tech Data Science Engineering, Manipal Institute of Technology
    CGPA: 7.6/10
    Courses: Machine Learning, Data Structures, Algorithms, Statistics

    Experience
    Data Analyst Web Development Intern, TechCorp – Remote
    Technical Head, CodeClub – Campus

    Projects
    CrimeConnect – MERN Stack, Supabase
    VARtificial Intelligence – Python, Machine Learning
    HackOps – Cybersecurity, Gamification

    Technical Skills
    Languages: Python, JavaScript, Java, C++
    Frameworks Libraries: React, Node.js, Express.js, TensorFlow, PyTorch
    Tools Platforms: Git, Docker, AWS, MongoDB
    Domains: Machine Learning, Web Development, Data Science
    """
