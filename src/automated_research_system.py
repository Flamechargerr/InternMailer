"""
Automated Professor Research & Email Generation System
Integrates with existing internmailing system to automatically research professors and generate personalized emails
"""

import json
import requests
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
import re
import time
from urllib.parse import quote_plus

@dataclass
class ProfessorResearch:
    name: str
    university: str
    email: str
    research_areas: List[str]
    recent_papers: List[Dict]
    lab_info: Dict
    research_evolution: Dict
    personalization_points: List[str]
    email_hooks: List[str]
    research_quality_score: int  # 1-10 scale

class AutomatedResearchSystem:
    def __init__(self, config_path: str = "config/research_config.json"):
        self.config = self.load_config(config_path)
        self.logger = self.setup_logging()
        self.user_profile = self.load_user_profile()
        
    def load_config(self, config_path: str) -> Dict:
        """Load research configuration"""
        default_config = {
            "semantic_scholar_api": "https://api.semanticscholar.org/graph/v1",
            "google_scholar_base": "https://scholar.google.com/citations",
            "research_timeout": 30,
            "min_quality_score": 7,
            "max_professors_per_batch": 10,
            "user_keywords": [
                "machine learning", "data science", "AI ethics", 
                "sustainable technology", "human-AI interaction"
            ]
        }
        try:
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        except FileNotFoundError:
            return default_config
    
    def setup_logging(self) -> logging.Logger:
        """Setup research logging"""
        logger = logging.getLogger('research_system')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('logs/research_automation.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def load_user_profile(self) -> Dict:
        """Load user's background for matching"""
        return {
            "experience": [
                "YaanBarpe - AI-driven sustainable technology",
                "Intellect Design Arena - ML pipelines and APIs",
                "VARtificial Intelligence - 89% accuracy prediction system",
                "CrimeConnect - Data-driven case management"
            ],
            "skills": [
                "Python", "Machine Learning", "Data Science", "AI Ethics",
                "System Architecture", "Sustainable Technology"
            ],
            "interests": [
                "AI Ethics", "Human-AI Interaction", "Sustainable AI",
                "Explainable AI", "Cross-cultural AI fairness"
            ],
            "unique_perspectives": [
                "Cross-cultural AI development (Indian context)",
                "Sustainability-focused AI applications",
                "Real-world ethical AI deployment challenges"
            ]
        }
    
    def research_professor_automatically(self, professor_data: Dict) -> ProfessorResearch:
        """Main automated research function"""
        self.logger.info(f"Starting automated research for {professor_data['name']}")
        
        try:
            # Step 1: Get basic faculty information
            faculty_info = self.scrape_faculty_page(professor_data)
            
            # Step 2: Get recent publications
            publications = self.get_recent_publications(professor_data['name'])
            
            # Step 3: Analyze research evolution
            research_evolution = self.analyze_research_evolution(publications)
            
            # Step 4: Find personalization points
            personalization_points = self.find_personalization_points(
                faculty_info, publications, self.user_profile
            )
            
            # Step 5: Generate email hooks
            email_hooks = self.generate_email_hooks(
                publications, personalization_points
            )
            
            # Step 6: Calculate research quality score
            quality_score = self.calculate_research_quality_score(
                faculty_info, publications, personalization_points
            )
            
            research = ProfessorResearch(
                name=professor_data['name'],
                university=professor_data['university'],
                email=professor_data['email'],
                research_areas=faculty_info.get('research_areas', []),
                recent_papers=publications,
                lab_info=faculty_info.get('lab_info', {}),
                research_evolution=research_evolution,
                personalization_points=personalization_points,
                email_hooks=email_hooks,
                research_quality_score=quality_score
            )
            
            self.logger.info(f"Research completed for {professor_data['name']} (Score: {quality_score})")
            return research
            
        except Exception as e:
            self.logger.error(f"Research failed for {professor_data['name']}: {str(e)}")
            return None
    
    def get_recent_publications(self, professor_name: str) -> List[Dict]:
        """Get recent publications using Semantic Scholar API"""
        try:
            # Search for author
            search_url = f"{self.config['semantic_scholar_api']}/author/search"
            params = {"query": professor_name, "limit": 1}
            
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            authors = response.json().get('data', [])
            if not authors:
                return []
            
            author_id = authors[0]['authorId']
            
            # Get author's recent papers
            papers_url = f"{self.config['semantic_scholar_api']}/author/{author_id}/papers"
            params = {
                "fields": "title,year,abstract,citationCount,publicationDate,journal",
                "limit": 10
            }
            
            response = requests.get(papers_url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            papers = response.json().get('data', [])
            
            # Filter recent papers (last 3 years)
            current_year = datetime.now().year
            recent_papers = [
                paper for paper in papers 
                if paper.get('year', 0) >= current_year - 3
            ]
            
            return recent_papers[:5]  # Top 5 recent papers
            
        except Exception as e:
            self.logger.error(f"Failed to get publications for {professor_name}: {str(e)}")
            return []
    
    def scrape_faculty_page(self, professor_data: Dict) -> Dict:
        """Simulate faculty page scraping (replace with actual scraping)"""
        # This would be replaced with actual web scraping
        # For now, returning simulated data
        return {
            "research_areas": ["Machine Learning", "AI Ethics", "Human-Computer Interaction"],
            "lab_info": {
                "name": f"{professor_data['name']} Research Lab",
                "focus": "Human-Centered AI",
                "current_projects": ["Explainable AI", "Fair ML Systems"]
            },
            "courses": ["CS229: Machine Learning", "CS224N: NLP"],
            "biography": "Professor focusing on ethical AI and human-computer interaction"
        }
    
    def analyze_research_evolution(self, publications: List[Dict]) -> Dict:
        """Analyze how professor's research has evolved"""
        if not publications:
            return {}
        
        # Sort papers by year
        sorted_papers = sorted(
            [p for p in publications if p.get('year')], 
            key=lambda x: x['year']
        )
        
        if len(sorted_papers) < 2:
            return {}
        
        early_papers = sorted_papers[:len(sorted_papers)//2]
        recent_papers = sorted_papers[len(sorted_papers)//2:]
        
        return {
            "early_focus": self.extract_keywords_from_papers(early_papers),
            "current_focus": self.extract_keywords_from_papers(recent_papers),
            "evolution_trend": "Moving towards more applied/ethical AI work"
        }
    
    def extract_keywords_from_papers(self, papers: List[Dict]) -> List[str]:
        """Extract keywords from paper titles and abstracts"""
        text = " ".join([
            (paper.get('title', '') + " " + paper.get('abstract', ''))
            for paper in papers
        ]).lower()
        
        # Common research keywords
        keywords = [
            'machine learning', 'deep learning', 'neural networks',
            'artificial intelligence', 'computer vision', 'nlp',
            'ethics', 'fairness', 'explainable', 'interpretable',
            'human-computer interaction', 'robotics', 'automation'
        ]
        
        found_keywords = [kw for kw in keywords if kw in text]
        return found_keywords[:5]
    
    def find_personalization_points(self, faculty_info: Dict, publications: List[Dict], user_profile: Dict) -> List[str]:
        """Find connection points between user and professor"""
        points = []
        
        # Match research areas with user interests
        prof_keywords = set()
        for paper in publications:
            prof_keywords.update(self.extract_keywords_from_papers([paper]))
        
        user_keywords = set(kw.lower() for kw in user_profile['interests'])
        
        common_keywords = prof_keywords.intersection(user_keywords)
        for keyword in common_keywords:
            points.append(f"Shared interest in {keyword}")
        
        # Match methodologies
        if 'machine learning' in prof_keywords and 'Machine Learning' in user_profile['skills']:
            points.append("Both work with ML systems in production")
        
        if 'ethics' in prof_keywords:
            points.append("Both address ethical challenges in AI deployment")
        
        # Match application domains
        if any('healthcare' in paper.get('title', '').lower() for paper in publications):
            points.append("Healthcare AI applications - relevant to your data analysis experience")
        
        return points[:5]
    
    def generate_email_hooks(self, publications: List[Dict], personalization_points: List[str]) -> List[str]:
        """Generate compelling email opening hooks"""
        hooks = []
        
        if publications:
            most_recent = publications[0]
            hooks.append(
                f"Your recent paper '{most_recent.get('title', '')}' addresses exactly the challenge I faced when..."
            )
        
        if personalization_points:
            hooks.append(
                f"Your work on {personalization_points[0].split()[-1]} particularly resonates with my experience at YaanBarpe, where..."
            )
        
        return hooks
    
    def calculate_research_quality_score(self, faculty_info: Dict, publications: List[Dict], personalization_points: List[str]) -> int:
        """Calculate research quality score (1-10)"""
        score = 5  # Base score
        
        # Recent publications boost
        if len(publications) >= 3:
            score += 2
        elif len(publications) >= 1:
            score += 1
        
        # High citation count boost
        if publications and any(p.get('citationCount', 0) > 50 for p in publications):
            score += 1
        
        # Strong personalization points
        if len(personalization_points) >= 3:
            score += 2
        elif len(personalization_points) >= 1:
            score += 1
        
        # Cap at 10
        return min(score, 10)
    
    def generate_personalized_email(self, research: ProfessorResearch) -> str:
        """Generate personalized email based on research"""
        if not research or research.research_quality_score < self.config['min_quality_score']:
            return None
        
        email_template = f"""
RESEARCH INTERNSHIP INQUIRY
Dear Prof. {research.name.split()[-1]},

I hope this message finds you well.

My name is Anamay Tripathy, a third-year B.Tech student in Data Science & Engineering at MIT Manipal, India. I am writing to express my sincere interest in joining your research group as a research intern.

Why Your Specific Research Resonates with Me
{research.email_hooks[0] if research.email_hooks else 'Your research particularly interests me because...'} 

{research.personalization_points[0] if research.personalization_points else 'I have experience with similar challenges in my work at YaanBarpe.'}

Technical Background & Research Alignment
My technical background uniquely positions me to contribute to your research. At YaanBarpe, I've led the development of AI systems that navigate similar challenges to those addressed in your work. My experience building scalable AI architectures (achieving 89% accuracy in my VARtificial Intelligence prediction system) demonstrates the technical depth needed for your research approach.

Professional Experience:
• Technical Head, YaanBarpe (Govt. of Karnataka-incubated startup): Leading AI-driven system architecture and sustainable technology solutions
• Data Analyst Intern, Intellect Design Arena, Mumbai: Built ML pipelines and scalable APIs, achieving 22% engagement increase
• Developed systems addressing challenges similar to those in your recent research

Potential Research Contributions
I could contribute to your research by bringing practical implementation experience and a unique perspective from developing AI systems in Indian contexts. My experience with {', '.join(research.personalization_points[:2]) if research.personalization_points else 'real-world AI challenges'} would be valuable for your ongoing projects.

I am available for internships in Winter 2025 or Summer 2026, and welcome remote or on-site, funded or volunteer opportunities. I have attached my detailed CV for your review and would be grateful for the opportunity to discuss how my background aligns with your research objectives.

Thank you for your time and consideration.

Contact Information
📧 tripathy.anamay23@gmail.com
📞 +91-9877454747
🌐 anamay.vercel.app | github.com/Flamechargerr

Warm regards,

Anamay Tripathy
B.Tech Data Science & Engineering, MIT Manipal
        """
        
        return email_template.strip()
    
    def process_professor_batch(self, professors: List[Dict]) -> List[Tuple[ProfessorResearch, str]]:
        """Process a batch of professors automatically"""
        results = []
        
        for professor in professors[:self.config['max_professors_per_batch']]:
            self.logger.info(f"Processing {professor['name']}...")
            
            # Research professor
            research = self.research_professor_automatically(professor)
            
            if research and research.research_quality_score >= self.config['min_quality_score']:
                # Generate email
                email = self.generate_personalized_email(research)
                results.append((research, email))
                
                self.logger.info(f"Generated email for {professor['name']} (Quality: {research.research_quality_score})")
            else:
                self.logger.info(f"Skipped {professor['name']} - insufficient research quality")
            
            # Rate limiting
            time.sleep(2)
        
        return results
    
    def save_research_results(self, results: List[Tuple[ProfessorResearch, str]], output_file: str):
        """Save research results to file"""
        output_data = []
        
        for research, email in results:
            output_data.append({
                "professor": research.name,
                "university": research.university,
                "email_address": research.email,
                "research_quality_score": research.research_quality_score,
                "research_areas": research.research_areas,
                "personalization_points": research.personalization_points,
                "generated_email": email,
                "timestamp": datetime.now().isoformat()
            })
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"Saved {len(output_data)} research results to {output_file}")

# Main execution function
def run_automated_research(professors_file: str = "data/professors.json"):
    """Run the automated research system"""
    system = AutomatedResearchSystem()
    
    # Load professors list
    try:
        with open(professors_file, 'r') as f:
            professors = json.load(f)
    except FileNotFoundError:
        print(f"Professors file {professors_file} not found. Please add professors to research.")
        return
    
    if not professors:
        print("No professors found to research. Please add professors to the database.")
        return
    
    print(f"Starting automated research for {len(professors)} professors...")
    
    # Process professors
    results = system.process_professor_batch(professors)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/research_results_{timestamp}.json"
    system.save_research_results(results, output_file)
    
    print(f"Research completed! Generated {len(results)} personalized emails.")
    print(f"Results saved to: {output_file}")
    
    # Show summary
    for research, email in results:
        print(f"\n✅ {research.name} ({research.university}) - Quality Score: {research.research_quality_score}")
        print(f"   Research Areas: {', '.join(research.research_areas[:3])}")

if __name__ == "__main__":
    run_automated_research()
