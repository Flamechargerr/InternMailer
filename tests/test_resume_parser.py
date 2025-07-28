"""
Unit tests for the ResumeParser orchestrator.
Tests parsing integration and fallback mechanisms.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from .src.resume_parser import ResumeParser
from .src.parsing.parser_interface import ParsingError


def get_sample_resume_text(format='pdf'):
    """Provides a sample resume text for testing various formats"""
    if format == 'pdf':
        return "Sample PDF resume content with various sections"
    elif format == 'docx':
        return "Sample DOCX resume content with various sections"
    return "Sample plain text resume"


@pytest.fixture(scope="module")

def sample_resume_path():
    """Fixture for providing a sample resume path."""
    return os.path.join(os.path.dirname(__file__), 'sample_resume.pdf')


class TestResumeParser:
    """Tests integration with different resume parsing strategies."""

    @patch('src.parsing.ollama_parser.OllamaResumeParser.is_available')
    def test_successful_parsing_with_ollama(self, mock_ollama_available, sample_resume_path):
        """Test successful parsing with Ollama parser."""
        mock_ollama_available.return_value = True

        parser = ResumeParser(sample_resume_path)

        # Mock extract_text to avoid dealing with actual files
        with patch.object(parser, 'extract_text', return_value=get_sample_resume_text('pdf')):
            data = parser.parse()
            assert isinstance(data, dict)
            assert len(data['skills']) > 0

    @patch('src.parsing.gemma3_parser.Gemma3ResumeParser.is_available')
    def test_successful_parsing_with_gemma3(self, mock_gemma3_available, sample_resume_path):
        """Test successful parsing with Gemma3 parser."""
        mock_gemma3_available.return_value = True

        parser = ResumeParser(sample_resume_path)

        with patch.object(parser, 'extract_text', return_value=get_sample_resume_text('pdf')):
            data = parser.parse()
            assert isinstance(data, dict)
            assert len(data['skills']) > 0

    def test_fallback_to_rule_based(self, sample_resume_path):
        """Test fallback to rule-based parser when LLMs fail."""

        parser = ResumeParser(sample_resume_path)

        with patch.object(parser, 'extract_text', return_value=get_sample_resume_text('pdf')):
            # Simulate all LLM parsers being unavailable
            with patch('src.parsing.ollama_parser.OllamaResumeParser.is_available', return_value=False), \
                 patch('src.parsing.gemma3_parser.Gemma3ResumeParser.is_available', return_value=False):

                data = parser.parse()
                assert isinstance(data, dict)
                assert len(data['skills']) > 0

    def test_json_output(self, sample_resume_path):
        """Test JSON output of parsed data."""
        parser = ResumeParser(sample_resume_path)

        with patch.object(parser, 'extract_text', return_value=get_sample_resume_text('pdf')):
            data = parser.parse()
            json_str = parser.to_json()
            assert json_str.startswith('{')
            assert 'skills' in json_str

    def test_parsing_failure_handling(self):
        """Test proper handling of parsing exceptions."""

        parser = ResumeParser("nonexistent_path.pdf")

        with pytest.raises(ParsingError):
            parser.parse()
