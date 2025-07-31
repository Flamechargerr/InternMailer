
import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class HRFinder:
    def __init__(self, api_key: str, cache_file: str = "data/scraped_companies.json"):
        self.api_key = api_key
        self.base_url = "https://api.hunter.io/v2"
        self.cache_file = cache_file
        self.scraped_companies = self._load_cache()

    def get_domain_search(self, company: str) -> Optional[str]:
        """Find the domain name for a given company."""
        endpoint = f"{self.base_url}/domain-search"
        params = {
            "company": company,
            "api_key": self.api_key
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("data") and data["data"].get("domain"):
                return data["data"]["domain"]
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error finding domain for {company}: {e}")
            return None

    def get_emails_from_domain(self, domain: str) -> List[Dict]:
        """Get email addresses from a given domain."""
        endpoint = f"{self.base_url}/emails"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "department": "hr",
            "limit": 10
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("emails", [])
        except requests.exceptions.RequestException as e:
            print(f"Error getting emails from {domain}: {e}")
            return []

    def _load_cache(self) -> Dict:
        """Load the cache of already scraped companies."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}
    
    def _save_cache(self):
        """Save the cache of scraped companies."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.scraped_companies, f, indent=4)
    
    def is_company_scraped(self, company: str) -> bool:
        """Check if a company has already been scraped."""
        return company in self.scraped_companies
    
    def mark_company_scraped(self, company: str, emails_found: int = 0):
        """Mark a company as scraped."""
        self.scraped_companies[company] = {
            "scraped_at": datetime.now().isoformat(),
            "emails_found": emails_found
        }
        self._save_cache()
    
    def get_unscraped_companies(self, companies: List[str]) -> List[str]:
        """Get list of companies that haven't been scraped yet."""
        return [company for company in companies if not self.is_company_scraped(company)]
    
    def get_scraped_summary(self) -> Dict:
        """Get summary of scraped companies."""
        total_scraped = len(self.scraped_companies)
        total_emails = sum(data.get('emails_found', 0) for data in self.scraped_companies.values())
        return {
            "total_companies_scraped": total_scraped,
            "total_emails_found": total_emails,
            "companies": list(self.scraped_companies.keys())
        }

    def find_hr_emails(self, company: str) -> List[Dict]:
        """Find HR emails for a given company if not already scraped."""
        if self.is_company_scraped(company):
            print(f"Skipping {company} - already scraped")
            return []
        
        domain = self.get_domain_search(company)
        emails = []
        if domain:
            emails = self.get_emails_from_domain(domain)
        
        # Mark company as scraped regardless of whether emails were found
        self.mark_company_scraped(company, len(emails))
        return emails

if __name__ == '__main__':
    # This is an example, please use your own API key
    hunter_api_key = "YOUR_HUNTER_API_KEY"
    finder = HRFinder(api_key=hunter_api_key)
    
    # --- Load companies from JSON ---
    try:
        with open("companies.json", 'r') as f:
            companies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        companies = []

    if not companies:
        print("No companies found in companies.json")
    else:
        all_emails = []
        for company in companies:
            print(f"Finding HR emails for: {company}")
            emails = finder.find_hr_emails(company)
            if emails:
                all_emails.extend(emails)
                print(f"  Found {len(emails)} emails.")
        
        # --- Save emails to a file ---
        with open("data/hr_emails.json", "w") as f:
            json.dump(all_emails, f, indent=4)
        
        print(f"\nSaved {len(all_emails)} HR emails to data/hr_emails.json")

