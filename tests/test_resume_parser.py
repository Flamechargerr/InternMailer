"""Tests for resume parser functionality"""
import pytest
import os
import sys
from unittest.mock import patch, Mock
import tempfile

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'InternMailer', 'src'))

try:
    from resume_parser import ResumeParser
except ImportError:
    ResumeParser = None

class TestResumeParser:
    """Test resume parsing functionality"""
    
    def test_rule_based_parsing(self, sample_resume_text):
        """Test rule-based resume parsing"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        # Create a temporary PDF file (mock)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            parser.text = sample_resume_text  # Set text directly for testing
            
            # Test rule-based parsing
            result = parser.parse_with_rules()
            
            assert isinstance(result, dict)
            assert 'skills' in result
            assert 'projects' in result
            assert 'courses' in result
            assert 'experience' in result
            
            # Check that skills were extracted
            assert len(result['skills']) > 0
            assert 'Python' in result['skills']
            assert 'JavaScript' in result['skills']
            
            # Check that projects were extracted
            assert len(result['projects']) > 0
            assert 'CrimeConnect' in result['projects']
            
            # Check that courses were extracted
            assert len(result['courses']) > 0
            assert 'Machine Learning' in result['courses']
            
            # Check that experience was extracted
            assert len(result['experience']) > 0
            assert any('Data Analyst' in exp for exp in result['experience'])
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('requests.post')
    def test_llm_parsing(self, mock_post, sample_resume_text):
        """Test LLM-based resume parsing"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': '''{
                "skills": ["Python", "Machine Learning", "Web Development"],
                "projects": ["AI Project", "Web App"],
                "courses": ["Computer Science", "Data Analysis"],
                "summary": "Experienced student in computer science"
            }'''
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            parser.text = sample_resume_text
            
            result = parser.parse_with_llm()
            
            assert isinstance(result, dict)
            assert 'skills' in result
            assert 'projects' in result
            assert 'courses' in result
            assert 'summary' in result
            
            # Verify LLM was called
            mock_post.assert_called_once()
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_fallback_mechanism(self, sample_resume_text):
        """Test fallback mechanism when parsing fails"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            parser.text = ""  # Empty text to trigger fallback
            
            # Mock LLM to fail
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("LLM failed")
                
                result = parser.parse()
                
                # Should use basic fallback data
                assert isinstance(result, dict)
                assert 'skills' in result
                assert 'projects' in result
                assert len(result['skills']) > 0  # Should have fallback skills
                assert len(result['projects']) > 0  # Should have fallback projects
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_text_extraction_fallback(self):
        """Test text extraction with fallback"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            
            # Mock PyPDF2 to fail and fallback to pdfplumber
            with patch('PyPDF2.PdfReader') as mock_pypdf:
                mock_pypdf.side_effect = Exception("PyPDF2 failed")
                
                with patch('pdfplumber.open') as mock_pdfplumber:
                    mock_page = Mock()
                    mock_page.extract_text.return_value = "Sample extracted text"
                    mock_pdf = Mock()
                    mock_pdf.__enter__.return_value.pages = [mock_page]
                    mock_pdfplumber.return_value = mock_pdf
                    
                    # This should use pdfplumber fallback
                    parser.extract_text()
                    
                    assert parser.text == "Sample extracted text"
                    
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_data_cleaning(self, sample_resume_text):
        """Test data cleaning and deduplication"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            parser.text = sample_resume_text
            
            result = parser.parse_with_rules()
            
            # Check that duplicates are removed
            skills = result['skills']
            assert len(skills) == len(set(skills))  # No duplicates
            
            # Check that empty entries are filtered out
            assert all(skill.strip() for skill in skills)  # No empty strings
            assert all(len(skill) > 1 for skill in skills)  # No single characters
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_json_output(self, sample_resume_text):
        """Test JSON output functionality"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            parser.text = sample_resume_text
            
            # Parse and get JSON
            parser.parse()
            json_output = parser.to_json()
            
            assert isinstance(json_output, str)
            
            # Should be valid JSON
            import json
            data = json.loads(json_output)
            assert isinstance(data, dict)
            assert 'skills' in data
            assert 'projects' in data
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_specific_parsing_patterns(self):
        """Test specific parsing patterns for different resume formats"""
        if ResumeParser is None:
            pytest.skip("ResumeParser not available")
        
        # Test different resume formats
        formats = [
            {
                'text': '''
                Technical Skills
                Languages: Python, Java, JavaScript
                Frameworks Libraries: React, Django, TensorFlow
                Tools Platforms: Git, Docker, AWS
                ''',
                'expected_skills': ['Python', 'Java', 'JavaScript', 'React', 'Django', 'TensorFlow', 'Git', 'Docker', 'AWS']
            },
            {
                'text': '''
                Projects
                E-Commerce Website – MERN Stack, MongoDB
                Machine Learning Model – Python, Scikit-learn
                ''',
                'expected_projects': ['E-Commerce Website', 'Machine Learning Model']
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            
            for format_test in formats:
                parser.text = format_test['text']
                result = parser.parse_with_rules()
                
                if 'expected_skills' in format_test:
                    found_skills = set(result['skills'])
                    expected_skills = set(format_test['expected_skills'])
                    # At least some expected skills should be found
                    assert len(found_skills.intersection(expected_skills)) > 0
                
                if 'expected_projects' in format_test:
                    found_projects = result['projects']
                    expected_projects = format_test['expected_projects']
                    # At least some expected projects should be found
                    assert any(proj in ' '.join(found_projects) for proj in expected_projects)
                    
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
