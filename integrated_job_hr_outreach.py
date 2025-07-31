#!/usr/bin/env python3
"""
Integrated Job Application & HR Outreach System
Combines job scraping, HR email discovery, and personalized outreach
"""

import os
import json
import time
import random
from typing import Dict, List
from enhanced_job_scraper import EnhancedJobScraper
from hr_finder import HRFinder
from send_email_with_cv import send_email_with_cv
from dotenv import load_dotenv

load_dotenv()

class IntegratedJobHROutreach:
    def __init__(self):
        self.job_scraper = EnhancedJobScraper()
        self.hr_finder = HRFinder(api_key=os.getenv('HUNTER_API_KEY'))
        
        # CV data from your resume
        self.cv_data = {
            "name": "Anamay Tripathy",
            "email": "tripathy.anamay23@gmail.com",
            "phone": "+91 9877454747",
            "portfolio": "anamay.vercel.app",
            "linkedin": "linkedin.com/in/anamay-tripathy",
            "github": "github.com/Flamechargerr",
            
            "education": "B.Tech in Data Science Engineering, Manipal Institute of Technology (CGPA: 7.6/10)",
            
            "experience": [
                {
                    "title": "Data Analyst Web Development Intern",
                    "company": "Intellect Design Arena",
                    "achievements": [
                        "Automated KPI dashboards using Python and SQL, reducing reporting time by 12+ hours/week",
                        "Developed REST APIs with Node.js, increasing CRM user engagement by 22%",
                        "Built React-based frontend for field agents"
                    ]
                },
                {
                    "title": "Technical Head",
                    "company": "YaanBarpe (Karnataka Govt-incubated startup)",
                    "achievements": [
                        "Engineered multilingual cultural tourism platform for 3,000+ users",
                        "Digitized 40+ heritage stories with CMS integration",
                        "Leading technical development and product strategy"
                    ]
                }
            ],
            
            "projects": [
                {
                    "name": "CrimeConnect",
                    "description": "FBI-inspired case management dashboard reducing processing time by 40%",
                    "tech": "MERN Stack, Supabase"
                },
                {
                    "name": "VARtificial Intelligence",
                    "description": "ML-based football predictor achieving 89% accuracy using XGBoost",
                    "tech": "Python, Pyodide, Flask, React"
                },
                {
                    "name": "HackOps",
                    "description": "Gamified cybersecurity training platform improving user awareness by 35%",
                    "tech": "MERN Stack, Docker"
                }
            ],
            
            "skills": {
                "ml_ai": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "XGBoost", "Machine Learning", "Deep Learning"],
                "data": ["SQL", "Pandas", "NumPy", "Data Analytics", "Data Visualization"],
                "web": ["JavaScript", "React", "Node.js", "Flask", "Express.js", "TailwindCSS"],
                "tools": ["Git", "Docker", "AWS", "GCP", "MongoDB", "Postman"]
            },
            
            "certifications": [
                "Meta Data Analytics", "IBM Generative AI", "Johns Hopkins Machine Learning",
                "Google Data Foundations", "Vskills ML/AI Certification"
            ]
        }

    def generate_personalized_email(self, job_data: Dict, hr_data: Dict = None) -> str:
        """
        Generate highly personalized email based on job and HR data
        """
        company = job_data.get('company', 'Your Company')
        job_title = job_data.get('title', 'Data Science Role')
        job_description = job_data.get('description', '')
        hr_name = hr_data.get('first_name', 'Hiring Manager') if hr_data else 'Hiring Manager'
        
        # Get relevant skills and experience
        relevant_skills = self._get_relevant_skills(job_title, job_description)
        relevant_experience = self._get_relevant_experience(job_title, job_description)
        relevant_projects = self._get_relevant_projects(job_title, job_description)
        
        # Generate greeting
        greeting = f"Dear {hr_name}," if hr_name != 'Hiring Manager' else "Dear Hiring Manager,"
        
        # Generate opening based on role type
        opening = self._generate_opening(company, job_title, job_description)
        
        # Highlight relevant experience
        experience_text = ""
        if relevant_experience:
            exp = relevant_experience[0]
            achievements = "\\n• ".join(exp['achievements'][:2])
            experience_text = f"""
**Professional Experience Highlight:**
**{exp['title']}** at **{exp['company']}**
• {achievements}

This hands-on experience has equipped me with practical skills in data analysis, automation, and software development that directly align with your requirements."""

        # Showcase relevant projects
        project_text = ""
        if relevant_projects:
            top_projects = relevant_projects[:2]
            project_list = []
            for i, project in enumerate(top_projects, 1):
                project_list.append(f"**{i}. {project['name']}** ({project['tech']}): {project['description']}")
            
            project_text = f"""
**Key Projects:**
{chr(10).join(project_list)}

These projects demonstrate my ability to deliver end-to-end solutions with measurable impact."""

        # Skills section
        skills_text = f"""
**Technical Expertise:**
My core competencies include: **{', '.join(relevant_skills[:6])}**, along with experience in cloud platforms (AWS, GCP), containerization (Docker), and modern development workflows.

With certifications from Meta, IBM, and Johns Hopkins in Data Analytics and Machine Learning, I stay current with industry best practices."""

        # Generate compelling closing
        closing = self._generate_closing(company, job_title)
        
        # Combine all sections
        email_body = f"""{greeting}

{opening}
{experience_text}
{project_text}
{skills_text}

{closing}

Best regards,
Anamay Tripathy
📧 {self.cv_data['email']}
📱 {self.cv_data['phone']}
🌐 Portfolio: {self.cv_data['portfolio']}
💼 LinkedIn: {self.cv_data['linkedin']}
🔗 GitHub: {self.cv_data['github']}

---
Attachments: Resume (PDF)"""

        return email_body

    def _get_relevant_skills(self, job_title: str, job_description: str) -> List[str]:
        """Extract relevant skills based on job requirements"""
        job_text = (job_title + " " + job_description).lower()
        
        all_skills = (self.cv_data['skills']['ml_ai'] + 
                     self.cv_data['skills']['data'] + 
                     self.cv_data['skills']['web'] + 
                     self.cv_data['skills']['tools'])
        
        relevant = [skill for skill in all_skills if skill.lower() in job_text]
        
        # Default skills based on job type if no matches
        if not relevant:
            if any(term in job_text for term in ['data scientist', 'ml engineer', 'ai engineer']):
                relevant = ['Python', 'TensorFlow', 'Scikit-learn', 'Machine Learning', 'Pandas']
            elif any(term in job_text for term in ['data analyst', 'business analyst']):
                relevant = ['Python', 'SQL', 'Pandas', 'Data Analytics', 'Data Visualization']
            else:
                relevant = ['Python', 'Machine Learning', 'JavaScript', 'React', 'SQL']
        
        return relevant

    def _get_relevant_experience(self, job_title: str, job_description: str) -> List[Dict]:
        """Get most relevant work experience"""
        job_text = (job_title + " " + job_description).lower()
        
        scored_experience = []
        for exp in self.cv_data['experience']:
            score = 0
            exp_text = (exp['title'] + " " + " ".join(exp['achievements'])).lower()
            
            # Score based on relevance
            if 'data' in job_text and 'data' in exp_text:
                score += 3
            if 'python' in job_text and 'python' in exp_text:
                score += 2
            if 'api' in job_text and 'api' in exp_text:
                score += 2
            if any(term in job_text for term in ['ml', 'machine learning', 'ai']):
                score += 2
            
            scored_experience.append((exp, score))
        
        scored_experience.sort(key=lambda x: x[1], reverse=True)
        return [exp[0] for exp in scored_experience]

    def _get_relevant_projects(self, job_title: str, job_description: str) -> List[Dict]:
        """Get most relevant projects"""
        job_text = (job_title + " " + job_description).lower()
        
        scored_projects = []
        for project in self.cv_data['projects']:
            score = 0
            project_text = (project['name'] + " " + project['description'] + " " + project['tech']).lower()
            
            if 'data' in job_text and 'data' in project_text:
                score += 3
            if 'ml' in job_text and ('ml' in project_text or 'machine learning' in project_text):
                score += 4
            if 'ai' in job_text and 'ai' in project_text:
                score += 3
            if 'web' in job_text and ('react' in project_text or 'web' in project_text):
                score += 2
            
            scored_projects.append((project, score))
        
        scored_projects.sort(key=lambda x: x[1], reverse=True)
        return [proj[0] for proj in scored_projects]

    def _generate_opening(self, company: str, job_title: str, job_description: str) -> str:
        """Generate engaging opening paragraph"""
        openings = [
            f"I hope this message finds you well. I'm writing to express my strong interest in the {job_title} position at {company}. As a passionate Data Science Engineering student at Manipal Institute of Technology with hands-on experience in machine learning and full-stack development, I'm excited about the opportunity to contribute to your innovative team.",
            
            f"I was thrilled to discover the {job_title} opening at {company}. With my background in Data Science Engineering and proven track record of delivering impactful projects (including 89% ML model accuracy and 22% user engagement improvements), I'm confident I can bring significant value to your organization.",
            
            f"Your {job_title} role at {company} caught my attention immediately. As someone who has successfully led technical initiatives that reduced processing times by 40% and built platforms serving 3,000+ users, I'm eager to bring my expertise to help drive {company}'s continued success."
        ]
        return random.choice(openings)

    def _generate_closing(self, company: str, job_title: str) -> str:
        """Generate compelling closing paragraph"""
        closings = [
            f"I'm particularly drawn to {company}'s innovative approach and would love to discuss how my combination of technical skills, proven results, and passion for data-driven solutions can contribute to your team's success. I'm available for an interview at your convenience and am excited about the possibility of joining {company}.",
            
            f"I believe my unique blend of hands-on experience, academic foundation, and demonstrated ability to deliver measurable results makes me an ideal candidate for this {job_title} role. I would welcome the opportunity to discuss how I can help {company} achieve its goals.",
            
            f"Thank you for considering my application. I'm genuinely excited about the opportunity to bring my skills in data science and software development to {company}, and I look forward to discussing how I can contribute to your team's continued success."
        ]
        return random.choice(closings)

    def run_complete_outreach_pipeline(self, max_jobs_per_board: int = 10) -> Dict:
        """
        Run complete job application and HR outreach pipeline
        """
        results = {
            "jobs_found": 0,
            "hr_emails_found": 0,
            "emails_sent": 0,
            "companies_contacted": [],
            "failed_contacts": []
        }
        
        print("🚀 Starting Complete Job Application & HR Outreach Pipeline")
        print("=" * 70)
        
        # Step 1: Scrape jobs
        print("📊 Step 1: Scraping job postings...")
        jobs = self.job_scraper.scrape_all_jobs(max_jobs_per_board=max_jobs_per_board)
        results["jobs_found"] = len(jobs)
        print(f"✅ Found {len(jobs)} job opportunities")
        
        if not jobs:
            print("❌ No jobs found. Exiting pipeline.")
            return results
        
        # Step 2: Process each job and find HR contacts
        print("\\n🔍 Step 2: Finding HR contacts and sending personalized emails...")
        
        for i, job in enumerate(jobs, 1):
            company = job.get('company')
            job_title = job.get('title')
            
            print(f"\\n📧 Processing {i}/{len(jobs)}: {job_title} at {company}")
            
            # Skip if already processed
            if self.hr_finder.is_company_scraped(company):
                print(f"⏭️  Skipping {company} - already processed")
                continue
            
            # Find HR emails
            try:
                hr_emails = self.hr_finder.find_hr_emails(company)
                
                if hr_emails:
                    results["hr_emails_found"] += len(hr_emails)
                    print(f"✅ Found {len(hr_emails)} HR contact(s) at {company}")
                    
                    # Send personalized emails to each HR contact
                    for hr_email_data in hr_emails:
                        hr_email = hr_email_data.get('value')
                        hr_name = hr_email_data.get('first_name', 'Hiring Manager')
                        
                        if hr_email:
                            # Create professor-like data structure for existing email function
                            professor_data = {
                                'name': hr_name,
                                'email': hr_email,
                                'university': company,
                                'research_area': job_title,
                                'job_title': job_title,
                                'job_description': job.get('description', ''),
                                'company': company
                            }
                            
                            # Generate personalized email content
                            personalized_content = self.generate_personalized_email(job, hr_email_data)
                            
                            # Send email using existing function
                            success = send_email_with_cv(professor_data, hr_email)
                            
                            if success:
                                results["emails_sent"] += 1
                                results["companies_contacted"].append({
                                    "company": company,
                                    "job_title": job_title,
                                    "hr_email": hr_email,
                                    "hr_name": hr_name
                                })
                                print(f"✅ Email sent to {hr_name} ({hr_email})")
                            else:
                                results["failed_contacts"].append({
                                    "company": company,
                                    "hr_email": hr_email,
                                    "error": "Email sending failed"
                                })
                                print(f"❌ Failed to send email to {hr_email}")
                            
                            # Add delay to avoid being flagged as spam
                            time.sleep(random.uniform(2, 5))
                    
                else:
                    print(f"⚠️  No HR emails found for {company}")
                    results["failed_contacts"].append({
                        "company": company,
                        "error": "No HR emails found"
                    })
                    
            except Exception as e:
                print(f"❌ Error processing {company}: {str(e)}")
                results["failed_contacts"].append({
                    "company": company,
                    "error": str(e)
                })
        
        # Step 3: Display results
        print("\\n" + "=" * 70)
        print("📊 PIPELINE COMPLETION SUMMARY")
        print("=" * 70)
        print(f"🎯 Jobs Found: {results['jobs_found']}")
        print(f"📧 HR Emails Discovered: {results['hr_emails_found']}")
        print(f"✅ Emails Sent Successfully: {results['emails_sent']}")
        print(f"🏢 Companies Contacted: {len(results['companies_contacted'])}")
        print(f"❌ Failed Contacts: {len(results['failed_contacts'])}")
        
        if results['companies_contacted']:
            print("\\n🎉 Successfully contacted companies:")
            for contact in results['companies_contacted']:
                print(f"  • {contact['company']} ({contact['job_title']}) - {contact['hr_name']}")
        
        # Save results to file
        with open('data/outreach_results.json', 'w') as f:
            json.dump(results, f, indent=4)
        
        print(f"\\n💾 Results saved to data/outreach_results.json")
        return results

def main():
    """Main function to run the integrated outreach system"""
    outreach_system = IntegratedJobHROutreach()
    
    # Run the complete pipeline
    results = outreach_system.run_complete_outreach_pipeline(max_jobs_per_board=5)
    
    print("\\n🎊 Job Application & HR Outreach Pipeline Complete!")

if __name__ == "__main__":
    main()
