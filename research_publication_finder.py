#!/usr/bin/env python3
"""
Research Publication Finder
Extract recent research publications for professors to enhance email personalization
"""

import requests
import json
import time
import re
from typing import Dict, List, Optional
from urllib.parse import quote_plus
import pandas as pd

class ResearchPublicationFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_semantic_scholar(self, professor_name: str, affiliation: str = "", max_results: int = 5) -> List[Dict]:
        """Search Semantic Scholar for professor's recent publications"""
        try:
            # Clean professor name
            clean_name = re.sub(r'\s+', ' ', professor_name.strip())
            
            # Search for author
            search_url = f"https://api.semanticscholar.org/graph/v1/author/search"
            params = {
                'query': clean_name,
                'limit': 10,
                'fields': 'authorId,name,affiliations,url'
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code != 200:
                return []
            
            authors_data = response.json().get('data', [])
            
            # Find the best matching author using the score-based approach
            best_author = None
            best_score = 0
            
            for author in authors_data:
                score = self._calculate_match_score(
                    clean_name, 
                    author.get('name', ''), 
                    affiliation, 
                    author.get('affiliations', [])
                )
                if score > best_score:
                    best_score = score
                    best_author = author
            
            # Only proceed if we have a reasonable match (score > 0.5)
            if not best_author or best_score < 0.5:
                return []
            
            # Get author's papers
            author_id = best_author['authorId']
            papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
            params = {
                'limit': max_results,
                'fields': 'title,year,abstract,authors,url,venue'
            }
            
            response = self.session.get(papers_url, params=params)
            if response.status_code != 200:
                return []
            
            papers_data = response.json().get('data', [])
            
            # Filter and format papers
            recent_papers = []
            for paper in papers_data:
                year = paper.get('year', 0)
                if year and 2020 <= year <= 2025:
                    recent_papers.append({
                        'title': paper.get('title', ''),
                        'year': str(year),
                        'summary': paper.get('abstract', '')[:300] + '...' if paper.get('abstract') else '',
                        'venue': paper.get('venue', ''),
                        'url': paper.get('url', '')
                    })
            
            return recent_papers[:max_results]
            
        except Exception as e:
            print(f"Error searching Semantic Scholar for {professor_name}: {e}")
            return []
    
    def search_google_scholar(self, professor_name: str, max_results: int = 5) -> List[Dict]:
        """Search Google Scholar for professor's recent publications (simplified)"""
        try:
            # Note: Google Scholar doesn't have a public API, so this is a simplified approach
            # In a real implementation, you might use a service like SerpAPI or similar
            
            # For now, return empty list - would need API key for proper implementation
            return []
            
        except Exception as e:
            print(f"Error searching Google Scholar for {professor_name}: {e}")
            return []
    
    def search_dblp(self, professor_name: str, max_results: int = 5) -> List[Dict]:
        """Search DBLP for professor's recent publications"""
        try:
            # Clean professor name
            clean_name = re.sub(r'\s+', ' ', professor_name.strip())
            
            # Search DBLP
            search_url = f"https://dblp.org/search/author"
            params = {
                'q': clean_name
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code != 200:
                return []
            
            # Parse DBLP response (simplified - would need proper HTML parsing)
            # For now, return empty list
            return []
            
        except Exception as e:
            print(f"Error searching DBLP for {professor_name}: {e}")
            return []
    
    def _name_matches(self, search_name: str, author_name: str) -> bool:
        """Check if names match (fuzzy matching)"""
        search_parts = set(search_name.lower().split())
        author_parts = set(author_name.lower().split())
        
        # Check for common parts
        common_parts = search_parts.intersection(author_parts)
        return len(common_parts) >= min(len(search_parts), len(author_parts)) * 0.7

    def _calculate_match_score(self, search_name: str, author_name: str, search_affiliation: str, author_affiliations: List[str]) -> float:
        """Calculate a match score between a search query and an author"""
        # Handle empty search name
        if not search_name.strip():
            return 0.0
            
        # Name similarity
        search_parts = set(search_name.lower().split())
        author_parts = set(author_name.lower().split())
        
        if not search_parts:
            return 0.0
            
        name_similarity = len(search_parts.intersection(author_parts)) / len(search_parts)

        # Affiliation similarity
        affiliation_similarity = 0
        if author_affiliations and search_affiliation:
            for aff in author_affiliations:
                if search_affiliation.lower() in aff.lower():
                    affiliation_similarity = 1
                    break

        # Combine scores
        return (name_similarity * 0.7) + (affiliation_similarity * 0.3)
    
    def get_professor_publications(self, professor_name: str, affiliation: str = "", max_results: int = 5) -> List[Dict]:
        """Get professor's recent publications from multiple sources"""
        publications = []
        
        # Try Semantic Scholar first (most reliable)
        publications = self.search_semantic_scholar(professor_name, affiliation, max_results)
        
        # If no results, try other sources
        if not publications:
            publications = self.search_google_scholar(professor_name, max_results)
        
        if not publications:
            publications = self.search_dblp(professor_name, max_results)
        
        return publications
    
    def get_publications_for_professors(self, professors_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Get publications for multiple professors"""
        results = {}
        
        for professor in professors_data:
            name = professor.get('name', '')
            affiliation = professor.get('affiliation', '')
            if name:
                print(f"🔍 Searching publications for {name}...")
                publications = self.get_professor_publications(name, affiliation, max_results=3)
                results[name] = publications
                
                if publications:
                    print(f"   ✅ Found {len(publications)} recent publications")
                else:
                    print(f"   ⚠️ No recent publications found")
                
                # Small delay to be respectful to APIs
                time.sleep(1)
        
        return results

def test_publication_finder():
    """Test the publication finder with sample professors"""
    finder = ResearchPublicationFinder()
    
    test_professors = [
        {'name': 'Abhishek Bhattacharjee', 'affiliation': 'Yale University'},
        {'name': 'Aaron Bernstein', 'affiliation': 'New York University'},
        {'name': 'Abhinav Gupta', 'affiliation': 'Carnegie Mellon University'}
    ]
    
    print("🧪 TESTING RESEARCH PUBLICATION FINDER")
    print("=" * 60)
    
    results = finder.get_publications_for_professors(test_professors)
    
    for professor_name, publications in results.items():
        print(f"\n👤 {professor_name}")
        if publications:
            for i, pub in enumerate(publications, 1):
                print(f"   📄 {i}. {pub['title']} ({pub['year']})")
                if pub['summary']:
                    print(f"      Summary: {pub['summary'][:100]}...")
        else:
            print("   ⚠️ No recent publications found")
    
    print("\n✅ Publication finder test completed!")

if __name__ == "__main__":
    test_publication_finder() 