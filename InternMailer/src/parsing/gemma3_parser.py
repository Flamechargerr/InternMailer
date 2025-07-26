"""
Gemma3-optimized resume parser implementation.
Specifically optimized for Gemma3 model with enhanced prompts and chunking.
"""

import json
import logging
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

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


class Gemma3ResumeParser(ResumeParserInterface):
    """Gemma3-optimized resume parser with advanced features."""
    
    def __init__(self, model: str = "gemma3"):
        self.model = model
        self.client = get_ollama_client()
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0,
            'chunks_processed': 0,
            'cache_hits': 0
        }
    
    def parse(self, text: str) -> ResumeData:
        """Parse resume text using optimized Gemma3 approach."""
        start_time = time.time()
        self._performance_metrics['total_requests'] += 1
        
        try:
            # Use chunked processing for large resumes
            if len(text) > 3000:
                logger.info("Using chunked processing for large resume")
                resume_data = self._parse_with_chunking(text)
            else:
                logger.info("Using direct processing for small resume")
                resume_data = self._parse_direct(text)
            
            # Update performance metrics
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=True)
            
            logger.info(f"Successfully parsed resume with Gemma3: {len(resume_data.skills)} skills")
            return resume_data
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=False)
            logger.error(f"Gemma3 resume parsing failed: {e}")
            raise ParsingError(f"Gemma3 parsing failed: {str(e)}", "gemma3", e)
    
    def _parse_direct(self, text: str) -> ResumeData:
        """Direct parsing for smaller resumes."""
        prompt = self._create_optimized_prompt(text[:2500])
        
        result = self.client.generate_with_fallback(prompt, self.model)
        if not result or len(result.strip()) < 10:
            raise ParsingError("Gemma3 returned empty response", "gemma3")
        
        return self._extract_resume_data(result)
    
    def _parse_with_chunking(self, text: str) -> ResumeData:
        """Parse large resume using intelligent chunking."""
        # Intelligent section-based chunking
        sections = self._chunk_by_sections(text)
        
        # Process chunks in parallel
        results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_section = {
                executor.submit(self._process_section, section_name, section_text): section_name
                for section_name, section_text in sections.items()
            }
            
            for future in as_completed(future_to_section):
                section_name = future_to_section[future]
                try:
                    results[section_name] = future.result()
                    self._performance_metrics['chunks_processed'] += 1
                except Exception as e:
                    logger.warning(f"Failed to process section {section_name}: {e}")
        
        # Merge results
        return self._merge_section_results(results)
    
    def _chunk_by_sections(self, text: str) -> Dict[str, str]:
        """Intelligently chunk resume by sections."""
        import re
        
        sections = {}
        
        # Define section patterns
        section_patterns = {
            'skills': r'(?i)(technical\s+skills?|skills?|technologies?)[\s\n]*(.*?)(?=\n[A-Z][^:\n]*:|$)',
            'projects': r'(?i)(projects?)[\s\n]*(.*?)(?=\n[A-Z][^:\n]*:|$)',
            'experience': r'(?i)(experience|work\s+experience)[\s\n]*(.*?)(?=\n[A-Z][^:\n]*:|$)',
            'education': r'(?i)(education)[\s\n]*(.*?)(?=\n[A-Z][^:\n]*:|$)'
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                sections[section_name] = match.group(0)[:1500]  # Limit section size
        
        # If no sections found, chunk by length
        if not sections:
            chunk_size = 1500
            sections = {
                f'chunk_{i}': text[i:i+chunk_size] 
                for i in range(0, len(text), chunk_size)
            }
        
        return sections
    
    def _process_section(self, section_name: str, section_text: str) -> Dict[str, Any]:
        """Process individual section with targeted prompt."""
        # Create section-specific prompt
        prompt = self._create_section_prompt(section_name, section_text)
        
        # Check cache first
        cache_key = f"{section_name}_{hash(section_text)}"
        if hasattr(self.client, 'cache') and cache_key in self.client.cache:
            self._performance_metrics['cache_hits'] += 1
            result = self.client.cache[cache_key]
        else:
            result = self.client.generate_with_fallback(prompt, self.model)
            if hasattr(self.client, 'cache'):
                self.client.cache[cache_key] = result
        
        if not result:
            return {}
        
        try:
            # Extract JSON from response
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse section {section_name}: {e}")
        
        return {}
    
    def _create_section_prompt(self, section_name: str, section_text: str) -> str:
        """Create targeted prompt for specific section."""
        prompts = {
            'skills': f"""Extract technical skills from this section:

{section_text}

Return JSON: {{"skills": ["skill1", "skill2", ...]}}""",
            
            'projects': f"""Extract project names from this section:

{section_text}

Return JSON: {{"projects": ["project1", "project2", ...]}}""",
            
            'experience': f"""Extract work experience from this section:

{section_text}

Return JSON: {{"experience": ["role1 at company1", "role2 at company2", ...]}}""",
            
            'education': f"""Extract courses and education from this section:

{section_text}

Return JSON: {{"courses": ["course1", "course2", ...], "education": "degree info"}}"""
        }
        
        return prompts.get(section_name, f"""Extract relevant information:

{section_text}

Return JSON with appropriate fields.""")
    
    def _merge_section_results(self, results: Dict[str, Dict[str, Any]]) -> ResumeData:
        """Merge results from different sections."""
        merged = {
            'skills': [],
            'projects': [],
            'courses': [],
            'experience': [],
            'summary': '',
            'domains': []
        }
        
        # Merge all section results
        for section_data in results.values():
            for key, value in section_data.items():
                if key in merged and isinstance(value, list):
                    merged[key].extend(value)
                elif key == 'education' and isinstance(value, str):
                    merged['courses'].extend(self._extract_courses_from_text(value))
                elif key == 'summary' and isinstance(value, str):
                    merged['summary'] = value
        
        # Remove duplicates and clean data
        for key in ['skills', 'projects', 'courses', 'experience', 'domains']:
            if key in merged:
                merged[key] = list(dict.fromkeys(merged[key]))  # Remove duplicates preserving order
                merged[key] = [item for item in merged[key] if item and len(item.strip()) > 2]
        
        # Generate summary if missing
        if not merged['summary']:
            merged['summary'] = self._generate_summary(merged)
        
        return ResumeData(
            skills=merged['skills'][:15],  # Limit to top 15
            projects=merged['projects'][:8],  # Limit to top 8
            courses=merged['courses'][:10],  # Limit to top 10
            experience=merged['experience'][:5],  # Limit to top 5
            summary=merged['summary'],
            domains=merged['domains'][:5]  # Limit to top 5
        )
    
    def _extract_courses_from_text(self, text: str) -> List[str]:
        """Extract course names from education text."""
        import re
        
        # Look for common course patterns
        course_patterns = [
            r'Courses?:\s*([^.\n]+)',
            r'Relevant\s+Coursework:\s*([^.\n]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'  # Title case course names
        ]
        
        courses = []
        for pattern in course_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    # Split by commas and clean
                    course_list = [course.strip() for course in match.split(',')]
                    courses.extend([c for c in course_list if len(c) > 5])
        
        return courses[:10]  # Limit to 10 courses
    
    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """Generate a summary if none exists."""
        skills = data.get('skills', [])
        domains = data.get('domains', [])
        
        if skills:
            top_skills = ', '.join(skills[:3])
            return f"Technical professional with experience in {top_skills} and related technologies."
        elif domains:
            return f"Professional with expertise in {', '.join(domains[:2])}."
        else:
            return "Technical professional with diverse skills and project experience."
    
    def _create_optimized_prompt(self, text: str) -> str:
        """Create optimized prompt for Gemma3."""
        return f"""Parse resume efficiently. Extract key information as JSON.

Text:
{text}

Required JSON format:
{{
  "skills": ["programming language", "framework", "tool"],
  "projects": ["project name 1", "project name 2"],
  "courses": ["course 1", "course 2"],
  "experience": ["role at company"],
  "summary": "brief professional summary",
  "domains": ["technical domain"]
}}

Return only JSON."""
    
    def _extract_resume_data(self, response: str) -> ResumeData:
        """Extract ResumeData from response."""
        # Find JSON boundaries
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start == -1 or json_end == -1:
            raise ParsingError("No valid JSON found in Gemma3 response", "gemma3")
        
        json_str = response[json_start:json_end]
        
        try:
            parsed = json.loads(json_str)
            
            resume_data = ResumeData(
                skills=parsed.get('skills', []),
                projects=parsed.get('projects', []),
                courses=parsed.get('courses', []),
                experience=parsed.get('experience', []),
                summary=parsed.get('summary', ''),
                domains=parsed.get('domains', [])
            )
            
            if not resume_data.validate():
                raise ParsingError("Parsed data failed validation", "gemma3")
            
            return resume_data
            
        except json.JSONDecodeError as e:
            raise ParsingError(f"Invalid JSON in Gemma3 response: {str(e)}", "gemma3", e)
    
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
        return f"Gemma3 (Optimized)"
    
    def is_available(self) -> bool:
        """Check if Gemma3 is available via Ollama."""
        try:
            import requests
            response = requests.get("http://localhost:11434", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics."""
        return self._performance_metrics.copy()
