"""
Complete Email Campaign System for InternMailer
Integrates CSV reading, template engine, and email sending
"""

import pandas as pd
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import random

# Import our custom modules
from template_manager import TemplateManager
from email_sender import EmailSender

# Load environment variables
load_dotenv()

class EmailCampaignSystem:
    """Complete system for running email campaigns from CSV data"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.template_manager = TemplateManager()
        
        # Initialize email sender
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            raise ValueError("Gmail credentials not found in environment variables")
        
        self.email_sender = EmailSender(gmail_user, gmail_password)
        
        # Setup logging
        self.setup_logging()
        
        # Load professor data
        self.professors_df = self.load_csv_data()
        
        # Setup default templates
        self.template_manager.setup_default_templates()
    
    def setup_logging(self):
        """Setup logging for campaign tracking"""
        log_filename = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_csv_data(self) -> pd.DataFrame:
        """Load and validate CSV data"""
        try:
            df = pd.read_csv(self.csv_path)
            self.logger.info(f"Loaded {len(df)} professors from {self.csv_path}")
            
            # Validate required columns
            required_columns = ['Name', 'Email', 'University', 'Research Area']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.warning(f"Missing columns: {missing_columns}")
            
            # Clean and validate emails
            df = df.dropna(subset=['Email'])
            df = df[df['Email'].str.contains('@', na=False)]
            
            self.logger.info(f"After cleaning: {len(df)} valid professor records")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV data: {e}")
            raise
    
    def create_personalized_context(self, professor_row: pd.Series, 
                                  student_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized context for email template"""
        
        # Extract professor information
        professor_name = professor_row.get('Name', '').split()[-1]  # Last name
        university = professor_row.get('University', 'your university')
        research_area = professor_row.get('Research Area', 'your research area')
        
        # Create comprehensive context
        context = {
            # Student information (you can customize these)
            'student_name': student_info.get('name', 'John Doe'),
            'student_year': student_info.get('year', 'Junior'),
            'student_major': student_info.get('major', 'Computer Science'),
            'student_university': student_info.get('university', 'MIT'),
            'student_email': student_info.get('email', 'student@university.edu'),
            'student_phone': student_info.get('phone', '+1-555-0123'),
            'gpa': student_info.get('gpa', '3.8/4.0'),
            'graduation_year': student_info.get('graduation_year', '2026'),
            
            # Professor information
            'professor_name': professor_name,
            'professor_university': university,
            
            # Research information
            'research_area': research_area,
            'specific_research_topic': self.get_specific_research_topic(research_area),
            'career_focus': self.get_career_focus(research_area),
            'specific_research_focus': research_area,
            'specific_project': self.get_specific_project(research_area),
            'specific_interest': self.get_specific_interest(research_area),
            
            # Qualifications (you can customize these based on your profile)
            'relevant_experience': student_info.get('experience', 'strong programming background in Python and machine learning frameworks'),
            'relevant_skills': student_info.get('skills', 'Python, TensorFlow, PyTorch, data analysis, statistical modeling'),
            'relevant_coursework': student_info.get('coursework', 'Machine Learning, Data Structures, Algorithms, Statistics'),
            'research_experience': student_info.get('research_exp', 'undergraduate research projects in computer science'),
            'key_qualifications': student_info.get('qualifications', 'strong programming skills and passion for research'),
            
            # Additional context
            'original_date': datetime.now().strftime("%B %d, %Y"),
            'additional_updates': 'completed additional coursework in advanced topics'
        }
        
        return context
    
    def get_specific_research_topic(self, research_area: str) -> str:
        """Generate specific research topic based on area"""
        topics = {
            'Machine Learning': 'neural network optimization and deep learning architectures',
            'AI': 'artificial intelligence applications and algorithmic improvements',
            'Computer Vision': 'image recognition and computer vision systems',
            'NLP': 'natural language processing and computational linguistics',
            'Robotics': 'autonomous systems and robotic control',
            'Data Science': 'big data analytics and statistical modeling',
            'Security': 'cybersecurity and privacy-preserving technologies',
            'Systems': 'distributed systems and performance optimization',
            'Theory': 'computational complexity and algorithm design'
        }
        
        for key, topic in topics.items():
            if key.lower() in research_area.lower():
                return topic
                
        return 'cutting-edge research methodologies'
    
    def get_career_focus(self, research_area: str) -> str:
        """Generate career focus based on research area"""
        focus_map = {
            'Machine Learning': 'machine learning research and development',
            'AI': 'artificial intelligence and automation',
            'Computer Vision': 'computer vision and image processing',
            'NLP': 'natural language processing and AI language systems',
            'Robotics': 'robotics and autonomous systems',
            'Data Science': 'data science and analytics',
            'Security': 'cybersecurity and information security',
            'Systems': 'systems engineering and software architecture',
            'Theory': 'theoretical computer science and algorithm design'
        }
        
        for key, focus in focus_map.items():
            if key.lower() in research_area.lower():
                return focus
                
        return 'computer science research and innovation'
    
    def get_specific_project(self, research_area: str) -> str:
        """Generate specific project based on research area"""
        projects = {
            'Machine Learning': 'advanced neural network architectures',
            'AI': 'intelligent decision-making systems',
            'Computer Vision': 'real-time image analysis systems',
            'NLP': 'language understanding and generation models',
            'Robotics': 'autonomous navigation systems',
            'Data Science': 'large-scale data processing pipelines',
            'Security': 'privacy-preserving machine learning',
            'Systems': 'high-performance computing systems',
            'Theory': 'algorithmic optimization problems'
        }
        
        for key, project in projects.items():
            if key.lower() in research_area.lower():
                return project
                
        return 'innovative research projects'
    
    def get_specific_interest(self, research_area: str) -> str:
        """Generate specific interest based on research area"""
        interests = {
            'Machine Learning': 'deep learning and neural architecture search',
            'AI': 'artificial general intelligence and reasoning systems',
            'Computer Vision': 'visual understanding and scene analysis',
            'NLP': 'conversational AI and language modeling',
            'Robotics': 'human-robot interaction and learning',
            'Data Science': 'predictive analytics and data mining',
            'Security': 'adversarial machine learning and privacy',
            'Systems': 'scalable distributed computing',
            'Theory': 'complexity theory and optimization'
        }
        
        for key, interest in interests.items():
            if key.lower() in research_area.lower():
                return interest
                
        return 'cutting-edge research methodologies'
    
    def select_best_template(self, research_area: str, professor_info: Dict) -> str:
        """Select the most appropriate template based on professor info"""
        # You can implement logic to choose templates based on criteria
        # For now, we'll use a simple selection based on research area
        
        if 'international' in professor_info.get('university', '').lower():
            return 'international_student'
        elif any(keyword in research_area.lower() for keyword in ['formal', 'theory', 'verification']):
            return 'research_internship_formal'
        else:
            return 'research_inquiry_concise'
    
    def run_campaign(self, student_info: Dict[str, Any], 
                    template_name: str = 'research_inquiry_concise',
                    max_emails: int = 10,
                    delay_seconds: int = 30,
                    dry_run: bool = True):
        """Run the email campaign"""
        
        self.logger.info(f"Starting email campaign - Template: {template_name}, Max emails: {max_emails}")
        
        if dry_run:
            self.logger.info("DRY RUN MODE - No emails will be sent")
        
        sent_count = 0
        failed_count = 0
        
        # Shuffle professors for random selection
        professors_sample = self.professors_df.sample(n=min(max_emails, len(self.professors_df)))
        
        for index, professor in professors_sample.iterrows():
            try:
                # Create personalized context
                context = self.create_personalized_context(professor, student_info)
                
                # Generate email content
                email_content = self.template_manager.generate_email(template_name, context)
                
                if not email_content:
                    self.logger.error(f"Failed to generate email for {professor['Name']}")
                    failed_count += 1
                    continue
                
                # Extract subject from email content (first line)
                lines = email_content.split('\n')
                subject = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject: ') else f"Research Opportunity Inquiry - {student_info['name']}"
                email_body = '\n'.join(lines[2:]) if lines[0].startswith('Subject: ') else email_content
                
                # Log email preview
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"EMAIL TO: {professor['Name']} ({professor['Email']})")
                self.logger.info(f"SUBJECT: {subject}")
                self.logger.info(f"UNIVERSITY: {professor['University']}")
                self.logger.info(f"RESEARCH: {professor['Research Area']}")
                self.logger.info(f"{'='*60}")
                self.logger.info(f"CONTENT:\n{email_body[:500]}...")
                self.logger.info(f"{'='*60}")
                
                # Send email (if not dry run)
                if not dry_run:
                    success = self.email_sender.send_email(
                        professor['Email'], 
                        subject, 
                        email_body
                    )
                    
                    if success:
                        sent_count += 1
                        self.logger.info(f"✓ Email sent to {professor['Name']}")
                    else:
                        failed_count += 1
                        self.logger.error(f"✗ Failed to send email to {professor['Name']}")
                    
                    # Add delay between emails
                    if sent_count < max_emails:
                        self.logger.info(f"Waiting {delay_seconds} seconds before next email...")
                        time.sleep(delay_seconds)
                else:
                    sent_count += 1
                    self.logger.info(f"✓ (DRY RUN) Would send email to {professor['Name']}")
                
            except Exception as e:
                self.logger.error(f"Error processing {professor['Name']}: {e}")
                failed_count += 1
                continue
        
        # Campaign summary
        self.logger.info(f"\n{'='*60}")
        self.logger.info("CAMPAIGN SUMMARY")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Total processed: {sent_count + failed_count}")
        self.logger.info(f"Successfully sent: {sent_count}")
        self.logger.info(f"Failed: {failed_count}")
        self.logger.info(f"Template used: {template_name}")
        if dry_run:
            self.logger.info("Mode: DRY RUN (no emails actually sent)")
        self.logger.info(f"{'='*60}")

