"""
✍️ AI COVER LETTER GENERATOR
===========================
Generates hyper-personalized cover letters using AI (OpenAI/Ollama).
"""

import os
import json
import requests
from typing import Optional

class CoverLetterGenerator:
    """AI-powered cover letter generator"""
    
    def __init__(self, provider: str = "ollama"):
        self.provider = provider
        # self.openai_key = os.getenv('OPENAI_API_KEY') # Disabled to save costs
        self.ollama_url = "http://localhost:11434/api/generate"
        
    def generate_cover_letter(self, user_data: dict, job_data: dict) -> str:
        """Generate a personalized cover letter"""
        
        prompt = self._create_prompt(user_data, job_data)
        
        if self.provider == "openai" and self.openai_key:
            return self._call_openai(prompt)
        else:
            return self._call_ollama(prompt)
            
    def _create_prompt(self, user_data: dict, job_data: dict) -> str:
        return f"""
        Write a professional and persuasive cover letter for the following role:
        
        CANDIDATE:
        Name: {user_data.get('name')}
        Role: {user_data.get('title')}
        Skills: {', '.join(user_data.get('skills', []))}
        Experience: {json.dumps(user_data.get('experience', []), indent=2)}
        
        JOB DETAILS:
        Company: {job_data.get('company')}
        Role: {job_data.get('role')}
        Description: {job_data.get('description')}
        
        REQUIREMENTS:
        1. Tone: Professional, enthusiastic, and confident.
        2. Structure: Introduction, Why Me (Skill match), Why Company (Culture/Mission), Call to Action.
        3. Specificity: Mention specific projects from my experience that match the job description.
        4. Length: Concise (300-400 words).
        5. Format: Plain text, ready to copy-paste.
        """
        
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert career coach and copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ OpenAI failed: {e}. Falling back to template.")
            return self._fallback_template()

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama API"""
        try:
            payload = {
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.ollama_url, json=payload)
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                print(f"⚠️ Ollama failed: {response.status_code}")
                return self._fallback_template()
        except Exception as e:
            print(f"⚠️ Ollama connection failed: {e}. Is Ollama running?")
            return self._fallback_template()
            
    def _fallback_template(self) -> str:
        return "Dear Hiring Manager,\n\nI am writing to express my interest in this position. [AI Generation Failed - Please Edit Manually]"

if __name__ == "__main__":
    # Test
    generator = CoverLetterGenerator(provider="ollama") # Default to Ollama for local test
    
    user = {
        "name": "Anamay Tripathy",
        "title": "Data Science Student",
        "skills": ["Python", "ML"],
        "experience": [{"role": "Intern", "company": "Intellect", "details": ["Built ML pipelines"]}]
    }
    
    job = {
        "company": "Google",
        "role": "Software Engineer",
        "description": "Looking for Python experts with ML experience."
    }
    
    print(generator.generate_cover_letter(user, job))
