import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    skills: List[str]
    contact_email: Optional[str] = None
    apply_url: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None  # remote, onsite, hybrid
    
    def to_dict(self):
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'requirements': self.requirements,
            'skills': self.skills,
            'contact_email': self.contact_email,
            'apply_url': self.apply_url,
            'salary': self.salary,
            'job_type': self.job_type
        }

class JobParser:
    def __init__(self):
        # Common technical skills to look for
        self.tech_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 
            'machine learning', 'ai', 'tensorflow', 'pytorch', 'docker',
            'kubernetes', 'aws', 'azure', 'gcp', 'data science', 'analytics',
            'pandas', 'numpy', 'scikit-learn', 'mongodb', 'postgresql',
            'git', 'agile', 'scrum', 'rest api', 'microservices'
        ]
        
        # Email regex pattern
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from job description."""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.tech_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements from description."""
        # Look for bullet points, numbered lists, or requirement sections
        requirements = []
        
        # Split by common requirement indicators
        patterns = [
            r'requirements?:?\s*(.+?)(?:responsibilities?:|skills?:|$)',
            r'qualifications?:?\s*(.+?)(?:responsibilities?:|skills?:|$)',
            r'must have:?\s*(.+?)(?:nice to have:|preferred:|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or new lines
                req_items = re.split(r'[•\-\*\n]', match)
                requirements.extend([req.strip() for req in req_items if req.strip()])
        
        return requirements[:10]  # Limit to top 10 requirements
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from job posting."""
        matches = re.findall(self.email_pattern, text)
        return matches[0] if matches else None
    
    def determine_job_type(self, text: str, location: str = "") -> str:
        """Determine if job is remote, onsite, or hybrid."""
        text_combined = (text + " " + location).lower()
        
        if any(keyword in text_combined for keyword in ['remote', 'work from home', 'distributed']):
            return 'remote'
        elif any(keyword in text_combined for keyword in ['hybrid', 'flexible']):
            return 'hybrid'
        else:
            return 'onsite'
    
    def parse_job_posting(self, raw_job_data: Dict) -> JobPosting:
        """Parse raw job data into structured JobPosting object."""
        description = raw_job_data.get('description', '')
        
        return JobPosting(
            title=raw_job_data.get('title', ''),
            company=raw_job_data.get('company', ''),
            location=raw_job_data.get('location', ''),
            description=description,
            requirements=self.extract_requirements(description),
            skills=self.extract_skills(description),
            contact_email=self.extract_email(description),
            apply_url=raw_job_data.get('apply_url'),
            salary=raw_job_data.get('salary'),
            job_type=self.determine_job_type(description, raw_job_data.get('location', ''))
        )
    
    def parse_job(self, raw_job_data: Dict) -> Dict:
        """Parse raw job data and return as dictionary (backwards compatibility)."""
        job_posting = self.parse_job_posting(raw_job_data)
        return job_posting.to_dict()

def process_job_postings(input_file: str, output_file: str):
    """Process raw job postings and save parsed results."""
    parser = JobParser()
    
    try:
        with open(input_file, 'r') as f:
            raw_jobs = json.load(f)
        
        parsed_jobs = []
        for job_data in raw_jobs:
            parsed_job = parser.parse_job_posting(job_data)
            parsed_jobs.append(parsed_job.to_dict())
        
        with open(output_file, 'w') as f:
            json.dump(parsed_jobs, f, indent=4)
        
        print(f"Successfully parsed {len(parsed_jobs)} job postings and saved to {output_file}")
        
    except FileNotFoundError:
        print(f"Input file {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error parsing JSON from {input_file}")

if __name__ == "__main__":
    # Process job postings from scraper output
    process_job_postings("data/job_postings.json", "data/parsed_jobs.json")
