import json
import os
from datetime import datetime


class HREmailGenerator:
    """Generate personalized HR application emails."""
    
    def __init__(self):
        self.template = self._load_template()
    
    def _load_template(self):
        """Load email template or use default."""
        template_path = "templates/hr_email_template.txt"
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Default template if file doesn't exist
        return """Subject: Application for {job_title} Position at {company}

Dear Hiring Manager,

I hope this message finds you well. I am writing to express my strong interest in the {job_title} position at {company}.

With my background in {skills}, I believe I would be a valuable addition to your team. My experience includes:

{experience_summary}

I have attached my customized resume for your review. I would welcome the opportunity to discuss how my skills and enthusiasm can contribute to {company}'s continued success.

Thank you for considering my application. I look forward to hearing from you soon.

Best regards,
[Your Name]
[Your Contact Information]"""
    
    def generate_email(self, job_posting, cv_data):
        """Generate a personalized email based on job posting and CV data."""
        try:
            # Extract relevant information
            job_title = job_posting.get('title', 'Position')
            company = job_posting.get('company', 'Company')
            skills = ', '.join(job_posting.get('skills', ['various technical skills']))
            
            # Generate experience summary from CV
            experience_summary = self._generate_experience_summary(cv_data)
            
            # Fill in the template
            email_content = self.template.format(
                job_title=job_title,
                company=company,
                skills=skills,
                experience_summary=experience_summary
            )
            
            return email_content
            
        except Exception as e:
            # Return a basic email if generation fails
            return f"""Subject: Application for Position at {job_posting.get('company', 'Company')}

Dear Hiring Manager,

I am writing to express my interest in the {job_posting.get('title', 'position')} at {job_posting.get('company', 'your company')}.

I believe my skills and experience make me a strong candidate for this role.

Thank you for your consideration.

Best regards,
[Your Name]"""
    
    def _generate_experience_summary(self, cv_data):
        """Generate a summary of experience from CV data."""
        if not cv_data:
            return "• Strong technical background and passion for learning"
        
        summary_points = []
        
        # Add skills if available
        if cv_data.get('skills'):
            skills = cv_data['skills'][:3]  # Top 3 skills
            summary_points.append(f"• Proficiency in {', '.join(skills)}")
        
        # Add experience if available
        if cv_data.get('experience'):
            exp_count = len(cv_data['experience'])
            summary_points.append(f"• {exp_count} relevant experience(s) in the field")
        
        # Add education if available
        if cv_data.get('education'):
            summary_points.append("• Strong educational background")
        
        # Add projects if available
        if cv_data.get('projects'):
            proj_count = len(cv_data['projects'])
            summary_points.append(f"• {proj_count} relevant project(s) completed")
        
        return '\n'.join(summary_points) if summary_points else "• Strong technical background and passion for learning"

    def batch_generate_emails(self, job_postings, cv_data):
        """Generate emails for multiple job postings."""
        emails = []
        
        for job in job_postings:
            email_content = self.generate_email(job, cv_data)
            emails.append({
                'job_title': job.get('title', 'Unknown'),
                'company': job.get('company', 'Unknown'),
                'email_content': email_content,
                'generated_at': datetime.now().isoformat()
            })
        
        return emails
