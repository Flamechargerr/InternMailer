#!/usr/bin/env python3
"""
ENHANCED RESEARCH SYSTEM v2.0
Multi-source research with AI inference - NO RATE LIMITING!

Sources:
1. CSV data (research interests from our database)
2. University domain inference
3. Name + Affiliation AI inference
4. DBLP (no rate limits, open API)
5. Semantic Scholar (generous rate limits)
"""

import requests
import re
import random
import time
from typing import Dict, List, Optional
import json

class SmartResearchSystem:
    """Multi-source research system with AI-like inference"""
    
    def __init__(self):
        # University research specializations (pre-loaded knowledge)
        self.university_specializations = {
            'mit.edu': ['AI/ML', 'Robotics', 'Computer Vision', 'NLP', 'Systems', 'Theory'],
            'stanford.edu': ['AI/ML', 'NLP', 'Databases', 'Security', 'HCI'],
            'berkeley.edu': ['Systems', 'Security', 'AI/ML', 'Theory', 'Databases'],
            'cmu.edu': ['Robotics', 'ML', 'NLP', 'Computer Vision', 'Software Engineering'],
            'gatech.edu': ['ML', 'Robotics', 'HCI', 'Systems', 'Graphics'],
            'washington.edu': ['NLP', 'AI', 'Systems', 'HCI', 'Data Science'],
            'cornell.edu': ['Theory', 'AI', 'Systems', 'Graphics', 'NLP'],
            'princeton.edu': ['Theory', 'ML', 'Computer Vision', 'Systems'],
            'harvard.edu': ['Computational Biology', 'ML', 'Theory', 'Systems'],
            'ox.ac.uk': ['ML', 'Computer Vision', 'NLP', 'Robotics'],
            'cam.ac.uk': ['ML', 'Systems', 'Theory', 'Graphics'],
            'imperial.ac.uk': ['AI', 'Robotics', 'Computer Vision', 'Data Science'],
            'ethz.ch': ['ML', 'Computer Vision', 'Robotics', 'Graphics'],
            'epfl.ch': ['ML', 'Signal Processing', 'Robotics', 'Computer Vision'],
            'default': ['Computer Science', 'Machine Learning', 'Data Science']
        }
        
        # Name keyword patterns to infer research areas
        self.name_research_hints = {
            'vision': 'Computer Vision',
            'robot': 'Robotics',
            'nlp': 'Natural Language Processing',
            'language': 'Natural Language Processing',
            'linguistics': 'Computational Linguistics',
            'security': 'Cybersecurity',
            'privacy': 'Data Privacy',
            'network': 'Computer Networks',
            'graph': 'Graph Neural Networks',
            'data': 'Data Science',
            'mining': 'Data Mining',
            'store': 'Data Systems',
            'learn': 'Machine Learning',
            'neural': 'Deep Learning',
            'adversarial': 'Adversarial ML',
            'reinforcement': 'Reinforcement Learning',
            'ai': 'Artificial Intelligence',
            'intelligent': 'Intelligent Systems',
            'system': 'Systems',
            'operating': 'Operating Systems',
            'distributed': 'Distributed Systems',
            'cloud': 'Cloud Computing',
            'database': 'Database Systems',
            'software': 'Software Engineering',
            'testing': 'Software Testing',
            'program': 'Programming Languages',
            'compiler': 'Compilers',
            'theory': 'Theoretical Computer Science',
            'complexity': 'Computational Complexity',
            'algorithm': 'Algorithms',
            'optimization': 'Optimization',
            'bio': 'Computational Biology',
            'genom': 'Genomics',
            'medical': 'Medical AI',
            'health': 'Health Informatics',
            'human': 'Human-Computer Interaction',
            'interface': 'HCI',
            'interaction': 'HCI',
            'user': 'HCI',
            'quantum': 'Quantum Computing',
            'crypto': 'Cryptography',
            'blockchain': 'Blockchain Technology',
            'ledger': 'Distributed Ledgers',
            'logic': 'Computational Logic',
            'formal': 'Formal Methods',
            'semantic': 'Semantic Web',
            'iot': 'Internet of Things',
            'edge': 'Edge Computing',
            'mobile': 'Mobile Computing',
            'wireless': 'Wireless Networks',
            'signal': 'Signal Processing',
            'speech': 'Speech Processing',
            'audio': 'Audio Processing',
            'image': 'Image Processing',
            'video': 'Video Understanding',
            '3d': '3D Computer Vision',
            'augmented': 'AR/VR',
            'virtual': 'AR/VR',
            'game': 'Game AI',
            'ethics': 'AI Ethics',
            'fairness': 'Responsible AI',
            'social': 'Social Computing',
            'education': 'AI for Education',
            'finance': 'Financial Computing'
        }
        
        # Research area descriptions for personalized emails
        self.research_descriptions = {
            'Machine Learning': {
                'mention': 'your pioneering work in machine learning and statistical learning',
                'focus': 'developing novel ML algorithms and their applications',
                'interest': 'particularly your contributions to scalable learning systems'
            },
            'Computer Vision': {
                'mention': 'your innovative research in computer vision and visual understanding',
                'focus': 'advancing visual recognition and scene understanding',
                'interest': 'especially your work on deep learning for visual perception'
            },
            'Natural Language Processing': {
                'mention': 'your groundbreaking work in natural language processing',
                'focus': 'developing language understanding and generation systems',
                'interest': 'particularly your contributions to neural language models'
            },
            'Robotics': {
                'mention': 'your cutting-edge research in robotics and autonomous systems',
                'focus': 'advancing robot perception, planning, and control',
                'interest': 'especially your work on learning-based robotics'
            },
            'AI': {
                'mention': 'your influential research in artificial intelligence',
                'focus': 'developing intelligent systems and decision-making algorithms',
                'interest': 'particularly your contributions to AI applications'
            },
            'Systems': {
                'mention': 'your impactful research in computer systems',
                'focus': 'building efficient and reliable computing systems',
                'interest': 'especially your work on system optimization and design'
            },
            'Data Science': {
                'mention': 'your significant contributions to data science',
                'focus': 'extracting insights from large-scale data',
                'interest': 'particularly your work on data analytics and mining'
            },
            'default': {
                'mention': 'your distinguished research contributions',
                'focus': 'advancing the field of computer science',
                'interest': 'particularly your innovative methodologies'
            }
        }
        
        # Cache to avoid repeated lookups
        self._cache = {}
    
    def research_professor(self, name: str, email: str, affiliation: str = '', csv_research_interest: str = '') -> Dict:
        """
        Multi-source research with NO rate limiting
        Returns personalized research data
        """
        cache_key = email.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        print(f"🔬 Smart researching: {name}")
        
        research_areas = []
        papers = []
        confidence = 0.5
        
        # Source 1: CSV data (highest priority - from our database)
        if csv_research_interest:
            research_areas.append(csv_research_interest)
            confidence += 0.3
            print(f"   📄 CSV data: {csv_research_interest}")
        
        # Source 2: University domain inference
        domain = email.split('@')[1].lower() if '@' in email else ''
        uni_areas = self._infer_from_university(domain)
        if uni_areas:
            research_areas.extend(uni_areas[:2])
            confidence += 0.1
            print(f"   🏫 University inference: {', '.join(uni_areas[:2])}")
        
        # Source 3: Name/title inference
        name_areas = self._infer_from_name(name, affiliation)
        if name_areas:
            research_areas.extend(name_areas)
            confidence += 0.1
            print(f"   👤 Name inference: {', '.join(name_areas)}")
        
        # Source 4: DBLP (open, no rate limits)
        dblp_data = self._query_dblp(name)
        if dblp_data:
            papers.extend(dblp_data.get('papers', []))
            if dblp_data.get('areas'):
                research_areas.extend(dblp_data['areas'])
            confidence += 0.2
            print(f"   📚 DBLP: {len(dblp_data.get('papers', []))} papers")
        
        # Source 5: Semantic Scholar (generous limits)
        if len(papers) < 3:
            ss_data = self._query_semantic_scholar(name)
            if ss_data:
                papers.extend(ss_data.get('papers', []))
                confidence += 0.1
                print(f"   🔬 Semantic Scholar: {len(ss_data.get('papers', []))} papers")
        
        # Deduplicate and select primary area
        research_areas = list(dict.fromkeys(research_areas))  # Remove duplicates preserving order
        primary_area = research_areas[0] if research_areas else 'Computer Science'
        
        # Generate personalized content
        result = self._generate_personalized_content(name, primary_area, papers, affiliation, confidence)
        
        self._cache[cache_key] = result
        return result
    
    def _infer_from_university(self, domain: str) -> List[str]:
        """Infer research areas from university domain"""
        for uni_domain, areas in self.university_specializations.items():
            if uni_domain in domain:
                return random.sample(areas, min(2, len(areas)))
        return self.university_specializations['default']
    
    def _infer_from_name(self, name: str, affiliation: str) -> List[str]:
        """Infer research areas from name and affiliation keywords"""
        text = f"{name} {affiliation}".lower()
        inferred = []
        
        for keyword, area in self.name_research_hints.items():
            if keyword in text:
                inferred.append(area)
        
        return inferred[:2]  # Max 2 inferences
    
    def _query_dblp(self, name: str) -> Optional[Dict]:
        """Query DBLP (no rate limits, open API)"""
        try:
            # Clean name for query
            query_name = name.replace(' ', '+')
            url = f"https://dblp.org/search/publ/api?q=author:{query_name}&format=json&h=5"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                hits = data.get('result', {}).get('hits', {}).get('hit', [])
                
                papers = []
                areas = set()
                
                for hit in hits[:5]:
                    info = hit.get('info', {})
                    title = info.get('title', '')
                    venue = info.get('venue', '')
                    year = info.get('year', '')
                    
                    if title:
                        papers.append({
                            'title': title,
                            'venue': venue,
                            'year': year
                        })
                        
                        # Infer area from title
                        title_lower = title.lower()
                        for keyword, area in self.name_research_hints.items():
                            if keyword in title_lower:
                                areas.add(area)
                
                return {'papers': papers, 'areas': list(areas)}
        except Exception as e:
            pass  # Silent fail, we have other sources
        
        return None
    
    def _query_semantic_scholar(self, name: str) -> Optional[Dict]:
        """Query Semantic Scholar (generous rate limits)"""
        try:
            query = name.replace(' ', '+')
            url = f"https://api.semanticscholar.org/graph/v1/author/search?query={query}&limit=1"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                authors = data.get('data', [])
                
                if authors:
                    author_id = authors[0].get('authorId')
                    # Get papers
                    papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,year,venue&limit=5"
                    papers_response = requests.get(papers_url, timeout=5)
                    
                    if papers_response.status_code == 200:
                        papers_data = papers_response.json().get('data', [])
                        papers = [{'title': p.get('title', ''), 'year': p.get('year', '')} for p in papers_data]
                        return {'papers': papers}
            
            # Rate limited or error - wait briefly
            time.sleep(0.5)
        except Exception as e:
            pass
        
        return None
    
    def _generate_personalized_content(self, name: str, primary_area: str, papers: List, affiliation: str, confidence: float) -> Dict:
        """Generate personalized email content based on research data"""
        
        # Get description for primary area
        area_key = primary_area
        for key in self.research_descriptions:
            if key.lower() in primary_area.lower():
                area_key = key
                break
        
        desc = self.research_descriptions.get(area_key, self.research_descriptions['default'])
        
        # Create paper reference if available
        # "PAPER-FIRST" PERSONALIZATION STRATEGY
        # If generic "Computer Science" or "Data Science", try to derive from paper title
        if primary_area in ['Computer Science', 'Data Science', 'Systems', 'AI'] and papers:
            recent_paper = papers[0]
            title = recent_paper.get('title', '')
            
            if title:
                # Use the title to generate a very specific research area
                # e.g. "Temporal Planning in RL" instead of "Computer Science"
                
                # Clean title for research area usage (remove colon parts sometimes)
                clean_title = title.split(':')[0] if ':' in title else title
                
                # Heuristic: If title is reasonably short, use it as the area context
                if len(clean_title) < 80:
                    # Update primary area to be specific
                    # We keep it title case for the email format
                    import string
                    # primary_area = string.capwords(clean_title) 
                    # Actually, better to say "your work on [Title]"
                    pass

                paper_reference = f"Your recent work on '{title}' particularly caught my attention"
                
                # DYNAMC DESCRIPTION GENERATION
                desc['mention'] = f"your distinguished research on {title}"
                desc['focus'] = f"advancing {title} and related methodologies"
                desc['interest'] = f"particularly your innovative approach to {clean_title}"
                
                # Override primary area for the "I am interested in [Area]" slot if it's generic
                if primary_area == 'Computer Science':
                    primary_area = clean_title # promoting specific title to area
        
        elif papers:
            # Standard paper reference for non-generic areas
            recent_paper = papers[0]
            title = recent_paper.get('title', '')
            if title:
                paper_reference = f"Your recent work on '{title}' particularly caught my attention"
            else:
                paper_reference = ""
        else:
             paper_reference = ""
        
        # Create affiliation reference
        affiliation_ref = ""
        if affiliation:
            affiliation_clean = affiliation.replace('University', '').replace('Institute', '').strip()
            affiliation_ref = f"the innovative research environment at {affiliation}"
        
        return {
            'research_area': primary_area,
            'research_focus': desc['focus'],
            'research_mention': desc['mention'],
            'specific_interest': desc['interest'],
            'paper_reference': paper_reference,
            'affiliation_reference': affiliation_ref,
            'papers_found': len(papers),
            'confidence': min(confidence, 1.0),
            'sources_used': ['csv', 'university_inference', 'dblp', 'semantic_scholar']
        }


# Singleton instance
_smart_research_system = None

def get_smart_research_system():
    """Get singleton instance of SmartResearchSystem"""
    global _smart_research_system
    if _smart_research_system is None:
        _smart_research_system = SmartResearchSystem()
    return _smart_research_system


# Test
if __name__ == "__main__":
    system = get_smart_research_system()
    
    # Test with sample professor
    result = system.research_professor(
        name="Yann LeCun",
        email="yann@cs.nyu.edu",
        affiliation="New York University",
        csv_research_interest="Deep Learning"
    )
    
    print("\n📊 RESULT:")
    for key, value in result.items():
        print(f"   {key}: {value}")
