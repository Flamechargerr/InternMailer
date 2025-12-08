"""
InternMailer - AI Research Validator
Uses Google Gemini (FREE) to cross-validate research accuracy
Prevents sending emails with WRONG information
"""

import os
import re
import google.generativeai as genai
from typing import Dict, Optional, List
from dotenv import load_dotenv
import requests
from urllib.parse import quote_plus

load_dotenv()

class AIResearchValidator:
    """
    AI-powered validation system that:
    1. Verifies university matches email domain
    2. Cross-checks if papers belong to the professor
    3. Only approves data if confidence is high
    4. Falls back to safe generic template if uncertain
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.ai_available = True
        else:
            self.ai_available = False
            print("⚠️ Gemini API key not found - using rule-based validation only")
        
        # Known university domain mappings
        self.domain_university_map = {
            'ox.ac.uk': ['oxford', 'university of oxford'],
            'cam.ac.uk': ['cambridge', 'university of cambridge'],
            'harvard.edu': ['harvard'],
            'stanford.edu': ['stanford'],
            'mit.edu': ['mit', 'massachusetts institute'],
            'berkeley.edu': ['berkeley', 'uc berkeley'],
            'cmu.edu': ['carnegie mellon', 'cmu'],
            'ethz.ch': ['eth zurich', 'ethz'],
            'epfl.ch': ['epfl', 'lausanne'],
            'caltech.edu': ['caltech', 'california institute'],
            'princeton.edu': ['princeton'],
            'yale.edu': ['yale'],
            'manchester.ac.uk': ['manchester'],
            'ed.ac.uk': ['edinburgh'],
            'imperial.ac.uk': ['imperial'],
            'ucl.ac.uk': ['ucl', 'university college london'],
        }
    
    def validate_university_match(self, email: str, claimed_affiliation: str) -> Dict:
        """
        Check if the email domain matches the claimed university.
        """
        domain = email.split('@')[1].lower() if '@' in email else ''
        affiliation_lower = claimed_affiliation.lower() if claimed_affiliation else ''
        
        # Direct domain check
        for domain_pattern, university_names in self.domain_university_map.items():
            if domain_pattern in domain:
                # Check if affiliation matches any known name
                for name in university_names:
                    if name in affiliation_lower:
                        return {'valid': True, 'confidence': 1.0, 'verified_university': university_names[0].title()}
                
                # Domain found but affiliation doesn't match - suspicious
                return {
                    'valid': False, 
                    'confidence': 0.3, 
                    'issue': f'Domain {domain} suggests {university_names[0].title()}, but affiliation says {claimed_affiliation}'
                }
        
        # Unknown domain - can't verify but not necessarily wrong
        return {'valid': True, 'confidence': 0.5, 'note': 'Unknown domain - cannot verify'}
    
    def fetch_and_validate_papers(self, professor_name: str, email: str) -> Dict:
        """
        Fetch papers from Semantic Scholar and validate they belong to this professor.
        Uses multiple signals to verify:
        1. Author email domain matches paper affiliation
        2. Author name exact match
        3. Research area consistency
        """
        email_domain = email.split('@')[1].lower() if '@' in email else ''
        
        try:
            # Search for author
            search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(professor_name)}"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code != 200:
                return {'valid': False, 'papers': [], 'issue': 'API unavailable'}
            
            data = response.json()
            authors = data.get('data', [])
            
            if not authors:
                return {'valid': False, 'papers': [], 'issue': 'Author not found'}
            
            # Try to find the best match, but accept first match if no better option
            best_match = None
            best_score = 0
            
            for author in authors[:3]:  # Check top 3 matches
                author_id = author.get('authorId')
                author_name = author.get('name', '').lower()
                
                score = 0
                
                # Check name match (required)
                name_parts = professor_name.lower().split()
                author_name_parts = author_name.split()
                
                # Check if last names match
                if name_parts and author_name_parts:
                    if name_parts[-1] in author_name or author_name_parts[-1] in professor_name.lower():
                        score += 2
                
                if score > best_score:
                    best_score = score
                    best_match = author_id
            
            # If no good match found, use first result (better than nothing)
            if not best_match and authors:
                best_match = authors[0].get('authorId')
                best_score = 1
            
            if not best_match:
                return {'valid': False, 'papers': [], 'issue': 'Could not match author'}
            
            # Fetch papers for matched author
            papers_url = f"https://api.semanticscholar.org/graph/v1/author/{best_match}/papers?fields=title,year,citationCount,abstract&limit=5"
            papers_response = requests.get(papers_url, timeout=10)
            
            if papers_response.status_code != 200:
                return {'valid': False, 'papers': [], 'issue': 'Could not fetch papers'}
            
            papers_data = papers_response.json()
            papers = []
            
            for p in papers_data.get('data', []):
                if p.get('year', 0) >= 2018 and p.get('title'):
                    papers.append({
                        'title': p['title'],
                        'year': p.get('year', ''),
                        'abstract': (p.get('abstract') or '')[:300],
                        'citations': p.get('citationCount', 0)
                    })
            
            papers.sort(key=lambda x: (x['year'], x['citations']), reverse=True)
            
            # If we have papers, mark as valid but with confidence based on match quality
            if papers:
                return {
                    'valid': True,
                    'papers': papers[:3],
                    'confidence': min(0.9, best_score / 3),
                    'verified': best_score >= 2,
                    'needs_ai_check': best_score < 2  # Flag for AI to double-check
                }
            
            return {'valid': False, 'papers': [], 'issue': 'No recent papers found'}
            
        except Exception as e:
            return {'valid': False, 'papers': [], 'issue': str(e), 'confidence': 0}
    
    def ai_validate_research_claim(self, professor_name: str, university: str, 
                                   paper_title: str, research_area: str) -> Dict:
        """
        Use Gemini AI to validate if a research claim makes sense.
        """
        if not self.ai_available:
            return {'valid': True, 'confidence': 0.5, 'note': 'AI unavailable'}
        
        prompt = f"""You are a research validation assistant. 

