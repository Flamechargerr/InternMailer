import os
import logging
from typing import Dict, Any
from jinja2 import Template
import requests

logging.basicConfig(level=logging.INFO)

def generate_with_ollama(prompt, model='mistral'):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        logging.error(f"Ollama LLM error: {e}")
        return ""

class EmailGenerator:
    """
    Generates personalized email subjects and bodies for professor outreach.
    """
    def __init__(self, student_info: Dict[str, Any], openai_api_key: str = None, use_ollama: bool = False, ollama_model: str = 'mistral'):
        self.student_info = student_info
        self.openai_api_key = openai_api_key
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model

    def generate_subject(self, professor: Dict[str, Any], informal: bool = False) -> str:
        research_area = professor.get('Research Area', professor.get('research_area', 'your research'))
        if informal:
            return f"Excited by your {research_area} – Prospective intern from {self.student_info.get('university', 'MIT India')}"
        else:
            return f"Research Internship Inquiry – {self.student_info.get('name', '')} re: {research_area}"

    def build_prompt(self, professor: Dict[str, Any], informal: bool = False) -> str:
        research_area = professor.get('Research Area', professor.get('research_area', ''))
        professor_name = professor.get('Name', professor.get('name', ''))
        university = professor.get('University', professor.get('university', ''))
        
        return f"""Write a {'slightly informal' if informal else 'professional'} outreach email to Prof. {professor_name} at {university} about their research in {research_area}.

My background: {self.student_info.get('summary', '')}
My skills: {', '.join(self.student_info.get('skills', []))}
My projects: {', '.join(self.student_info.get('projects', []))}
My courses: {', '.join(self.student_info.get('courses', []))}
My email: {self.student_info.get('email', '')}

The email should be concise, polite, and mention why I am interested in their work."""

    def generate_body(self, professor: Dict[str, Any], informal: bool = False) -> str:
        # Offline fallback: use Jinja2 template
        template_path = os.path.join(os.path.dirname(__file__), '../templates/email_template.txt')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
            template = Template(template_str)
            
            # Map professor data to template variables
            prof_data = {
                'name': professor.get('Name', professor.get('name', '')),
                'research_area': professor.get('Research Area', professor.get('research_area', 'your research')),
                'recent_paper': professor.get('recent_paper', ''),
                'university': professor.get('University', professor.get('university', ''))
            }
            
            body = template.render(student=self.student_info, professor=prof_data, informal=informal)
            return body
        except Exception as e:
            logging.error(f"Failed to generate email body: {e}")
            return ""

    def generate_with_llm(self, professor: Dict[str, Any], informal: bool = False, custom_prompt: str = None) -> str:
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.build_prompt(professor, informal)
            
        if self.use_ollama:
            return generate_with_ollama(prompt, self.ollama_model)
        elif self.openai_api_key:
            # TODO: Implement OpenAI GPT-4 logic if needed
            return self.generate_body(professor, informal)
        else:
            return self.generate_body(professor, informal)

# TODO: Add unit tests for EmailGenerator 