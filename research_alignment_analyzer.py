#!/usr/bin/env python3
"""
Research Alignment Analyzer
Generate personalized explanations for why professor's publications align with student's background
"""

import re
from typing import Dict, List, Optional
import json

class ResearchAlignmentAnalyzer:
    def __init__(self):
        # Your background and interests
        self.student_profile = {
            "name": "Anamay Tripathy",
            "degree": "B.Tech Data Science Engineering",
            "cgpa": "7.6/10",
            "institution": "MIT Manipal, India",
            "year": "Third-year (2023-2027)",
            
            "technical_skills": [
                "Machine Learning", "Deep Learning", "Neural Networks", "Python Programming",
                "TensorFlow", "PyTorch", "Scikit-learn", "XGBoost", "Statistical Analysis",
                "Data Visualization", "Predictive Modeling", "JavaScript", "Java", "C++", "SQL",
                "React.js", "Node.js", "MongoDB", "Next.js", "RESTful APIs", "AWS", "GCP", 
                "Docker", "Git", "Linux/Unix"
            ],
            
            "experience": [
                {
                    "role": "Technical Head",
                    "company": "YaanBarpe (Karnataka Government-incubated startup)",
                    "description": "Leading technical development and product strategy for sustainable solutions. System architecture, team coordination, strategic technology decisions."
                },
                {
                    "role": "Data Analyst Intern", 
                    "company": "Intellect Design Arena, Mumbai",
                    "description": "Automated KPI dashboard systems using Python and SQL (12+ hours weekly savings). Developed REST APIs improving user engagement by 22%. Statistical analysis on large datasets."
                }
            ],
            
            "projects": [
                {
                    "name": "VARtificial Intelligence - Machine Learning Sports Prediction System",
                    "description": "Sophisticated prediction model using XGBoost and Pyodide, incorporating real-time player statistics, historical performance data, and game dynamics analysis. Achieved 89% prediction accuracy through advanced feature engineering and ensemble learning techniques.",
                    "technologies": ["XGBoost", "Pyodide", "Machine Learning", "Feature Engineering", "Ensemble Learning"]
                }
            ],
            
            "research_interests": [
                "Machine Learning algorithms and real-world applications",
                "Predictive modeling and automated decision-making systems", 
                "Deep learning and neural network architectures",
                "Data science and statistical analysis",
                "AI applications in various domains",
                "Computer vision and image processing",
                "Natural language processing",
                "Cybersecurity and privacy",
                "Human-computer interaction",
                "Software engineering and system design"
            ]
        }
        
        # Research area specific alignment keywords
        self.research_alignment_keywords = {
            "machine_learning": [
                "machine learning", "ML", "deep learning", "neural networks", "artificial intelligence",
                "predictive modeling", "classification", "regression", "clustering", "ensemble learning",
                "feature engineering", "model optimization", "supervised learning", "unsupervised learning",
                "reinforcement learning", "computer vision", "natural language processing", "data mining"
            ],
            
            "cybersecurity": [
                "cybersecurity", "security", "privacy", "encryption", "authentication", "malware",
                "network security", "information security", "data protection", "vulnerability",
                "threat detection", "intrusion detection", "cryptography", "access control",
                "security analysis", "risk assessment", "digital forensics", "secure systems"
            ],
            
            "data_science": [
                "data science", "data analysis", "statistical analysis", "big data", "data mining",
                "data visualization", "business intelligence", "analytics", "statistical modeling",
                "data processing", "database systems", "data warehousing", "ETL", "data engineering"
            ],
            
            "software_engineering": [
                "software engineering", "system design", "software architecture", "programming",
                "web development", "mobile development", "API development", "cloud computing",
                "distributed systems", "microservices", "DevOps", "software testing", "agile"
            ],
            
            "ai_applications": [
                "artificial intelligence", "AI applications", "intelligent systems", "automation",
                "recommendation systems", "expert systems", "knowledge representation",
                "cognitive computing", "human-computer interaction", "robotics", "IoT"
            ]
        }

    def analyze_publication_alignment(self, publication: Dict, research_area: str) -> str:
        """
        Analyze how a publication aligns with student's background and generate explanation
        """
        title = publication.get('title', '').lower()
        summary = publication.get('summary', '').lower()
        venue = publication.get('venue', '').lower()
        year = publication.get('year', 2024)
        
        # Combine title and summary for analysis
        content = f"{title} {summary}"
        
        # Generate alignment explanation based on research area and content
        alignment_explanation = self._generate_alignment_explanation(
            content, research_area, publication, title, summary, venue, year
        )
        
        return alignment_explanation

    def _generate_alignment_explanation(self, content: str, research_area: str, 
                                      publication: Dict, title: str, summary: str, 
                                      venue: str, year: int) -> str:
        """Generate detailed alignment explanation"""
        
        explanations = []
        
        # Check for direct technical skill matches
        skill_matches = []
        for skill in self.student_profile["technical_skills"]:
            if skill.lower() in content:
                skill_matches.append(skill)
        
        # Check for research interest matches
        interest_matches = []
        for interest in self.student_profile["research_interests"]:
            interest_keywords = interest.lower().split()
            if any(keyword in content for keyword in interest_keywords):
                interest_matches.append(interest)
        
        # Check for experience relevance
        experience_matches = []
        for exp in self.student_profile["experience"]:
            exp_keywords = exp["description"].lower().split()
            common_keywords = ["data", "analysis", "system", "development", "api", "python", "statistical"]
            if any(keyword in content for keyword in common_keywords):
                experience_matches.append(exp["role"])
        
        # Generate explanation based on research area
        if research_area.lower() == "machine learning":
            explanations.append(self._generate_ml_alignment(content, skill_matches, interest_matches))
        elif research_area.lower() == "cybersecurity":
            explanations.append(self._generate_cybersecurity_alignment(content, skill_matches, interest_matches))
        elif research_area.lower() == "data science":
            explanations.append(self._generate_data_science_alignment(content, skill_matches, interest_matches))
        else:
            explanations.append(self._generate_general_alignment(content, skill_matches, interest_matches))
        
        # Add project relevance
        project_relevance = self._check_project_relevance(content)
        if project_relevance:
            explanations.append(project_relevance)
        
        # Add experience relevance
        if experience_matches:
            explanations.append(f"This research directly relates to my professional experience as {' and '.join(experience_matches)}, where I've worked on similar technical challenges.")
        
        # Combine explanations
        final_explanation = " ".join(explanations)
        
        # Ensure explanation is not empty
        if not final_explanation.strip():
            final_explanation = f"This research aligns with my academic focus in Data Science Engineering and my interest in applying {research_area.lower()} techniques to solve real-world problems."
        
        return final_explanation

    def _generate_ml_alignment(self, content: str, skill_matches: List[str], interest_matches: List[str]) -> str:
        """Generate ML-specific alignment explanation"""
        explanations = []
        
        if "machine learning" in content or "deep learning" in content:
            explanations.append("This research directly aligns with my core expertise in machine learning algorithms and deep learning frameworks.")
        
        if "neural network" in content or "neural" in content:
            explanations.append("The neural network approaches discussed connect perfectly with my coursework in Neural Networks and practical experience with TensorFlow and PyTorch.")
        
        if "prediction" in content or "predictive" in content:
            explanations.append("This predictive modeling research resonates with my VARtificial Intelligence project, where I achieved 89% prediction accuracy using advanced ML techniques.")
        
        if "feature" in content and "engineering" in content:
            explanations.append("The feature engineering aspects align with my hands-on experience in developing sophisticated prediction models with advanced feature engineering techniques.")
        
        if skill_matches:
            relevant_skills = [skill for skill in skill_matches if skill in ["TensorFlow", "PyTorch", "Scikit-learn", "XGBoost", "Machine Learning", "Deep Learning"]]
            if relevant_skills:
                explanations.append(f"My technical proficiency in {', '.join(relevant_skills)} makes me well-equipped to contribute to this research area.")
        
        return " ".join(explanations)

    def _generate_cybersecurity_alignment(self, content: str, skill_matches: List[str], interest_matches: List[str]) -> str:
        """Generate cybersecurity-specific alignment explanation"""
        explanations = []
        
        if "security" in content or "privacy" in content:
            explanations.append("This security research aligns with my growing interest in cybersecurity applications and data privacy protection.")
        
        if "data" in content and ("protection" in content or "privacy" in content):
            explanations.append("The data protection aspects connect with my experience in handling sensitive data during my internship at Intellect Design Arena.")
        
        if "system" in content and "security" in content:
            explanations.append("This systems security research complements my technical background in system architecture and development from my role as Technical Head at YaanBarpe.")
        
        if "analysis" in content:
            explanations.append("The analytical components of this research align with my strong background in statistical analysis and data processing.")
        
        return " ".join(explanations)

    def _generate_data_science_alignment(self, content: str, skill_matches: List[str], interest_matches: List[str]) -> str:
        """Generate data science-specific alignment explanation"""
        explanations = []
        
        if "data" in content and ("analysis" in content or "mining" in content):
            explanations.append("This data analysis research directly aligns with my B.Tech in Data Science Engineering and practical experience in statistical analysis.")
        
        if "statistical" in content or "statistics" in content:
            explanations.append("The statistical methodologies discussed connect perfectly with my coursework and professional experience in statistical analysis at Intellect Design Arena.")
        
        if "visualization" in content or "dashboard" in content:
            explanations.append("This visualization research resonates with my experience in developing automated KPI dashboard systems that saved 12+ hours weekly.")
        
        return " ".join(explanations)

    def _generate_general_alignment(self, content: str, skill_matches: List[str], interest_matches: List[str]) -> str:
        """Generate general alignment explanation"""
        explanations = []
        
        if "algorithm" in content or "computational" in content:
            explanations.append("This computational research aligns with my strong programming background and algorithmic thinking developed through my Data Science Engineering curriculum.")
        
        if "system" in content or "application" in content:
            explanations.append("The systems and applications focus connects with my experience in system architecture and technical leadership at YaanBarpe.")
        
        if skill_matches:
            explanations.append(f"My technical skills in {', '.join(skill_matches[:3])} provide a strong foundation for contributing to this research.")
        
        return " ".join(explanations)

    def _check_project_relevance(self, content: str) -> Optional[str]:
        """Check if content relates to student's projects"""
        project = self.student_profile["projects"][0]  # VARtificial Intelligence project
        
        project_keywords = ["prediction", "sports", "real-time", "statistics", "performance", "accuracy", "ensemble"]
        
        matches = [keyword for keyword in project_keywords if keyword in content]
        
        if matches:
            return f"This research particularly resonates with my VARtificial Intelligence project, where I developed a sports prediction system achieving 89% accuracy through similar methodologies."
        
        return None

    def generate_publications_with_alignment(self, publications: List[Dict], research_area: str) -> str:
        """Generate HTML for publications with alignment explanations"""
        if not publications:
            return "<p>No recent publications found.</p>"
        
        html_parts = []
        
        for i, pub in enumerate(publications, 1):
            title = pub.get('title', 'Untitled')
            year = pub.get('year', 'N/A')
            venue = pub.get('venue', 'Unknown Venue')
            summary = pub.get('summary', 'No summary available.')
            
            # Generate alignment explanation
            alignment = self.analyze_publication_alignment(pub, research_area)
            
            # Truncate summary if too long
            if len(summary) > 200:
                summary = summary[:200] + "..."
            
            html_parts.append(f"""
            <div class="publication-item">
                <div class="publication-header">
                    <strong>{i}. {title}</strong> ({year})
                </div>
                <div class="publication-venue">
                    <em>Venue:</em> {venue}
                </div>
                <div class="publication-summary">
                    <em>Summary:</em> {summary}
                </div>
                <div class="research-alignment">
                    <strong>🎯 Research Alignment:</strong> {alignment}
                </div>
            </div>
            """)
        
        return "".join(html_parts)

def test_alignment_analyzer():
    """Test the research alignment analyzer"""
    analyzer = ResearchAlignmentAnalyzer()
    
    # Sample publication
    sample_pub = {
        'title': 'Deep Learning Approaches for Predictive Analytics in Sports',
        'year': 2024,
        'venue': 'IEEE Conference on Machine Learning',
        'summary': 'This paper presents novel deep learning techniques for predicting sports outcomes using real-time player statistics and historical performance data. The proposed ensemble learning approach achieves high accuracy in prediction tasks.'
    }
    
    alignment = analyzer.analyze_publication_alignment(sample_pub, "Machine Learning")
    print("Sample Alignment Explanation:")
    print(alignment)
    print("\n" + "="*80 + "\n")
    
    # Test HTML generation
    html = analyzer.generate_publications_with_alignment([sample_pub], "Machine Learning")
    print("Sample HTML Output:")
    print(html)

if __name__ == "__main__":
    test_alignment_analyzer()
