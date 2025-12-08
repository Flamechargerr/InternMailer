"""
🆓 FREE AI-POWERED EMAIL GENERATION
=====================================
Uses free APIs and models to generate personalized academic emails
- Hugging Face Inference API (100% FREE)
- No API key required for basic usage
- Fallback to template-based generation if API fails
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

@dataclass
class FreeAIResult:
    """Result from free AI analysis"""
    personalized_intro: str
    paper_mention: str
    research_connection: str
    collaboration_idea: str
    confidence_score: float

class FreeAIEmailGenerator:
    """Free AI-powered email personalization using Hugging Face"""
    
    def __init__(self):
        # Hugging Face free inference endpoint
        self.hf_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        # No API key needed for free tier (rate limited but sufficient)
        # If rate limited, we'll use template-based fallback
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # Simple prompt templates for email generation
        self.prompts = {
            'intro': """Generate a professional, personalized opening paragraph for an academic email.
Professor: {name}
University: {university}
Research Area: {research_area}

Create a 2-3 sentence introduction that:
- Shows genuine interest in their specific research
- Mentions their affiliation
- Sounds natural and professional (not AI-generated)

Output only the paragraph, no extra text:""",

            'paper_mention': """Create a specific mention of a professor's research paper.
Professor: {name}
Research Area: {research_area}
Paper Title (if available): {paper_title}

Generate 1-2 sentences that:
- Reference their work specifically
- Show understanding of the research
- Connect to data science/ML

Output only the sentences:""",

            'alignment': """Explain how a student's background aligns with a professor's research.
Professor Research: {research_area}
Student Background: Data Science Engineering, ML, Python, TensorFlow, Statistical Analysis
Student Experience: YaanBarpe (ML efficiency improvement 34%), Intellect Design Arena (financial data processing)

Generate 2-3 sentences explaining alignment. Be specific:""",

            'collaboration': """Suggest a specific collaboration idea.
Professor Research: {research_area}
Student Skills: ML, Data Science, Python, Statistical Modeling

Generate 1-2 sentences proposing how the student could contribute:"""
        }
    
    def generate_personalized_email(self, professor_name: str, university: str, 
                                   research_area: str, paper_title: str = None) -> FreeAIResult:
        """
        Generate personalized email content using free AI
        Falls back to template if AI fails
        """
        try:
            print(f"🤖 Generating AI-powered content for {professor_name}...")
            
            # Generate each section
            intro = self._generate_section('intro', {
                'name': professor_name,
                'university': university,
                'research_area': research_area
            })
            
            paper_mention = self._generate_section('paper_mention', {
                'name': professor_name,
                'research_area': research_area,
                'paper_title': paper_title or research_area
            })
            
            alignment = self._generate_section('alignment', {
                'research_area': research_area
            })
            
            collaboration = self._generate_section('collaboration', {
                'research_area': research_area
            })
            
            return FreeAIResult(
                personalized_intro=intro,
                paper_mention=paper_mention,
                research_connection=alignment,
                collaboration_idea=collaboration,
                confidence_score=0.8
            )
            
        except Exception as e:
            print(f"⚠️ AI generation failed, using enhanced template: {e}")
            return self._generate_template_based(professor_name, university, research_area, paper_title)
    
    def _generate_section(self, section_type: str, params: Dict) -> str:
        """Generate a section using free AI"""
        try:
            prompt = self.prompts[section_type].format(**params)
            
            # Call Hugging Face free API
            response = requests.post(
                self.hf_api_url,
                headers=self.headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 150,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '').strip()
                    # Clean up the output
                    generated_text = self._clean_ai_output(generated_text)
                    if generated_text and len(generated_text) > 20:
                        return generated_text
            
            # If API fails, use template fallback
            return self._template_fallback(section_type, params)
            
        except Exception as e:
            print(f"⚠️ Section generation failed: {e}")
            return self._template_fallback(section_type, params)
    
    def _clean_ai_output(self, text: str) -> str:
        """Clean AI-generated text"""
        # Remove common AI artifacts
        text = re.sub(r'^(Output:|Response:|Here is|Here\'s|Sure,|Certainly)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n+', ' ', text)
        text = text.strip()
        
        # Remove quotes if the entire text is quoted
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        return text
    
    def _template_fallback(self, section_type: str, params: Dict) -> str:
        """Enhanced template-based fallback"""
        research_area = params.get('research_area', 'computational research')
        name = params.get('name', 'Professor')
        university = params.get('university', '')
        paper_title = params.get('paper_title', research_area)
        
        templates = {
            'intro': [
                f"I am writing to express my strong interest in joining your research group at {university}. Your work in {research_area} has significantly influenced my academic interests, particularly in how it addresses fundamental challenges in the field.",
                f"I hope this email finds you well. As a Data Science Engineering student at MIT Manipal, I have been following your research in {research_area} with great interest. The innovative approaches your group has developed align closely with my academic and research goals.",
                f"I am reaching out to inquire about research opportunities in your group at {university}. Your contributions to {research_area} represent exactly the type of impactful, rigorous research I aspire to be part of."
            ],
            'paper_mention': [
                f"Your research on {paper_title} particularly resonates with me. The methodological rigor and practical implications of this work demonstrate the kind of research excellence I aim to contribute to.",
                f"I was particularly drawn to your work on {paper_title}, as it addresses critical challenges in {research_area} that I have encountered in my own projects.",
                f"The innovative approach you've taken in your research on {paper_title} aligns perfectly with my interests in applying machine learning to real-world problems."
            ],
            'alignment': [
                f"My background in machine learning and data science, combined with hands-on experience leading ML projects at YaanBarpe (achieving 34% efficiency improvements) and optimizing large-scale data processing at Intellect Design Arena, has prepared me to contribute meaningfully to research in {research_area}.",
                f"Through my work at YaanBarpe, where I led ML-powered solutions, and my internship at Intellect Design Arena optimizing financial data pipelines, I have developed strong technical skills in Python, TensorFlow, and statistical modeling that directly apply to {research_area}.",
                f"My experience building scalable ML systems and working with large datasets (2.3M+ daily transactions) has given me practical insights that complement the theoretical foundations of {research_area} research."
            ],
            'collaboration': [
                f"I believe my experience in deploying ML models to production and optimizing computational efficiency could contribute to extending your {research_area} research to real-world applications.",
                f"Given my background in data-driven optimization and machine learning deployment, I see strong potential to contribute to your ongoing projects in {research_area}, particularly in areas requiring large-scale data analysis.",
                f"My skills in statistical modeling and ML pipeline development could support your research objectives in {research_area}, especially in projects involving empirical validation or system optimization."
            ]
        }
        
        # Deterministic selection based on professor name
        template_list = templates.get(section_type, templates['intro'])
        index = hash(name + section_type) % len(template_list)
        return template_list[index]
    
    def _generate_template_based(self, professor_name: str, university: str, 
                                 research_area: str, paper_title: str = None) -> FreeAIResult:
        """Generate content using enhanced templates"""
        return FreeAIResult(
            personalized_intro=self._template_fallback('intro', {
                'name': professor_name,
                'university': university,
                'research_area': research_area
            }),
            paper_mention=self._template_fallback('paper_mention', {
                'name': professor_name,
                'research_area': research_area,
                'paper_title': paper_title or research_area
            }),
            research_connection=self._template_fallback('alignment', {
                'research_area': research_area
            }),
            collaboration_idea=self._template_fallback('collaboration', {
                'research_area': research_area
            }),
            confidence_score=0.7  # Slightly lower for template-based
        )

def get_free_ai_generator():
    """Get free AI email generator instance"""
    return FreeAIEmailGenerator()
