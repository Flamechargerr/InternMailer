import os
import csv
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Set
import re
import time
from urllib.parse import urljoin, urlparse, quote
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)

class ProfessorDiscovery:
    """
    Discover new professors from multiple academic sources.
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.discovered_professors = []
        self.existing_professors = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        os.makedirs(self.data_dir, exist_ok=True)
        self._load_existing_professors()
    
    def _load_existing_professors(self):
        """Load existing professors to avoid duplicates."""
        existing_files = [
            "scraped_professors_1000.csv",
            "scraped_professors_enhanced.csv",
            "scraped_professors_merged.csv"
        ]
        
        for filename in existing_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            name = row.get('name', '').strip()
                            affiliation = row.get('affiliation', '').strip()
                            if name and affiliation:
                                self.existing_professors.add(f"{name}|{affiliation}")
                except Exception as e:
                    logging.warning(f"Could not load {filename}: {e}")
        
        logging.info(f"Loaded {len(self.existing_professors)} existing professors")
    
    def discover_from_google_scholar(self, search_queries: List[str], max_results_per_query: int = 50) -> List[Dict]:
        """
        Discover professors from Google Scholar search results.
        Note: This is limited due to Google Scholar's anti-bot measures.
        """
        discovered = []
        
        for query in search_queries:
            try:
                logging.info(f"Searching Google Scholar for: {query}")
                
                # Use a more specific search URL that might work better
                search_url = f"https://scholar.google.com/citations?view_op=search_authors&mauthors={quote(query)}&hl=en&oi=ao"
                
                response = self.session.get(search_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for author profiles
                    author_divs = soup.find_all('div', class_='gsc_1usr')
                    
                    for div in author_divs[:max_results_per_query]:
                        try:
                            name_elem = div.find('h3', class_='gs_ai_name')
                            affiliation_elem = div.find('div', class_='gs_ai_aff')
                            
                            if name_elem and affiliation_elem:
                                name = name_elem.get_text().strip()
                                affiliation = affiliation_elem.get_text().strip()
                                
                                # Get profile link if available
                                link_elem = name_elem.find('a')
                                profile_url = ""
                                if link_elem and link_elem.get('href'):
                                    profile_url = urljoin("https://scholar.google.com", link_elem['href'])
                                
                                prof_key = f"{name}|{affiliation}"
                                if prof_key not in self.existing_professors:
                                    discovered.append({
                                        'name': name,
                                        'affiliation': affiliation,
                                        'homepage': profile_url,
                                        'scholarid': '',
                                        'source': 'google_scholar',
                                        'discovered_at': datetime.now().isoformat()
                                    })
                                    self.existing_professors.add(prof_key)
                        except Exception as e:
                            logging.warning(f"Error parsing author div: {e}")
                            continue
                
                # Be respectful with delays
                time.sleep(2)
                
            except Exception as e:
                logging.warning(f"Error searching Google Scholar for '{query}': {e}")
                time.sleep(5)  # Longer delay on error
        
        return discovered
    
    def discover_from_university_directories(self, universities: List[Dict]) -> List[Dict]:
        """
        Discover professors from university faculty directories.
        """
        discovered = []
        
        def scrape_university(uni):
            try:
                uni_name = uni.get('name', '')
                directory_url = uni.get('directory_url', '')
                
                if not directory_url:
                    return
                
                logging.info(f"Scraping {uni_name} directory: {directory_url}")
                
                response = self.session.get(directory_url, timeout=15, verify=False)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Common selectors for faculty listings
                    faculty_selectors = [
                        '.faculty-member', '.staff-member', '.professor',
                        '.faculty-listing', '.people-listing',
                        '[class*="faculty"]', '[class*="staff"]',
                        '.person', '.member', '.profile'
                    ]
                    
                    for selector in faculty_selectors:
                        faculty_elements = soup.select(selector)
                        
                        for element in faculty_elements:
                            try:
                                name = self._extract_name_from_element(element)
                                homepage = self._extract_homepage_from_element(element, directory_url)
                                
                                if name and len(name.split()) >= 2:  # At least first and last name
                                    prof_key = f"{name}|{uni_name}"
                                    if prof_key not in self.existing_professors:
                                        discovered.append({
                                            'name': name,
                                            'affiliation': uni_name,
                                            'homepage': homepage,
                                            'scholarid': '',
                                            'source': 'university_directory',
                                            'discovered_at': datetime.now().isoformat()
                                        })
                                        self.existing_professors.add(prof_key)
                            except Exception as e:
                                continue
            except Exception as e:
                logging.warning(f"Error scraping {uni.get('name', 'Unknown')}: {e}")
        
        with ThreadPoolExecutor() as executor:
            executor.map(scrape_university, universities)
        
        return discovered
    
    def discover_from_conference_proceedings(self, conference_urls: List[str]) -> List[Dict]:
        """
        Discover professors from conference proceedings and author lists.
        """
        discovered = []
        
        for conf_url in conference_urls:
            try:
                logging.info(f"Scraping conference: {conf_url}")
                
                response = self.session.get(conf_url, timeout=15, verify=False)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for author names and affiliations
                    author_patterns = [
                        {'name': '.author-name', 'affiliation': '.author-affiliation'},
                        {'name': '.author', 'affiliation': '.affiliation'},
                        {'name': '[class*="author"]', 'affiliation': '[class*="affil"]'},
                    ]
                    
                    for pattern in author_patterns:
                        name_elements = soup.select(pattern['name'])
                        affil_elements = soup.select(pattern['affiliation'])
                        
                        # Match names with affiliations
                        for i, name_elem in enumerate(name_elements):
                            try:
                                name = name_elem.get_text().strip()
                                affiliation = ""
                                
                                if i < len(affil_elements):
                                    affiliation = affil_elements[i].get_text().strip()
                                
                                if name and affiliation and len(name.split()) >= 2:
                                    prof_key = f"{name}|{affiliation}"
                                    if prof_key not in self.existing_professors:
                                        discovered.append({
                                            'name': name,
                                            'affiliation': affiliation,
                                            'homepage': '',
                                            'scholarid': '',
                                            'source': 'conference',
                                            'discovered_at': datetime.now().isoformat()
                                        })
                                        self.existing_professors.add(prof_key)
                            except Exception:
                                continue
                
                time.sleep(1)
                
            except Exception as e:
                logging.warning(f"Error scraping conference {conf_url}: {e}")
        
        return discovered
    
    def discover_from_research_networks(self) -> List[Dict]:
        """
        Discover professors from research networks and academic social platforms.
        """
        discovered = []
        
        # Academic search engines and databases
        sources = [
            {
                'name': 'DBLP',
                'search_url': 'https://dblp.org/search/author?q=computer+science',
                'selector_patterns': {
                    'name': '.data .name a',
                    'affiliation': '.data .affiliation'
                }
            },
            # Add more sources as needed
        ]
        
        for source in sources:
            try:
                logging.info(f"Searching {source['name']}")
                
                response = self.session.get(source['search_url'], timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract using the source's specific patterns
                    patterns = source['selector_patterns']
                    name_elements = soup.select(patterns['name'])
                    
                    for name_elem in name_elements[:50]:  # Limit results
                        try:
                            name = name_elem.get_text().strip()
                            
                            # Try to find affiliation nearby
                            affiliation = ""
                            parent = name_elem.parent
                            if parent:
                                affil_elem = parent.select_one(patterns.get('affiliation', ''))
                                if affil_elem:
                                    affiliation = affil_elem.get_text().strip()
                            
                            if name and affiliation and len(name.split()) >= 2:
                                prof_key = f"{name}|{affiliation}"
                                if prof_key not in self.existing_professors:
                                    discovered.append({
                                        'name': name,
                                        'affiliation': affiliation,
                                        'homepage': '',
                                        'scholarid': '',
                                        'source': source['name'].lower(),
                                        'discovered_at': datetime.now().isoformat()
                                    })
                                    self.existing_professors.add(prof_key)
                        except Exception:
                            continue
                
                time.sleep(1)
                
            except Exception as e:
                logging.warning(f"Error with {source['name']}: {e}")
        
        return discovered
    
    def _extract_name_from_element(self, element) -> str:
        """Extract professor name from HTML element."""
        # Common name selectors
        name_selectors = [
            '.name', '.full-name', '.person-name', '.faculty-name',
            'h1', 'h2', 'h3', 'h4', '.title', 'strong', 'b'
        ]
        
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text().strip()
                # Clean and validate name
                name = re.sub(r'\s+', ' ', name)
                if len(name.split()) >= 2 and len(name) < 100:
                    return name
        
        # Try to extract from element text directly
        text = element.get_text().strip()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines[:3]:  # Check first few lines
            if len(line.split()) >= 2 and len(line) < 100:
                # Check if it looks like a name (not too many special characters)
                if len(re.findall(r'[^a-zA-Z\s.-]', line)) < len(line) * 0.2:
                    return line
        
        return ""
    
    def _extract_homepage_from_element(self, element, base_url: str) -> str:
        """Extract homepage URL from HTML element."""
        # Look for links
        link_elem = element.find('a')
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            if href.startswith('http'):
                return href
            else:
                return urljoin(base_url, href)
        
        return ""
    
    def run_discovery(self, max_new_professors: int = 500) -> List[Dict]:
        """
        Run comprehensive professor discovery from multiple sources.
        """
        logging.info("Starting comprehensive professor discovery...")
        
        all_discovered = []
        
        # 1. Google Scholar searches (limited due to anti-bot measures)
        scholar_queries = [
            "computer science professor",
            "machine learning researcher",
            "artificial intelligence professor",
            "data science professor",
            "software engineering professor"
        ]
        
        try:
            scholar_results = self.discover_from_google_scholar(scholar_queries, max_results_per_query=20)
            all_discovered.extend(scholar_results)
            logging.info(f"Discovered {len(scholar_results)} professors from Google Scholar")
        except Exception as e:
            logging.warning(f"Google Scholar discovery failed: {e}")
        
        # 2. University directories
        universities = [
            {'name': 'MIT', 'directory_url': 'https://www.csail.mit.edu/people'},
            {'name': 'Stanford University', 'directory_url': 'https://cs.stanford.edu/directory/faculty'},
            {'name': 'UC Berkeley', 'directory_url': 'https://eecs.berkeley.edu/faculty'},
            {'name': 'Carnegie Mellon University', 'directory_url': 'https://www.cs.cmu.edu/directory/faculty'},
            {'name': 'University of Washington', 'directory_url': 'https://www.cs.washington.edu/people/faculty'},
            # Add more universities as needed
        ]
        
        try:
            uni_results = self.discover_from_university_directories(universities)
            all_discovered.extend(uni_results)
            logging.info(f"Discovered {len(uni_results)} professors from university directories")
        except Exception as e:
            logging.warning(f"University directory discovery failed: {e}")
        
        # 3. Research networks
        try:
            network_results = self.discover_from_research_networks()
            all_discovered.extend(network_results)
            logging.info(f"Discovered {len(network_results)} professors from research networks")
        except Exception as e:
            logging.warning(f"Research network discovery failed: {e}")
        
        # Limit results if needed
        if len(all_discovered) > max_new_professors:
            all_discovered = all_discovered[:max_new_professors]
        
        # Save discovered professors
        if all_discovered:
            output_file = os.path.join(self.data_dir, "discovered_professors.csv")
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'affiliation', 'homepage', 'scholarid', 'source', 'discovered_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_discovered)
            
            logging.info(f"✅ Saved {len(all_discovered)} newly discovered professors to {output_file}")
        
        return all_discovered
    
    def get_discovery_summary(self) -> Dict:
        """Get summary of discovery results."""
        return {
            'existing_professors_count': len(self.existing_professors),
            'newly_discovered_count': len(self.discovered_professors),
            'data_directory': self.data_dir
        }

def main():
    """Main function to run professor discovery."""
    import sys
    
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        discovery = ProfessorDiscovery(data_dir)
        discovered = discovery.run_discovery(max_new_professors=1000)
        
        print(f"\n📊 Discovery Summary:")
        print(f"   - Existing professors: {len(discovery.existing_professors)}")
        print(f"   - Newly discovered: {len(discovered)}")
        
        if discovered:
            sources = {}
            for prof in discovered:
                source = prof.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"   - Sources breakdown:")
            for source, count in sources.items():
                print(f"     * {source}: {count}")
    else:
        print("Usage: python professor_discovery.py <data_directory>")

if __name__ == "__main__":
    main()