# Demo and testing
if __name__ == "__main__":
    # Sample student information (customize this with your details)
    student_info = {
        'name': 'Jane Doe',
        'year': 'Junior',
        'major': 'Computer Science',
        'university': 'MIT',
        'email': 'jane.doe@mit.edu',
        'phone': '+1-555-0123',
        'gpa': '3.85/4.0',
        'graduation_year': '2026',
        'experience': 'two years of intensive programming experience and machine learning projects',
        'skills': 'Python, TensorFlow, PyTorch, scikit-learn, data analysis, statistical modeling',
        'coursework': 'Machine Learning, Deep Learning, Data Structures, Algorithms, Statistics, Linear Algebra',
        'research_exp': 'undergraduate research project on computer vision and natural language processing',
        'qualifications': 'strong programming skills, research experience, and genuine passion for AI research'
    }
    
    # Initialize system
    csv_path = "InternMailer/data/proffesor_verified_emails.csv"
    
    try:
        campaign = EmailCampaignSystem(csv_path)
        
        # Run campaign (dry run first)
        campaign.run_campaign(
            student_info=student_info,
            template_name='research_inquiry_concise',
            max_emails=5,
            delay_seconds=10,
            dry_run=True  # Set to False to actually send emails
        )
        
    except Exception as e:
        print(f"Error running campaign: {e}")
