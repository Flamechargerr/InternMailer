"""Tests for template engine functionality"""
import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, Mock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from advanced_template_engine import AdvancedTemplateEngine
except ImportError:
    AdvancedTemplateEngine = None

try:
    from template_manager import TemplateManager
except ImportError:
    TemplateManager = None

try:
    from template_engine import render_template
except ImportError:
    render_template = None

class TestAdvancedTemplateEngine:
    """Test advanced template engine functionality"""
    
    @pytest.fixture
    def temp_engine(self, temp_templates_dir):
        """Create a temporary template engine"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
        return AdvancedTemplateEngine(temp_templates_dir)
    
    def test_template_creation(self, temp_engine):
        """Test creating a new template"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
            
        template_content = """
        Dear Prof. {{ professor_name }},
        
        I am {{ student_name }}, a {{ student_major }} student interested in your research on {{ research_area }}.
        
        Best regards,
        {{ student_name }}
        """
        
        success = temp_engine.create_template(
            name="test_template",
            content=template_content,
            description="A test template",
            category="test"
        )
        
        assert success is True
        assert "test_template" in temp_engine.metadata
        
        # Verify metadata
        metadata = temp_engine.metadata["test_template"]
        assert metadata.name == "test_template"
        assert metadata.description == "A test template"
        assert metadata.category == "test"
        assert "professor_name" in metadata.variables
        assert "student_name" in metadata.variables
        assert "research_area" in metadata.variables
    
    def test_template_validation(self, temp_engine):
        """Test template validation"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
            
        # Valid template
        valid_template = "Dear Prof. {{ professor_name }}, Best regards, {{ student_name }}"
        validation = temp_engine.validate_template(valid_template)
        
        assert validation['valid'] is True
        assert len(validation['errors']) == 0
        assert "professor_name" in validation['variables']
        assert "student_name" in validation['variables']
        
        # Invalid template (empty)
        invalid_template = ""
        validation = temp_engine.validate_template(invalid_template)
        
        assert validation['valid'] is False
        assert len(validation['errors']) > 0
        assert "empty" in validation['errors'][0].lower()
    
    def test_template_rendering(self, temp_engine):
        """Test template rendering with context"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
            
        # Create a template
        template_content = "Dear Prof. {{ professor_name }}, I am {{ student_name }} from {{ university }}."
        temp_engine.create_template("render_test", template_content, "Test rendering")
        
        # Render with context
        context = {
            "professor_name": "Smith",
            "student_name": "John Doe",
            "university": "MIT"
        }
        
        rendered = temp_engine.render_template("render_test", context)
        
        assert rendered is not None
        assert "Dear Prof. Smith" in rendered
        assert "I am John Doe" in rendered
        assert "from MIT" in rendered
    
    def test_variable_extraction(self, temp_engine):
        """Test extraction of template variables"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
            
        template_content = """
        Hello {{ name }},
        Your {{ item }} is ready for {{ action }}.
        Contact us at {{ email }}.
        """
        
        variables = temp_engine.get_template_variables(template_content)
        
        expected_vars = ["name", "item", "action", "email"]
        for var in expected_vars:
            assert var in variables
    
    def test_template_preview(self, temp_engine):
        """Test template preview functionality"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
            
        # Create a template
        template_content = "Dear {{ professor_name }}, I study {{ research_area }}."
        temp_engine.create_template("preview_test", template_content, "Preview test")
        
        # Generate preview
        preview = temp_engine.preview_template("preview_test")
        
        assert preview is not None
        assert "PREVIEW" in preview
        assert "Dear" in preview
        assert len(preview) > 50
    
    def test_templates_listing(self, temp_engine):
        """Test listing templates"""
        if AdvancedTemplateEngine is None:
            pytest.skip("AdvancedTemplateEngine not available")
            
        # Create multiple templates
        templates_to_create = [
            ("template1", "Content 1", "formal"),
            ("template2", "Content 2", "informal"),
            ("template3", "Content 3", "formal")
        ]
        
        for name, content, category in templates_to_create:
            temp_engine.create_template(name, f"Dear Prof., {content}", f"Test {name}", category)
        
        # List all templates
        templates = temp_engine.list_templates()
        assert len(templates) >= 3
        
        # Check template info
        template_names = [t['name'] for t in templates]
        assert "template1" in template_names
        assert "template2" in template_names
        assert "template3" in template_names
        
        # Test filtering by category
        formal_templates = temp_engine.get_templates_by_category("formal")
        assert "template1" in formal_templates
        assert "template3" in formal_templates
        assert "template2" not in formal_templates

