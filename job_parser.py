"""
Job Parser Module

This module parses job postings and extracts relevant information
like required skills, experience, company details, etc.
"""

import re
import json
from typing import Dict, List, Any
from datetime import datetime


class JobParser:
    """Parse job postings and extract structured information."""
    
    def __init__(self):
        """Initialize the job parser with common skill patterns."""
        self.skill_patterns = [
            r'\bpython\b',
            r'\bjava\b',
            r'\bjavascript\b',
            r'\bmachine learning\b',
            r'\bdata science\b',
            r'\bsql\b',
            r'\breact\b',
            r'\bangular\b',
            r'\bnode\.?js\b',
            r'\baws\b',
            r'\bdocker\b',
            r'\bkubernetes\b',
            r'\bgit\b',
            r'\bagile\b',
            r'\bscrum\b'
        ]
        
        self.experience_patterns = [
            r'(\d+)[\s\-]*(?:years?|yrs?)\s+(?:of\s+)?experience',
            r'(\d+)\+\s*years?',
            r'minimum\s+(\d+)\s+years?',
            r'at least\s+(\d+)\s+years?'
        ]
    
    def parse_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a job posting and extract structured information.
        
        Args:
            job_data: Raw job data containing title, description, company, etc.
        
        Returns:
            Parsed job information with extracted skills, requirements, etc.
        """
        parsed_job = {
            'title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'location': job_data.get('location', ''),
            'description': job_data.get('description', ''),
            'url': job_data.get('url', ''),
            'posted_date': job_data.get('posted_date', ''),
            'parsed_at': datetime.now().isoformat(),
            'skills': self._extract_skills(job_data.get('description', '')),
            'experience_required': self._extract_experience(job_data.get('description', '')),
            'requirements': self._extract_requirements(job_data.get('description', '')),
            'job_type': self._classify_job_type(job_data),
            'salary_range': self._extract_salary(job_data.get('description', '')),
        }
        
        return parsed_job
    
    def _extract_skills(self, description: str) -> List[str]:
        """Extract technical skills from job description."""
        if not description:
            return []
        
        description_lower = description.lower()
        found_skills = []
        
        for pattern in self.skill_patterns:
            matches = re.findall(pattern, description_lower, re.IGNORECASE)
            found_skills.extend(matches)
        
        # Remove duplicates and clean up
        unique_skills = list(set(found_skills))
        return [skill.strip().title() for skill in unique_skills if skill.strip()]
    
    def _extract_experience(self, description: str) -> str:
        """Extract experience requirements from job description."""
        if not description:
            return "Not specified"
        
        for pattern in self.experience_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                years = match.group(1)
                return f"{years} years"
        
        # Check for entry level indicators
        entry_level_patterns = [
            r'\bentry[\s\-]level\b',
            r'\bintern\b',
            r'\bgraduate\b',
            r'\bjunior\b',
            r'\bno experience\b'
        ]
        
        for pattern in entry_level_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return "Entry level"
        
        return "Not specified"
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract job requirements from description."""
        if not description:
            return []
        
        requirements = []
        
        # Look for requirement sections
        requirement_patterns = [
            r'requirements?:([^\.]+(?:\.[^\.]*)*)',
            r'qualifications?:([^\.]+(?:\.[^\.]*)*)',
            r'must have:([^\.]+(?:\.[^\.]*)*)',
            r'you should have:([^\.]+(?:\.[^\.]*)*)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by common delimiters and clean up
                items = re.split(r'[•\n\r\*\-]', match)
                for item in items:
                    cleaned = item.strip()
                    if cleaned and len(cleaned) > 10:  # Filter out very short items
                        requirements.append(cleaned)
        
        return requirements[:10]  # Limit to top 10 requirements
    
    def _classify_job_type(self, job_data: Dict[str, Any]) -> str:
        """Classify the type of job (internship, full-time, part-time, etc.)."""
        title = job_data.get('title', '').lower()
        description = job_data.get('description', '').lower()
        
        if any(word in title for word in ['intern', 'internship']):
            return 'Internship'
        elif any(word in title for word in ['part-time', 'part time']):
            return 'Part-time'
        elif any(word in title for word in ['contract', 'contractor']):
            return 'Contract'
        elif any(word in title for word in ['remote']):
            return 'Remote'
        else:
            return 'Full-time'
    
    def _extract_salary(self, description: str) -> str:
        """Extract salary information from job description."""
        if not description:
            return "Not specified"
        
        salary_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|[-–])\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|\/)\s*(?:year|hour|month)',
            r'(\d{1,3}(?:,\d{3})*)\s*(?:to|[-–])\s*(\d{1,3}(?:,\d{3})*)\s*(?:per|\/)\s*(?:year|hour|month)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Not specified"
    
    def parse_multiple_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse multiple job postings."""
        return [self.parse_job(job) for job in jobs]
    
    def get_parsing_summary(self, parsed_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics of parsed jobs."""
        if not parsed_jobs:
            return {"total_jobs": 0}
        
        all_skills = []
        job_types = []
        companies = []
        
        for job in parsed_jobs:
            all_skills.extend(job.get('skills', []))
            job_types.append(job.get('job_type', 'Unknown'))
            companies.append(job.get('company', 'Unknown'))
        
        # Count occurrences
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        type_counts = {}
        for job_type in job_types:
            type_counts[job_type] = type_counts.get(job_type, 0) + 1
        
        return {
            "total_jobs": len(parsed_jobs),
            "unique_companies": len(set(companies)),
            "most_common_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "job_type_distribution": type_counts,
            "companies": list(set(companies))
        }


def main():
    """Test the job parser with sample data."""
    sample_jobs = [
        {
            "title": "Data Science Intern",
            "company": "Tech Corp",
            "location": "Remote",
            "description": "Looking for a data science intern with Python, SQL, and machine learning experience. Must have 1 year of experience with data analysis."
        },
        {
            "title": "Software Engineer Intern",
            "company": "StartupXYZ",
            "location": "New York",
            "description": "Backend development internship position. Requirements: Java, Spring Boot, Docker. Entry level position perfect for new graduates."
        }
    ]
    
    parser = JobParser()
    parsed_jobs = parser.parse_multiple_jobs(sample_jobs)
    
    print("Parsed Jobs:")
    for job in parsed_jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Skills: {job['skills']}")
        print(f"Experience: {job['experience_required']}")
        print(f"Job Type: {job['job_type']}")
    
    summary = parser.get_parsing_summary(parsed_jobs)
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()
