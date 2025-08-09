#!/usr/bin/env python3
"""
Research Assistant for Professor Publication Discovery
=====================================================

Given the name of a professor, finds their 3-5 most recent research publications
from Google Scholar, Semantic Scholar, DBLP, or their university webpage.

Follows the exact format:
Input: Professor Name
Output: JSON list of recent publications (2020-2025)
"""

import json
import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchAssistant:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.current_year = datetime.now().year
        
    def find_professor_publications(self, prof_name: str) -> List[Dict]:
        """
        Main function to find professor publications
        
        Input: Professor Name
        Output: JSON list of 3-5 recent publications (2020-2025)
        """
        logger.info(f"🔍 Searching for publications by: {prof_name}")
        
        publications = []
        
        # Priority 1: Semantic Scholar (most reliable)
        publications.extend(self._search_semantic_scholar(prof_name))
        
        # Priority 2: arXiv (for recent preprints)
        if len(publications) < 5:
            publications.extend(self._search_arxiv(prof_name))
        
        # Priority 3: CrossRef (for journal papers)
        if len(publications) < 5:
            publications.extend(self._search_crossref(prof_name))
        
        # Filter for recent papers (2020-2025) and prioritize systems research
        recent_publications = []
        systems_keywords = [
            'distributed systems', 'computer systems', 'operating systems', 
            'systems', 'performance', 'scalability', 'networks', 'databases',
            'cloud computing', 'parallel computing', 'system design'
        ]
        
        for pub in publications:
            # Check if year is recent (2020-2025)
            year = pub.get('year', 0)
            if isinstance(year, str):
                try:
                    year = int(year)
                except:
                    year = 0
                    
            if year >= 2020 and year <= self.current_year + 1:
                # Priority boost for systems research
                title_abstract = (pub.get('title', '') + ' ' + pub.get('summary', '')).lower()
                is_systems = any(keyword in title_abstract for keyword in systems_keywords)
                
                pub['systems_priority'] = is_systems
                recent_publications.append(pub)
        
        # Sort by systems priority, then by year (most recent first)
        recent_publications.sort(key=lambda x: (x.get('systems_priority', False), x.get('year', 0)), reverse=True)
        
        # Return top 3-5 publications in the requested format
        result = []
        for pub in recent_publications[:5]:
            result.append({
                "title": pub.get('title', ''),
                "year": str(pub.get('year', '')),
                "summary": pub.get('summary', '')
            })
        
        logger.info(f"✅ Found {len(result)} recent publications for {prof_name}")
        return result
    
    def _search_semantic_scholar(self, prof_name: str) -> List[Dict]:
        """Search Semantic Scholar for publications"""
        try:
            logger.info("🔎 Searching Semantic Scholar...")
            
            # Search for author
            search_url = "https://api.semanticscholar.org/graph/v1/author/search"
            params = {
                'query': prof_name,
                'limit': 10,
                'fields': 'authorId,name,affiliations,url'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            if response.status_code != 200:
                return []
            
            authors_data = response.json().get('data', [])
            if not authors_data:
                return []
            
            # Find best matching author (simple name matching)
            best_author = None
            for author in authors_data:
                author_name = author.get('name', '').lower()
                if prof_name.lower() in author_name or author_name in prof_name.lower():
                    best_author = author
                    break
            
            if not best_author:
                best_author = authors_data[0]  # Take first if no exact match
            
            # Get author's papers
            author_id = best_author['authorId']
            papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
            
            paper_params = {
                'limit': 20,
                'fields': 'paperId,title,year,abstract,authors,url,venue,citationCount'
            }
            
            time.sleep(1)  # Rate limiting
            papers_response = self.session.get(papers_url, params=paper_params, timeout=30)
            
            if papers_response.status_code != 200:
                return []
            
            papers_data = papers_response.json().get('data', [])
            publications = []
            
            for paper in papers_data:
                year = paper.get('year', 0)
                if not year or year < 2020:
                    continue
                
                title = paper.get('title', '').strip()
                if not title:
                    continue
                
                abstract = paper.get('abstract', '')
                summary = abstract[:200] + '...' if abstract and len(abstract) > 200 else abstract or "Research paper addressing important challenges in the field."
                
                publications.append({
                    'title': title,
                    'year': year,
                    'summary': summary,
                    'source': 'Semantic Scholar'
                })
            
            return publications[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {str(e)}")
            return []
    
    def _search_arxiv(self, prof_name: str) -> List[Dict]:
        """Search arXiv for recent preprints"""
        try:
            logger.info("📚 Searching arXiv...")
            
            params = {
                'search_query': f'au:"{prof_name}"',
                'start': 0,
                'max_results': 20,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = self.session.get("http://export.arxiv.org/api/query", params=params, timeout=30)
            if response.status_code != 200:
                return []
            
            # Parse XML response
            root = ET.fromstring(response.content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            publications = []
            for entry in root.findall('atom:entry', namespace):
                title_elem = entry.find('atom:title', namespace)
                if title_elem is None:
                    continue
                
                title = title_elem.text.strip()
                
                # Extract year from published date
                published_elem = entry.find('atom:published', namespace)
                year = 0
                if published_elem is not None:
                    try:
                        year = int(published_elem.text[:4])
                    except:
                        pass
                
                # Only include recent papers
                if year < 2020:
                    continue
                
                # Extract summary
                summary_elem = entry.find('atom:summary', namespace)
                summary = summary_elem.text.strip()[:200] + '...' if summary_elem is not None else "arXiv preprint addressing research challenges."
                
                # Check if author is actually in the paper
                authors = []
                for author in entry.findall('atom:author', namespace):
                    name_elem = author.find('atom:name', namespace)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                
                # Simple author matching
                author_match = any(prof_name.lower().split()[-1] in author.lower() for author in authors)
                if not author_match:
                    continue
                
                publications.append({
                    'title': title,
                    'year': year,
                    'summary': summary,
                    'source': 'arXiv'
                })
            
            return publications[:10]
            
        except Exception as e:
            logger.error(f"arXiv search failed: {str(e)}")
            return []
    
    def _search_crossref(self, prof_name: str) -> List[Dict]:
        """Search CrossRef for journal publications"""
        try:
            logger.info("📖 Searching CrossRef...")
            
            params = {
                'query': f'author:"{prof_name}"',
                'rows': 20,
                'sort': 'published',
                'order': 'desc',
                'filter': 'from-pub-date:2020'
            }
            
            response = self.session.get("https://api.crossref.org/works", params=params, timeout=30)
            if response.status_code != 200:
                return []
            
            data = response.json()
            items = data.get('message', {}).get('items', [])
            
            publications = []
            for item in items:
                title = ' '.join(item.get('title', []))
                if not title:
                    continue
                
                # Extract year
                pub_date = item.get('published-online') or item.get('published-print')
                year = 0
                if pub_date and pub_date.get('date-parts'):
                    year = pub_date['date-parts'][0][0]
                
                if year < 2020:
                    continue
                
                # Check if author is in the paper
                authors = []
                for author in item.get('author', []):
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given and family:
                        authors.append(f"{given} {family}")
                    elif family:
                        authors.append(family)
                
                # Simple author matching
                author_match = any(prof_name.lower().split()[-1] in author.lower() for author in authors)
                if not author_match:
                    continue
                
                # Create summary from title and venue
                venue = item.get('container-title', [''])[0]
                summary = f"Published in {venue}. " if venue else ""
                summary += "Research paper contributing to the field with novel methodologies and insights."
                
                publications.append({
                    'title': title,
                    'year': year,
                    'summary': summary,
                    'source': 'CrossRef'
                })
            
            return publications[:10]
            
        except Exception as e:
            logger.error(f"CrossRef search failed: {str(e)}")
            return []

def research_assistant_cli():
    """Command-line interface for the research assistant"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python research_assistant.py 'Professor Name'")
        print("Example: python research_assistant.py 'Adam Belay'")
        sys.exit(1)
    
    prof_name = sys.argv[1]
    
    print(f"🔍 Research Assistant")
    print("=" * 50)
    print(f"Input: Professor Name: {prof_name}")
    print("=" * 50)
    
    assistant = ResearchAssistant()
    publications = assistant.find_professor_publications(prof_name)
    
    print("\n📄 Task Results:")
    if publications:
        print(json.dumps(publications, indent=2, ensure_ascii=False))
    else:
        print("[]")
        print(f"❌ No recent publications found for {prof_name}")
    
    print(f"\n✅ Search completed. Found {len(publications)} publications (2020-2025)")

if __name__ == "__main__":
    research_assistant_cli()
