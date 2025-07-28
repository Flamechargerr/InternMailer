"""
Rule-based fallback parser for when LLMs are unavailable.
Uses regex patterns and heuristics to extract resume information.
"""

import re
import logging
import time
from typing import Dict, Any, List

from .parser_interface import ResumeParserInterface, ResumeData, ParsingError

logger = logging.getLogger(__name__)


class RuleBasedParser(ResumeParserInterface):
    """Rule-based resume parser using regex patterns and heuristics."""
    
    def __init__(self):
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
        
        # Define common technical keywords
        self.tech_keywords = {
            'languages': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'laravel', 'rails'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'cassandra'],
            'tools': ['git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'tensorflow', 'pytorch'],
            'web': ['html', 'css', 'bootstrap', 'sass', 'webpack', 'nodejs', 'npm', 'yarn']
        }
    
    def parse(self, text: str) -> ResumeData:
        """Parse resume text using rule-based approach."""
        start_time = time.time()
        self._performance_metrics['total_requests'] += 1
        
        try:
            logger.info(f"Parsing resume with rule-based parser (text length: {len(text)} chars)")
            
            # Extract different sections
            skills = self._extract_skills(text)
            projects = self._extract_projects(text)
            courses = self._extract_courses(text)
            experience = self._extract_experience(text)
            summary = self._generate_summary(text, skills, experience)
            domains = self._extract_domains(text, skills)
            
            resume_data = ResumeData(
                skills=skills[:15],  # Limit to top 15
                projects=projects[:8],  # Limit to top 8
                courses=courses[:10],  # Limit to top 10
                experience=experience[:5],  # Limit to top 5
                summary=summary,
                domains=domains[:5]  # Limit to top 5
            )
            
            # Update performance metrics
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=True)
            
            logger.info(f"Successfully parsed resume with rules: {len(skills)} skills, {len(projects)} projects")
            return resume_data
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success=False)
            logger.error(f"Rule-based parsing failed: {e}")
            raise ParsingError(f"Rule-based parsing failed: {str(e)}", "rule_based", e)
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills using patterns and keyword matching."""
        skills = set()
        text_lower = text.lower()
        
        # Look for skills section
        skills_section = self._extract_section(text, ['technical skills', 'skills', 'technologies'])
        if skills_section:
            skills.update(self._parse_skills_section(skills_section))
        
        # Scan entire text for technical keywords
        for category, keywords in self.tech_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    skills.add(keyword.title())
        
        # Look for common skill patterns
        skill_patterns = [
            r'(?i)(python|java|javascript|c\+\+|c#|go|rust|php|ruby|swift|kotlin)',
            r'(?i)(react|angular|vue|django|flask|spring|express|laravel|rails)',
            r'(?i)(mysql|postgresql|mongodb|redis|sqlite|oracle|cassandra)',
            r'(?i)(git|docker|kubernetes|jenkins|aws|azure|gcp|tensorflow|pytorch)',
            r'(?i)(html|css|bootstrap|sass|webpack|node\.?js|npm|yarn)'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str) and len(match) > 1:
                    skills.add(match.title())
        
        # Clean and validate skills
        cleaned_skills = []
        for skill in skills:
            if len(skill) > 1 and skill.isalpha() or '.' in skill or '+' in skill or '#' in skill:
                cleaned_skills.append(skill)
        
        return sorted(list(set(cleaned_skills)))
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract project names using patterns."""
        projects = []
        
        # Look for projects section
        projects_section = self._extract_section(text, ['projects', 'personal projects', 'academic projects'])
        if projects_section:
            projects.extend(self._parse_projects_section(projects_section))
        
        # Look for project patterns in entire text
        project_patterns = [
            r'^([A-Z][A-Za-z\s]{3,30})\s*[-–]\s*([A-Z].*?)$',  # "Project Name – Description"
            r'([A-Z][A-Za-z\s]{3,30})\s*\([^)]+\)',  # "Project Name (technology)"
            r'([A-Z][A-Za-z]{3,20})\s*Web\s*(?:App|Application|Site)',  # "Name Web App"
            r'([A-Z][A-Za-z]{3,20})\s*(?:System|Platform|Tool|App)'  # "Name System"
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    project_name = match[0].strip()
                else:
                    project_name = match.strip()
                
                if len(project_name) > 3 and project_name not in projects:
                    projects.append(project_name)
        
        return projects[:8]
    
    def _extract_courses(self, text: str) -> List[str]:
        """Extract academic courses."""
        courses = []
        
        # Look for education section
        education_section = self._extract_section(text, ['education', 'academic background'])
        if education_section:
            courses.extend(self._parse_courses_section(education_section))
        
        # Look for common course patterns
        course_patterns = [
            r'(?i)courses?:\s*([^.\n]+)',
            r'(?i)relevant\s+coursework:\s*([^.\n]+)',
            r'(?i)(data\s+structures?|algorithms?|machine\s+learning|artificial\s+intelligence)',
            r'(?i)(computer\s+networks?|database\s+systems?|operating\s+systems?)',
            r'(?i)(software\s+engineering|web\s+development|mobile\s+development)'
        ]
        
        for pattern in course_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str):
                    if ':' in match:  # Handle "Courses: course1, course2"
                        course_list = [c.strip() for c in match.split(',')]
                        courses.extend([c for c in course_list if len(c) > 5])
                    else:
                        if len(match) > 5:
                            courses.append(match.title())
        
        return list(set(courses))[:10]
    
    def _extract_experience(self, text: str) -> List[str]:
        """Extract work experience."""
        experience = []
        
        # Look for experience section
        exp_section = self._extract_section(text, ['experience', 'work experience', 'professional experience'])
        if exp_section:
            experience.extend(self._parse_experience_section(exp_section))
        
        # Look for common experience patterns
        exp_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*([A-Z][^–\n]+)\s*[-–]\s*([^.\n]+)',  # "Job Title, Company – Description"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:at|@)\s+([A-Z][^.\n]+)',  # "Job Title at Company"
            r'(Intern|Developer|Analyst|Engineer|Manager)\s+[-–]\s*([A-Z][^.\n]+)'  # "Role – Company"
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        role = match[0].strip()
                        company = match[1].strip()
                        exp_entry = f"{role} at {company}"
                        if exp_entry not in experience:
                            experience.append(exp_entry)
        
        return experience[:5]
    
    def _extract_domains(self, text: str, skills: List[str]) -> List[str]:
        """Extract technical domains based on skills and text analysis."""
        domains = set()
        text_lower = text.lower()
        
        # Domain mapping based on skills
        domain_mappings = {
            'Web Development': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'nodejs'],
            'Machine Learning': ['python', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'],
            'Data Science': ['python', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'jupyter'],
            'Mobile Development': ['swift', 'kotlin', 'react native', 'flutter', 'android', 'ios'],
            'Cloud Computing': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'Database Management': ['mysql', 'postgresql', 'mongodb', 'redis', 'sql'],
            'DevOps': ['docker', 'kubernetes', 'jenkins', 'git', 'ci/cd']
        }
        
        skills_lower = [skill.lower() for skill in skills]
        
        for domain, required_skills in domain_mappings.items():
            if any(skill in skills_lower for skill in required_skills):
                domains.add(domain)
        
        # Look for explicit domain mentions
        domain_keywords = ['machine learning', 'web development', 'data science', 'mobile development', 
                          'cloud computing', 'artificial intelligence', 'cybersecurity', 'blockchain']
        
        for keyword in domain_keywords:
            if keyword in text_lower:
                domains.add(keyword.title())
        
        return list(domains)
    
    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Extract a specific section from resume text."""
        for section_name in section_names:
            # Look for section header
            pattern = rf'(?i)^{re.escape(section_name)}\s*\n(.*?)(?=^[A-Z][^\n]*\n|$)'
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def _parse_skills_section(self, section_text: str) -> List[str]:
        """Parse skills from a skills section."""
        skills = []
        
        # Look for structured format like "Languages: Python, Java"
        category_patterns = [
            r'(?i)languages?:\s*([^.\n]+)',
            r'(?i)frameworks?(?:\s+libraries?)?:\s*([^.\n]+)',
            r'(?i)tools?(?:\s+platforms?)?:\s*([^.\n]+)',
            r'(?i)databases?:\s*([^.\n]+)'
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, section_text)
            for match in matches:
                skill_list = [skill.strip() for skill in re.split(r'[,;]', match)]
                skills.extend([s for s in skill_list if s and len(s) > 1])
        
        return skills
    
    def _parse_projects_section(self, section_text: str) -> List[str]:
        """Parse projects from projects section."""
        projects = []
        
        # Look for project names (usually start of line, capitalized)
        project_lines = re.findall(r'^([A-Z][A-Za-z\s]{3,40}?)(?:\s*[-–]|\s*\()', section_text, re.MULTILINE)
        for project in project_lines:
            clean_project = project.strip()
            if len(clean_project) > 3:
                projects.append(clean_project)
        
        return projects
    
    def _parse_courses_section(self, section_text: str) -> List[str]:
        """Parse courses from education section."""
        courses = []
        
        # Look for courses line
        courses_match = re.search(r'(?i)courses?:\s*([^.\n]+)', section_text)
        if courses_match:
            course_text = courses_match.group(1)
            course_list = [course.strip() for course in re.split(r'[,;]', course_text)]
            courses.extend([c for c in course_list if c and len(c) > 3])
        
        return courses
    
    def _parse_experience_section(self, section_text: str) -> List[str]:
        """Parse experience from experience section."""
        experience = []
        
        # Look for job entries
        job_patterns = [
            r'^([A-Z][^,\n]+),\s*([A-Z][^–\n]+)\s*[-–]',  # "Job Title, Company –"
            r'^([A-Z][A-Za-z\s]+)\s+at\s+([A-Z][^.\n]+)'  # "Job Title at Company"
        ]
        
        for pattern in job_patterns:
            matches = re.findall(pattern, section_text, re.MULTILINE)
            for match in matches:
                if len(match) >= 2:
                    role = match[0].strip()
                    company = match[1].strip()
                    experience.append(f"{role} at {company}")
        
        return experience
    
    def _generate_summary(self, text: str, skills: List[str], experience: List[str]) -> str:
        """Generate a professional summary."""
        # Look for existing summary
        summary_section = self._extract_section(text, ['summary', 'objective', 'profile'])
        if summary_section and len(summary_section) > 20:
            # Take first two sentences
            sentences = re.split(r'[.!?]', summary_section)
            return '. '.join(sentences[:2]).strip() + '.'
        
        # Generate based on skills and experience
        if skills and experience:
            top_skills = ', '.join(skills[:3])
            return f"Technical professional with experience in {top_skills} and demonstrated expertise in software development."
        elif skills:
            top_skills = ', '.join(skills[:3])
            return f"Technical professional with strong skills in {top_skills} and related technologies."
        else:
            return "Technical professional with diverse skills and project experience."
    
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
        return "Rule-Based Parser"
    
    def is_available(self) -> bool:
        """Rule-based parser is always available."""
        return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics."""
        return self._performance_metrics.copy()
