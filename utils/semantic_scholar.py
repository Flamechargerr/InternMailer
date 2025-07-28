"""
Semantic Scholar API integration for fetching professor research data.

This module provides functionality to:
- Fetch recent papers and abstracts using professor names or IDs
- Extract key research keywords and focus areas from papers
- Identify collaboration patterns and trending research directions
- Enhance email generation with current research insights
"""

import requests
import time
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime, timedelta
import re
from collections import Counter


class SemanticScholarAPI:
    """Interface for Semantic Scholar Academic Graph API."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Semantic Scholar API client.
        
        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.headers = {
            'User-Agent': 'Academic-Email-Generator/1.0',
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['x-api-key'] = api_key
        
        # Rate limiting
        self.last_request_time = 0
        self.min_interval = 1.0  # Minimum seconds between requests
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to the Semantic Scholar API."""
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
    
    def search_author(self, author_name: str, limit: int = 10) -> List[Dict]:
        """
        Search for authors by name.
        
        Args:
            author_name: Name of the author to search for
            limit: Maximum number of results to return
            
        Returns:
            List of author dictionaries with basic info
        """
        params = {
            'query': author_name,
            'limit': limit,
            'fields': 'authorId,name,affiliations,paperCount,citationCount,hIndex'
        }
        
        result = self._make_request('author/search', params)
        return result.get('data', []) if result else []
    
    def get_author_papers(self, author_id: str, limit: int = 50, 
                         years_back: int = 3) -> List[Dict]:
        """
        Get recent papers by an author.
        
        Args:
            author_id: Semantic Scholar author ID
            limit: Maximum number of papers to fetch
            years_back: How many years back to look for papers
            
        Returns:
            List of paper dictionaries
        """
        current_year = datetime.now().year
        start_year = current_year - years_back
        
        params = {
            'limit': limit,
            'fields': 'paperId,title,abstract,year,citationCount,authors,venue,fieldsOfStudy,publicationDate'
        }
        
        result = self._make_request(f'author/{author_id}/papers', params)
        papers = result.get('data', []) if result else []
        
        # Filter by year
        recent_papers = [
            paper for paper in papers 
            if paper.get('year') and paper['year'] >= start_year
        ]
        
        return recent_papers
    
    def extract_research_keywords(self, papers: List[Dict], 
                                top_n: int = 20) -> List[Tuple[str, int]]:
        """
        Extract key research terms from paper titles and abstracts.
        
        Args:
            papers: List of paper dictionaries
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, frequency) tuples
        """
        text_content = []
        
        for paper in papers:
            if paper.get('title'):
                text_content.append(paper['title'])
            if paper.get('abstract'):
                text_content.append(paper['abstract'])
        
        # Combine all text
        full_text = ' '.join(text_content).lower()
        
        # Extract meaningful terms (simple approach)
        # Remove common words and extract technical terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'we', 'our',
            'using', 'used', 'use', 'based', 'approach', 'method', 'methods',
            'results', 'show', 'shows', 'paper', 'study', 'research', 'work'
        }
        
        # Extract words (including compound terms with hyphens)
        words = re.findall(r'\b[a-z][\w-]*[a-z]\b|\b[a-z]\b', full_text)
        
        # Filter and count
        meaningful_words = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        word_counts = Counter(meaningful_words)
        return word_counts.most_common(top_n)
    
    def get_collaboration_network(self, papers: List[Dict]) -> Dict[str, int]:
        """
        Identify frequent collaborators from papers.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Dictionary of collaborator names and collaboration counts
        """
        collaborators = Counter()
        
        for paper in papers:
            if paper.get('authors'):
                for author in paper['authors']:
                    if author.get('name'):
                        collaborators[author['name']] += 1
        
        # Remove the main author (highest count) if present
        if collaborators:
            main_author = collaborators.most_common(1)[0][0]
            del collaborators[main_author]
        
        return dict(collaborators.most_common(10))
    
    def analyze_research_trends(self, papers: List[Dict]) -> Dict:
        """
        Analyze research trends from recent papers.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Dictionary with trend analysis
        """
        if not papers:
            return {}
        
        # Sort papers by year
        papers_by_year = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                if year not in papers_by_year:
                    papers_by_year[year] = []
                papers_by_year[year].append(paper)
        
        # Get recent trends
        keywords_by_year = {}
        for year, year_papers in papers_by_year.items():
            keywords = self.extract_research_keywords(year_papers, top_n=10)
            keywords_by_year[year] = keywords
        
        # Get fields of study trends
        fields_counter = Counter()
        for paper in papers:
            if paper.get('fieldsOfStudy'):
                for field in paper['fieldsOfStudy']:
                    fields_counter[field] += 1
        
        # Calculate citation trends
        total_citations = sum(paper.get('citationCount', 0) for paper in papers)
        avg_citations = total_citations / len(papers) if papers else 0
        
        return {
            'papers_by_year': {year: len(papers) for year, papers in papers_by_year.items()},
            'top_fields': dict(fields_counter.most_common(10)),
            'recent_keywords': keywords_by_year,
            'total_citations': total_citations,
            'avg_citations_per_paper': round(avg_citations, 2),
            'total_papers_analyzed': len(papers)
        }


