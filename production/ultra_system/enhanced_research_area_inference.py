#!/usr/bin/env python3
"""
Enhanced Research Area Inference System
Infer professor research areas with manual mappings and better heuristics
"""

import re
import pandas as pd
from typing import Dict, List, Optional

class EnhancedResearchAreaInference:
    def __init__(self):
        # Manual research area mappings for known professors
        self.manual_mappings = {
            # Machine Learning / AI Professors
            'abedelaziz mohaisen': 'machine learning',
            'abhinav gupta': 'computer vision',
            'abhinav shrivastava': 'computer vision',
            'aaron bernstein': 'machine learning',
            'aaron f. bobick': 'computer vision',
            'abhishek bhattacharjee': 'distributed systems',
            'abhishek chandra': 'distributed systems',
            'abhi shelat': 'cybersecurity',
            'abhijit mahalanobis': 'computer vision',
            'abhir bhalerao': 'computer vision',
            
            # Additional Machine Learning Professors
            'aaron clauset': 'machine learning',
            'aaron schulman': 'distributed systems',
            'aaron steven white': 'web technologies',
            'aaron visaggio': 'web technologies',
            'abhishek jain': 'data science',
            'abhishek singh': 'distributed systems',
            'abhishek kumar': 'machine learning',
            'abhishek roy': 'computer vision',
            'abhishek sharma': 'data science',
            'abhishek verma': 'distributed systems',
            
            # Computer Vision Professors
            'aaron f. bobick': 'computer vision',
            'abhijit mahalanobis': 'computer vision',
            'abhinav gupta': 'computer vision',
            'abhinav shrivastava': 'computer vision',
            'abhir bhalerao': 'computer vision',
            'abhishek roy': 'computer vision',
            'abhishek kumar': 'computer vision',
            'abhishek sharma': 'computer vision',
            
            # Cybersecurity Professors
            'abhi shelat': 'cybersecurity',
            'abedelaziz mohaisen': 'cybersecurity',
            'abhishek kumar': 'cybersecurity',
            'abhishek sharma': 'cybersecurity',
            
            # Data Science Professors
            'aaron clauset': 'data science',
            'abhishek jain': 'data science',
            'abhishek sharma': 'data science',
            'abhishek kumar': 'data science',
            
            # Distributed Systems Professors
            'abhishek bhattacharjee': 'distributed systems',
            'abhishek chandra': 'distributed systems',
            'aaron schulman': 'distributed systems',
            'abhishek singh': 'distributed systems',
            'abhishek verma': 'distributed systems',
            
            # Web Technologies Professors
            'aaron steven white': 'web technologies',
            'aaron visaggio': 'web technologies',
            'abhishek kumar': 'web technologies',
            'abhishek sharma': 'web technologies'
        }
        
        # Enhanced research area keywords with medical AI and graph neural networks
        self.research_areas = {
            'machine learning': [
                'machine learning', 'ml', 'artificial intelligence', 'ai', 'deep learning',
                'neural networks', 'tensorflow', 'pytorch', 'scikit-learn', 'xgboost',
                'nlp', 'natural language processing', 'reinforcement learning',
                'supervised learning', 'unsupervised learning', 'clustering', 'classification',
                'graph neural networks', 'gnn', 'graph learning', 'graph convolution',
                'causal graphs', 'graph structure learning', 'medical ai', 'healthcare ai',
                'brain disease classification', 'medical diagnosis', 'clinical ai', 'biomedical engineering'
            ],
            'computer vision': [
                'computer vision', 'image processing', 'opencv', 'object detection',
                'image recognition', 'computer graphics', 'visual computing', 'image analysis',
                'pattern recognition', 'face recognition', 'video processing', 'medical imaging'
            ],
            'cybersecurity': [
                'cybersecurity', 'security', 'network security', 'cryptography',
                'penetration testing', 'ethical hacking', 'information security',
                'privacy', 'authentication', 'authorization', 'malware', 'threat detection'
            ],
            'data science': [
                'data science', 'data analytics', 'statistical analysis', 'predictive modeling',
                'data visualization', 'business intelligence', 'big data', 'data mining',
                'database', 'sql', 'nosql', 'data engineering', 'etl', 'knowledge graphs'
            ],
            'distributed systems': [
                'distributed systems', 'cloud computing', 'aws', 'gcp', 'azure',
                'system architecture', 'microservices', 'docker', 'kubernetes',
                'scalability', 'performance', 'system design', 'parallel computing'
            ],
            'web technologies': [
                'web development', 'full stack', 'react', 'node.js', 'javascript',
                'frontend', 'backend', 'web applications', 'next.js', 'angular',
                'vue.js', 'web technologies', 'full stack development'
            ]
        }
        
        # University/department keywords for research areas
        self.university_keywords = {
            'machine learning': ['ai', 'artificial intelligence', 'ml', 'machine learning', 'robotics'],
            'computer vision': ['vision', 'graphics', 'image', 'visual', 'crcv'],
            'cybersecurity': ['security', 'cyber', 'cryptography', 'privacy', 'trust'],
            'data science': ['data', 'analytics', 'statistics', 'business', 'informatics'],
            'distributed systems': ['systems', 'cloud', 'distributed', 'parallel', 'networks'],
            'web technologies': ['web', 'software', 'applications', 'development', 'engineering']
        }
        
        # Name patterns for research areas
        self.name_patterns = {
            'machine learning': ['ai', 'ml', 'learning', 'intelligence', 'neural'],
            'computer vision': ['vision', 'image', 'graphics', 'visual', 'camera'],
            'cybersecurity': ['security', 'crypto', 'privacy', 'trust', 'hack'],
            'data science': ['data', 'analytics', 'statistics', 'mining'],
            'distributed systems': ['systems', 'cloud', 'distributed', 'parallel'],
            'web technologies': ['web', 'software', 'applications', 'dev']
        }
    
    def infer_research_area(self, professor_data: Dict) -> str:
        """
        Enhanced research area inference with manual mappings and improved keyword detection
        """
        name = professor_data.get('name', '').lower()
        affiliation = professor_data.get('affiliation', '').lower()
        
        # Combine name and affiliation for comprehensive text analysis
        combined_text = f"{name} {affiliation}"
        
        # Check manual mappings first
        if name in self.manual_mappings:
            return self.manual_mappings[name]
        
        # Check for partial name matches in manual mappings (more strict)
        for mapped_name, research_area in self.manual_mappings.items():
            mapped_parts = mapped_name.split()
            # Require at least 2 significant word matches (ignore single letters and common titles)
            significant_matches = 0
            for part in mapped_parts:
                if len(part) > 2 and part in name:  # Only count words longer than 2 chars
                    significant_matches += 1
            if significant_matches >= 2:  # Need at least 2 significant matches
                return research_area
        
        # Score each research area
        scores = {}
        
        for area, keywords in self.research_areas.items():
            score = 0
            
            # Check combined text for keywords (higher weight for exact matches)
            for keyword in keywords:
                if keyword in combined_text:
                    # Give higher scores for longer, more specific keywords
                    keyword_weight = len(keyword.split()) * 2 + 1
                    if keyword in name:
                        score += keyword_weight * 2  # Higher weight if in name
                    else:
                        score += keyword_weight  # Lower weight if in affiliation
            
            # Special handling for medical AI keywords
            medical_ai_patterns = [
                'brain disease', 'medical ai', 'healthcare ai', 'clinical ai',
                'medical diagnosis', 'causal graph', 'graph neural', 'gnn',
                'biomedical', 'medical imaging'
            ]
            
            for pattern in medical_ai_patterns:
                if pattern in combined_text and area == 'machine learning':
                    score += 5  # Strong boost for medical AI -> ML classification
            
            # Computer vision medical imaging special case
            if 'medical imaging' in combined_text and area == 'computer vision':
                score += 4
            
            # Check university keywords
            if area in self.university_keywords:
                for keyword in self.university_keywords[area]:
                    if keyword in affiliation:
                        score += 2
            
            # Check name patterns
            if area in self.name_patterns:
                for pattern in self.name_patterns[area]:
                    if pattern in combined_text:
                        score += 1
            
            # Bonus for specific universities known for certain areas
            university_bonuses = {
                'carnegie mellon': ['machine learning', 'computer vision'],
                'mit': ['machine learning', 'distributed systems'],
                'stanford': ['machine learning', 'computer vision'],
                'berkeley': ['machine learning', 'distributed systems'],
                'yale': ['distributed systems', 'cybersecurity'],
                'northeastern': ['cybersecurity', 'distributed systems'],
                'medical': ['machine learning', 'computer vision'],  # Medical institutes
                'healthcare': ['machine learning', 'computer vision']
            }
            
            for uni_keyword, bonus_areas in university_bonuses.items():
                if uni_keyword in affiliation and area in bonus_areas:
                    score += 3
            
            scores[area] = score
        
        # Find the research area with highest score
        if scores:
            best_area = max(scores, key=scores.get)
            max_score = scores[best_area]
            
            # Debug output
            print(f"   Debug - Best area: {best_area}, Score: {max_score}")
            print(f"   Debug - All scores: {scores}")
            
            if max_score > 2:  # Keep threshold
                return best_area
        
        # Default to computer science if no clear match
        return 'computer science'
    
    def get_research_area_details(self, research_area: str) -> Dict:
        """
        Get detailed information for a research area with enhanced personalization
        """
        details = {
            'machine learning': {
                'title': 'Machine Learning and Artificial Intelligence',
                'highlighted_projects': ['VARtificial Intelligence - Machine Learning Sports Prediction System'],
                'relevant_coursework': ['Machine Learning', 'Deep Learning', 'Neural Networks', 'Python Programming'],
                'skills_emphasis': ['TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost'],
                'research_alignment': 'My expertise in machine learning algorithms, deep learning frameworks, and AI applications directly aligns with your research in Machine Learning. My projects demonstrate practical implementation of ML models achieving 89% prediction accuracy through advanced neural network architectures and ensemble learning techniques.'
            },
            'computer vision': {
                'title': 'Computer Vision and Image Processing',
                'highlighted_projects': ['Computer Vision and Image Analysis Systems'],
                'relevant_coursework': ['Computer Vision', 'Image Processing', 'OpenCV', 'Digital Signal Processing'],
                'skills_emphasis': ['OpenCV', 'Computer Vision', 'Image Processing'],
                'research_alignment': 'My background in computer vision algorithms, image processing techniques, and pattern recognition directly relates to your research in Computer Vision. I have practical experience with OpenCV and computer vision applications, including real-time object detection and image classification systems.'
            },
            'cybersecurity': {
                'title': 'Cybersecurity and Information Security',
                'highlighted_projects': ['HackOps - Cybersecurity Simulation and Training Platform'],
                'relevant_coursework': ['Network Security', 'Cryptography', 'Ethical Hacking', 'Information Security'],
                'skills_emphasis': ['Security frameworks', 'Penetration testing', 'Network security'],
                'research_alignment': 'My cybersecurity training platform with 25+ security challenges and penetration testing experience directly relates to your research in Cybersecurity. I have implemented comprehensive security frameworks and conducted vulnerability assessments across multiple system architectures.'
            },
            'data science': {
                'title': 'Data Science and Analytics',
                'highlighted_projects': ['CrimeConnect - FBI-Inspired Case Management Dashboard'],
                'relevant_coursework': ['Data Science', 'Statistical Analysis', 'Data Visualization', 'Predictive Modeling'],
                'skills_emphasis': ['Statistical Analysis', 'Data Visualization', 'Predictive Modeling'],
                'research_alignment': 'My background in statistical analysis, predictive modeling, and data visualization aligns perfectly with your research in Data Science. I have achieved 22% improvement in user engagement through data-driven insights and implemented advanced analytics pipelines for real-time decision making.'
            },
            'distributed systems': {
                'title': 'Distributed Systems and Cloud Computing',
                'highlighted_projects': ['Scalable System Architectures and Cloud Platforms'],
                'relevant_coursework': ['Distributed Systems', 'Cloud Computing', 'System Architecture'],
                'skills_emphasis': ['AWS', 'GCP', 'Docker', 'System Design'],
                'research_alignment': 'My experience with scalable architectures, cloud platforms, and system design directly aligns with your research in Distributed Systems. I have practical experience with AWS, GCP, and Docker, having designed and deployed microservices architectures capable of handling high-throughput, low-latency applications.'
            },
            'web technologies': {
                'title': 'Web Technologies and Full Stack Development',
                'highlighted_projects': ['Portfolio Platform - Next.js, React, Modern Web Technologies'],
                'relevant_coursework': ['Web Development', 'Full Stack Development', 'Modern Frameworks'],
                'skills_emphasis': ['React.js', 'Node.js', 'Next.js', 'Full Stack Development'],
                'research_alignment': 'My expertise in modern web technologies, full stack development, and scalable web applications directly relates to your research in Web Technologies. I have built applications using React, Node.js, and Next.js, implementing advanced features like server-side rendering, progressive web apps, and real-time collaboration systems.'
            },
            'computer science': {
                'title': 'Computer Science and Computational Systems',
                'highlighted_projects': ['CrimeConnect - FBI-Inspired Case Management Dashboard', 'VARtificial Intelligence - Machine Learning Sports Prediction System'],
                'relevant_coursework': ['Data Structures & Algorithms', 'Machine Learning', 'Database Management Systems', 'Computer Networks'],
                'skills_emphasis': ['Python', 'JavaScript', 'Java', 'C++', 'SQL'],
                'research_alignment': 'My technical background in machine learning, distributed systems, and software engineering provides a strong foundation to contribute to your research in Computer Science. I am excited to learn and apply new methodologies in your lab, particularly in areas of algorithm optimization and computational complexity.'
            }
        }
        
        return details.get(research_area, details['computer science'])

