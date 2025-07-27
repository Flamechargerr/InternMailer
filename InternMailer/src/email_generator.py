import os
import logging
import time
import json
import hashlib
from typing import Dict, Any
from jinja2 import Template
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)

class OllamaClient:
    """
    Enhanced Ollama client with timeout fixes, streaming, retries, and connection pooling.
    """
    def __init__(self, base_url="http://localhost:11434", timeout=180):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.cache = {}  # Cache for identical resume segments
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,  # 2, 4, 8 seconds
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=1, pool_maxsize=1)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set connection timeout and keep-alive
        self.session.headers.update({
            'Connection': 'keep-alive',
            'Content-Type': 'application/json'
        })
    
    def chunk_prompt(self, prompt: str, max_chunk_size: int = 2000) -> list:
        """
        Chunk long prompts to reduce processing time.
        """
        if len(prompt) <= max_chunk_size:
            return [prompt]
        
        # Try to split at sentence boundaries
        sentences = prompt.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [prompt[:max_chunk_size]]
    
    def generate_with_streaming(self, prompt: str, model: str = 'mistral', use_chunking: bool = True) -> str:
        """
        Generate response with streaming enabled for better timeout handling.
        """
        url = f"{self.base_url}/api/generate"
        
        # Parallel chunk processing
        chunks = self.chunk_prompt(prompt, 1500) if use_chunking and len(prompt) > 2000 else [prompt]
        logging.info(f"Chunking prompt into {len(chunks)} parts")
        
        from concurrent.futures import ThreadPoolExecutor

        def process_chunk(i, chunk):
            payload = {
                "model": model,
                "prompt": chunk,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500,
                }
            }
            try:
                logging.info(f"Processing chunk {i+1}/{len(chunks)}")
                start_time = time.time()
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=(30, self.timeout),
                    stream=True
                )
                response.raise_for_status()
                chunk_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line.decode('utf-8'))
                            if 'response' in json_response:
                                chunk_response += json_response['response']
                            if json_response.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
                duration = time.time() - start_time
                logging.info(f"Chunk {i+1} completed in {duration:.2f}s")
                return chunk_response
            except Exception as e:
                logging.error(f"Error processing chunk {i+1}: {e}")
                return f"[Error - chunk {i+1}]"
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_chunk, i, chunk) for i, chunk in enumerate(chunks)]
            responses = [f.result() for f in futures]

        return " ".join(responses)
    
    def generate_with_fallback(self, prompt: str, model: str = 'mistral') -> str:
        """
        Generate with multiple fallback strategies.
        """
        # Check cache first
        cache_key = hashlib.md5(f"{prompt}_{model}".encode()).hexdigest()
        if cache_key in self.cache:
            logging.info("Using cached response")
            return self.cache[cache_key]
        
        # Strategy 1: Streaming with chunking
        try:
            logging.info("Attempting streaming generation with chunking")
            result = self.generate_with_streaming(prompt, model, use_chunking=True)
            if result and len(result.strip()) > 10 and "[Timeout" not in result and "[Error" not in result:
                self.cache[cache_key] = result  # Cache the result
                return result
        except Exception as e:
            logging.warning(f"Streaming with chunking failed: {e}")
        
        # Strategy 2: Streaming without chunking
        try:
            logging.info("Attempting streaming generation without chunking")
            result = self.generate_with_streaming(prompt, model, use_chunking=False)
            if result and len(result.strip()) > 10 and "[Timeout" not in result and "[Error" not in result:
                self.cache[cache_key] = result  # Cache the result
                return result
        except Exception as e:
            logging.warning(f"Streaming without chunking failed: {e}")
        
        # Strategy 3: Non-streaming with shorter prompt
        try:
            logging.info("Attempting non-streaming generation with shortened prompt")
            short_prompt = prompt[:1000] + "\n\nPlease provide a concise response."
            result = self.generate_non_streaming(short_prompt, model)
            if result and len(result.strip()) > 10:
                self.cache[cache_key] = result  # Cache the result
                return result
        except Exception as e:
            logging.warning(f"Non-streaming fallback failed: {e}")
        
        return ""
    
    def generate_non_streaming(self, prompt: str, model: str = 'mistral') -> str:
        """
        Fallback non-streaming generation with increased timeout.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 300,
            }
        }
        
        response = self.session.post(
            url, 
            json=payload, 
            timeout=(30, 120)  # 2 minute read timeout
        )
        response.raise_for_status()
        return response.json().get("response", "")

# Global client instance
_ollama_client = None

def get_ollama_client():
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

def generate_with_ollama(prompt, model='mistral'):
    """
    Enhanced generate function with comprehensive timeout fixes.
    """
    client = get_ollama_client()
    try:
        return client.generate_with_fallback(prompt, model)
    except Exception as e:
        logging.error(f"All Ollama strategies failed: {e}")
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

    def find_relevant_skills_and_projects(self, professor: Dict[str, Any]) -> Dict[str, Any]:
        """Find skills and projects most relevant to professor's research area"""
        research_area = professor.get('Research Area', professor.get('research_area', '')).lower()
        
        # Define research area keywords and their related skills/projects
        area_mappings = {
            'machine learning': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost', 'Pandas', 'NumPy'],
            'ml': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost', 'Pandas', 'NumPy'],
            'ai': ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Deep Learning'],
            'artificial intelligence': ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Deep Learning'],
            'web': ['JavaScript', 'React', 'Node.js', 'Express.js', 'HTML/CSS', 'MongoDB'],
            'networks': ['Computer Networks', 'Web Security', 'API Development'],
            'security': ['Web Security', 'Information Security', 'HackOps'],
            'data': ['Python', 'Pandas', 'NumPy', 'Data Analytics', 'Data Visualization'],
            'database': ['SQL', 'MongoDB', 'Database Management Systems'],
            'cloud': ['AWS', 'GCP', 'Docker', 'Cloud Computing'],
            'nlp': ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning'],
            'computer vision': ['Python', 'TensorFlow', 'PyTorch', 'Deep Learning'],
            'software engineering': ['Python', 'JavaScript', 'Git', 'Docker'],
            'systems': ['Operating Systems', 'High Performance Computing', 'Docker']
        }
        
        relevant_skills = set()
        relevant_projects = []
        
        # Find relevant skills based on research area
        all_skills = self.student_info.get('skills', [])
        for keyword, skills in area_mappings.items():
            if keyword in research_area:
                for skill in skills:
                    if skill in all_skills:
                        relevant_skills.add(skill)
        
        # If no specific matches, include top general skills
        if not relevant_skills:
            relevant_skills = set(all_skills[:8])
        
        # Find relevant projects
        all_projects = self.student_info.get('projects', [])
        project_keywords = {
            'CrimeConnect': ['web development', 'dashboard', 'data management', 'security'],
            'VARtificial Intelligence': ['machine learning', 'ai', 'prediction', 'data analysis'],
            'HackOps': ['cybersecurity', 'web security', 'gamification', 'education'],
            'Flora Fight Frenzy': ['game development', 'javascript', 'algorithms', 'ui/ux']
        }
        
        for project in all_projects:
            if project in project_keywords:
                keywords = project_keywords[project]
                if any(keyword in research_area for keyword in keywords):
                    relevant_projects.append(project)
        
        # If no relevant projects found, include 1-2 most impressive ones
        if not relevant_projects:
            relevant_projects = all_projects[:2]
        
        return {
            'skills': list(relevant_skills)[:8],  # Limit to top 8 skills
            'projects': relevant_projects[:3]  # Limit to top 3 projects
        }

    def build_prompt(self, professor: Dict[str, Any], informal: bool = False) -> str:
        research_area = professor.get('Research Area', professor.get('research_area', ''))
        professor_name = professor.get('Name', professor.get('name', ''))
        university = professor.get('University', professor.get('university', ''))
        
        # Get relevant skills and projects
        relevant = self.find_relevant_skills_and_projects(professor)
        
        # Get recent experience relevant to the research
        experience = self.student_info.get('experience', [])
        relevant_exp = [exp for exp in experience if any(keyword in exp.lower() for keyword in ['data', 'technical', 'development', 'analyst'])]
        
        # Optimized concise prompt for Gemma3
        tone = 'informal professional' if informal else 'formal'
        return f"""Write {tone} internship email from Anamay to Prof. {professor_name}.

Research: {research_area}
Skills: {', '.join(relevant['skills'][:5])}
Projects: {', '.join(relevant['projects'][:2])}
Background: B.Tech Data Science, MIT India

Requirements:
- Show interest in research
- Highlight relevant skills
- Request internship
- Under 150 words
- Professional tone

Email:"""

    def generate_body(self, professor: Dict[str, Any], informal: bool = False) -> str:
        # Use Jinja2 template with updated format
        template_path = os.path.join(os.path.dirname(__file__), '../../templates/email_template.txt')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
            template = Template(template_str)
            
            # Map professor data to template variables with proper field names
            prof_data = {
                'name': professor.get('Name', professor.get('name', '')),
                'research_area': professor.get('Research Area', professor.get('research_area', 'your research')),
                'university': professor.get('University', professor.get('university', ''))
            }
            
            # Ensure student info has required fields
            student_data = self.student_info.copy()
            if 'season' not in student_data:
                student_data['season'] = 'Winter of 2025 or Summer of 2026'
            
            body = template.render(student=student_data, professor=prof_data, informal=informal)
            return body
        except Exception as e:
            logging.error(f"Failed to generate email body: {e}")
            # Fallback template
            return self.generate_fallback_body(professor)

    def generate_fallback_body(self, professor: Dict[str, Any]) -> str:
        """Generate fallback email body when template fails"""
        prof_name = professor.get('Name', professor.get('name', 'Professor'))
        research_area = professor.get('Research Area', professor.get('research_area', 'your research'))
        university = professor.get('University', professor.get('university', 'your university'))
        student_name = self.student_info.get('name', 'Anamay Tripathy')
        student_email = self.student_info.get('email', 'tripathy.anamay23@gmail.com')
        skills = self.student_info.get('skills', ['Python', 'Machine Learning', 'React.js', 'Node.js'])
        
        return f"""Dear Prof. {prof_name},

I hope this message finds you well.

My name is {student_name}, and I'm currently in my third year of a BTech in Data Science at MIT Manipal, India. I currently hold a CGPA of 7.6, which, under our institute's rigorous evaluation system, is considered a solid performance and one that I am confident will continue to improve in the coming semesters.

I'm writing to express my keen interest in contributing to your research group at {university} through a remote or on-site research internship, ideally during the Winter of 2025 or Summer of 2026. I'm deeply interested in {research_area.lower()}, data science, and artificial intelligence, and I'm actively preparing to pursue higher studies in this field.

A brief overview of my current experience:

• I'm interning at Intellect Design Arena, Mumbai, working on data analytics and web development.

• I serve as the Technical Head at YaanBarpe, a startup incubated under the Karnataka Government and E-Cell MIT Manipal, where I lead the product's technical development.

• I have hands-on experience with {', '.join(skills[:5])}, and various data science tools.

Due to financial constraints, I am particularly exploring fully funded or remote opportunities. I would be truly grateful for any chance to learn, contribute, and grow under your guidance — even in a short-term or flexible format.

I have attached my CV for your review. I'd be happy to provide any additional documents or information if needed.

Thank you very much for your time and consideration. I sincerely look forward to the opportunity to connect.

Warm regards,
{student_name}
BTech Data Science | MIT Manipal
📧 {student_email}
📱 +91 98774 54747
🔗 LinkedIn: linkedin.com/in/anamay-tripathy | GitHub: github.com/anamay-tripathy"""

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
