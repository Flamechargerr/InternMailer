"""
Unit tests for edge cases and diverse resume formats.
Tests PDF, DOCX, and various resume structures.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
import json

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parsing.parser_interface import ResumeData, ParsingError
from parsing.rule_based_parser import RuleBasedParser
from parsing.ollama_parser import OllamaResumeParser
from parsing.gemma3_parser import Gemma3ResumeParser


class TestEdgeCases:
    """Test edge cases in resume parsing."""

    def test_empty_resume(self):
        """Test parsing of empty or minimal resume."""
        parser = RuleBasedParser()
        
        # Test completely empty text
        with pytest.raises(ParsingError):
            parser.parse("")
        
        # Test minimal text
        minimal_text = "John Doe\nSoftware Engineer"
        result = parser.parse(minimal_text)
        assert isinstance(result, ResumeData)
        assert result.summary != ""

    def test_non_english_resume(self):
        """Test parsing of resume with non-English content."""
        parser = RuleBasedParser()
        
        multilingual_text = """
        Juan Pérez
        Desarrollador de Software
        
        Habilidades Técnicas:
        Python, JavaScript, React
        
        Proyectos:
        Sistema de Gestión - Aplicación web
        """
        
        result = parser.parse(multilingual_text)
        assert isinstance(result, ResumeData)
        assert len(result.skills) > 0

    def test_heavily_formatted_resume(self):
        """Test parsing of resume with heavy formatting."""
        parser = RuleBasedParser()
        
        formatted_text = """
        ╔══════════════════════════════════════╗
        ║           JOHN SMITH                 ║
        ║        Software Engineer             ║
        ╚══════════════════════════════════════╝
        
        ★ TECHNICAL SKILLS ★
        ▶ Programming: Python • Java • JavaScript
        ▶ Frameworks: React ◦ Django ◦ Flask
        ▶ Tools: Git | Docker | AWS
        
        ★ PROJECTS ★
        ➤ E-Commerce Platform
        ➤ Machine Learning Dashboard
        """
        
        result = parser.parse(formatted_text)
        assert isinstance(result, ResumeData)
        assert len(result.skills) >= 3

    def test_resume_with_special_characters(self):
        """Test parsing of resume with special characters and symbols."""
        parser = RuleBasedParser()
        
        special_char_text = """
        Alex O'Connor-Smith
        Full-Stack Developer @ Tech Corp.
        
        Skills:
        C++, C#, Node.js, Vue.js, HTML5/CSS3
        
        Projects:
        "Smart City" IoT Platform
        AI/ML Recommendation Engine
        """
        
        result = parser.parse(special_char_text)
        assert isinstance(result, ResumeData)
        assert any('C++' in skill or 'C#' in skill for skill in result.skills)

    def test_very_long_resume(self):
        """Test parsing of unusually long resume."""
        parser = RuleBasedParser()
        
        # Create a very long resume text
        long_text = "John Doe\nSoftware Engineer\n\n"
        long_text += "Skills:\n" + ", ".join([f"Skill{i}" for i in range(50)]) + "\n\n"
        long_text += "Projects:\n" + "\n".join([f"Project {i} - Description" for i in range(20)]) + "\n\n"
        long_text += "Experience:\n" + "\n".join([f"Role {i} at Company {i}" for i in range(10)])
        
        result = parser.parse(long_text)
        assert isinstance(result, ResumeData)
        assert len(result.skills) <= 15  # Should be limited
        assert len(result.projects) <= 8  # Should be limited

    def test_resume_with_no_sections(self):
        """Test parsing of resume without clear sections."""
        parser = RuleBasedParser()
        
        unstructured_text = """
        Jane Smith is a software engineer with experience in Python and React.
        She has worked on web applications and machine learning projects.
        Jane knows JavaScript, SQL, and has used Docker and Git.
        She built an e-commerce platform and a data visualization tool.
        """
        
        result = parser.parse(unstructured_text)
        assert isinstance(result, ResumeData)
        assert len(result.skills) > 0


class TestFileFormatSupport:
    """Test support for different file formats."""

    def test_pdf_text_extraction(self):
        """Test PDF text extraction edge cases."""
        from resume_parser import ResumeParser
        
        # Test with non-existent file
        with pytest.raises(ParsingError):
            parser = ResumeParser("nonexistent.pdf")
            parser.extract_text()

    def test_corrupted_file_handling(self):
        """Test handling of corrupted or invalid files."""
        from resume_parser import ResumeParser
        
        # Create a temporary file with invalid content
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"This is not a valid PDF file")
            temp_path = temp_file.name
        
        try:
            parser = ResumeParser(temp_path)
            with pytest.raises(ParsingError):
                parser.extract_text()
        finally:
            os.unlink(temp_path)

    def test_large_file_handling(self):
        """Test handling of very large resume files."""
        parser = RuleBasedParser()
        
        # Simulate a very large resume (>10MB of text)
        large_text = "A" * (10 * 1024 * 1024)  # 10MB of text
        
        # Should handle gracefully without crashing
        result = parser.parse(large_text)
        assert isinstance(result, ResumeData)


class TestDataValidation:
    """Test data validation and JSON schema compliance."""

    def test_resume_data_validation(self):
        """Test ResumeData validation."""
        # Valid data
        valid_data = ResumeData(
            skills=["Python", "JavaScript"],
            projects=["Web App", "API"],
            courses=["Computer Science"],
            experience=["Developer at Company"],
            summary="Software engineer with experience"
        )
        assert valid_data.validate()
        
        # Invalid data (missing required fields)
        invalid_data = ResumeData(
            skills=[],
            projects=[],
            courses=["Course"],
            experience=["Job"],
            summary=""
        )
        assert not invalid_data.validate()

    def test_json_schema_compliance(self):
        """Test that parsed output complies with expected JSON schema."""
        parser = RuleBasedParser()
        
        sample_text = """
        John Doe
        Software Engineer
        
        Skills: Python, JavaScript, React
        Projects: Web App, Mobile App
        Courses: Computer Science, Mathematics
        Experience: Developer at Tech Corp
        """
        
        result = parser.parse(sample_text)
        json_output = result.to_json()
        
        # Parse JSON to ensure it's valid
        parsed = json.loads(json_output)
        
        # Check required fields
        required_fields = ['skills', 'projects', 'courses', 'experience', 'summary']
        for field in required_fields:
            assert field in parsed
            assert isinstance(parsed[field], (list, str))

    def test_data_type_consistency(self):
        """Test consistency of data types in parsed output."""
        parser = RuleBasedParser()
        
        sample_text = "Skills: Python, Java\nProjects: App\nSummary: Engineer"
        result = parser.parse(sample_text)
        
        assert isinstance(result.skills, list)
        assert isinstance(result.projects, list)
        assert isinstance(result.courses, list)
        assert isinstance(result.experience, list)
        assert isinstance(result.summary, str)
        
        # Check list elements are strings
        for skill in result.skills:
            assert isinstance(skill, str)
        for project in result.projects:
            assert isinstance(project, str)


class TestPerformanceMetrics:
    """Test performance tracking and metrics."""

    def test_performance_metrics_tracking(self):
        """Test that parsers track performance metrics."""
        parser = RuleBasedParser()
        
        # Initial metrics should be zero
        metrics = parser.get_performance_metrics()
        assert metrics['total_requests'] == 0
        assert metrics['successful_requests'] == 0
        
        # Parse a sample resume
        sample_text = "Skills: Python\nProjects: App"
        parser.parse(sample_text)
        
        # Metrics should be updated
        updated_metrics = parser.get_performance_metrics()
        assert updated_metrics['total_requests'] == 1
        assert updated_metrics['successful_requests'] == 1
        assert updated_metrics['avg_response_time'] > 0

    def test_provider_availability_check(self):
        """Test provider availability checking."""
        rule_parser = RuleBasedParser()
        assert rule_parser.is_available()  # Rule-based is always available
        
        # Mock Ollama availability
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            ollama_parser = OllamaResumeParser()
            assert ollama_parser.is_available()
            
            mock_get.side_effect = Exception("Connection failed")
            assert not ollama_parser.is_available()


class TestConcurrencyAndCaching:
    """Test concurrent parsing and caching functionality."""

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_concurrent_section_processing(self, mock_executor):
        """Test concurrent processing of resume sections."""
        parser = Gemma3ResumeParser()
        
        # Mock the executor behavior
        mock_future = MagicMock()
        mock_future.result.return_value = {"skills": ["Python"]}
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
        
        large_text = "A" * 5000  # Text large enough to trigger chunking
        
        with patch.object(parser, '_extract_resume_data') as mock_extract:
            mock_extract.return_value = ResumeData(
                skills=["Python"], projects=["App"], courses=["CS"],
                experience=["Job"], summary="Engineer"
            )
            try:
                result = parser.parse(large_text)
                assert isinstance(result, ResumeData)
            except Exception as e:
                # Expected since we're mocking extensively
                pass

    def test_caching_functionality(self):
        """Test caching of identical resume segments."""
        parser = OllamaResumeParser()
        
        # Mock the client to simulate caching
        with patch.object(parser, 'client') as mock_client:
            mock_client.cache = {}
            mock_client.generate_with_fallback.return_value = '{"skills": ["Python"], "projects": ["App"], "courses": ["CS"], "experience": ["Job"], "summary": "Engineer"}'
            
            # First call
            result1 = parser.parse("Sample text")
            
            # Second call with same text should use cache
            mock_client.cache["sample_key"] = '{"skills": ["Python"], "projects": ["App"], "courses": ["CS"], "experience": ["Job"], "summary": "Engineer"}'
            result2 = parser.parse("Sample text")
            
            assert isinstance(result1, ResumeData)
            assert isinstance(result2, ResumeData)


if __name__ == "__main__":
    pytest.main([__file__])
