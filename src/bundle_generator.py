"""
Application Bundle Generator for InternMailer
Generates complete application packages with tailored materials
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uuid

# Import InternMailer modules
from resume_tailor import ResumeTailor
from cover_letter_generator import CoverLetterGenerator
from contact_finder import ContactFinder
from prestige_scorer import PrestigeScorer
from ai_matcher import AIJobMatcher
from database_manager import DatabaseManager

class ApplicationBundleGenerator:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.resume_tailor = ResumeTailor()
        self.cover_letter_generator = CoverLetterGenerator()
        self.contact_finder = ContactFinder()
        self.prestige_scorer = PrestigeScorer()
        self.ai_matcher = AIJobMatcher()
        self.db_manager = DatabaseManager()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.warning(f"Could not load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'user_profile': {
                'degree': 'BTech',
                'branch': 'Data Science',
                'semester': 5,
                'level': 'Undergraduate',
                'target_term': 'Summer 2026'
            },
            'preferences': {
                'min_match_score': 0.65,
                'min_prestige_tier': 'Tier 3',
                'max_applications_per_day': 10
            }
        }
    
    def generate_application_bundle(self, job_opportunity: Dict) -> Dict:
        """
        Generate complete application bundle for a job opportunity
        
        Args:
            job_opportunity: Job opportunity data
            
        Returns:
            Complete application bundle in canonical JSON format
        """
        try:
            self.logger.info(f"Generating application bundle for {job_opportunity.get('company')} - {job_opportunity.get('job_title')}")
            
            # Step 1: Enhance job data with additional scoring
            enhanced_job = self._enhance_job_data(job_opportunity)
            
            # Step 2: Generate tailored resume
            tailored_resume = self.resume_tailor.tailor_resume(enhanced_job)
            
            # Step 3: Generate personalized cover letter
            cover_letter = self.cover_letter_generator.generate_cover_letter(enhanced_job)
            
            # Step 4: Find contact information
            contact_info = self.contact_finder.find_contacts(
                enhanced_job.get('company', ''),
                enhanced_job.get('job_title', ''),
                enhanced_job.get('description', '')
            )
            
            # Step 5: Create application bundle
            bundle = self._create_application_bundle(
                enhanced_job,
                tailored_resume,
                cover_letter,
                contact_info
            )
            
            # Step 6: Validate bundle
            if self._validate_bundle(bundle):
                self.logger.info(f"Application bundle generated successfully for {enhanced_job.get('company')}")
                return bundle
            else:
                self.logger.error(f"Bundle validation failed for {enhanced_job.get('company')}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error generating application bundle: {e}")
            return {}
    
    def _enhance_job_data(self, job_opportunity: Dict) -> Dict:
        """Enhance job data with prestige scoring and AI matching"""
        enhanced_job = job_opportunity.copy()
        
        # Add prestige scoring if not present
        if 'prestige_tier' not in enhanced_job or 'prestige_score' not in enhanced_job:
            company = enhanced_job.get('company', '')
            tier, score, reasoning = self.prestige_scorer.get_prestige_score(company)
            enhanced_job.update({
                'prestige_tier': tier,
                'prestige_score': score,
                'prestige_reasoning': reasoning
            })
        
        # Add AI matching score if not present
        if 'match_score' not in enhanced_job:
            match_score = self.ai_matcher.calculate_match_score(enhanced_job)
            enhanced_job['match_score'] = match_score
        
        # Add unique identifier
        if 'id' not in enhanced_job:
            enhanced_job['id'] = str(uuid.uuid4())
        
        # Add timestamp
        enhanced_job['processed_at'] = datetime.now().isoformat()
        
        return enhanced_job
    
    def _create_application_bundle(self, job_data: Dict, resume: Dict, 
                                 cover_letter: Dict, contact: Dict) -> Dict:
        """Create the final application bundle in canonical JSON format"""
        
        # Extract key information
        job_title = job_data.get('job_title', '')
        company = job_data.get('company', '')
        location = job_data.get('location', '')
        apply_link = job_data.get('apply_link', '')
        match_score = job_data.get('match_score', 0.0)
        prestige_tier = job_data.get('prestige_tier', 'Unknown')
        prestige_score = job_data.get('prestige_score', 0.0)
        
        # Get contact email
        contact_email = ''
        if contact and isinstance(contact, dict):
            contact_email = contact.get('email', '')
        elif contact and isinstance(contact, list) and len(contact) > 0:
            contact_email = contact[0].get('email', '')
        
        # Create application bundle
        bundle = {
            "application_bundle": {
                "job_title": job_title,
                "company": company,
                "location": location,
                "contact_email": contact_email,
                "apply_link": apply_link,
                "tailored_resume_text": resume.get('raw_text', ''),
                "cover_letter_text": cover_letter.get('raw_text', ''),
                "match_score": match_score,
                "prestige_tier": prestige_tier,
                "prestige_score": prestige_score,
                "status": "not_applied",
                "created_at": datetime.now().isoformat(),
                "application_id": job_data.get('id', str(uuid.uuid4()))
            },
            "job_details": {
                "job_title": job_title,
                "company": company,
                "location": location,
                "duration": job_data.get('duration', ''),
                "job_type": job_data.get('job_type', 'Internship'),
                "apply_link": apply_link,
                "description": job_data.get('description', ''),
                "eligibility": job_data.get('eligibility', ''),
                "posted_date": job_data.get('posted_date', ''),
                "deadline": job_data.get('deadline', ''),
                "source": job_data.get('source', ''),
                "prestige_tier": prestige_tier,
                "prestige_score": prestige_score,
                "match_score": match_score
            },
            "tailored_resume": {
                "job_title": job_title,
                "company": company,
                "raw_text": resume.get('raw_text', ''),
                "key_modifications": resume.get('key_modifications', []),
                "skills_highlighted": resume.get('skills_highlighted', []),
                "projects_prioritized": resume.get('projects_prioritized', [])
            },
            "cover_letter": {
                "job_title": job_title,
                "company": company,
                "raw_text": cover_letter.get('raw_text', ''),
                "personalization_elements": cover_letter.get('personalization_elements', []),
                "company_research": cover_letter.get('company_research', {}),
                "tone": cover_letter.get('tone', 'professional')
            },
            "contact_info": contact,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0",
                "user_profile": self.config.get('user_profile', {}),
                "processing_notes": []
            }
        }
        
        return bundle
    
    def _validate_bundle(self, bundle: Dict) -> bool:
        """Validate application bundle completeness and quality"""
        try:
            # Check required fields
            required_fields = [
                'application_bundle',
                'job_details',
                'tailored_resume',
                'cover_letter'
            ]
            
            for field in required_fields:
                if field not in bundle:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate application bundle
            app_bundle = bundle['application_bundle']
            required_app_fields = [
                'job_title', 'company', 'tailored_resume_text',
                'cover_letter_text', 'match_score', 'prestige_tier'
            ]
            
            for field in required_app_fields:
                if field not in app_bundle or not app_bundle[field]:
                    self.logger.error(f"Missing or empty application bundle field: {field}")
                    return False
            
            # Validate match score
            match_score = app_bundle.get('match_score', 0)
            if not isinstance(match_score, (int, float)) or match_score < 0 or match_score > 1:
                self.logger.error(f"Invalid match score: {match_score}")
                return False
            
            # Validate prestige tier
            prestige_tier = app_bundle.get('prestige_tier', '')
            valid_tiers = ['Tier 1', 'Tier 2', 'Tier 3', 'Unknown']
            if prestige_tier not in valid_tiers:
                self.logger.error(f"Invalid prestige tier: {prestige_tier}")
                return False
            
            # Validate resume content
            resume_text = app_bundle.get('tailored_resume_text', '')
            if len(resume_text) < 100:
                self.logger.error("Resume text too short")
                return False
            
            # Validate cover letter content
            cover_letter_text = app_bundle.get('cover_letter_text', '')
            if len(cover_letter_text) < 50:
                self.logger.error("Cover letter text too short")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating bundle: {e}")
            return False
    
    def generate_multiple_bundles(self, job_opportunities: List[Dict]) -> List[Dict]:
        """
        Generate application bundles for multiple job opportunities
        
        Args:
            job_opportunities: List of job opportunity data
            
        Returns:
            List of application bundles
        """
        bundles = []
        
        for i, job in enumerate(job_opportunities, 1):
            try:
                self.logger.info(f"Processing job {i}/{len(job_opportunities)}: {job.get('company')}")
                bundle = self.generate_application_bundle(job)
                
                if bundle:
                    bundles.append(bundle)
                else:
                    self.logger.warning(f"Failed to generate bundle for {job.get('company')}")
                    
            except Exception as e:
                self.logger.error(f"Error processing job {i}: {e}")
                continue
        
        self.logger.info(f"Generated {len(bundles)} application bundles from {len(job_opportunities)} opportunities")
        return bundles
    
    def save_bundle_to_database(self, bundle: Dict) -> Optional[str]:
        """Save application bundle to database"""
        try:
            # Extract application data
            app_data = bundle.get('job_details', {})
            app_data.update(bundle.get('application_bundle', {}))
            
            # Save to database
            app_id = self.db_manager.save_application(app_data)
            
            if app_id:
                # Save application materials
                self.db_manager.save_application_materials(
                    app_id,
                    bundle.get('tailored_resume', {}),
                    bundle.get('cover_letter', {})
                )
                
                # Save contact information
                contact_info = bundle.get('contact_info', {})
                if contact_info:
                    self.db_manager.save_contact(contact_info)
                
                self.logger.info(f"Bundle saved to database with ID: {app_id}")
                return app_id
            
        except Exception as e:
            self.logger.error(f"Error saving bundle to database: {e}")
        
        return None
    
    def export_bundle_to_json(self, bundle: Dict, output_path: str = None) -> str:
        """Export application bundle to JSON file"""
        try:
            if not output_path:
                company = bundle.get('application_bundle', {}).get('company', 'unknown')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"data/bundles/application_bundle_{company}_{timestamp}.json"
            
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(bundle, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Bundle exported to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting bundle to JSON: {e}")
            return ""
    
    def get_bundle_summary(self, bundle: Dict) -> Dict:
        """Get summary information from application bundle"""
        app_bundle = bundle.get('application_bundle', {})
        
        return {
            'company': app_bundle.get('company', ''),
            'job_title': app_bundle.get('job_title', ''),
            'location': app_bundle.get('location', ''),
            'match_score': app_bundle.get('match_score', 0),
            'prestige_tier': app_bundle.get('prestige_tier', ''),
            'prestige_score': app_bundle.get('prestige_score', 0),
            'contact_email': app_bundle.get('contact_email', ''),
            'apply_link': app_bundle.get('apply_link', ''),
            'status': app_bundle.get('status', ''),
            'created_at': app_bundle.get('created_at', ''),
            'application_id': app_bundle.get('application_id', '')
        }
    
    def filter_bundles_by_criteria(self, bundles: List[Dict], 
                                 min_match_score: float = 0.65,
                                 min_prestige_tier: str = "Tier 3") -> List[Dict]:
        """Filter application bundles by quality criteria"""
        tier_hierarchy = {"Tier 1": 3, "Tier 2": 2, "Tier 3": 1, "Unknown": 0}
        min_tier_level = tier_hierarchy.get(min_prestige_tier, 0)
        
        filtered_bundles = []
        
        for bundle in bundles:
            app_bundle = bundle.get('application_bundle', {})
            match_score = app_bundle.get('match_score', 0)
            prestige_tier = app_bundle.get('prestige_tier', 'Unknown')
            tier_level = tier_hierarchy.get(prestige_tier, 0)
            
            if match_score >= min_match_score and tier_level >= min_tier_level:
                filtered_bundles.append(bundle)
        
        # Sort by prestige score then match score
        filtered_bundles.sort(
            key=lambda x: (
                x.get('application_bundle', {}).get('prestige_score', 0),
                x.get('application_bundle', {}).get('match_score', 0)
            ),
            reverse=True
        )
        
        return filtered_bundles

if __name__ == "__main__":
    # Test the application bundle generator
    generator = ApplicationBundleGenerator()
    
    # Sample job opportunity
    sample_job = {
        'job_title': 'Machine Learning Intern',
        'company': 'Google',
        'location': 'Mountain View, CA',
        'duration': 'Summer 2026 (12 weeks)',
        'job_type': 'Internship',
        'apply_link': 'https://careers.google.com/jobs/123',
        'description': 'Work on cutting-edge ML projects with our research team...',
        'eligibility': 'Undergraduate students in Computer Science or related fields',
        'posted_date': '2024-12-01',
        'deadline': '2025-02-15',
        'source': 'Google Careers'
    }
    
    # Generate bundle
    print("Generating application bundle...")
    bundle = generator.generate_application_bundle(sample_job)
    
    if bundle:
        print("✅ Application bundle generated successfully")
        summary = generator.get_bundle_summary(bundle)
        print(f"Company: {summary['company']}")
        print(f"Position: {summary['job_title']}")
        print(f"Match Score: {summary['match_score']:.2f}")
        print(f"Prestige: {summary['prestige_tier']}")
    else:
        print("❌ Failed to generate application bundle")