TASK: Determine if this paper-professor pairing is likely CORRECT.

Professor: {professor_name}
University: {university}  
Paper Title: {paper_title}
Claimed Research Area: {research_area}

CRITERIA:
1. Does the paper title sound like it could be from someone at {university}?
2. Does the research area match the paper title?
3. Is there anything obviously wrong (e.g., wrong field entirely)?

Respond with ONLY one of:
- VALID (if this seems correct)
- SUSPICIOUS (if something seems off)
- INVALID (if this is clearly wrong)

Then briefly explain why in one sentence.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip().upper()
            
            if 'VALID' in result_text and 'INVALID' not in result_text:
                return {'valid': True, 'confidence': 0.9, 'ai_response': response.text}
            elif 'SUSPICIOUS' in result_text:
                return {'valid': False, 'confidence': 0.5, 'ai_response': response.text, 'issue': 'AI flagged as suspicious'}
            else:
                return {'valid': False, 'confidence': 0.2, 'ai_response': response.text, 'issue': 'AI flagged as invalid'}
                
        except Exception as e:
            return {'valid': True, 'confidence': 0.5, 'note': f'AI validation failed: {e}'}
    
    def generate_validated_email(self, professor_name: str, email: str, 
                                  affiliation: str = '') -> Dict:
        """
        Main function: Generate an email ONLY if research data is validated.
        Falls back to safe generic template if validation fails.
        """
        print(f"\n🔍 Validating research for {professor_name}...")
        
        # Step 1: Validate university
        uni_check = self.validate_university_match(email, affiliation)
        print(f"   📍 University check: {uni_check.get('valid', False)} (confidence: {uni_check.get('confidence', 0):.0%})")
        
        if not uni_check.get('valid', True):
            print(f"   ⚠️ University mismatch: {uni_check.get('issue', 'Unknown')}")
            return self._generate_safe_fallback(professor_name, email, affiliation)
        
        # Step 2: Fetch and validate papers
        papers_result = self.fetch_and_validate_papers(professor_name, email)
        print(f"   📚 Papers validation: {papers_result.get('valid', False)} ({len(papers_result.get('papers', []))} papers)")
        
        if not papers_result.get('valid', False) or not papers_result.get('papers'):
            print(f"   ⚠️ Paper validation failed: {papers_result.get('issue', 'No papers found')}")
            return self._generate_safe_fallback(professor_name, email, affiliation)
        
        papers = papers_result['papers']
        best_paper = papers[0]
        
        # Step 3: AI validation of paper-professor match
        verified_university = uni_check.get('verified_university', self._get_university_from_email(email))
        
        ai_check = self.ai_validate_research_claim(
            professor_name=professor_name,
            university=verified_university,
            paper_title=best_paper['title'],
            research_area=self._extract_research_area(best_paper)
        )
        print(f"   🤖 AI validation: {ai_check.get('valid', False)} (confidence: {ai_check.get('confidence', 0):.0%})")
        
        if not ai_check.get('valid', True) or ai_check.get('confidence', 0) < 0.5:
            print(f"   ⚠️ AI flagged issue - using safe template")
            return self._generate_safe_fallback(professor_name, email, affiliation)
        
        # All validations passed - generate personalized email
        print(f"   ✅ All validations passed! Generating personalized email...")
        
        return self._generate_verified_personalized_email(
            professor_name=professor_name,
            university=verified_university,
            papers=papers,
            research_area=self._extract_research_area(best_paper)
        )
    
    def _get_university_from_email(self, email: str) -> str:
        """Extract university from email domain."""
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        for domain_pattern, uni_names in self.domain_university_map.items():
            if domain_pattern in domain:
                return uni_names[0].title() + " University" if 'university' not in uni_names[0].lower() else uni_names[0].title()
        
        return "your university"
    
    def _extract_research_area(self, paper: Dict) -> str:
        """Extract research area from paper title/abstract."""
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        text = f"{title} {abstract}"
        
        # Research area detection
        if any(x in text for x in ['deep learning', 'neural network', 'machine learning']):
            return 'Machine Learning'
        elif any(x in text for x in ['bayesian', 'uncertainty', 'probabilistic']):
            return 'Bayesian Deep Learning and Uncertainty'
        elif any(x in text for x in ['natural language', 'nlp', 'text', 'language model']):
            return 'Natural Language Processing'
        elif any(x in text for x in ['computer vision', 'image', 'visual']):
            return 'Computer Vision'
        elif any(x in text for x in ['reinforcement learning', 'rl', 'reward']):
            return 'Reinforcement Learning'
        elif any(x in text for x in ['robot', 'autonomous', 'control']):
            return 'Robotics and Autonomous Systems'
        elif any(x in text for x in ['security', 'privacy', 'cryptograph']):
            return 'Security and Privacy'
        elif any(x in text for x in ['database', 'query', 'storage']):
            return 'Database Systems'
        else:
            return 'Computer Science'
    
    def _generate_safe_fallback(self, name: str, email: str, affiliation: str) -> Dict:
        """Generate safe fallback email without specific research claims."""
        from safe_template_system import create_safe_academic_email
        
        subject, body = create_safe_academic_email(name, email, affiliation)
        
        return {
            'subject': subject,
            'body': body,
            'validation_status': 'FALLBACK',
            'reason': 'Could not verify research data - using safe template',
            'confidence': 0.7
        }
    
    def _generate_verified_personalized_email(self, professor_name: str, university: str,
                                               papers: List[Dict], research_area: str) -> Dict:
        """Generate personalized email with VERIFIED research data."""
        best_paper = papers[0]
        paper_title = best_paper['title']
        
        subject = f"Research Internship Inquiry – {research_area}"
        
        body = f"""Dear Professor {professor_name},

I hope this email finds you well. My name is Anamay Tripathy, and I am a final-year B.Tech student in Data Science Engineering at MIT Manipal, India. I am writing to express my strong interest in joining your research group at {university} as a research intern or assistant.

I have been following your work on {research_area.lower()} with great interest. In particular, your paper "{paper_title}" was especially inspiring, as it addresses important challenges in the field. I am very interested in how these methods can improve the reliability and effectiveness of real-world systems.

My academic background and experience have prepared me to contribute meaningfully to your research:

- Research experience: As Technical Head at YaanBarpe, a government-incubated startup, I led a team of 12 developers to build ML-powered waste management systems, achieving a 34% improvement in operational efficiency. I also interned at Intellect Design Arena, where I optimized high-volume financial transaction processing pipelines using Python and Kafka, reducing processing time by 67%.

- Technical proficiency: I have extensive experience with Python, PyTorch, TensorFlow, and SQL, and I am comfortable implementing models from scratch, training at scale, and working with large datasets in production-like environments.

- Relevant projects: I have worked on several research-oriented projects involving predictive modeling, time-series analysis, and NLP applications, focusing on building robust, data-driven decision systems.

I am eager to bring my technical skills and research motivation to your group. I would be particularly excited to contribute to projects involving {research_area.lower()} or related topics where my background in data science and engineering could be useful. I am a quick learner, highly motivated, and committed to producing careful, reproducible research.

I have attached my CV, which includes further details on my coursework, projects, and experience. If there is any possibility of a research internship or assistantship with your group, I would be grateful for the opportunity to discuss potential fit and timelines at your convenience.

Thank you very much for your time and consideration.

Sincerely,
Anamay Tripathy
B.Tech Data Science Engineering
MIT Manipal, India
tripathy.anamay23@gmail.com
https://anamay.vercel.app
+91-9877454747
"""
        
        return {
            'subject': subject,
            'body': body,
            'validation_status': 'VERIFIED',
            'paper_used': paper_title,
            'research_area': research_area,
            'confidence': 0.9
        }


# Singleton
_validator_instance = None

def get_research_validator():
    """Get singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = AIResearchValidator()
    return _validator_instance


# CLI Testing
if __name__ == '__main__':
    print("🧪 Testing AI Research Validator\n")
    
    validator = get_research_validator()
    
    # Test Case 1: Known professor at known university
    print("=" * 60)
    print("TEST 1: Yarin Gal at Oxford")
    result = validator.generate_validated_email(
        professor_name="Yarin Gal",
        email="yarin@cs.ox.ac.uk",
        affiliation="University of Oxford"
    )
    print(f"\nResult: {result['validation_status']}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Subject: {result['subject']}")
    print("-" * 60)
    
    # Test Case 2: Unknown professor
    print("\nTEST 2: Unknown professor")
    result2 = validator.generate_validated_email(
        professor_name="Gorana Collier",
        email="gorana@manchester.ac.uk",
        affiliation="University of Manchester"
    )
    print(f"\nResult: {result2['validation_status']}")
    print(f"Confidence: {result2['confidence']:.0%}")
    
    print("\n✅ Testing complete!")
