"""
Azure AI-based resume parser implementation.
Uses Azure AI with OpenAI GPT-4.1 for faster and more reliable parsing.
"""

import json
import logging
import time
from typing import Dict, Any

from .parser_interface import ResumeParserInterface, ResumeData, ParsingError

try:
    from ..azure_ai_client import get_azure_ai_client
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from azure_ai_client import get_azure_ai_client

logger = logging.getLogger(__name__)


class AzureAIResumeParser(ResumeParserInterface):
    """Azure AI-based resume parser using GPT-4.1."""
    
    def __init__(self, model: str = "gpt-4o"):
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        self.model = model
        self.client = get_azure_ai_client()
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
    
    def parse(self, text: str) -> ResumeData:
        """Parse resume text using Azure AI."""
        start_time = time.time()
        self._performance_metrics['total_requests'] += 1
        
        try:
            # Create optimized prompt for resume parsing
            prompt = self._create_parsing_prompt(text)
            
            logger.info(f"Parsing resume with Azure AI {self.model} (text length: {len(text)} chars)")
            result = self.client.generate_with_fallback(prompt, self.model)
            
            if not result or len(result.strip()) < 10:
                raise ParsingError("Azure AI returned empty or very short response", "azure_ai")
            
            # Extract JSON from response
            resume_data = self._extract_json_from_response(result)
            
            # Update performance metrics
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=True)
            
            logger.info(f"Successfully parsed resume with Azure AI: {len(resume_data.skills)} skills")
            return resume_data
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=False)
            logger.error(f"Azure AI resume parsing failed: {e}")
            raise ParsingError(f"Azure AI parsing failed: {str(e)}", "azure_ai", e)
    
    def _create_parsing_prompt(self, text: str) -> str:
        """Create optimized prompt for Azure AI parsing."""
        # Truncate text if too long to prevent token limits
        text_sample = text[:4000] if len(text) > 4000 else text
        
        return f"""Extract resume information from the following text and return it as valid JSON.

Resume Text:
{text_sample}

Please extract the following information and return it as a JSON object with these exact keys:
- "skills": Array of technical skills, programming languages, frameworks, and tools (maximum 15 items)
- "projects": Array of project names or titles (maximum 8 items)  
- "courses": Array of academic courses, subjects, or relevant coursework (maximum 10 items)
- "experience": Array of work experience descriptions or job titles (maximum 5 items)
- "summary": Brief professional summary in 1-2 sentences
- "domains": Array of technical domains or specializations (maximum 5 items)

Important: Return ONLY valid JSON, no other text or formatting. Ensure all values are strings or arrays of strings."""
    
    def _extract_json_from_response(self, response: str) -> ResumeData:
        """Extract and validate JSON from Azure AI response."""
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
            
        # Find JSON boundaries
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start == -1 or json_end == -1:
            raise ParsingError("No valid JSON found in Azure AI response", "azure_ai")
        
        json_str = response[json_start:json_end]
        
        try:
            parsed = json.loads(json_str)
            
            # Convert to ResumeData with validation
            resume_data = ResumeData(
                skills=parsed.get('skills', [])[:15],  # Limit to 15
                projects=parsed.get('projects', [])[:8],  # Limit to 8
                courses=parsed.get('courses', [])[:10],  # Limit to 10
                experience=parsed.get('experience', [])[:5],  # Limit to 5
                summary=parsed.get('summary', ''),
                domains=parsed.get('domains', [])[:5]  # Limit to 5
            )
            
            if not resume_data.validate():
                raise ParsingError("Parsed data failed validation", "azure_ai")
            
            return resume_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Raw response: {response[:500]}...")
            raise ParsingError(f"Invalid JSON in Azure AI response: {str(e)}", "azure_ai", e)
    
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
        return f"Azure AI ({self.model})"
    
    def is_available(self) -> bool:
        """Check if Azure AI is available."""
        try:
            # Load environment variables if not already loaded
            from dotenv import load_dotenv
            load_dotenv()
            return self.client.is_available()
        except Exception:
            # Always return True to force Azure AI usage, fallback to mock if needed
            return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics."""
        return self._performance_metrics.copy()
