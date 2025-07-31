
import json
import os
from typing import Dict, List

class CVCustomizer:
    def __init__(self, base_cv_file: str = None):
        """
        Initializes the CV Customizer with a base CV.
        
        Args:
            base_cv_file (str): Path to the base CV JSON file, or None to use default.
        """
        if base_cv_file and os.path.exists(base_cv_file):
            with open(base_cv_file, 'r') as f:
                data = json.load(f)
                # Handle both list and dict format
                self.base_cv = data[0] if isinstance(data, list) else data
        else:
            # Default CV data if file doesn't exist
            self.base_cv = {
                "name": "Anamay Tripathy",
                "email": "tripathy.anamay23@gmail.com",
                "phone": "+91-9877454747",
                "skills": ["Python", "JavaScript", "Machine Learning", "Data Science", 
                          "TensorFlow", "PyTorch", "React.js", "Node.js", "AWS", "Docker", "SQL"],
                "experience": [
                    {
                        "title": "Technical Head",
                        "company": "YaanBarpe",
                        "description": "Leading technical development and product strategy for a Karnataka Government-incubated startup."
                    },
                    {
                        "title": "Data Analyst Intern",
                        "company": "Intellect Design Arena",
                        "description": "Automated KPI dashboard systems and developed REST APIs improving user engagement by 22%."
                    }
                ],
                "projects": [
                    {"name": "VARtificial Intelligence", "description": "ML prediction system with 89% accuracy using XGBoost."},
                    {"name": "CrimeConnect", "description": "FBI-inspired case management dashboard with AI-powered analytics."}
                ]
            }
    
    def customize_cv(self, job_posting: Dict) -> Dict:
        """Alias for customize_for_job for backwards compatibility."""
        return self.customize_for_job(job_posting)

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
        
        # Enhance logic to tailor CV to the job posting
        job_title = job_posting.get('title', 'the role').lower()
        required_skills = job_posting.get('description', '').lower()
        
        # Tailor skills
        tailored_skills = [skill for skill in self.base_cv['skills'] if skill.lower() in required_skills]
        customized_cv['skills'] = tailored_skills
        
        # Highlight relevant experience
        relevant_experience = []
        for exp in self.base_cv['experience']:
            if any(skill.lower() in exp['description'].lower() for skill in tailored_skills):
                relevant_experience.append(exp)
        customized_cv['experience'] = relevant_experience

        # Add job title to 'objective'
        customized_cv['objective'] = f"To excel as a {job_title}, leveraging skills in {', '.join(tailored_skills)}."
        
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

