#!/usr/bin/env python3
"""
Ultra-Accurate Research Detail Finder
Multi-source academic publication scraper with sophisticated fallback mechanisms
and validation for near-zero failure rate.
"""

import requests
import json
import time
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from datetime import datetime, timedelta
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_finder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Publication:
    """Represents a research publication with comprehensive metadata"""
    title: str
    authors: List[str]
    year: int
    venue: str
    abstract: str = ""
    url: str = ""
    doi: str = ""
    citations: int = 0
    pdf_url: str = ""
    keywords: List[str] = None
    source: str = ""
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

@dataclass
class AuthorProfile:
    """Represents a comprehensive author profile"""
    name: str
    affiliations: List[str]
    email: str = ""
    homepage: str = ""
    scholar_id: str = ""
    h_index: int = 0
    total_citations: int = 0
    research_interests: List[str] = None
    recent_publications: List[Publication] = None
    
    def __post_init__(self):
        if self.research_interests is None:
            self.research_interests = []
        if self.recent_publications is None:
            self.recent_publications = []

class UltraAccurateResearchFinder:
    """
    Ultra-accurate research publication finder with multiple data sources,
    sophisticated matching algorithms, and comprehensive fallback mechanisms.
    """
    
    def __init__(self, rate_limit_delay: float = 1.0):
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Data sources configuration
        self.data_sources = {
            'semantic_scholar': {
                'base_url': 'https://api.semanticscholar.org/graph/v1',
                'weight': 0.4,
                'rate_limit': 1.0
            },
            'crossref': {
                'base_url': 'https://api.crossref.org/works',
                'weight': 0.2,
                'rate_limit': 1.0
            },
            'dblp': {
                'base_url': 'https://dblp.org/search',
                'weight': 0.2,
                'rate_limit': 0.5
            },
            'arxiv': {
                'base_url': 'http://export.arxiv.org/api/query',
                'weight': 0.2,
                'rate_limit': 0.5
            }
        }
        
        # Cache for reducing API calls
        self.author_cache = {}
        self.publication_cache = {}
        
        # Matching thresholds
        self.match_threshold = 0.75
        self.min_confidence = 0.6
        
    def _normalize_name(self, name: str) -> str:
        """Normalize author names for better matching"""
        # Remove common titles and suffixes
        titles = ['dr.', 'prof.', 'professor', 'dr', 'prof']
        suffixes = ['jr.', 'sr.', 'ii', 'iii', 'ph.d.', 'phd']
        
        name = name.lower().strip()
        for title in titles:
            name = re.sub(rf'\b{title}\b', '', name).strip()
        for suffix in suffixes:
            name = re.sub(rf'\b{suffix}\b', '', name).strip()
            
        # Normalize spacing and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate sophisticated name similarity score"""
        name1_norm = self._normalize_name(name1)
        name2_norm = self._normalize_name(name2)
        
        # Exact match
        if name1_norm == name2_norm:
            return 1.0
        
        # Split into components
        parts1 = name1_norm.split()
        parts2 = name2_norm.split()
        
        if not parts1 or not parts2:
            return 0.0
        
        # Check for initials handling (e.g., "John A. Smith" vs "J. A. Smith")
        def expand_initials(parts):
            expanded = []
            for part in parts:
                if len(part) == 1 or (len(part) == 2 and part.endswith('.')):
                    expanded.append(part.replace('.', ''))
                else:
                    expanded.append(part)
            return expanded
        
        parts1_exp = expand_initials(parts1)
        parts2_exp = expand_initials(parts2)
        
        # Calculate component similarity
        matches = 0
        total_components = max(len(parts1_exp), len(parts2_exp))
        
        # Check for partial matches and initial matches
        for p1 in parts1_exp:
            for p2 in parts2_exp:
                if p1 == p2:
                    matches += 1
                elif len(p1) == 1 and p2.startswith(p1):
                    matches += 0.8
                elif len(p2) == 1 and p1.startswith(p2):
                    matches += 0.8
                elif self._levenshtein_similarity(p1, p2) > 0.8:
                    matches += 0.7
        
        return min(matches / total_components, 1.0)
    
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein similarity between two strings"""
        if not s1 or not s2:
            return 0.0
        
        # Simple Levenshtein distance implementation
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
            
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        max_len = max(m, n)
        return 1 - (dp[m][n] / max_len) if max_len > 0 else 0.0
    
    def _calculate_affiliation_similarity(self, search_aff: str, author_affs: List[str]) -> float:
        """Calculate affiliation similarity with fuzzy matching"""
        if not search_aff or not author_affs:
            return 0.0
        
        search_aff_norm = self._normalize_name(search_aff)
        max_similarity = 0.0
        
        for aff in author_affs:
            aff_norm = self._normalize_name(aff)
            
            # Exact match
            if search_aff_norm in aff_norm or aff_norm in search_aff_norm:
                return 1.0
            
            # Partial matches
            search_words = set(search_aff_norm.split())
            aff_words = set(aff_norm.split())
            
            if search_words and aff_words:
                common_words = search_words.intersection(aff_words)
                similarity = len(common_words) / len(search_words.union(aff_words))
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_match_score(self, search_name: str, author_name: str, 
                             search_affiliation: str, author_affiliations: List[str]) -> float:
        """Calculate comprehensive match score"""
        if not search_name.strip():
            return 0.0
        
        name_sim = self._calculate_name_similarity(search_name, author_name)
        aff_sim = self._calculate_affiliation_similarity(search_affiliation, author_affiliations)
        
        # Weighted combination
        return (name_sim * 0.7) + (aff_sim * 0.3)
    
    def search_semantic_scholar(self, author_name: str, affiliation: str = "", 
                               max_results: int = 10) -> List[Publication]:
        """Enhanced Semantic Scholar search with comprehensive error handling"""
        try:
            logger.info(f"Searching Semantic Scholar for {author_name}")
            
            # Search for author
            search_url = f"{self.data_sources['semantic_scholar']['base_url']}/author/search"
            params = {
                'query': author_name,
                'limit': 20,
                'fields': 'authorId,name,affiliations,url,paperCount,citationCount,hIndex'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            if response.status_code == 429:
                logger.warning("Rate limited by Semantic Scholar, waiting...")
                time.sleep(5)
                response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Semantic Scholar author search failed: {response.status_code}")
                return []
            
            authors_data = response.json().get('data', [])
            if not authors_data:
                logger.warning(f"No authors found for {author_name}")
                return []
            
            # Find best matching author
            best_author = None
            best_score = 0
            
            for author in authors_data:
                score = self._calculate_match_score(
                    author_name, 
                    author.get('name', ''), 
                    affiliation, 
                    author.get('affiliations', [])
                )
                if score > best_score:
                    best_score = score
                    best_author = author
            
            if not best_author or best_score < self.match_threshold:
                logger.warning(f"No good match found for {author_name} (best score: {best_score})")
                return []
            
            logger.info(f"Found author match: {best_author.get('name')} (score: {best_score:.2f})")
            
            # Get author's papers
            author_id = best_author['authorId']
            papers_url = f"{self.data_sources['semantic_scholar']['base_url']}/author/{author_id}/papers"
            
            # Get comprehensive paper data
            paper_params = {
                'limit': max_results * 2,  # Get more to filter
                'fields': 'paperId,title,year,abstract,authors,url,venue,citationCount,referenceCount,publicationTypes,publicationDate,journal,externalIds'
            }
            
            time.sleep(self.data_sources['semantic_scholar']['rate_limit'])
            papers_response = self.session.get(papers_url, params=paper_params, timeout=30)
            
            if papers_response.status_code != 200:
                logger.error(f"Failed to fetch papers for {author_name}: {papers_response.status_code}")
                return []
            
            papers_data = papers_response.json().get('data', [])
            
            # Process and validate papers
            publications = []
            current_year = datetime.now().year
            
            for paper in papers_data:
                year = paper.get('year')
                if not year or year < 2020 or year > current_year + 1:
                    continue
                
                # Extract comprehensive paper info
                pub = Publication(
                    title=paper.get('title', '').strip(),
                    authors=[author.get('name', '') for author in paper.get('authors', [])],
                    year=year,
                    venue=paper.get('venue', '') or paper.get('journal', {}).get('name', ''),
                    abstract=paper.get('abstract', '').strip()[:500] + '...' if paper.get('abstract') else '',
                    url=paper.get('url', ''),
                    citations=paper.get('citationCount', 0),
                    source='Semantic Scholar',
                    confidence_score=best_score
                )
                
                # Add DOI if available
                external_ids = paper.get('externalIds', {})
                if external_ids and external_ids.get('DOI'):
                    pub.doi = external_ids['DOI']
                
                # Validate publication quality
                if pub.title and len(pub.title) > 10:
                    publications.append(pub)
            
            # Sort by year (most recent first) and citations
            publications.sort(key=lambda x: (x.year, x.citations), reverse=True)
            
            logger.info(f"Found {len(publications)} valid publications for {author_name}")
            return publications[:max_results]
            
        except Exception as e:
            logger.error(f"Error in Semantic Scholar search for {author_name}: {str(e)}")
            return []
    
    def search_crossref(self, author_name: str, affiliation: str = "", 
                       max_results: int = 10) -> List[Publication]:
        """Search CrossRef for publications"""
        try:
            logger.info(f"Searching CrossRef for {author_name}")
            
            # Build query
            query_parts = [f'author:"{author_name}"']
            if affiliation:
                query_parts.append(f'affiliation:"{affiliation}"')
            
            params = {
                'query': ' AND '.join(query_parts),
                'rows': max_results * 2,
                'sort': 'published',
                'order': 'desc',
                'filter': 'from-pub-date:2020'
            }
            
            response = self.session.get(self.data_sources['crossref']['base_url'], 
                                      params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"CrossRef search failed: {response.status_code}")
                return []
            
            data = response.json()
            items = data.get('message', {}).get('items', [])
            
            publications = []
            for item in items:
                # Extract publication info
                title = ' '.join(item.get('title', []))
                if not title:
                    continue
                
                authors = []
                for author in item.get('author', []):
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given and family:
                        authors.append(f"{given} {family}")
                    elif family:
                        authors.append(family)
                
                # Check if our target author is in the author list
                target_found = any(
                    self._calculate_name_similarity(author_name, author) > 0.7
                    for author in authors
                )
                
                if not target_found:
                    continue
                
                pub_date = item.get('published-online') or item.get('published-print')
                year = 0
                if pub_date and pub_date.get('date-parts'):
                    year = pub_date['date-parts'][0][0]
                
                pub = Publication(
                    title=title,
                    authors=authors,
                    year=year,
                    venue=item.get('container-title', [''])[0],
                    url=item.get('URL', ''),
                    doi=item.get('DOI', ''),
                    source='CrossRef',
                    confidence_score=0.8
                )
                
                publications.append(pub)
            
            logger.info(f"Found {len(publications)} publications from CrossRef")
            return publications[:max_results]
            
        except Exception as e:
            logger.error(f"Error in CrossRef search: {str(e)}")
            return []
    
    def search_arxiv(self, author_name: str, max_results: int = 10) -> List[Publication]:
        """Search arXiv for publications"""
        try:
            logger.info(f"Searching arXiv for {author_name}")
            
            params = {
                'search_query': f'au:"{author_name}"',
                'start': 0,
                'max_results': max_results * 2,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = self.session.get(self.data_sources['arxiv']['base_url'], 
                                      params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"arXiv search failed: {response.status_code}")
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
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', namespace):
                    name_elem = author.find('atom:name', namespace)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                
                # Check if target author is in the list
                target_found = any(
                    self._calculate_name_similarity(author_name, author) > 0.7
                    for author in authors
                )
                
                if not target_found:
                    continue
                
                # Extract other metadata
                summary_elem = entry.find('atom:summary', namespace)
                abstract = summary_elem.text.strip()[:300] + '...' if summary_elem is not None else ''
                
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
                
                id_elem = entry.find('atom:id', namespace)
                url = id_elem.text if id_elem is not None else ''
                
                pub = Publication(
                    title=title,
                    authors=authors,
                    year=year,
                    venue='arXiv',
                    abstract=abstract,
                    url=url,
                    source='arXiv',
                    confidence_score=0.7
                )
                
                publications.append(pub)
            
            logger.info(f"Found {len(publications)} publications from arXiv")
            return publications[:max_results]
            
        except Exception as e:
            logger.error(f"Error in arXiv search: {str(e)}")
            return []
    
    def search_by_scholar_id(self, scholar_id: str, max_results: int = 10) -> List[Publication]:
        """Search using Google Scholar ID - highest reliability method"""
        if not scholar_id or 'noscholar' in scholar_id.lower():
            return []
            
        logger.info(f"Searching by Scholar ID: {scholar_id}")
        
        try:
            # Clean Scholar ID - extract from URL if needed
            if 'scholar.google' in scholar_id:
                scholar_id = scholar_id.split('user=')[1].split('&')[0]
            
            # Use Semantic Scholar's author endpoint with high confidence
            search_url = f"{self.data_sources['semantic_scholar']['base_url']}/author/{scholar_id}"
            params = {
                'fields': 'name,affiliations,url,paperCount,citationCount,hIndex,papers.title,papers.year,papers.abstract,papers.authors,papers.url,papers.venue,papers.citationCount,papers.referenceCount'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Scholar ID search failed: {response.status_code}")
                return []
            
            data = response.json()
            papers = data.get('papers', [])
            
            publications = []
            current_year = datetime.now().year
            
            for paper in papers[:max_results * 2]:  # Get more to filter
                year = paper.get('year', 0)
                if year < 2020 or year > current_year + 1:
                    continue
                
                title = paper.get('title', '').strip()
                if not title or len(title) < 10:
                    continue
                
                pub = Publication(
                    title=title,
                    authors=[author.get('name', '') for author in paper.get('authors', [])],
                    year=year,
                    venue=paper.get('venue', ''),
                    abstract=paper.get('abstract', '').strip()[:500] + '...' if paper.get('abstract') else '',
                    url=paper.get('url', ''),
                    citations=paper.get('citationCount', 0),
                    source='Semantic Scholar (Scholar ID)',
                    confidence_score=0.95  # Very high confidence for Scholar ID matches
                )
                publications.append(pub)
            
            publications.sort(key=lambda x: (x.year, x.citations), reverse=True)
            logger.info(f"Found {len(publications)} publications via Scholar ID")
            return publications[:max_results]
            
        except Exception as e:
            logger.error(f"Error in Scholar ID search: {str(e)}")
            return []
    
    def search_openalex(self, name: str, affiliation: str = "", max_results: int = 10) -> List[Publication]:
        """Search OpenAlex API for additional coverage"""
        try:
            logger.info(f"Searching OpenAlex for {name}")
            
            # Build author search query
            url = "https://api.openalex.org/authors"
            params = {
                'search': name,
                'per-page': 5
            }
            
            if affiliation:
                params['filter'] = f'affiliations.institution.display_name:{affiliation}'
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code != 200:
                return []
            
            data = response.json()
            authors = data.get('results', [])
            
            best_author = None
            best_score = 0
            
            for author in authors:
                author_name = author.get('display_name', '')
                author_affs = [inst.get('display_name', '') for inst in author.get('affiliations', [])]
                
                score = self._calculate_match_score(name, author_name, affiliation, author_affs)
                if score > best_score:
                    best_score = score
                    best_author = author
            
            if not best_author or best_score < 0.7:
                return []
            
            # Get author's works
            author_id = best_author.get('id', '').split('/')[-1]
            works_url = "https://api.openalex.org/works"
            works_params = {
                'filter': f'authorships.author.id:A{author_id}',
                'sort': 'cited_by_count:desc',
                'per-page': max_results
            }
            
            time.sleep(0.5)  # Rate limiting
            works_response = self.session.get(works_url, params=works_params, timeout=30)
            if works_response.status_code != 200:
                return []
            
            works_data = works_response.json()
            publications = []
            
            for work in works_data.get('results', []):
                year = work.get('publication_year', 0)
                if year < 2020:
                    continue
                
                title = work.get('title', '').strip()
                if not title:
                    continue
                
                authors = []
                for authorship in work.get('authorships', []):
                    author_name = authorship.get('author', {}).get('display_name', '')
                    if author_name:
                        authors.append(author_name)
                
                venue_info = work.get('primary_location', {}).get('source', {})
                venue = venue_info.get('display_name', '') if venue_info else ''
                
                pub = Publication(
                    title=title,
                    authors=authors,
                    year=year,
                    venue=venue,
                    doi=work.get('doi', ''),
                    citations=work.get('cited_by_count', 0),
                    url=work.get('id', ''),
                    source='OpenAlex',
                    confidence_score=best_score * 0.85
                )
                publications.append(pub)
            
            logger.info(f"Found {len(publications)} publications from OpenAlex")
            return publications
            
        except Exception as e:
            logger.error(f"Error in OpenAlex search: {str(e)}")
            return []
    
    def find_author_publications(self, name: str, affiliation: str = "", 
                                email: str = "", scholar_id: str = None, max_results: int = 5) -> List[Publication]:
        """
        Ultra-accurate publication finding with Scholar ID prioritization and comprehensive fallbacks
        """
        logger.info(f"Starting comprehensive search for {name} at {affiliation}")
        
        # Enhanced cache key including Scholar ID
        cache_components = [name, affiliation, scholar_id or ""]
        cache_key = hashlib.md5('_'.join(cache_components).encode()).hexdigest()
        
        if cache_key in self.publication_cache:
            logger.info(f"Using cached results for {name}")
            return self.publication_cache[cache_key]
        
        all_publications = []
        
        # PRIORITY 1: Use Scholar ID if available (highest accuracy)
        if scholar_id and 'noscholar' not in scholar_id.lower():
            scholar_pubs = self.search_by_scholar_id(scholar_id, max_results * 2)
            if scholar_pubs:
                logger.info(f"Scholar ID search successful: {len(scholar_pubs)} publications")
                all_publications.extend(scholar_pubs)
                
                # If Scholar ID gives good results, use fewer supplementary sources
                max_supplementary = max_results // 2
            else:
                max_supplementary = max_results
        else:
            max_supplementary = max_results
        
        # PRIORITY 2: Search all other sources with parallel execution
        search_functions = [
            (self.search_semantic_scholar, 'semantic_scholar'),
            (self.search_openalex, 'openalex'),
            (self.search_crossref, 'crossref'),
            (self.search_arxiv, 'arxiv')
        ]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for search_func, source_name in search_functions:
                if source_name == 'semantic_scholar' and scholar_id:
                    continue  # Skip if we already used Scholar ID
                
                if source_name in ['crossref', 'openalex']:
                    future = executor.submit(search_func, name, affiliation, max_supplementary)
                else:
                    future = executor.submit(search_func, name, max_supplementary)
                
                futures[future] = source_name
            
            for future in as_completed(futures, timeout=120):
                source = futures[future]
                try:
                    results = future.result(timeout=60)
                    logger.info(f"Got {len(results)} results from {source}")
                    all_publications.extend(results)
                except Exception as e:
                    logger.error(f"Error from {source}: {str(e)}")
        
        if not all_publications:
            logger.warning(f"No publications found for {name} from any source")
            return []
        
        # STEP 3: Intelligent deduplication and merging
        unique_publications = self._deduplicate_publications(all_publications)
        
        # STEP 4: Enhanced scoring with Scholar ID bias
        scored_publications = self._score_and_rank_publications(unique_publications, name, scholar_id is not None)
        
        # STEP 5: Quality filtering with adaptive thresholds
        min_confidence = self.min_confidence if not scholar_id else 0.5  # Lower threshold if we have Scholar ID
        final_publications = [
            pub for pub in scored_publications 
            if pub.confidence_score >= min_confidence and pub.year >= 2020
        ]
        
        # STEP 6: Final ranking and selection
        final_publications.sort(key=lambda x: (x.confidence_score, x.year, x.citations), reverse=True)
        
        # Take the best results
        result = final_publications[:max_results]
        
        # Cache the result
        self.publication_cache[cache_key] = result
        
        logger.info(f"Final result: {len(result)} high-quality publications for {name}")
        return result
    
    def _deduplicate_publications(self, publications: List[Publication]) -> List[Publication]:
        """Remove duplicate publications using intelligent matching"""
        if not publications:
            return []
        
        unique_pubs = []
        seen_titles = set()
        
        for pub in publications:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', ' ', pub.title.lower())
            normalized_title = ' '.join(normalized_title.split())
            
            # Check for exact or very similar titles
            is_duplicate = False
            for seen_title in seen_titles:
                if self._levenshtein_similarity(normalized_title, seen_title) > 0.9:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    for i, existing_pub in enumerate(unique_pubs):
                        if self._levenshtein_similarity(
                            re.sub(r'[^\w\s]', ' ', existing_pub.title.lower()),
                            seen_title
                        ) > 0.9:
                            if pub.confidence_score > existing_pub.confidence_score:
                                unique_pubs[i] = pub
                            break
                    break
            
            if not is_duplicate:
                unique_pubs.append(pub)
                seen_titles.add(normalized_title)
        
        return unique_pubs
    
    def _score_and_rank_publications(self, publications: List[Publication], 
                                   target_author: str, has_scholar_id: bool = False) -> List[Publication]:
        """Score publications based on relevance and quality"""
        for pub in publications:
            score = pub.confidence_score
            
            # Higher base bonus if we have Scholar ID (more confident in results)
            if has_scholar_id and 'Scholar ID' in pub.source:
                score += 0.1
            
            # Bonus for recent publications
            current_year = datetime.now().year
            year_bonus = max(0, (pub.year - 2020) / (current_year - 2020)) * 0.2
            score += year_bonus
            
            # Bonus for having the target author as first author
            if pub.authors and self._calculate_name_similarity(target_author, pub.authors[0]) > 0.8:
                score += 0.15
            
            # Bonus for high citation count (relative scoring)
            if pub.citations > 50:
                score += 0.1
            elif pub.citations > 10:
                score += 0.05
            
            # Bonus for having abstract
            if pub.abstract and len(pub.abstract) > 100:
                score += 0.05
            
            # Update confidence score
            pub.confidence_score = min(score, 1.0)
        
        return publications
    
    def create_author_profile(self, name: str, affiliation: str, email: str = "", 
                            homepage: str = "", scholar_id: str = None) -> AuthorProfile:
        """Create comprehensive author profile with publications"""
        logger.info(f"Creating author profile for {name}")
        
        # Pass scholar_id to find_author_publications
        publications = self.find_author_publications(name, affiliation, email, scholar_id, max_results=5)
        
        # Extract research interests from abstracts
        research_interests = self._extract_research_interests(publications)
        
        profile = AuthorProfile(
            name=name,
            affiliations=[affiliation] if affiliation else [],
            email=email,
            homepage=homepage,
            scholar_id=scholar_id or "",
            research_interests=research_interests,
            recent_publications=publications
        )
        
        return profile
    
    def _extract_research_interests(self, publications: List[Publication]) -> List[str]:
        """Extract research interests from publication abstracts using enhanced keyword analysis"""
        if not publications:
            return []
        
        # Enhanced CS/research keywords with medical AI and graph networks
        keywords = {
            'machine learning', 'deep learning', 'artificial intelligence', 'neural networks',
            'computer vision', 'natural language processing', 'data mining', 'algorithms',
            'systems', 'security', 'cryptography', 'distributed systems',
            'human-computer interaction', 'databases', 'software engineering', 'programming languages',
            'theory', 'optimization', 'robotics', 'quantum computing', 'bioinformatics',
            'computer graphics', 'visualization', 'mobile computing', 'cloud computing',
            # Enhanced medical AI and graph neural networks
            'graph neural networks', 'medical ai', 'healthcare ai', 'medical imaging',
            'brain disease', 'causal graphs', 'graph structure learning', 'medical diagnosis',
            'biomedical engineering', 'clinical ai', 'drug discovery', 'genomics',
            'graph learning', 'graph convolution', 'knowledge graphs', 'social networks',
            'network analysis', 'graph algorithms', 'complex networks', 'graph mining'
        }
        
        # Specialized patterns for better classification
        specialized_patterns = {
            'graph neural networks': ['graph neural', 'gnn', 'graph convolution', 'graph learning', 'causal graph'],
            'medical ai': ['medical', 'healthcare', 'clinical', 'disease', 'diagnosis', 'biomedical'],
            'machine learning': ['ml', 'learning algorithm', 'supervised learning', 'reinforcement'],
            'computer vision': ['image processing', 'object detection', 'visual', 'opencv'],
            'natural language processing': ['nlp', 'text mining', 'language model', 'sentiment']
        }
        
        # Count keyword occurrences in abstracts and titles
        keyword_counts = {}
        total_abstracts = 0
        
        for pub in publications:
            text_sources = []
            if pub.abstract:
                text_sources.append(pub.abstract.lower())
            if pub.title:
                text_sources.append(pub.title.lower())
            if pub.venue:
                text_sources.append(pub.venue.lower())
            
            if text_sources:
                total_abstracts += 1
                combined_text = ' '.join(text_sources)
                
                # Direct keyword matching
                for keyword in keywords:
                    if keyword in combined_text:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                # Pattern-based matching for specialized areas
                for area, patterns in specialized_patterns.items():
                    for pattern in patterns:
                        if pattern in combined_text:
                            keyword_counts[area] = keyword_counts.get(area, 0) + 0.5
        
        # Return keywords that appear in at least 25% of abstracts (lower threshold for better detection)
        min_frequency = max(1, total_abstracts * 0.25)
        frequent_keywords = [
            keyword for keyword, count in keyword_counts.items()
            if count >= min_frequency
        ]
        
        # Sort by frequency and return top interests
        frequent_keywords.sort(key=lambda x: keyword_counts[x], reverse=True)
        return frequent_keywords[:7]  # Return more interests

def test_ultra_accurate_finder():
    """Test the ultra-accurate research finder"""
    finder = UltraAccurateResearchFinder()
    
    # Test with known professors
    test_cases = [
        ("Yann LeCun", "Meta AI", "yann@cs.nyu.edu"),
        ("Geoffrey Hinton", "University of Toronto", "hinton@cs.toronto.edu"),
        ("Andrew Ng", "Stanford University", "ang@cs.stanford.edu")
    ]
    
    print("🧪 TESTING ULTRA-ACCURATE RESEARCH FINDER")
    print("=" * 80)
    
    for name, affiliation, email in test_cases:
        print(f"\n👤 Testing: {name} at {affiliation}")
        print("-" * 60)
        
        profile = finder.create_author_profile(name, affiliation, email)
        
        print(f"📝 Research Interests: {', '.join(profile.research_interests[:3])}")
        print(f"📚 Recent Publications ({len(profile.recent_publications)}):")
        
        for i, pub in enumerate(profile.recent_publications, 1):
            print(f"\n   {i}. {pub.title}")
            print(f"      Year: {pub.year} | Venue: {pub.venue}")
            print(f"      Citations: {pub.citations} | Source: {pub.source}")
            print(f"      Confidence: {pub.confidence_score:.2f}")
            if pub.abstract:
                print(f"      Abstract: {pub.abstract[:150]}...")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    test_ultra_accurate_finder()
