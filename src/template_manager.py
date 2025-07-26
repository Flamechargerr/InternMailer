"""
Template Manager for InternMailer
Provides easy-to-use interface for template operations
"""

from advanced_template_engine import AdvancedTemplateEngine
from typing import Dict, List, Any
import json

class TemplateManager:
    """High-level interface for managing email templates"""
    
    def __init__(self):
        self.engine = AdvancedTemplateEngine()
    
    def setup_default_templates(self):
        """Set up default email templates"""
        templates = {
            "research_internship_formal": {
                "description": "Formal research internship application",
                "category": "internship"
            },
            "research_inquiry_concise": {
                "description": "Concise research opportunity inquiry",
                "category": "inquiry"
            },
            "follow_up_polite": {
                "description": "Polite follow-up email",
                "category": "follow-up"
            },
            "international_student": {
                "description": "Template for international students",
                "category": "international"
            }
        }
        
        print("Setting up default templates...")
        for template_name, metadata in templates.items():
            try:
                # Templates are already created as .jinja2 files
                template_path = f"{self.engine.templates_dir}\\{template_name}.jinja2"
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create template metadata if it doesn't exist
                if template_name not in self.engine.metadata:
                    self.engine.create_template(
                        template_name, 
                        content, 
                        metadata["description"], 
                        metadata["category"]
                    )
                print(f"✓ Template '{template_name}' ready")
            except Exception as e:
                print(f"✗ Error setting up template '{template_name}': {e}")
    
    def get_template_for_scenario(self, scenario: str) -> str:
        """Get recommended template for specific scenario"""
        scenario_mapping = {
            "formal_application": "research_internship_formal",
            "quick_inquiry": "research_inquiry_concise",
            "follow_up": "follow_up_polite",
            "international": "international_student"
        }
        return scenario_mapping.get(scenario, "research_inquiry_concise")
    
    def create_sample_context(self, template_name: str) -> Dict[str, Any]:
        """Create sample context for template preview"""
        sample_data = {
            # Student information
            "student_name": "Jane Doe",
            "student_year": "Junior",
            "student_major": "Computer Science",
            "student_university": "MIT",
            "student_degree": "Bachelor's",
            "student_country": "USA",
            "student_email": "jane.doe@mit.edu",
            "student_phone": "+1-555-0123",
            "graduation_year": "2026",
            "gpa": "3.8/4.0",
            
            # Professor information
            "professor_name": "Smith",
            "professor_university": "Stanford University",
            
            # Research information
            "research_area": "Machine Learning and Artificial Intelligence",
            "specific_research_topic": "neural network optimization",
            "specific_topic": "deep reinforcement learning",
            "career_focus": "AI research and development",
            "related_field": "computational intelligence",
            "specific_research_focus": "computer vision applications",
            "specific_project": "automated image recognition systems",
            "specific_interest": "neural architecture search",
            
            # Qualifications
            "key_qualifications": "strong programming skills in Python and machine learning frameworks",
            "relevant_experience": "2 years of Python programming and ML projects",
            "relevant_skills": "TensorFlow, PyTorch, data analysis, statistical modeling",
            "relevant_coursework": "Machine Learning, Data Structures, Algorithms, Statistics",
            "research_experience": "undergraduate research project on computer vision",
            "academic_achievements": "Dean's List for 3 consecutive semesters",
            "technical_skills": "Python, R, MATLAB, Git, Docker",
            "language_skills": "English (native), Spanish (conversational)",
            
            # International student specific
            "english_proficiency": "IELTS 7.5",
            "visa_status": "F-1 eligible",
            
            # Follow-up specific
            "original_date": "January 15, 2025",
            "additional_updates": "completed an advanced course in deep learning"
        }
        
        # Filter context based on template variables
        if template_name in self.engine.metadata:
            required_vars = self.engine.metadata[template_name].variables
            return {var: sample_data.get(var, f"[Sample {var}]") for var in required_vars}
        
        return sample_data
    
    def preview_all_templates(self):
        """Preview all available templates"""
        templates = self.engine.list_templates()
        
        for template in templates:
            print(f"\n{'='*60}")
            print(f"TEMPLATE: {template['name'].upper()}")
            print(f"Category: {template['category']}")
            print(f"Description: {template['description']}")
            print(f"Variables: {', '.join(template['variables'])}")
            print(f"{'='*60}")
            
            context = self.create_sample_context(template['name'])
            preview = self.engine.preview_template(template['name'], context)
            print(preview)
    
    def generate_email(self, template_name: str, context: Dict[str, Any]) -> str:
        """Generate email using specified template and context"""
        return self.engine.render_template(template_name, context)
    
    def list_templates_by_category(self):
        """List templates organized by category"""
        templates = self.engine.list_templates()
        categories = {}
        
        for template in templates:
            category = template['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(template)
        
        print("Available Templates by Category:")
        print("=" * 40)
        for category, template_list in categories.items():
            print(f"\n{category.upper()}:")
            for template in template_list:
                print(f"  • {template['name']} - {template['description']}")
        
        return categories

# Demo and testing
if __name__ == "__main__":
    manager = TemplateManager()
    
    print("InternMailer Template Manager")
    print("=" * 50)
    
    # Setup default templates
    manager.setup_default_templates()
    
    print("\n" + "=" * 50)
    print("TEMPLATE CATEGORIES")
    print("=" * 50)
    manager.list_templates_by_category()
    
    print("\n" + "=" * 50)
    print("TEMPLATE PREVIEWS")
    print("=" * 50)
    manager.preview_all_templates()
    
    print("\n" + "=" * 50)
    print("Template Manager Ready!")
    print("=" * 50)