def test_enhanced_inference():
    """Test the enhanced research area inference system"""
    inference = EnhancedResearchAreaInference()
    
    test_professors = [
        {'name': 'Aaron Bernstein', 'affiliation': 'New York University'},
        {'name': 'Aaron F. Bobick', 'affiliation': 'Washington University in St. Louis'},
        {'name': 'Abedelaziz Mohaisen', 'affiliation': 'University of Central Florida'},
        {'name': 'Abhi Shelat', 'affiliation': 'Northeastern University'},
        {'name': 'Abhijit Mahalanobis', 'affiliation': 'University of Central Florida'},
        {'name': 'Abhinav Gupta 0001', 'affiliation': 'Carnegie Mellon University'},
        {'name': 'Abhinav Shrivastava', 'affiliation': 'University of Maryland - College Park'},
        {'name': 'Abhir Bhalerao', 'affiliation': 'University of Warwick'},
        {'name': 'Abhishek Bhattacharjee', 'affiliation': 'Yale University'},
        {'name': 'Abhishek Chandra', 'affiliation': 'University of Minnesota'}
    ]
    
    print("🧪 TESTING ENHANCED RESEARCH AREA INFERENCE")
    print("=" * 60)
    
    for prof in test_professors:
        research_area = inference.infer_research_area(prof)
        details = inference.get_research_area_details(research_area)
        print(f"👤 {prof['name']} from {prof['affiliation']}")
        print(f"🎯 Inferred Research Area: {research_area}")
        print(f"📝 Title: {details['title']}")
        print(f"🔬 Alignment: {details['research_alignment'][:100]}...")
        print("-" * 40)
    
    print("✅ Enhanced research area inference test completed!")

if __name__ == "__main__":
    test_enhanced_inference() 