class TestTemplateManager:
    """Test template manager functionality"""
    
    @pytest.fixture
    def temp_manager(self, temp_templates_dir):
        """Create a temporary template manager"""
        if TemplateManager is None:
            pytest.skip("TemplateManager not available")
        
        # Create templates directory structure
        os.makedirs(temp_templates_dir, exist_ok=True)
        
        # Create a sample template file
        sample_template = """Dear Prof. {{ professor_name }},

I am {{ student_name }}, a {{ student_major }} student at {{ student_university }}.
I am writing to express my interest in your research on {{ research_area }}.

Best regards,
{{ student_name }}
{{ student_email }}"""
        
        template_path = os.path.join(temp_templates_dir, "sample_template.jinja2")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(sample_template)
        
        # Mock the engine to use our temporary directory
        with patch.object(TemplateManager, '__init__') as mock_init:
            mock_init.return_value = None
            manager = TemplateManager()
            manager.engine = Mock()
            manager.engine.templates_dir = temp_templates_dir
            manager.engine.metadata = {}
            
            # Mock engine methods
            manager.engine.render_template = Mock(return_value="Rendered email content")
            manager.engine.list_templates = Mock(return_value=[
                {
                    'name': 'sample_template',
                    'category': 'general',
                    'description': 'Sample template',
                    'variables': ['professor_name', 'student_name', 'research_area']
                }
            ])
            
            return manager
    
    def test_template_generation(self, temp_manager):
        """Test email generation using template manager"""
        if TemplateManager is None:
            pytest.skip("TemplateManager not available")
            
        context = {
            'professor_name': 'Dr. Smith',
            'student_name': 'John Doe',
            'research_area': 'Machine Learning'
        }
        
        result = temp_manager.generate_email('sample_template', context)
        
        assert result is not None
        temp_manager.engine.render_template.assert_called_once_with('sample_template', context)
    
    def test_sample_context_creation(self, temp_manager):
        """Test creation of sample context for templates"""
        if TemplateManager is None:
            pytest.skip("TemplateManager not available")
            
        context = temp_manager.create_sample_context('sample_template')
        
        assert context is not None
        assert isinstance(context, dict)
        assert len(context) > 0
        
        # Should contain sample data for common variables
        assert 'student_name' in context
        assert 'professor_name' in context
    
    def test_scenario_template_mapping(self, temp_manager):
        """Test getting appropriate template for scenarios"""
        if TemplateManager is None:
            pytest.skip("TemplateManager not available")
            
        scenarios = [
            "formal_application",
            "quick_inquiry", 
            "follow_up",
            "international"
        ]
        
        for scenario in scenarios:
            template_name = temp_manager.get_template_for_scenario(scenario)
            assert template_name is not None
            assert isinstance(template_name, str)
            assert len(template_name) > 0

