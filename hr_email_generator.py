import json
from typing import Dict, List

class HREmailGenerator:
    def __init__(self):
        self.email_templates = {
            "general_application": """
Subject: Application for {job_title} Position - {applicant_name}

Dear Hiring Manager,

I hope this email finds you well. I am writing to express my strong interest in the {job_title} position at {company_name}.

As a {current_position} with experience in {key_skills}, I am particularly excited about this opportunity because {company_connection}.

Relevant Experience:
{relevant_experience}

Technical Skills:
{technical_skills}

I have attached my resume for your review and would be delighted to discuss how my background and enthusiasm can contribute to {company_name}'s continued success.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
{applicant_name}
{applicant_email}
{applicant_phone}
            """,
            
            "tech_internship": """
Subject: Software Engineering Internship Application - {applicant_name}

Dear {company_name} Recruitment Team,

I am writing to apply for the {job_title} internship position at {company_name}. As a {current_position} specializing in {specialization}, I am eager to contribute to your team and learn from industry experts.

Technical Background:
{technical_background}

Recent Projects:
{recent_projects}

Why {company_name}:
{company_interest}

I have attached my resume and would welcome the opportunity to discuss how my skills and passion for {field} align with your team's goals.

Thank you for considering my application.

Sincerely,
{applicant_name}
{applicant_email}
            """
        }
    
    def generate_email(self, job_posting: Dict, customized_cv: Dict, template_type: str = "general_application") -> str:
        """
        Generates an application email based on job posting and customized CV.
        """
        template = self.email_templates.get(template_type, self.email_templates["general_application"])
        
        # Extract data from CV and job posting
        applicant_name = customized_cv.get('name', 'Your Name')
        applicant_email = customized_cv.get('email', 'your.email@example.com')
        applicant_phone = customized_cv.get('phone', '+91-9877454747')
        
        job_title = job_posting.get('title', 'the position')
        company_name = job_posting.get('company', 'your company')
        
        # Generate dynamic content
        key_skills = ', '.join(customized_cv.get('skills', [])[:3])
        
        # Create relevant experience summary
        experience_list = customized_cv.get('experience', [])
        relevant_experience = '\n'.join([
            f"• {exp.get('title', 'Position')} at {exp.get('company', 'Company')}: {exp.get('description', 'Description')}"
            for exp in experience_list[:2]
        ])
        
        # Create technical skills summary
        technical_skills = ', '.join(customized_cv.get('skills', []))
        
        # Generate recent projects summary
        projects = customized_cv.get('projects', [])
        recent_projects = '\n'.join([
            f"• {proj.get('name', 'Project')}: {proj.get('description', 'Description')}"
            for proj in projects[:2]
        ])
        
        # Create company connection (could be enhanced with AI)
        company_connection = self._generate_company_connection(job_posting, customized_cv)
        
        # Fill template
        email_content = template.format(
            job_title=job_title,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone,
            company_name=company_name,
            current_position="Data Science & Engineering Student",
            specialization="Machine Learning and AI Systems",
            key_skills=key_skills,
            relevant_experience=relevant_experience,
            technical_skills=technical_skills,
            technical_background=self._generate_technical_background(customized_cv),
            recent_projects=recent_projects,
            company_interest=self._generate_company_interest(job_posting),
            field="technology and data science"
        )
        
        return email_content
    
    def _generate_company_connection(self, job_posting: Dict, cv: Dict) -> str:
        """Generate a personalized connection to the company."""
        company = job_posting.get('company', 'the company')
        job_skills = job_posting.get('skills', [])
        cv_skills = cv.get('skills', [])
        
        # Find matching skills
        matching_skills = [skill for skill in job_skills if skill.lower() in [s.lower() for s in cv_skills]]
        
        if matching_skills:
            return f"my experience with {', '.join(matching_skills[:2])} aligns perfectly with your requirements"
        else:
            return f"I admire {company}'s innovative approach and would love to contribute to your team"
    
    def _generate_technical_background(self, cv: Dict) -> str:
        """Generate technical background summary."""
        skills = cv.get('skills', [])
        experience = cv.get('experience', [])
        
        background = f"Proficient in {', '.join(skills[:4])}"
        if experience:
            background += f", with hands-on experience in {experience[0].get('description', 'various projects')}"
        
        return background
    
    def _generate_company_interest(self, job_posting: Dict) -> str:
        """Generate company-specific interest statement."""
        company = job_posting.get('company', 'the company')
        job_type = job_posting.get('job_type', 'onsite')
        
        if job_type == 'remote':
            return f"I'm particularly drawn to {company}'s embrace of remote work culture and innovation in the tech space"
        else:
            return f"I'm excited about the opportunity to work directly with {company}'s talented team and contribute to your mission"

def generate_application_emails(customized_cvs_file: str, output_file: str):
    """
    Generate application emails for all customized CVs.
    """
    try:
        with open(customized_cvs_file, 'r') as f:
            customized_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error loading {customized_cvs_file}")
        return
    
    generator = HREmailGenerator()
    generated_emails = []
    
    for item in customized_data:
        job_title = item.get('job_title', 'Unknown Position')
        company = item.get('company', 'Unknown Company')
        cv = item.get('customized_cv', {})
        
        # Create job posting dict for email generation
        job_posting = {
            'title': job_title,
            'company': company,
            'skills': cv.get('skills', []),
            'job_type': 'remote'  # Default assumption
        }
        
        # Determine template type based on job title
        template_type = "tech_internship" if "intern" in job_title.lower() else "general_application"
        
        email_content = generator.generate_email(job_posting, cv, template_type)
        
        generated_emails.append({
            'job_title': job_title,
            'company': company,
            'email_content': email_content,
            'template_used': template_type
        })
        
        print(f"Generated email for {job_title} at {company}")
    
    # Save generated emails
    with open(output_file, 'w') as f:
        json.dump(generated_emails, f, indent=4)
    
    print(f"Successfully generated {len(generated_emails)} application emails and saved to {output_file}")

if __name__ == "__main__":
    # Generate application emails from customized CVs
    generate_application_emails("data/customized_cvs.json", "data/generated_application_emails.json")
