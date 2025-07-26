"""
Advanced Email Template Engine for InternMailer
Provides flexible, reusable template system with validation and preview
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from jinja2 import Environment, FileSystemLoader, Template, meta
from dataclasses import dataclass
import re

@dataclass
class TemplateMetadata:
    """Metadata for email templates"""
    name: str
    description: str
    category: str
    variables: List[str]
    created_date: str
    last_modified: str
    author: str
    version: str

class AdvancedTemplateEngine:
    """Advanced template engine with validation and management features"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        self.templates_dir = templates_dir
        self.metadata_file = os.path.join(templates_dir, 'template_metadata.json')
        
        # Create directories if they don't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load template metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, TemplateMetadata]:
        """Load template metadata from JSON file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        name: TemplateMetadata(**meta) 
                        for name, meta in data.items()
                    }
            except Exception as e:
                print(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save template metadata to JSON file"""
        try:
            data = {
                name: {
                    'name': meta.name,
                    'description': meta.description,
                    'category': meta.category,
                    'variables': meta.variables,
                    'created_date': meta.created_date,
                    'last_modified': meta.last_modified,
                    'author': meta.author,
                    'version': meta.version
                }
                for name, meta in self.metadata.items()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def get_template_variables(self, template_content: str) -> List[str]:
        """Extract template variables from Jinja2 template"""
        try:
            ast = self.env.parse(template_content)
            variables = meta.find_undeclared_variables(ast)
            return sorted(list(variables))
        except Exception as e:
            print(f"Error parsing template: {e}")
            return []
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template syntax and structure"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'variables': []
        }
        
        try:
            # Check Jinja2 syntax
            template = Template(template_content)
            validation_result['variables'] = self.get_template_variables(template_content)
            
            # Check for common issues
            if not template_content.strip():
                validation_result['errors'].append("Template is empty")
                validation_result['valid'] = False
            
            # Check for basic email structure
            if 'Dear' not in template_content and 'Hello' not in template_content:
                validation_result['warnings'].append("Template might be missing a greeting")
            
            if 'Best regards' not in template_content and 'Sincerely' not in template_content:
                validation_result['warnings'].append("Template might be missing a closing")
                
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Template syntax error: {str(e)}")
        
        return validation_result
    
    def create_template(self, name: str, content: str, description: str = "", 
                       category: str = "general", author: str = "InternMailer") -> bool:
        """Create a new email template"""
        try:
            # Validate template first
            validation = self.validate_template(content)
            if not validation['valid']:
                print(f"Template validation failed: {validation['errors']}")
                return False
            
            # Save template file
            template_path = os.path.join(self.templates_dir, f"{name}.jinja2")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Create metadata
            now = datetime.now().isoformat()
            self.metadata[name] = TemplateMetadata(
                name=name,
                description=description,
                category=category,
                variables=validation['variables'],
                created_date=now,
                last_modified=now,
                author=author,
                version="1.0.0"
            )
            
            self._save_metadata()
            print(f"Template '{name}' created successfully")
            return True
            
        except Exception as e:
            print(f"Error creating template: {e}")
            return False
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Render template with context data"""
        try:
            template = self.env.get_template(f"{template_name}.jinja2")
            return template.render(context)
        except Exception as e:
            print(f"Error rendering template '{template_name}': {e}")
            return None
    
    def preview_template(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """Generate a preview of the template with sample or provided data"""
        if context is None:
            context = self._get_sample_context(template_name)
        
        rendered = self.render_template(template_name, context)
        if rendered:
            return f"=== PREVIEW: {template_name} ===\n\n{rendered}\n\n=== END PREVIEW ==="
        return f"Failed to preview template '{template_name}'"
    
    def _get_sample_context(self, template_name: str) -> Dict[str, Any]:
        """Generate sample context data for template preview"""
        if template_name in self.metadata:
            variables = self.metadata[template_name].variables
        else:
            # Try to get variables from template directly
            try:
                template_content = self._read_template_file(template_name)
                variables = self.get_template_variables(template_content)
            except:
                variables = []
        
        # Generate sample data based on variable names
        sample_context = {}
        for var in variables:
            if 'name' in var.lower():
                sample_context[var] = "Dr. John Smith"
            elif 'university' in var.lower() or 'institution' in var.lower():
                sample_context[var] = "Stanford University"
            elif 'research' in var.lower():
                sample_context[var] = "Machine Learning and Artificial Intelligence"
            elif 'email' in var.lower():
                sample_context[var] = "john.smith@stanford.edu"
            elif 'student' in var.lower():
                sample_context[var] = "Jane Doe"
            elif 'date' in var.lower():
                sample_context[var] = datetime.now().strftime("%B %d, %Y")
            else:
                sample_context[var] = f"[Sample {var}]"
        
        return sample_context
    
    def _read_template_file(self, template_name: str) -> str:
        """Read template file content"""
        template_path = os.path.join(self.templates_dir, f"{template_name}.jinja2")
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with metadata"""
        templates = []
        for name, meta in self.metadata.items():
            templates.append({
                'name': name,
                'description': meta.description,
                'category': meta.category,
                'variables': meta.variables,
                'last_modified': meta.last_modified
            })
        return templates
    
    def get_templates_by_category(self, category: str) -> List[str]:
        """Get template names filtered by category"""
        return [
            name for name, meta in self.metadata.items() 
            if meta.category == category
        ]
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template and its metadata"""
        try:
            template_path = os.path.join(self.templates_dir, f"{template_name}.jinja2")
            if os.path.exists(template_path):
                os.remove(template_path)
            
            if template_name in self.metadata:
                del self.metadata[template_name]
                self._save_metadata()
            
            print(f"Template '{template_name}' deleted successfully")
            return True
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False

# Usage example and testing
if __name__ == "__main__":
    engine = AdvancedTemplateEngine()
    
    # Test template creation and rendering
    print("Advanced Template Engine Demo")
    print("=" * 50)
    
    # List existing templates
    templates = engine.list_templates()
    print(f"Found {len(templates)} existing templates:")
    for template in templates:
        print(f"  - {template['name']} ({template['category']})")
    
    print("\n" + "=" * 50)
