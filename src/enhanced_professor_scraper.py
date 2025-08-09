import os
import csv
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)

class EnhancedProfessorScraper:
    """
    Enhanced professor scraper with parallel processing and advanced email extraction.
    """
    def __init__(self, data_dir: str, cache_file: str = None, max_workers: int = 800):
        self.data_dir = data_dir
        self.professors = []
        self.cache_file = cache_file or os.path.join(data_dir, "scraped_professors_cache.json")
        self.scraped_professors = self._load_cache()
        self.max_workers = max_workers
        self.session_lock = threading.Lock()
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Setup EXTREME optimized session with maximum connection pooling for ultra-high concurrency
        self.session = requests.Session()
        retry_strategy = Retry(
            total=1,  # Single retry for maximum speed
            backoff_factor=0.3,  # Ultra-fast backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )
        # EXTREME adapter for ultra-high concurrency
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=200,  # Massive connection pool
            pool_maxsize=800,     # Match max_workers for optimal performance
            pool_block=False      # Non-blocking pool
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def parse_csvs(self) -> List[Dict[str, Any]]:
        """Parse only CSRankings professor CSVs in the data directory."""
        for fname in os.listdir(self.data_dir):
            if fname.startswith('csrankings-') and fname.endswith('.csv'):
                with open(os.path.join(self.data_dir, fname), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        self.professors.append(row)
        logging.info(f"Parsed {len(self.professors)} professors from CSRankings CSVs.")
        return self.professors

    def scrape_email_from_homepage(self, url: str) -> str:
        """Enhanced email extraction with multiple strategies and improved parsing."""
        if not url or not url.startswith('http'):
            return ""
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            with self.session_lock:
                resp = self.session.get(url, timeout=8, headers=headers, verify=False)  # Ultra-fast timeout for extreme processing
                resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Strategy 1: Look for mailto links first (most reliable)
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '').split('?')[0].strip()
                if self._is_valid_email_format(email):
                    return email
            
            # Strategy 2: Enhanced email selectors
            email_selectors = [
                '[href*="@"]',  # Any link containing @
                '.email', '.contact-email', '.faculty-email', '.prof-email',
                '#email', '#contact-email', '#faculty-email', '#prof-email',
                '[class*="email"]', '[id*="email"]', '[class*="contact"]',
                '.contact-info', '.contact', '.profile-contact', '.personal-info',
                '.faculty-info', '.staff-info', '.researcher-info',
                'span:contains("@")', 'div:contains("@")', 'p:contains("@")',
                '[data-email]', '[data-contact]'
            ]
            
            for selector in email_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        email = self._extract_email_from_element(element)
                        if email:
                            return email
                except Exception:
                    continue
            
            # Strategy 3: Advanced text-based extraction
            text_content = soup.get_text()
            email = self._extract_email_from_text_advanced(text_content)
            if email:
                return email
            
            # Strategy 4: Check HTML source for obfuscated emails
            html_source = str(soup)
            email = self._extract_obfuscated_email_advanced(html_source)
            if email:
                return email
            
            # Strategy 5: Look for JavaScript-generated emails
            email = self._extract_js_email(html_source)
            if email:
                return email
            
            return ""

        except Exception as e:
            logging.warning(f"Failed to scrape {url}: {e}")
            return ""

    def enrich_with_emails_parallel(self):
        """Enrich professor data with emails using parallel scraping."""
        unscraped_professors = self.get_unscraped_professors(self.professors)
        
        if not unscraped_professors:
            logging.info("All professors have already been scraped. Loading cached emails...")
            self._load_cached_emails()
            return self.professors
        
        logging.info(f"Scraping {len(unscraped_professors)} unscraped professors with {self.max_workers} workers")
        
        def scrape_single_professor(prof):
            homepage = prof.get('homepage', '')
            email = self.scrape_email_from_homepage(homepage)
            prof['email'] = email
            
            # Mark as scraped
            self.mark_professor_scraped(prof, email)
            
            if email:
                logging.info(f"Found email {email} for {prof['name']}")
            
            return prof, email
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_prof = {executor.submit(scrape_single_professor, prof): prof for prof in unscraped_professors}
            
            # Process completed tasks
            for future in as_completed(future_to_prof):
                prof = future_to_prof[future]
                try:
                    result_prof, email = future.result()
                except Exception as exc:
                    logging.error(f"Professor {prof.get('name', 'Unknown')} generated an exception: {exc}")
        
        # Load cached emails for already scraped professors
        self._load_cached_emails()
        
        return self.professors

    def deduplicate_and_filter(self) -> List[Dict[str, Any]]:
        """Deduplicate by email and filter for valid emails."""
        seen = set()
        filtered = []
        for prof in self.professors:
            email = prof.get('email', '').strip()
            if email and self._is_valid_email_format(email) and email not in seen:
                seen.add(email)
                filtered.append(prof)
        logging.info(f"Deduplicated to {len(filtered)} unique professors with valid emails.")
        return filtered

    def _load_cache(self) -> Dict:
        """Load the cache of already scraped professors."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save the cache of scraped professors."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_professors, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Could not save cache: {e}")
    
    def _get_professor_key(self, prof: Dict) -> str:
        """Generate a unique key for a professor (name + affiliation)."""
        name = prof.get('name', '').strip()
        affiliation = prof.get('affiliation', '').strip()
        return f"{name}|{affiliation}"
    
    def is_professor_scraped(self, prof: Dict) -> bool:
        """Check if a professor has already been scraped."""
        prof_key = self._get_professor_key(prof)
        return prof_key in self.scraped_professors
    
    def mark_professor_scraped(self, prof: Dict, email_found: str = ""):
        """Mark a professor as scraped."""
        prof_key = self._get_professor_key(prof)
        self.scraped_professors[prof_key] = {
            "scraped_at": datetime.now().isoformat(),
            "email_found": email_found,
            "homepage": prof.get('homepage', ''),
            "name": prof.get('name', ''),
            "affiliation": prof.get('affiliation', '')
        }
        self._save_cache()
    
    def get_unscraped_professors(self, professors: List[Dict]) -> List[Dict]:
        """Get list of professors that haven't been scraped yet."""
        return [prof for prof in professors if not self.is_professor_scraped(prof)]
    
    def _load_cached_emails(self):
        """Load cached emails for already scraped professors."""
        for prof in self.professors:
            prof_key = self._get_professor_key(prof)
            if prof_key in self.scraped_professors:
                prof['email'] = self.scraped_professors[prof_key].get('email_found', '')

    def _is_valid_email_format(self, email: str) -> bool:
        """Check if the given string is a valid email format."""
        # Enhanced email validation regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None

    def _extract_email_from_element(self, element) -> str:
        """Extracts email from a BeautifulSoup element."""
        if not element:
            return ""
        
        # Check data attributes first
        for attr in ['data-email', 'data-contact', 'data-mail']:
            if element.has_attr(attr):
                email = element[attr]
                if self._is_valid_email_format(email):
                    return email
        
        # Check text content
        text = element.get_text(strip=True)
        email = self._extract_email_from_text_advanced(text)
        if email:
            return email
            
        # Check href attributes
        if element.has_attr('href'):
            href = element['href']
            if '@' in href and '.' in href and not href.startswith('mailto:'):
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', href)
                if email_match:
                    return email_match.group(1)

        return ""

    def _extract_email_from_text_advanced(self, text: str) -> str:
        """Advanced email extraction from text with multiple patterns."""
        # Standard email pattern
        email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}'
        ]
        
        for pattern in email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for email in matches:
                cleaned_email = re.sub(r'\s+', '', email)  # Remove spaces
                if self._is_valid_email_format(cleaned_email):
                    return cleaned_email
        
        return ""

    def _extract_obfuscated_email_advanced(self, html_source: str) -> str:
        """Enhanced extraction of obfuscated emails from HTML source."""
        obfuscation_patterns = [
            # Format: user [at] domain [dot] com
            r'([a-zA-Z0-9._-]+)\s*\[\s*(?:at|AT|@)\s*\]\s*([a-zA-Z0-9_-]+)\s*\[\s*(?:dot|DOT|\.)\s*\]\s*([a-zA-Z0-9._-]+)',
            # Format: user AT domain DOT com
            r'([a-zA-Z0-9._-]+)\s+(?:AT|at)\s+([a-zA-Z0-9_-]+)\s+(?:DOT|dot)\s+([a-zA-Z0-9._-]+)',
            # Format: user(at)domain(dot)com
            r'([a-zA-Z0-9._-]+)\((?:at|AT|@)\)([a-zA-Z0-9_-]+)\((?:dot|DOT|\.)\)([a-zA-Z0-9._-]+)',
            # Format: user_at_domain_dot_com
            r'([a-zA-Z0-9._-]+)_(?:at|AT)_([a-zA-Z0-9_-]+)_(?:dot|DOT)_([a-zA-Z0-9._-]+)',
            # Format: user-at-domain-dot-com
            r'([a-zA-Z0-9._-]+)-(?:at|AT)-([a-zA-Z0-9_-]+)-(?:dot|DOT)-([a-zA-Z0-9._-]+)'
        ]
        
        for pattern in obfuscation_patterns:
            match = re.search(pattern, html_source, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    user, domain, tld = match.groups()
                    email = f"{user}@{domain}.{tld}"
                    if self._is_valid_email_format(email):
                        return email
        
        # Handle encoded characters
        if 'mailto:' in html_source:
            mailto_match = re.search(r'mailto:([^"\'>\s]+)', html_source)
            if mailto_match:
                email = mailto_match.group(1)
                # Decode HTML entities
                email = email.replace('&#64;', '@').replace('&#46;', '.')
                if self._is_valid_email_format(email):
                    return email
        
        return ""

    def _extract_js_email(self, html_source: str) -> str:
        """Extract emails that might be generated by JavaScript."""
        # Look for common JavaScript email patterns
        js_patterns = [
            r'var\s+email\s*=\s*["\']([^"\']+@[^"\']+)["\']',
            r'email\s*[:=]\s*["\']([^"\']+@[^"\']+)["\']',
            r'contact\s*[:=]\s*["\']([^"\']+@[^"\']+)["\']',
            r'mailto\s*[:=]\s*["\']([^"\']+@[^"\']+)["\']'
        ]
        
        for pattern in js_patterns:
            match = re.search(pattern, html_source, re.IGNORECASE)
            if match:
                email = match.group(1)
                if self._is_valid_email_format(email):
                    return email
        
        return ""

    def get_scraped_summary(self) -> Dict:
        """Get summary of scraped professors."""
        total_scraped = len(self.scraped_professors)
        total_emails = sum(1 for data in self.scraped_professors.values() if data.get('email_found'))
        return {
            "total_professors_scraped": total_scraped,
            "total_emails_found": total_emails,
            "success_rate": round(total_emails / total_scraped * 100, 1) if total_scraped > 0 else 0,
            "cache_file": self.cache_file
        }

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Static method to validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
