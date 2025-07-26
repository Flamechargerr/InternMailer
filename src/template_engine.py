from jinja2 import Environment, FileSystemLoader
import os

# Setup Jinja2 environment to load templates
env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def render_template(template_name, context):
    """Render the template with the provided context."""
    try:
        template = env.get_template(template_name)
        return template.render(context)
    except Exception as e:
        print(f"An error occurred while rendering the template: {e}")
        return None

# Sample usage
if __name__ == "__main__":
    sample_context = {
        'name': 'John Doe',
        'university': 'Example University',
        'research_area': 'Artificial Intelligence'
    }
    email_content = render_template('sample_template.txt', sample_context)
    if email_content:
        print(email_content)
