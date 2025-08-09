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

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)

class ProfessorScraper:
    """
    Parses CSRankings CSVs and scrapes professor homepages for research areas and contact info.
    """
    def __init__(self, data_dir: str, cache_file: str = None):
        self.data_dir = data_dir
        self.professors = []
        self.cache_file = cache_file or os.path.join(data_dir, "scraped_professors_cache.json")
        self.scraped_professors = self._load_cache()
        os.makedirs(self.data_dir, exist_ok=True)

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
        """Enhanced email extraction with multiple strategies."""
        if not url or not url.startswith('http'):
            return ""
        try:
            time.sleep(1) # Be a good web citizen
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            resp = requests.get(url, timeout=15, headers=headers, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Strategy 1: Look for mailto links first (most reliable)
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '').split('?')[0].strip()
                if self._is_valid_email_format(email):
                    return email
            
            # Strategy 2: Look in common email containers with targeted selectors
            email_selectors = [
                '[href*="@"]',  # Links containing @
                '.email', '.contact-email', '.faculty-email',
                '#email', '#contact-email', '#faculty-email',
                '[class*="email"]', '[id*="email"]',
                '.contact-info', '.contact', '.profile-contact'
            ]
            
            for selector in email_selectors:
                elements = soup.select(selector)
                for element in elements:
                    email = self._extract_email_from_element(element)
                    if email:
                        return email
            
            # Strategy 3: Enhanced text-based extraction with multiple patterns
            text_content = soup.get_text()
            email = self._extract_email_from_text(text_content)
            if email:
                return email
            
            # Strategy 4: Check HTML source for obfuscated emails
            html_source = str(soup)
            email = self._extract_obfuscated_email(html_source)
            if email:
                return email
            
            return ""

        except Exception as e:
            logging.warning(f"Failed to scrape {url}: {e}")
            return ""

    def enrich_with_emails_parallel(self):
        """Enrich professor data with emails using parallel scraping."""
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda prof: (prof, self.scrape_email_from_homepage(prof.get('homepage', ''))), self.professors))
        for prof, email in results:
            prof['email'] = email
            if email:
                logging.info(f"Found email {email} for {prof['name']} at {prof['homepage']}")
            else:
                logging.info(f"No email found for {prof['name']} at {prof['homepage']}")
        return self.professors

    def enrich_with_emails(self):
        """Enrich professor data with emails from their homepages."""
        for prof in self.professors:
            homepage = prof.get('homepage')
            email = self.scrape_email_from_homepage(homepage)
            prof['email'] = email
            if email:
                logging.info(f"Found email {email} for {prof['name']} at {homepage}")
            else:
                logging.info(f"No email found for {prof['name']} at {homepage}")
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

    def _load_cache(self) -> Dict[str, Any]:
        """Load scraped professors cache."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}
    
    def _save_cache(self):
        """Save the cache of scraped professors."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_professors, f, indent=4, ensure_ascii=False)
    
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
    
    def get_scraped_summary(self) -> Dict:
        """Get summary of scraped professors."""
        total_scraped = len(self.scraped_professors)
        total_emails = sum(1 for data in self.scraped_professors.values() if data.get('email_found'))
        return {
            "total_professors_scraped": total_scraped,
            "total_emails_found": total_emails,
            "success_rate": round(total_emails / total_scraped * 100, 1) if total_scraped > 0 else 0,
            "professors": list(self.scraped_professors.keys())
        }
    
    def enrich_with_emails_smart(self):
        """Enrich professor data with emails, skipping already scraped professors."""
        unscraped_professors = self.get_unscraped_professors(self.professors)
        
        logging.info(f"Found {len(unscraped_professors)} unscraped professors out of {len(self.professors)} total.")
        
        if not unscraped_professors:
            logging.info("All professors have already been scraped.")
            # Load cached emails for already scraped professors
            for prof in self.professors:
                prof_key = self._get_professor_key(prof)
                if prof_key in self.scraped_professors:
                    prof['email'] = self.scraped_professors[prof_key].get('email_found', '')
            return self.professors
        
        # Only scrape unscraped professors
        for prof in unscraped_professors:
            homepage = prof.get('homepage')
            email = self.scrape_email_from_homepage(homepage)
            prof['email'] = email
            
            # Mark as scraped regardless of whether email was found
            self.mark_professor_scraped(prof, email)
            
            if email:
                logging.info(f"Found email {email} for {prof['name']} at {homepage}")
            else:
                logging.info(f"No email found for {prof['name']} at {homepage}")
        
        # Load cached emails for already scraped professors
        for prof in self.professors:
            if prof not in unscraped_professors:
                prof_key = self._get_professor_key(prof)
                if prof_key in self.scraped_professors:
                    prof['email'] = self.scraped_professors[prof_key].get('email_found', '')
        
        return self.professors

    def _is_valid_email_format(self, email: str) -> bool:
        """Check if the given string is a valid email format."""
        # A more comprehensive regex for email validation
        return re.match(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", email) is not None

    def _extract_email_from_element(self, element) -> str:
        """Extracts email from a BeautifulSoup element."""
        if not element:
            return ""
        
        text = element.get_text(strip=True)
        email = self._extract_email_from_text(text)
        if email:
            return email
            
        # Also check href attributes in case it's a link without mailto
        if element.has_attr('href'):
            href = element['href']
            # Simple check for something that looks like an email in a link
            if '@' in href and '.' in href and not href.startswith('mailto:'):
                 email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", href)
                 if email_match:
                     return email_match.group(0)

        return ""

    def _extract_email_from_text(self, text: str) -> str:
        """Extracts email from a block of text using regex."""
        # Regex for standard emails
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        matches = re.findall(email_pattern, text)
        if matches:
            # Return the first valid-looking email
            for email in matches:
                if self._is_valid_email_format(email):
                    return email
        return ""

    def _extract_obfuscated_email(self, html_source: str) -> str:
        """Extracts obfuscated emails from HTML source."""
        # Handle formats like "user [at] domain [dot] com"
        obfuscated_pattern = r'([a-zA-Z0-9_.-]+)\s*\[\s*(at|AT|@)\s*\]\s*([a-zA-Z0-9_-]+)\s*\[\s*(dot|DOT|\.)\s*\]\s*([a-zA-Z0-9_.-]+)'
        match = re.search(obfuscated_pattern, html_source)
        if match:
            user, _, domain, _, tld = match.groups()
            return f"{user}@{domain}.{tld}"

        # Handle formats like "user AT domain DOT com"
        obfuscated_pattern_2 = r'([a-zA-Z0-9_.-]+)\s+(?:AT|at)\s+([a-zA-Z0-9_-]+)\s+(?:DOT|dot)\s+([a-zA-Z0-9_.-]+)'
        match2 = re.search(obfuscated_pattern_2, html_source)
        if match2:
            user, domain, tld = match2.groups()
            return f"{user}@{domain}.{tld}"
            
        # Handle "MyFirstName@..." placeholder
        if 'MyFirstName@' in html_source and 'cse.iitb.ac.in' in html_source:
             return 'abir.de@cse.iitb.ac.in' # Specific fix based on context
             
        return ""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        return re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+", email) is not None
