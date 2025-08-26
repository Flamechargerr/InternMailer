"""
🤖 GPT-4 RESEARCH PAPER ANALYSIS SYSTEM
=======================================
Revolutionary AI-powered research paper analysis for 10x personalization
- Auto-analyze professor's recent papers using OpenAI GPT-4
- Generate highly personalized research connections
- Create contextual email content based on paper abstracts
- Extract specific paper titles, methodologies, and findings
"""

import openai
import requests
import json
import time
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import concurrent.futures
from urllib.parse import quote_plus
import re

@dataclass
class ResearchPaper:
    """Data structure for research paper information"""
    title: str
    abstract: str
    authors: List[str]
    year: str
    journal: str
    doi: str = ""
    citations: int = 0
    keywords: List[str] = None
    methodology: str = ""
    findings: str = ""
    impact_score: float = 0.0

@dataclass
class GPTAnalysisResult:
    """Result of GPT-4 analysis"""
    personalized_mention: str
    specific_paper_reference: str
    methodology_connection: str
    research_alignment: str
    collaboration_potential: str
    technical_depth: str
    confidence_score: float
    paper_summaries: List[Dict]

class GPT4ResearchAnalyzer:
    """Revolutionary GPT-4 powered research analysis system"""
    
    def __init__(self):
        # Initialize OpenAI API
        self.openai_client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')  # Set in .env file
        )
        
        # Analysis prompts for different aspects
        self.analysis_prompts = {
            'paper_summary': """
                Analyze this research paper and extract:
                1. Main research question/problem
                2. Methodology used
                3. Key findings/contributions
                4. Technical innovation
                5. Real-world applications
                
                Paper: {paper_info}
                
                Provide a structured analysis in JSON format.
            """,
            
            'personalization': """
                Based on these research papers by Professor {professor_name}, create a highly personalized 
                email mention that:
                1. References specific paper titles and findings
                2. Shows deep understanding of their methodology  
                3. Connects to student's ML/data science background
                4. Suggests specific collaboration opportunities
                5. Demonstrates genuine research interest
                
                Research papers: {papers_info}
                
                Create a compelling, specific research mention (not generic).
            """,
            
            'collaboration_analysis': """
                Analyze the research papers and identify:
                1. Potential collaboration areas for a Data Science student
                2. Specific technical skills that would be valuable
                3. Research gaps where student could contribute
                4. Methodological improvements student could suggest
                
                Papers: {papers_info}
                Student background: ML, Data Science, Python, TensorFlow, Statistical Analysis
                
                Provide actionable collaboration suggestions.
            """
        }
        
        # Enhanced research sources
        self.research_sources = {
            'semantic_scholar': 'https://api.semanticscholar.org/graph/v1/author/search',
            'crossref': 'https://api.crossref.org/works',
            'arxiv': 'http://export.arxiv.org/api/query',
            'pubmed': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        }
        
        # Cache for processed papers
        self.paper_cache = {}
        
    def analyze_professor_research(self, professor_name: str, email: str, limit: int = 5) -> GPTAnalysisResult:
        """
        🚀 Revolutionary GPT-4 analysis of professor's research
        Returns specific paper mentions and collaboration insights
        """
        try:
            print(f"🤖 GPT-4 analyzing research for {professor_name}...")
            
            # Step 1: Get recent papers from multiple sources
            papers = self._fetch_recent_papers(professor_name, email, limit)
            
            if not papers:
                return self._generate_fallback_analysis(professor_name, email)
            
            # Step 2: GPT-4 analysis of each paper
            paper_analyses = self._analyze_papers_with_gpt4(papers)
            
            # Step 3: Generate personalized mentions
            personalized_content = self._generate_personalized_content(
                professor_name, papers, paper_analyses
            )
            
            # Step 4: Create collaboration analysis
            collaboration_insights = self._analyze_collaboration_potential(
                papers, paper_analyses
            )
            
            return GPTAnalysisResult(
                personalized_mention=personalized_content['mention'],
                specific_paper_reference=personalized_content['paper_ref'],
                methodology_connection=personalized_content['methodology'],
                research_alignment=personalized_content['alignment'],
                collaboration_potential=collaboration_insights['potential'],
                technical_depth=collaboration_insights['technical_areas'],
                confidence_score=self._calculate_confidence_score(papers, paper_analyses),
                paper_summaries=paper_analyses
            )
            
        except Exception as e:
            print(f"❌ GPT-4 analysis failed for {professor_name}: {e}")
            return self._generate_fallback_analysis(professor_name, email)
    
    def _fetch_recent_papers(self, professor_name: str, email: str, limit: int) -> List[ResearchPaper]:
        """Fetch recent papers from multiple academic sources"""
        papers = []
        
        try:
            # Source 1: Semantic Scholar (most comprehensive)
            semantic_papers = self._fetch_semantic_scholar_papers(professor_name, limit)
            papers.extend(semantic_papers)
            
            # Source 2: ArXiv (for CS papers)
            arxiv_papers = self._fetch_arxiv_papers(professor_name, limit//2)
            papers.extend(arxiv_papers)
            
            # Source 3: CrossRef (journal papers)
            crossref_papers = self._fetch_crossref_papers(professor_name, limit//2)
            papers.extend(crossref_papers)
            
            # Remove duplicates and sort by year
            unique_papers = self._deduplicate_papers(papers)
            recent_papers = sorted(unique_papers, key=lambda x: x.year, reverse=True)[:limit]
            
            print(f"📚 Found {len(recent_papers)} recent papers for analysis")
            return recent_papers
            
        except Exception as e:
            print(f"⚠️ Paper fetching failed: {e}")
            return []
    
    def _fetch_semantic_scholar_papers(self, professor_name: str, limit: int) -> List[ResearchPaper]:
        """Fetch papers from Semantic Scholar API"""
        papers = []
        
        try:
            # Search for author
            search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(professor_name)}"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                authors_data = response.json()
                
                if authors_data.get('data'):
                    author_id = authors_data['data'][0]['authorId']
                    
                    # Get author's papers
                    papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
                    papers_response = requests.get(
                        papers_url, 
                        params={
                            'fields': 'title,abstract,year,journal,authors,citationCount,url',
                            'limit': limit * 2  # Get more to filter recent ones
                        },
                        timeout=15
                    )
                    
                    if papers_response.status_code == 200:
                        papers_data = papers_response.json()
                        
                        for paper_info in papers_data.get('data', []):
                            if paper_info.get('year', 0) >= 2020:  # Recent papers only
                                paper = ResearchPaper(
                                    title=paper_info.get('title', ''),
                                    abstract=paper_info.get('abstract', '')[:500],  # Limit abstract length
                                    authors=[a.get('name', '') for a in paper_info.get('authors', [])],
                                    year=str(paper_info.get('year', '')),
                                    journal=paper_info.get('journal', {}).get('name', '') if paper_info.get('journal') else '',
                                    citations=paper_info.get('citationCount', 0)
                                )
                                papers.append(paper)
            
            print(f"📊 Semantic Scholar: {len(papers)} papers found")
            
        except Exception as e:
            print(f"⚠️ Semantic Scholar fetch failed: {e}")
        
        return papers[:limit]
    
    def _fetch_arxiv_papers(self, professor_name: str, limit: int) -> List[ResearchPaper]:
        """Fetch papers from ArXiv for computer science papers"""
        papers = []
        
        try:
            # ArXiv search query
            query = f"au:{quote_plus(professor_name)}"
            arxiv_url = f"http://export.arxiv.org/api/query?search_query={query}&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
            
            response = requests.get(arxiv_url, timeout=10)
            
            if response.status_code == 200:
                # Parse XML response (simplified)
                content = response.text
                
                # Extract paper information using regex (basic XML parsing)
                titles = re.findall(r'<title>(.*?)</title>', content)
                abstracts = re.findall(r'<summary>(.*?)</summary>', content, re.DOTALL)
                
                for i, title in enumerate(titles[1:]):  # Skip first title (query info)
                    if i < len(abstracts) and i < limit:
                        paper = ResearchPaper(
                            title=title.strip(),
                            abstract=abstracts[i].strip()[:500],
                            authors=[professor_name],  # Simplified
                            year=str(datetime.now().year),  # Approximate
                            journal="arXiv preprint"
                        )
                        papers.append(paper)
            
            print(f"📄 ArXiv: {len(papers)} papers found")
            
        except Exception as e:
            print(f"⚠️ ArXiv fetch failed: {e}")
        
        return papers
    
    def _fetch_crossref_papers(self, professor_name: str, limit: int) -> List[ResearchPaper]:
        """Fetch papers from CrossRef for journal publications"""
        papers = []
        
        try:
            # CrossRef search
            crossref_url = f"https://api.crossref.org/works?query.author={quote_plus(professor_name)}&rows={limit}&sort=published&order=desc"
            
            response = requests.get(crossref_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('message', {}).get('items', []):
                    if item.get('published-print', {}).get('date-parts'):
                        year = item['published-print']['date-parts'][0][0]
                        if year >= 2020:  # Recent papers only
                            paper = ResearchPaper(
                                title=' '.join(item.get('title', [])),
                                abstract=item.get('abstract', '')[:500] if item.get('abstract') else '',
                                authors=[f"{a.get('given', '')} {a.get('family', '')}" for a in item.get('author', [])],
                                year=str(year),
                                journal=item.get('container-title', [''])[0] if item.get('container-title') else '',
                                doi=item.get('DOI', '')
                            )
                            papers.append(paper)
            
            print(f"📖 CrossRef: {len(papers)} papers found")
            
        except Exception as e:
            print(f"⚠️ CrossRef fetch failed: {e}")
        
        return papers
    
    def _deduplicate_papers(self, papers: List[ResearchPaper]) -> List[ResearchPaper]:
        """Remove duplicate papers based on title similarity"""
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            # Simple deduplication by normalized title
            normalized_title = re.sub(r'[^\w\s]', '', paper.title.lower()).strip()
            if normalized_title and normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_papers.append(paper)
        
        return unique_papers
    
    def _analyze_papers_with_gpt4(self, papers: List[ResearchPaper]) -> List[Dict]:
        """Analyze papers using GPT-4 for deep insights"""
        analyses = []
        
        for paper in papers[:3]:  # Analyze top 3 papers to avoid rate limits
            try:
                # Prepare paper information for GPT-4
                paper_info = {
                    'title': paper.title,
                    'abstract': paper.abstract[:800],  # Limit for token usage
                    'year': paper.year,
                    'journal': paper.journal,
                    'authors': paper.authors[:5]  # Limit authors
                }
                
                # GPT-4 analysis
                analysis = self._call_gpt4_analysis(paper_info)
                analyses.append({
                    'paper': paper_info,
                    'analysis': analysis,
                    'processed_at': datetime.now().isoformat()
                })
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ GPT-4 analysis failed for paper: {paper.title[:50]}...")
                analyses.append({
                    'paper': {'title': paper.title},
                    'analysis': {'error': str(e)},
                    'processed_at': datetime.now().isoformat()
                })
        
        return analyses
    
    def _call_gpt4_analysis(self, paper_info: Dict) -> Dict:
        """Call GPT-4 API for paper analysis"""
        try:
            prompt = self.analysis_prompts['paper_summary'].format(
                paper_info=json.dumps(paper_info, indent=2)
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert research analyst. Analyze academic papers and provide structured insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(analysis_text)
            except:
                return {'summary': analysis_text}
                
        except Exception as e:
            print(f"⚠️ GPT-4 API call failed: {e}")
            return {'error': str(e)}
    
    def _generate_personalized_content(self, professor_name: str, papers: List[ResearchPaper], analyses: List[Dict]) -> Dict:
        """Generate highly personalized content using GPT-4"""
        try:
            # Prepare papers info for GPT-4
            papers_summary = []
            for i, paper in enumerate(papers[:3]):
                analysis = analyses[i].get('analysis', {}) if i < len(analyses) else {}
                papers_summary.append({
                    'title': paper.title,
                    'year': paper.year,
                    'journal': paper.journal,
                    'key_findings': analysis.get('summary', 'Innovative research in the field'),
                    'methodology': analysis.get('methodology', 'Advanced computational methods')
                })
            
            # Generate personalized mention using GPT-4
            prompt = self.analysis_prompts['personalization'].format(
                professor_name=professor_name,
                papers_info=json.dumps(papers_summary, indent=2)
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Create highly personalized, specific research mentions for academic emails. Be specific about papers, methodologies, and findings."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.4
            )
            
            personalized_text = response.choices[0].message.content
            
            # Parse the response (fallback to sections if not structured)
            return {
                'mention': f"your groundbreaking research in {papers[0].title[:50]}..." if papers else "your research contributions",
                'paper_ref': f"particularly your {papers[0].year} work on '{papers[0].title}'" if papers else "your recent publications",
                'methodology': personalized_text[:200],
                'alignment': personalized_text[200:] if len(personalized_text) > 200 else personalized_text
            }
            
        except Exception as e:
            print(f"⚠️ GPT-4 personalization failed: {e}")
            return {
                'mention': f"your research contributions in computational science",
                'paper_ref': "your recent academic publications",
                'methodology': "innovative computational approaches",
                'alignment': "research methodologies that align with data science applications"
            }
    
    def _analyze_collaboration_potential(self, papers: List[ResearchPaper], analyses: List[Dict]) -> Dict:
        """Analyze collaboration potential using GPT-4"""
        try:
            papers_info = json.dumps([
                {'title': p.title, 'abstract': p.abstract[:300]}
                for p in papers[:2]
            ])
            
            prompt = self.analysis_prompts['collaboration_analysis'].format(
                papers_info=papers_info
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Analyze research for collaboration opportunities with data science students."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            collaboration_text = response.choices[0].message.content
            
            return {
                'potential': collaboration_text[:150],
                'technical_areas': collaboration_text[150:] if len(collaboration_text) > 150 else "machine learning and data analysis applications"
            }
            
        except Exception as e:
            print(f"⚠️ Collaboration analysis failed: {e}")
            return {
                'potential': "strong alignment with data science and machine learning applications",
                'technical_areas': "statistical analysis, predictive modeling, and computational research methods"
            }
    
    def _calculate_confidence_score(self, papers: List[ResearchPaper], analyses: List[Dict]) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.0
        
        # Base score from number of papers found
        score += min(len(papers) * 0.2, 0.6)
        
        # Score from successful GPT-4 analyses
        successful_analyses = sum(1 for a in analyses if 'error' not in a.get('analysis', {}))
        score += min(successful_analyses * 0.15, 0.3)
        
        # Score from recent papers (2022+)
        recent_papers = sum(1 for p in papers if int(p.year) >= 2022)
        score += min(recent_papers * 0.1, 0.1)
        
        return min(score, 1.0)
    
    def _generate_fallback_analysis(self, professor_name: str, email: str) -> GPTAnalysisResult:
        """Generate fallback analysis when GPT-4 analysis fails"""
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        # Domain-based fallback research areas
        domain_research = {
            'mit.edu': 'artificial intelligence and computational systems',
            'stanford.edu': 'machine learning and human-computer interaction',
            'berkeley.edu': 'data science and computational research',
            'cmu.edu': 'computer science and software engineering'
        }
        
        research_area = next((area for d, area in domain_research.items() if d in domain), 
                           'computational research and data science')
        
        return GPTAnalysisResult(
            personalized_mention=f"your research contributions in {research_area}",
            specific_paper_reference=f"your work in {research_area} and related fields",
            methodology_connection="computational methodologies and data-driven approaches",
            research_alignment=f"research in {research_area} that aligns with data science applications",
            collaboration_potential="potential for collaborative research in computational methods",
            technical_depth="advanced computational research and analytical methods",
            confidence_score=0.4,  # Lower confidence for fallback
            paper_summaries=[]
        )

def get_gpt4_research_analyzer():
    """Get GPT-4 research analyzer instance"""
    return GPT4ResearchAnalyzer()