class ProfessorResearchAnalyzer:
    """High-level analyzer for professor research data."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api = SemanticScholarAPI(api_key)
    
    def analyze_professor(self, professor_name: str, 
                         affiliation_hint: Optional[str] = None) -> Dict:
        """
        Comprehensive analysis of a professor's recent research.
        
        Args:
            professor_name: Name of the professor
            affiliation_hint: Optional university/institution name to help disambiguation
            
        Returns:
            Dictionary with comprehensive research analysis
        """
        print(f"Searching for professor: {professor_name}")
        
        # Search for the author
        authors = self.api.search_author(professor_name)
        
        if not authors:
            return {"error": f"No authors found for '{professor_name}'"}
        
        # If affiliation hint provided, try to find best match
        best_author = authors[0]
        if affiliation_hint and len(authors) > 1:
            for author in authors:
                if author.get('affiliations'):
                    for affiliation in author['affiliations']:
                        if affiliation_hint.lower() in affiliation.lower():
                            best_author = author
                            break
        
        print(f"Analyzing author: {best_author.get('name')} (ID: {best_author.get('authorId')})")
        
        # Get recent papers
        papers = self.api.get_author_papers(best_author['authorId'])
        
        if not papers:
            return {
                "author_info": best_author,
                "error": "No recent papers found"
            }
        
        print(f"Found {len(papers)} recent papers")
        
        # Perform comprehensive analysis
        keywords = self.api.extract_research_keywords(papers)
        collaborators = self.api.get_collaboration_network(papers)
        trends = self.api.analyze_research_trends(papers)
        
        # Get most recent and highly cited papers
        recent_papers = sorted(papers, key=lambda x: x.get('year', 0), reverse=True)[:5]
        cited_papers = sorted(papers, key=lambda x: x.get('citationCount', 0), reverse=True)[:5]
        
        return {
            "author_info": best_author,
            "research_keywords": keywords,
            "frequent_collaborators": collaborators,
            "research_trends": trends,
            "recent_papers": [
                {
                    "title": paper.get('title'),
                    "year": paper.get('year'),
                    "abstract": paper.get('abstract', '')[:300] + '...' if paper.get('abstract') else '',
                    "citations": paper.get('citationCount', 0),
                    "venue": paper.get('venue')
                }
                for paper in recent_papers
            ],
            "highly_cited_papers": [
                {
                    "title": paper.get('title'),
                    "year": paper.get('year'),
                    "citations": paper.get('citationCount', 0),
                    "venue": paper.get('venue')
                }
                for paper in cited_papers
            ]
        }
    
    def generate_research_summary(self, analysis: Dict) -> str:
        """
        Generate a human-readable research summary from analysis data.
        
        Args:
            analysis: Result from analyze_professor
            
        Returns:
            Formatted research summary string
        """
        if "error" in analysis:
            return f"Analysis Error: {analysis['error']}"
        
        author_info = analysis.get("author_info", {})
        keywords = analysis.get("research_keywords", [])
        trends = analysis.get("research_trends", {})
        recent_papers = analysis.get("recent_papers", [])
        
        summary_parts = []
        
        # Author info
        name = author_info.get('name', 'Unknown')
        paper_count = author_info.get('paperCount', 0)
        citation_count = author_info.get('citationCount', 0)
        h_index = author_info.get('hIndex', 0)
        
        summary_parts.append(f"Professor {name} has published {paper_count} papers with {citation_count} total citations (h-index: {h_index}).")
        
        # Research focus
        if keywords:
            top_keywords = [kw[0] for kw in keywords[:8]]
            summary_parts.append(f"Current research focuses on: {', '.join(top_keywords[:5])} and related areas including {', '.join(top_keywords[5:8])}.")
        
        # Recent activity
        total_papers = trends.get('total_papers_analyzed', 0)
        if total_papers > 0:
            summary_parts.append(f"In recent years, published {total_papers} papers with an average of {trends.get('avg_citations_per_paper', 0)} citations per paper.")
        
        # Recent work highlights
        if recent_papers:
            latest_paper = recent_papers[0]
            if latest_paper.get('title'):
                summary_parts.append(f"Most recent work includes '{latest_paper['title'][:100]}...' ({latest_paper.get('year')}).")
        
        return " ".join(summary_parts)


def main():
    """Example usage of the Semantic Scholar integration."""
    # Initialize analyzer (add your API key if you have one)
    analyzer = ProfessorResearchAnalyzer(api_key=None)
    
    # Example analysis
    professor_name = input("Enter professor name: ").strip()
    university = input("Enter university (optional): ").strip() or None
    
    print("\nAnalyzing professor's research...")
    analysis = analyzer.analyze_professor(professor_name, university)
    
    print("\n" + "="*50)
    print("RESEARCH ANALYSIS SUMMARY")
    print("="*50)
    
    summary = analyzer.generate_research_summary(analysis)
    print(summary)
    
    # Print detailed results
    if "research_keywords" in analysis:
        print(f"\nTop Research Keywords:")
        for keyword, count in analysis["research_keywords"][:10]:
            print(f"  - {keyword} ({count} mentions)")
    
    if "recent_papers" in analysis:
        print(f"\nRecent Papers:")
        for paper in analysis["recent_papers"][:3]:
            print(f"  - {paper['title']} ({paper['year']}) - {paper['citations']} citations")


if __name__ == "__main__":
    main()
