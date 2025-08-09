#!/usr/bin/env python3
"""
🚀 HTML ULTRA AUTOMATED AI CAMPAIGN SYSTEM 
==========================================
YOUR ORIGINAL SOPHISTICATED HTML SYSTEM FULLY RESTORED:
✅ HTML Templates with Advanced Styling 
✅ Research Area-Specific Content Generation
✅ Professional Email Layout with Modern Design
✅ CV Attachment Integration
✅ Publication Analysis and Personalization
✅ 478k+ Professor Database Integration
✅ Duplicate Prevention System
✅ Real-time Campaign Analytics

This matches your original sophisticated HTML email system!
"""

import smtplib
import ssl
import pandas as pd
import logging
import json
import time
import random
import sys
import os
import re
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from jinja2 import Template

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'html_ultra_campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProfessorResult:
    email: str
    name: str
    university: str
    research_area: str
    status: str
    timestamp: datetime
    template_used: str = "html_sophisticated"
    publications_found: int = 0
    error: Optional[str] = None

class HTMLUltraResearchAssistant:
    """Advanced research assistant for publication analysis and HTML content generation"""
    
    def __init__(self):
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.research_cache = {}
        
    async def analyze_professor_profile(self, name: str, university: str, email: str) -> Dict:
        """Comprehensive professor profile analysis for HTML content generation"""
        try:
            # Clean and process name
            clean_name = self.clean_professor_name(name)
            cache_key = f"{clean_name}_{university}"
            
            if cache_key in self.research_cache:
                return self.research_cache[cache_key]
            
            # Multi-source research analysis
            profile_data = await self._comprehensive_research_analysis(clean_name, university, email)
            
            # Cache results
            self.research_cache[cache_key] = profile_data
            return profile_data
            
        except Exception as e:
            logger.error(f"Profile analysis error for {name}: {e}")
            return self._get_default_profile(name, university, email)
    
    async def _comprehensive_research_analysis(self, name: str, university: str, email: str) -> Dict:
        """Comprehensive research analysis combining multiple sources"""
        
        # 1. Semantic Scholar API search
        publications = await self._search_publications(name, university)
        
        # 2. Domain-based university analysis  
        university_profile = self._analyze_university_domain(email, university)
        
        # 3. Research area inference
        research_areas = self._infer_research_areas(publications, email, name)
        
        # 4. Generate personalized content data
        return {
            'name': name,
            'university': university,
            'email': email,
            'research_areas': research_areas,
            'primary_research_area': research_areas[0] if research_areas else 'Computer Science',
            'publications': publications[:5],  # Top 5
            'university_tier': university_profile['tier'],
            'university_specialties': university_profile['specialties'],
            'alignment_score': self._calculate_alignment_score(research_areas, publications),
            'personalization_data': self._generate_personalization_data(research_areas, publications),
            'found_research': len(publications) > 0
        }
    
    async def _search_publications(self, name: str, university: str) -> List[Dict]:
        """Search for professor publications using Semantic Scholar"""
        try:
            url = f"{self.semantic_scholar_base}/author/search"
            params = {"query": f"{name} {university}", "limit": 10}
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                for author in data.get('data', []):
                    if self._name_similarity(name, author.get('name', '')):
                        # Get publications
                        pub_url = f"{self.semantic_scholar_base}/author/{author.get('authorId')}/papers"
                        pub_response = requests.get(pub_url, params={"limit": 20}, timeout=15)
                        
                        if pub_response.status_code == 200:
                            pub_data = pub_response.json()
                            return pub_data.get('data', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Publication search error: {e}")
            return []
    
    def _analyze_university_domain(self, email: str, university: str) -> Dict:
        """Analyze university profile based on domain and name"""
        if not email:
            return {'tier': 'Research University', 'specialties': ['Computer Science']}
        
        domain = email.split('@')[-1].lower()
        
        # Top-tier university analysis
        tier1_universities = {
            'mit.edu': {'tier': 'Top Tier Research University', 'specialties': ['AI', 'Machine Learning', 'Robotics', 'Computer Systems']},
            'stanford.edu': {'tier': 'Top Tier Research University', 'specialties': ['AI', 'Machine Learning', 'Computer Vision', 'NLP']},
            'berkeley.edu': {'tier': 'Top Tier Research University', 'specialties': ['Computer Systems', 'AI', 'Theory']},
            'cmu.edu': {'tier': 'Top Tier Research University', 'specialties': ['Machine Learning', 'Robotics', 'Computer Vision']},
            'harvard.edu': {'tier': 'Top Tier Research University', 'specialties': ['Computational Biology', 'AI', 'Theory']},
            'princeton.edu': {'tier': 'Top Tier Research University', 'specialties': ['Theory', 'Machine Learning', 'Systems']}
        }
        
        return tier1_universities.get(domain, {'tier': 'Research University', 'specialties': ['Computer Science']})
    
    def _infer_research_areas(self, publications: List[Dict], email: str, name: str) -> List[str]:
        """Infer research areas from publications and context"""
        areas = set()
        
        # Analyze publications
        for pub in publications:
            title_abstract = (pub.get('title', '') + ' ' + pub.get('abstract', '')).lower()
            
            if any(word in title_abstract for word in ['neural', 'deep learning', 'machine learning', 'ai']):
                areas.add('Machine Learning')
            if any(word in title_abstract for word in ['computer vision', 'image', 'visual', 'cv']):
                areas.add('Computer Vision') 
            if any(word in title_abstract for word in ['nlp', 'natural language', 'text']):
                areas.add('Natural Language Processing')
            if any(word in title_abstract for word in ['system', 'distributed', 'network']):
                areas.add('Computer Systems')
            if any(word in title_abstract for word in ['algorithm', 'theory', 'complexity']):
                areas.add('Algorithms & Theory')
            if any(word in title_abstract for word in ['security', 'crypto', 'privacy']):
                areas.add('Cybersecurity')
            if any(word in title_abstract for word in ['robot', 'autonomous', 'control']):
                areas.add('Robotics')
        
        # Fallback to email/name analysis
        if not areas:
            text = f"{email} {name}".lower()
            if any(word in text for word in ['ml', 'ai', 'neural']):
                areas.add('Machine Learning')
            else:
                areas.add('Computer Science')
        
        return list(areas)
    
    def _calculate_alignment_score(self, research_areas: List[str], publications: List[Dict]) -> float:
        """Calculate research alignment score for personalization"""
        ai_areas = ['Machine Learning', 'Computer Vision', 'Natural Language Processing', 'AI', 'Robotics']
        alignment = len(set(research_areas) & set(ai_areas)) / max(len(ai_areas), 1)
        
        # Boost score if publications found
        if publications:
            alignment += 0.2
            
        return min(alignment, 1.0)
    
    def _generate_personalization_data(self, research_areas: List[str], publications: List[Dict]) -> Dict:
        """Generate personalization data for HTML template"""
        recent_pub = publications[0] if publications else None
        
        return {
            'has_publications': len(publications) > 0,
            'recent_publication': {
                'title': recent_pub.get('title', '') if recent_pub else '',
                'year': recent_pub.get('year', '') if recent_pub else '',
                'venue': recent_pub.get('venue', '') if recent_pub else ''
            },
            'research_alignment_strength': 'Strong' if len(research_areas) > 2 else 'Moderate',
            'collaboration_opportunities': self._generate_collaboration_ideas(research_areas),
            'technical_synergy': self._assess_technical_synergy(research_areas)
        }
    
    def _generate_collaboration_ideas(self, research_areas: List[str]) -> List[str]:
        """Generate specific collaboration ideas based on research areas"""
        ideas = []
        
        if 'Machine Learning' in research_areas:
            ideas.append('Novel AI/ML algorithm development and optimization')
        if 'Computer Vision' in research_areas:
            ideas.append('Computer vision applications in real-world systems')
        if 'Natural Language Processing' in research_areas:
            ideas.append('Advanced NLP models for domain-specific applications')
        if 'Computer Systems' in research_areas:
            ideas.append('High-performance computing and distributed systems')
        if 'Robotics' in research_areas:
            ideas.append('Autonomous systems and intelligent robotics')
        
        return ideas or ['Interdisciplinary research in computer science applications']
    
    def _assess_technical_synergy(self, research_areas: List[str]) -> str:
        """Assess technical synergy level"""
        ai_related = ['Machine Learning', 'Computer Vision', 'Natural Language Processing', 'Robotics']
        synergy_count = len(set(research_areas) & set(ai_related))
        
        if synergy_count >= 3:
            return 'Exceptional synergy with multiple AI/ML research areas'
        elif synergy_count >= 2:
            return 'Strong synergy with core AI research areas'
        elif synergy_count >= 1:
            return 'Good synergy with AI applications and methodologies'
        else:
            return 'Promising synergy through computational methods'
    
    def clean_professor_name(self, name: str) -> str:
        """Clean professor name"""
        prefixes = ['Dr.', 'Prof.', 'Professor', 'Dr', 'Prof']
        suffixes = ['Ph.D', 'PhD', 'Ph.D.', 'Jr.', 'Sr.']
        
        cleaned = str(name).strip()
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        return cleaned
    
    def _name_similarity(self, name1: str, name2: str) -> bool:
        """Check name similarity"""
        clean1 = self.clean_professor_name(name1).lower().split()
        clean2 = self.clean_professor_name(name2).lower().split()
        
        if not clean1 or not clean2:
            return False
        
        # Check last name match
        return clean1[-1] == clean2[-1] and len(set(clean1) & set(clean2)) >= 2
    
    def _get_default_profile(self, name: str, university: str, email: str) -> Dict:
        """Default profile when research analysis fails"""
        return {
            'name': name,
            'university': university,
            'email': email,
            'research_areas': ['Computer Science'],
            'primary_research_area': 'Computer Science',
            'publications': [],
            'university_tier': 'Research University',
            'university_specialties': ['Computer Science'],
            'alignment_score': 0.5,
            'personalization_data': {
                'has_publications': False,
                'recent_publication': {'title': '', 'year': '', 'venue': ''},
                'research_alignment_strength': 'Moderate',
                'collaboration_opportunities': ['Computational research and methodology development'],
                'technical_synergy': 'Strong potential through computational methods and AI applications'
            },
            'found_research': False
        }

class HTMLUltraAutomatedAICampaignSystem:
    """Your original sophisticated HTML email campaign system - FULLY RESTORED"""
    
    def __init__(self):
        """Initialize the HTML ultra system"""
        print("🚀 HTML ULTRA AUTOMATED AI CAMPAIGN SYSTEM")
        print("=" * 65)
        print("✅ Advanced HTML Templates with Professional Styling")
        print("✅ Research-Based Content Personalization")
        print("✅ CV Attachment Integration")
        print("✅ 478k+ Professor Database")
        print("✅ Publication Analysis & Research Alignment")
        print("=" * 65)
        
        # Initialize components
        self.research_assistant = HTMLUltraResearchAssistant()
        
        # Email configuration
        self.smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': 'tripathy.anamay23@gmail.com',
            'password': 'xctf elgn llfo aohf'
        }
        
        # File paths
        self.base_dir = Path(__file__).parent
        self.database_path = self.base_dir / "enhanced_background_emails.csv"
        self.templates_dir = self.base_dir / "templates"
        self.cv_path = self.base_dir / "resumes" / "CV_Anamay_Modern.pdf"
        self.results_dir = self.base_dir / "html_campaign_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Tracking
        self.sent_emails_file = self.base_dir / "sent_emails_log.json"
        self.sent_emails: Set[str] = self.load_sent_emails()
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'emails_sent': 0,
            'research_found': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        self.results: List[ProfessorResult] = []
        self.lock = threading.Lock()
        
        print(f"🗄️  Database: {self.database_path.name}")
        print(f"📊 Sent emails tracked: {len(self.sent_emails):,}")
        print(f"📁 Templates directory: {self.templates_dir}")
        print(f"📎 CV path: {self.cv_path}")
        print("🔧 HTML Ultra system ready!")
        
    def load_sent_emails(self) -> Set[str]:
        """Load sent emails log"""
        if self.sent_emails_file.exists():
            try:
                with open(self.sent_emails_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('sent_emails', []))
            except Exception as e:
                logger.error(f"Error loading sent emails: {e}")
        return set()
    
    def save_sent_emails(self):
        """Save sent emails log"""
        try:
            data = {
                'sent_emails': list(self.sent_emails),
                'last_updated': datetime.now().isoformat(),
                'total_sent': len(self.sent_emails)
            }
            with open(self.sent_emails_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sent emails: {e}")
    
    def load_professor_database(self) -> pd.DataFrame:
        """Load and clean the professor database"""
        try:
            print(f"\n📊 Loading HTML campaign database...")
            
            if not self.database_path.exists():
                print(f"❌ Database not found: {self.database_path}")
                return pd.DataFrame()
            
            df = pd.read_csv(self.database_path)
            initial_count = len(df)
            print(f"📈 Initial records: {initial_count:,}")
            
            # Clean email addresses from corrupted data
            df['email'] = df['email'].astype(str).str.strip()
            df['email'] = df['email'].str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')
            
            # Handle missing data
            df['name'] = df['name'].fillna('Unknown')
            df['affiliation'] = df['affiliation'].fillna('University')
            
            # Fix names from email when needed
            empty_names = (df['name'].isna()) | (df['name'] == '') | (df['name'] == 'Unknown')
            df.loc[empty_names, 'name'] = df.loc[empty_names, 'email'].str.split('@').str[0].str.replace('.', ' ').str.title()
            
            # Clean and filter
            df = df.dropna(subset=['email'])
            df = df[df['email'].str.contains('@', na=False)]
            df = df.drop_duplicates(subset=['email'])
            
            # Remove already sent
            initial_clean = len(df)
            df = df[~df['email'].isin(self.sent_emails)]
            
            # Final validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            df = df[df['email'].str.match(email_pattern, na=False)]
            
            final_count = len(df)
            
            print(f"✅ Clean records: {final_count:,}")
            print(f"🚫 Already sent: {initial_clean - final_count:,}")
            print(f"🗑️  Invalid emails: {initial_count - initial_clean:,}")
            
            return df
            
        except Exception as e:
            logger.error(f"Database loading error: {e}")
            print(f"❌ Database error: {e}")
            return pd.DataFrame()
    
    def load_html_template(self) -> str:
        """Load the sophisticated HTML template"""
        template_path = self.templates_dir / "enhanced_academic_research_template.html"
        
        if not template_path.exists():
            # Create a sophisticated default template
            return self.get_default_html_template()
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Template loading error: {e}")
            return self.get_default_html_template()
    
    def get_default_html_template(self) -> str:
        """Sophisticated HTML template matching your original style"""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta charset="UTF-8">
    <title>Research Collaboration Opportunity - {{ professor.research_area }}</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.6;
            color: #2c3e50;
        }
        
        .container {
            max-width: 800px;
            margin: 40px auto;
            background: #ffffff;
            padding: 60px 50px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            letter-spacing: 1px;
        }
        
        .research-highlight {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
            text-align: center;
        }
        
        .research-highlight h3 {
            margin: 0 0 15px 0;
            font-size: 18px;
            font-weight: bold;
        }
        
        .section {
            margin-bottom: 35px;
        }
        
        .section-title {
            margin: 0 0 20px 0;
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }
        
        .project-item {
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .contact-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
        }
        
        .signature {
            margin-top: 40px;
            border-top: 2px solid #2c3e50;
            padding-top: 25px;
            text-align: center;
        }
        
        .signature .name {
            font-weight: bold;
            font-size: 18px;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RESEARCH INTERNSHIP INQUIRY</h1>
            <p>Computer Science and Computational Systems Research Opportunity</p>
        </div>
        
        <p><strong>Dear Prof. {{ professor.last_name }},</strong></p>
        
        <div class="research-highlight">
            <h3>🎯 Research Alignment with {{ professor.research_area }}</h3>
            <p>{{ personalization.technical_synergy }}</p>
        </div>
        
        <p>I am Anamay Tripathy, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in a research internship opportunity with your esteemed group at {{ professor.university }}, particularly in the areas of <strong>{{ professor.research_area }}</strong> and its intersection with artificial intelligence applications.</p>

        <p>Your pioneering contributions to {{ professor.research_area }} and computational systems have been a significant inspiration for my academic journey. I am particularly drawn to the intersection of theoretical concepts and practical applications, and I am eager to contribute meaningfully to your ongoing research while deepening my understanding under your guidance.</p>
        
        <div class="section">
            <h3 class="section-title">🎓 Academic Background</h3>
            <p><strong>Degree:</strong> B.Tech in Data Science Engineering (2023–2027)<br>
            <strong>Institution:</strong> MIT Manipal, India<br>
            <strong>CGPA:</strong> 7.6 / 10</p>
            <p><strong>Relevant Coursework:</strong> Data Structures & Algorithms, Machine Learning, Database Management Systems, Computer Networks</p>
        </div>
        
        <div class="section">
            <h3 class="section-title">💼 Professional Experience</h3>
            <div class="project-item">
                <strong>Technical Head – YaanBarpe (Current)</strong><br>
                Leading technical development and product strategy for a Karnataka Government-incubated startup focused on sustainable solutions. Responsible for system architecture, team coordination, and strategic technology decisions.
            </div>
            
            <div class="project-item">
                <strong>Data Analyst Intern – Intellect Design Arena, Mumbai (3 months)</strong><br>
                • Automated KPI dashboard systems using Python and SQL, resulting in 12+ hours weekly time savings<br>
                • Developed and deployed REST APIs that improved user engagement metrics by 22%<br>
                • Conducted statistical analysis on large datasets to derive actionable business insights
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">🚀 Selected Research-Oriented Projects</h3>
            
            <div class="project-item">
                <strong>CrimeConnect - FBI-Inspired Case Management Dashboard</strong><br>
                Implemented a sophisticated prediction model using XGBoost and Pyodide, incorporating real-time player statistics, historical performance data, and game dynamics analysis. The system achieves 89% prediction accuracy through advanced feature engineering and ensemble learning techniques.
            </div>
            
            <div class="project-item">
                <strong>Advanced Data Analytics Platform</strong><br>
                Developed innovative solutions using cutting-edge technologies and methodologies. Implemented robust systems with focus on performance, scalability, and user experience.
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">🛠️ Technical Competencies</h3>
            <p><strong>Programming Languages:</strong> Python, JavaScript, Java, C++, SQL<br>
            <strong>Web Technologies:</strong> React.js, Node.js, MongoDB, Next.js, RESTful APIs<br>
            <strong>Cloud & DevOps:</strong> AWS, GCP, Docker, Git, Linux/Unix<br>
            <strong>Data Science & Analytics:</strong> Statistical Analysis, Data Visualization, Predictive Modeling<br>
            <strong>Development Tools:</strong> Supabase, Firebase, Jupyter Notebooks, VS Code</p>
        </div>
        
        {% if personalization.has_publications %}
        <div class="section">
            <h3 class="section-title">📄 Research Alignment Analysis</h3>
            <div class="project-item">
                <p><strong>🎯 Research Alignment:</strong> Your research in {{ professor.research_area }} aligns exceptionally well with my systems architecture experience at YaanBarpe, where I design scalable communication systems for our government-incubated platform. My background in distributed systems, cloud infrastructure, and API development provides relevant experience for advancing research in computational methods.</p>
                
                {% if personalization.recent_publication.title %}
                <p><strong>Recent Work Analysis:</strong> I was particularly intrigued by your {{ personalization.recent_publication.year }} work on "{{ personalization.recent_publication.title }}". This research demonstrates exactly the kind of innovative approach I'm passionate about contributing to.</p>
                {% endif %}
            </div>
        </div>
        {% endif %}
        
        <div class="section">
            <h3 class="section-title">🔬 Research Interests and Alignment</h3>
            <p>I am particularly fascinated by the intersection of {{ professor.research_area }} algorithms and real-world applications, especially in the context of predictive modeling and automated decision-making systems. My academic coursework in deep learning and practical experience in implementing ML models has prepared me to contribute meaningfully to research in these areas.</p>
            
            <p><strong>Proposed Collaboration Areas:</strong></p>
            <ul>
                {% for opportunity in personalization.collaboration_opportunities %}
                <li>{{ opportunity }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <p>I am seeking a research internship opportunity—whether remote or on-site, funded or voluntary—to contribute to your ongoing research while gaining invaluable experience that will inform my planned graduate studies in computer science and related fields.</p>

        <p>I would be honored to discuss how my technical background, research interests, and enthusiasm for {{ professor.research_area }} can contribute to your laboratory's ongoing work. I have attached my detailed curriculum vitae for your review, and I would welcome the opportunity to provide any additional information or documentation that would be helpful.</p>

        <p>Thank you very much for your time and consideration. I look forward to the possibility of contributing to your research group.</p>
        
        <div class="contact-info">
            <h3 class="section-title">📞 Contact Information</h3>
            <p><strong>Email:</strong> tripathy.anamay23@gmail.com<br>
            <strong>Phone:</strong> +91-9877454747<br>
            <strong>Portfolio:</strong> <a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
            <strong>LinkedIn:</strong> <a href="https://linkedin.com/in/anamay-tripathy">linkedin.com/in/anamay-tripathy</a><br>
            <strong>GitHub:</strong> <a href="https://github.com/Flamechargerr">github.com/Flamechargerr</a></p>
        </div>
        
        <div class="signature">
            <p>Sincerely,</p>
            <p class="name">Anamay Tripathy</p>
            <p><em>B.Tech Data Science Engineering</em><br>
            MIT Manipal, India</p>
        </div>
    </div>
</body>
</html>'''
    
    async def generate_html_email_content(self, professor: dict) -> tuple:
        """Generate sophisticated HTML email content with research analysis"""
        try:
            # Extract professor data
            name = str(professor.get('name', 'Professor')).strip()
            email = str(professor.get('email', '')).strip()
            university = str(professor.get('affiliation', 'University')).strip()
            
            # Research analysis
            profile_data = await self.research_assistant.analyze_professor_profile(name, university, email)
            
            # Prepare template context
            context = {
                'professor': {
                    'name': name,
                    'last_name': name.split()[-1] if name.split() else 'Professor',
                    'university': university,
                    'research_area': profile_data['primary_research_area'],
                    'email': email
                },
                'personalization': profile_data['personalization_data'],
                'research_areas': profile_data['research_areas'],
                'alignment_score': profile_data['alignment_score']
            }
            
            # Load and render template
            template_content = self.load_html_template()
            template = Template(template_content)
            html_content = template.render(**context)
            
            # Generate subject
            subject = f"Research Collaboration Opportunity - {profile_data['primary_research_area']}"
            
            return subject, html_content, profile_data
            
        except Exception as e:
            logger.error(f"HTML content generation error: {e}")
            # Fallback to simplified content
            return self._generate_fallback_content(professor)
    
    def _generate_fallback_content(self, professor: dict) -> tuple:
        """Generate fallback HTML content if analysis fails"""
        name = str(professor.get('name', 'Professor')).strip()
        university = str(professor.get('affiliation', 'University')).strip()
        
        simple_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Research Collaboration Inquiry</h2>
                <p>Dear Professor {name.split()[-1] if name.split() else 'Professor'},</p>
                <p>I am Anamay Tripathy, a Computer Science student interested in research collaboration opportunities at {university}.</p>
                <p>I would welcome the opportunity to discuss potential research collaboration in your area of expertise.</p>
                <p>Best regards,<br>Anamay Tripathy</p>
            </div>
        </body>
        </html>
        """
        
        return f"Research Collaboration Opportunity - Computer Science", simple_html, {'found_research': False}
    
    async def send_html_email_with_cv(self, professor: dict, index: int) -> ProfessorResult:
        """Send sophisticated HTML email with CV attachment"""
        try:
            email = professor['email']
            name = professor['name']
            university = professor.get('affiliation', 'University')
            
            # Check duplicates
            if email in self.sent_emails:
                with self.lock:
                    self.stats['duplicates_skipped'] += 1
                
                return ProfessorResult(
                    email=email,
                    name=name,
                    university=university,
                    research_area='Unknown',
                    status='duplicate_skipped',
                    timestamp=datetime.now()
                )
            
            # Generate HTML content
            subject, html_content, profile_data = await self.generate_html_email_content(professor)
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("Anamay Tripathy", self.smtp_config['username']))
            msg['To'] = email
            msg['Subject'] = subject
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach CV if available
            if self.cv_path.exists():
                with open(self.cv_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    'attachment; filename=CV_Anamay_Tripathy.pdf'
                )
                msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'], timeout=30) as server:
                server.starttls(context=context)
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.sendmail(self.smtp_config['username'], email, msg.as_string())
            
            # Track success
            with self.lock:
                self.sent_emails.add(email)
                self.stats['emails_sent'] += 1
                if profile_data.get('found_research'):
                    self.stats['research_found'] += 1
            
            # Save email record
            self._save_email_record(professor, subject, html_content, profile_data)
            
            return ProfessorResult(
                email=email,
                name=name,
                university=university,
                research_area=profile_data.get('primary_research_area', 'Computer Science'),
                status='success',
                timestamp=datetime.now(),
                publications_found=len(profile_data.get('publications', []))
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"HTML email send error for {professor.get('email', 'unknown')}: {error_msg}")
            
            with self.lock:
                self.stats['errors'] += 1
            
            return ProfessorResult(
                email=professor.get('email', ''),
                name=professor.get('name', ''),
                university=professor.get('affiliation', ''),
                research_area='Unknown',
                status='failed',
                timestamp=datetime.now(),
                error=error_msg
            )
    
    def _save_email_record(self, professor: dict, subject: str, html_content: str, profile_data: dict):
        """Save email record for tracking"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', professor['name'][:20])
            filename = f"html_email_{timestamp}_{safe_name}.html"
            
            filepath = self.results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"<!-- HTML ULTRA CAMPAIGN EMAIL RECORD -->\n")
                f.write(f"<!-- TO: {professor['name']} <{professor['email']}> -->\n")
                f.write(f"<!-- SUBJECT: {subject} -->\n")
                f.write(f"<!-- UNIVERSITY: {professor.get('affiliation', 'Unknown')} -->\n")
                f.write(f"<!-- TIMESTAMP: {datetime.now()} -->\n")
                f.write(f"<!-- RESEARCH AREAS: {', '.join(profile_data.get('research_areas', []))} -->\n")
                f.write(f"<!-- PUBLICATIONS FOUND: {len(profile_data.get('publications', []))} -->\n")
                f.write(f"<!-- TEMPLATE: html_sophisticated -->\n\n")
                f.write(html_content)
                
        except Exception as e:
            logger.error(f"Error saving HTML email record: {e}")
    
    async def run_html_campaign(self, max_emails: int = 50):
        """Run the sophisticated HTML campaign"""
        print(f"\n🚀 LAUNCHING HTML ULTRA CAMPAIGN")
        print("=" * 55)
        print(f"🎯 Target emails: {max_emails}")
        print(f"🎨 Template: Advanced HTML with Research Analysis")
        print(f"📎 CV Attachment: Enabled")
        print(f"🔍 Research Analysis: Active")
        print(f"🚫 Duplicate Prevention: Active")
        
        # Load database
        df = self.load_professor_database()
        if df.empty:
            print("❌ No valid professor data available")
            return
        
        # Select professors
        target_df = df.head(max_emails)
        print(f"\n📧 Processing {len(target_df)} professors")
        print(f"⏱️  Estimated time: {len(target_df) * 2:.1f} seconds")
        
        # Confirm launch
        print(f"\n🎯 Ready to launch HTML campaign")
        confirm = input("🚀 Launch campaign? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Campaign cancelled")
            return
        
        start_time = time.time()
        print(f"\n⚡ HTML CAMPAIGN LAUNCHED at {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        # Process with asyncio
        tasks = []
        for idx, (_, professor) in enumerate(target_df.iterrows()):
            task = self.send_html_email_with_cv(professor.to_dict(), idx)
            tasks.append(task)
        
        # Execute with progress tracking
        completed = 0
        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
                with self.lock:
                    self.stats['errors'] += 1
            else:
                self.results.append(result)
            
            completed += 1
            
            # Progress updates
            if completed % 5 == 0 or completed == len(tasks):
                success_rate = (self.stats['emails_sent'] / max(completed, 1)) * 100
                research_rate = (self.stats['research_found'] / max(self.stats['emails_sent'], 1)) * 100
                
                print(f"📊 Progress: {completed}/{len(tasks)} | "
                      f"Success: {success_rate:.1f}% | "
                      f"Research: {research_rate:.1f}% | "
                      f"Sent: {self.stats['emails_sent']}")
        
        # Save results
        self.save_sent_emails()
        
        # Final report
        total_time = time.time() - start_time
        success_rate = (self.stats['emails_sent'] / max(len(target_df), 1)) * 100
        
        print(f"\n🎉 HTML ULTRA CAMPAIGN COMPLETE!")
        print("=" * 60)
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📧 HTML Emails sent: {self.stats['emails_sent']}")
        print(f"📎 CV attachments: {self.stats['emails_sent']}")
        print(f"🔍 Research analysis: {self.stats['research_found']}")
        print(f"🚫 Duplicates skipped: {self.stats['duplicates_skipped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"🎯 Success rate: {success_rate:.1f}%")
        print(f"📁 HTML records saved to: {self.results_dir}")
        print("=" * 60)

def main():
    """Main function to run the HTML ultra campaign"""
    try:
        # Initialize system
        system = HTMLUltraAutomatedAICampaignSystem()
        
        # Get parameters
        print(f"\n📋 HTML CAMPAIGN CONFIGURATION")
        print("=" * 45)
        
        try:
            max_emails = int(input("📧 How many HTML emails to send? (recommended: 5-50): ").strip())
            if max_emails <= 0 or max_emails > 500:
                print("⚠️  Using default: 25 emails")
                max_emails = 25
        except:
            print("⚠️  Invalid input, using default: 25 emails")
            max_emails = 25
        
        # Run campaign
        asyncio.run(system.run_html_campaign(max_emails))
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  HTML campaign stopped by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        logger.error(f"HTML system error: {e}")

if __name__ == "__main__":
    main()
