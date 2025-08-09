"""
CV Customizer Module

This module customizes a CV for each job application
using a base CV and modifying it with keywords
from the job posting.
"""

import json
import os
from typing import Dict, Any


class CVCustomizer:
    """Customize CV for job applications based on job details."""
    
    def __init__(self, base_cv_path: str):
        """Initialize the CV customizer with the base CV settings."""
        self.base_cv_path = base_cv_path
        self.base_cv = self._load_base_cv()
    
    def _load_base_cv(self) - Dict[str, Any]:
        """Load the base CV from a JSON file."""
        if not os.path.exists(self.base_cv_path):
            raise FileNotFoundError(f"Base CV file not found: {self.base_cv_path}")
        
        with open(self.base_cv_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def customize_cv(self, job_data: Dict[str, Any]) - Dict[str, Any]:
        """
        Customize the CV using the job description, role, and required skills.
        
        Args:
            job_data: Parsed job data with title, skills, company, etc.
        
        Returns:
            Customized CV with job-relevant details included.
        """
        customized_cv = self.base_cv.copy()
        
        # Update job title and company details
        customized_cv["job_title"] = job_data.get("title", "N/A")
        customized_cv["company"] = job_data.get("company", "N/A")
        customized_cv["location"] = job_data.get("location", "N/A")
        
        # Add relevant skills to the CV
        relevant_skills = job_data.get("skills", [])
        customized_cv["skills"] = list(set(customized_cv.get("skills", []) + relevant_skills))
        
        # Add job-specific sections or achievements if available
        job_specific_description = (
            f"Applying for a {job_data.get('title', 'role')} position at {job_data.get('company', 'Unknown Company')} with a focus on "
            f"using skills in {', '.join(relevant_skills) if relevant_skills else 'key areas'} to contribute effectively to projects."
        )
        customized_cv["job_specific_description"] = job_specific_description
        
        return customized_cv


def main():
    """Simple test for CV Customizer."""
    customizer = CVCustomizer(base_cv_path="data/base_cv.json")
    job_posting = {
        "title": "Machine Learning Engineer",
        "company": "Innovate Corp",
        "location": "San Francisco",
        "description": "We are seeking a Machine Learning Engineer with strong skills in Python, TensorFlow, and cloud platforms.",
        "skills": ["Python", "TensorFlow", "AWS"]
    }
    
    customized_cv = customizer.customize_cv(job_posting)
    print("Customized CV:", json.dumps(customized_cv, indent=4))


if __name__ == "__main__":
    main()

