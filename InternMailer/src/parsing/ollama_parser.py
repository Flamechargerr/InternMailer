"""
Ollama-based resume parser implementation.
Uses Ollama LLM API for intelligent resume parsing.
"""

import json
import logging
import time
from typing import Dict, Any

from .parser_interface import ResumeParserInterface, ResumeData, ParsingError

try:
    from ..email_generator import get_ollama_client
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from email_generator import get_ollama_client

logger = logging.getLogger(__name__)


class OllamaResumeParser(ResumeParserInterface):
    """Ollama-based resume parser using Ollama LLM."""
    
    def __init__(self, model: str = "gemma3"):
        self.model = model
        self.client = get_ollama_client()
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
    
    def parse(self, text: str) -> ResumeData:
        """Parse resume text using Ollama LLM."""
        start_time = time.time()
        self._performance_metrics['total_requests'] += 1
        
        try:
            # Create optimized prompt for resume parsing
            prompt = self._create_parsing_prompt(text)
            
            logger.info(f"Parsing resume with Ollama {self.model} (text length: {len(text)} chars)")
            result = self.client.generate_with_fallback(prompt, self.model)
            
            if not result or len(result.strip()) < 10:
                raise ParsingError("Ollama returned empty or very short response", "ollama")
            
            # Extract JSON from response
            resume_data = self._extract_json_from_response(result)
            
            # Update performance metrics
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=True)
            
            logger.info(f"Successfully parsed resume with Ollama: {len(resume_data.skills)} skills")
            return resume_data
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=False)
            logger.error(f"Ollama resume parsing failed: {e}")
            raise ParsingError(f"Ollama parsing failed: {str(e)}", "ollama", e)
    
    def _create_parsing_prompt(self, text: str) -> str:
        """Create optimized prompt for Ollama parsing."""
        # Truncate text if too long to prevent timeouts
        text_sample = text[:2000] if len(text) > 2000 else text
        
        return f"""Extract resume information as JSON:

Resume Text:
{text_sample}

Return JSON with keys:
- skills: programming languages, frameworks, tools (max 15)
- projects: project names (max 8)  
- courses: academic courses (max 10)
- experience: work experience descriptions (max 5)
- summary: brief professional summary (max 2 sentences)
- domains: technical domains/specializations (max 5)

Only return valid JSON, no other text."""
    
    def _extract_json_from_response(self, response: str) -> ResumeData:
        """Extract and validate JSON from Ollama response."""
        # Find JSON boundaries
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start == -1 or json_end == -1:
            raise ParsingError("No valid JSON found in Ollama response", "ollama")
        
        json_str = response[json_start:json_end]
        
        try:
            parsed = json.loads(json_str)
            
            # Convert to ResumeData with validation
            resume_data = ResumeData(
                skills=parsed.get('skills', []),
                projects=parsed.get('projects', []),
                courses=parsed.get('courses', []),
                experience=parsed.get('experience', []),
                summary=parsed.get('summary', ''),
                domains=parsed.get('domains', [])
            )
            
            if not resume_data.validate():
                raise ParsingError("Parsed data failed validation", "ollama")
            
            return resume_data
            
        except json.JSONDecodeError as e:
            raise ParsingError(f"Invalid JSON in Ollama response: {str(e)}", "ollama", e)
    
    def _update_performance_metrics(self, response_time: float, success: bool):
        """Update performance tracking metrics."""
        if success:
            self._performance_metrics['successful_requests'] += 1
        else:
            self._performance_metrics['failed_requests'] += 1
        
        self._performance_metrics['total_response_time'] += response_time
        self._performance_metrics['avg_response_time'] = (
            self._performance_metrics['total_response_time'] / 
            self._performance_metrics['total_requests']
        )
    
    def get_provider_name(self) -> str:
        """Return provider name."""
        return f"Ollama ({self.model})"
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get("http://localhost:11434", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics."""
        return self._performance_metrics.copy()
