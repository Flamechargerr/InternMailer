
import json
from typing import Dict, List

class CVCustomizer:
    def __init__(self, base_cv: Dict):
        """
        Initializes the CV Customizer with a base CV.
        
        Args:
            base_cv (Dict): A dictionary representing the user's base CV.
        """
        self.base_cv = base_cv

    def customize_for_job(self, job_posting: Dict) -> Dict:
        """
        Customizes the CV for a specific job posting.

        This is a placeholder for the actual customization logic. 
        We will implement this to highlight relevant skills and experiences.
        
        Args:
            job_posting (Dict): A dictionary representing the parsed job posting.
        
        Returns:
            Dict: A dictionary representing the customized CV.
        """
        customized_cv = self.base_cv.copy()
        
        # Placeholder logic: Add job title to a new 'objective' section
        job_title = job_posting.get('title', 'the role')
        customized_cv['objective'] = f"To obtain a challenging and rewarding position as {job_title}."
        
        print(f"Customizing CV for: {job_title}")
        return customized_cv


def load_json(file_path: str) -> List[Dict]:
    """
    Loads a list of dictionaries from a JSON file.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_customized_cvs(cvs: List[Dict], filename: str):
    """
    Saves a list of customized CVs to a JSON file.
    """
    with open(filename, 'w') as f:
        json.dump(cvs, f, indent=4)

if __name__ == "__main__":
    # Load the parsed job postings
    parsed_jobs = load_json("data/parsed_jobs.json")
    
    # In a real scenario, you would load your CV from a structured format (e.g., JSON)
    # For now, we'll use a simplified dictionary representation of your CV
    base_cv_data = {
        "name": "Anamay Tripathy",
        "email": "tripathy.anamay23@gmail.com",
        "skills": ["Python", "Data Analysis", "Machine Learning", "AWS"],
        "experience": [
            {
                "title": "Technical Head",
                "company": "YaanBarpe",
                "description": "Led AI-driven system architecture."
            },
            {
                "title": "Data Analyst Intern",
                "company": "Intellect Design Arena",
                "description": "Built ML pipelines and scalable APIs."
            }
        ],
        "projects": [
            {"name": "VARtificial Intelligence", "description": "ML prediction system with 89% accuracy."},
            {"name": "CrimeConnect", "description": "Data-driven case management platform."}
        ]
    }
    
    if parsed_jobs:
        customizer = CVCustomizer(base_cv=base_cv_data)
        customized_resumes = []

        for job in parsed_jobs:
            customized_cv = customizer.customize_for_job(job)
            customized_resumes.append({
                'job_title': job.get('title'),
                'company': job.get('company'),
                'customized_cv': customized_cv
            })
        
        save_customized_cvs(customized_resumes, "data/customized_cvs.json")
        print(f"Successfully generated {len(customized_resumes)} customized CVs.")