class TestTemplateRendering:
    """Test template rendering and output comparison"""
    
    def test_email_template_rendering(self, sample_student_info, sample_professor):
        """Test rendering of email templates with sample data"""
        
        # Define template content
        template_content = """Dear Prof. {{ professor.name.split()[-1] }},

I am {{ student.name }}, a {{ student.major | default('Computer Science') }} student at {{ student.university | default('University') }}.

I am very interested in your research on {{ professor.research_area }}. My background includes:
- Skills: {{ student.skills | join(', ') }}
- Projects: {{ student.projects | join(', ') }}

I would be grateful for the opportunity to discuss potential research opportunities.

Best regards,
{{ student.name }}
{{ student.email }}"""
        
        # Test with Jinja2 directly
        from jinja2 import Template
        
        template = Template(template_content)
        
        context = {
            'professor': {
                'name': sample_professor['Name'],
                'research_area': sample_professor['Research Area']
            },
            'student': {
                'name': sample_student_info['name'],
                'email': sample_student_info['email'],
                'major': 'Data Science Engineering',
                'university': 'Manipal Institute of Technology',
                'skills': sample_student_info['skills'][:5],  # First 5 skills
                'projects': sample_student_info['projects'][:3]  # First 3 projects
            }
        }
        
        rendered = template.render(context)
        
        # Verify rendered content
        assert rendered is not None
        assert len(rendered) > 100
        assert sample_professor['Name'].split()[-1] in rendered  # Last name
        assert sample_student_info['name'] in rendered
        assert sample_student_info['email'] in rendered
        assert sample_professor['Research Area'] in rendered
        
        # Check that skills and projects are included
        for skill in context['student']['skills']:
            assert skill in rendered
        
        for project in context['student']['projects']:
            assert project in rendered
    
    def test_template_comparison(self):
        """Test comparison of different template outputs"""
        
        formal_template = """Dear Prof. {{ professor_name }},

I am writing to formally express my interest in your research on {{ research_area }}.

Sincerely,
{{ student_name }}"""
        
        informal_template = """Hi Prof. {{ professor_name }},

I'm {{ student_name }} and I'm really excited about your work on {{ research_area }}!

Best,
{{ student_name }}"""
        
        from jinja2 import Template
        
        context = {
            'professor_name': 'Smith',
            'student_name': 'John',
            'research_area': 'AI'
        }
        
        formal_rendered = Template(formal_template).render(context)
        informal_rendered = Template(informal_template).render(context)
        
        # Both should contain the same key information
        for template_output in [formal_rendered, informal_rendered]:
            assert 'Prof. Smith' in template_output
            assert 'John' in template_output
            assert 'AI' in template_output
        
        # But should have different tones
        assert 'formally' in formal_rendered
        assert 'Sincerely' in formal_rendered
        assert 'excited' in informal_rendered
        assert "I'm" in informal_rendered
    
    def test_template_edge_cases(self):
        """Test template rendering with edge cases"""
        
        template_content = """
        {%- if professor_name -%}
        Dear Prof. {{ professor_name }},
        {%- else -%}
        Dear Professor,
        {%- endif %}
        
        {%- if research_area %}
        I am interested in {{ research_area }}.
        {%- endif %}
        
        {%- if student_skills %}
        My skills include: {{ student_skills | join(', ') }}.
        {%- endif %}
        
        Best regards,
        {{ student_name | default('Student') }}
        """
        
        from jinja2 import Template
        template = Template(template_content)
        
        # Test with complete data
        complete_context = {
            'professor_name': 'Smith',
            'research_area': 'Machine Learning',
            'student_skills': ['Python', 'TensorFlow'],
            'student_name': 'John Doe'
        }
        
        rendered_complete = template.render(complete_context)
        assert 'Dear Prof. Smith' in rendered_complete
        assert 'Machine Learning' in rendered_complete
        assert 'Python, TensorFlow' in rendered_complete
        assert 'John Doe' in rendered_complete
        
        # Test with minimal data
        minimal_context = {
            'professor_name': None,
            'research_area': None,
            'student_skills': [],
            'student_name': None
        }
        
        rendered_minimal = template.render(minimal_context)
        assert 'Dear Professor,' in rendered_minimal
        assert 'Student' in rendered_minimal  # Default value
        
        # Should not contain None or empty strings
        assert 'None' not in rendered_minimal
        assert 'I am interested in .' not in rendered_minimal  # Empty research area
    
    def test_template_performance(self):
        """Test template rendering performance"""
        import time
        from jinja2 import Template
        
        template_content = """Dear Prof. {{ professor_name }},
        
I am {{ student_name }} with skills in {{ skills | join(', ') }}.
I have worked on {{ projects | length }} projects including {{ projects[0] }}.

Best regards,
{{ student_name }}"""
        
        template = Template(template_content)
        
        context = {
            'professor_name': 'Dr. Test',
            'student_name': 'Test Student',
            'skills': ['Python', 'Machine Learning', 'Data Analysis'] * 10,  # 30 skills
            'projects': ['Project ' + str(i) for i in range(100)]  # 100 projects
        }
        
        # Measure rendering time
        start_time = time.time()
        
        for _ in range(100):  # Render 100 times
            rendered = template.render(context)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second for 100 renders)
        assert total_time < 1.0
        
        # Verify the last render is correct
        assert 'Dr. Test' in rendered
        assert 'Test Student' in rendered
        assert '100 projects' in rendered
        assert 'Project 0' in rendered  # First project
