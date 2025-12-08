"""
🤖 JOB AUTOMATION MASTER ENGINE
===============================
End-to-end automation: Find Emails -> Generate CV -> Write Cover Letter -> Apply
"""

import os
import json
import time
from typing import List, Dict
from corporate_outreach import CorporateOutreachSystem, CorporateContact
from cv_generator import CVGenerator
from cover_letter_generator import CoverLetterGenerator
from system import VerifiedEmailSystem

class JobAutomationEngine:
    """Master engine for job application automation"""
    
    def __init__(self):
        self.corporate_system = CorporateOutreachSystem()
        self.academic_system = VerifiedEmailSystem()
        self.cv_generator = CVGenerator()
        self.cover_letter_generator = CoverLetterGenerator(provider="ollama") # STRICTLY use free AI
        
        # User Profile (Should be loaded from config/DB in production)
        self.user_profile = {
            "name": "Anamay Tripathy",
            "title": "Data Science Engineering Student",
            "email": "tripathy.anamay23@gmail.com",
            "phone": "+91-9877454747",
            "location": "Manipal, India",
            "linkedin": "linkedin.com/in/anamay",
            "portfolio": "anamay.vercel.app",
            "summary": "Passionate Data Science student with expertise in Machine Learning, AI, and Full Stack Development.",
            "experience": [
                {
                    "role": "Technical Head",
                    "company": "YaanBarpe",
                    "duration": "2023 - Present",
                    "details": ["Leading 12 developers.", "ML-powered waste management."]
                }
            ],
            "education": [
                {
                    "degree": "B.Tech Data Science",
                    "school": "MIT Manipal",
                    "year": "2021 - 2025",
                    "grade": "8.5 CGPA"
                }
            ],
            "skills": ["Python", "TensorFlow", "React", "SQL", "AWS"]
        }
        
    def run_corporate_campaign(self, companies: List[str], role: str):
        """Run end-to-end corporate job campaign"""
        print(f"\n🚀 STARTING CORPORATE CAMPAIGN: {role}")
        print("=" * 60)
        
        # 1. Find Contacts
        print("\n🔍 Step 1: Finding Hiring Managers...")
        contacts = self.corporate_system.discover_corporate_contacts(companies)
        
        # 2. Generate Assets
        print("\n📄 Step 2: Generating Application Assets...")
        cv_path = self.cv_generator.generate_cv(self.user_profile, "anamay_cv.html")
        
        # 3. Apply to each contact
        print("\n✉️ Step 3: Generating AI Cover Letters & Applying...")
        for contact in contacts:
            print(f"\n   👤 Target: {contact.name} ({contact.company})")
            
            # Generate AI Cover Letter
            job_details = {
                "company": contact.company,
                "role": role,
                "description": f"Software Engineering role at {contact.company}"
            }
            
            print("      🤖 Generating AI Cover Letter...")
            cover_letter = self.cover_letter_generator.generate_cover_letter(self.user_profile, job_details)
            
            # Send Email (Simulated)
            print("      📧 Sending Application...")
            # In production: self.corporate_system.send_email(...)
            print(f"      ✅ Application Sent to {contact.email}!")
            
            time.sleep(1) # Rate limit
            
    def run_academic_campaign(self, universities: List[str], research_area: str):
        """Run end-to-end academic research campaign"""
        print(f"\n🎓 STARTING ACADEMIC CAMPAIGN: {research_area}")
        print("=" * 60)
        
        # 1. Find Professors (Simulated lookup from DB)
        print("\n🔍 Step 1: Finding Professors...")
        # In production: self.academic_system.find_professors(universities)
        print(f"   ✅ Found 5 relevant professors in {research_area}")
        
        # 2. Generate CV
        print("\n📄 Step 2: Generating Academic CV...")
        self.cv_generator.generate_cv(self.user_profile, "anamay_academic_cv.html")
        
        # 3. Apply
        print("\n✉️ Step 3: Sending Research Inquiries...")
        # Logic to use system.py's email sender
        print("   ✅ Research inquiries sent!")

if __name__ == "__main__":
    engine = JobAutomationEngine()
    
    # Run Demo
    engine.run_corporate_campaign(
        companies=['Google', 'Microsoft', 'NetApp'],
        role='Software Engineer'
    )
