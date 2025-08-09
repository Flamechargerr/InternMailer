import requests
from bs4 import BeautifulSoup
import re
import json
import logging

# Config logging
logging.basicConfig(level=logging.INFO)

class HREmailScraper:
    """Scrapes HR emails from company websites"""

    def __init__(self):
        self.email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    def get_hr_emails(self, url):
        """Scrape HR emails from a given URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            emails = set(re.findall(self.email_pattern, soup.get_text()))
            hr_emails = [email for email in emails if 'hr' in email]

            logging.info(f"Found {len(hr_emails)} HR emails from {url}")
            return hr_emails

        except requests.RequestException as e:
            logging.error(f"Error accessing {url}: {e}")
            return []

    def save_emails(self, emails, file_path='hr_emails.json'):
        """Save emails to a JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(emails, f, indent=4)
            logging.info(f"Emails saved to {file_path}")
        except IOError as e:
            logging.error(f"Error saving emails: {e}")


if __name__ == "__main__":
    scraper = HREmailScraper()
    urls = [
        # Add company URLs here
        'https://example-company.com/careers',
        'https://another-company.com/jobs'
    ]
    all_emails = {}

    for url in urls:
        hr_emails = scraper.get_hr_emails(url)
        all_emails[url] = hr_emails

    scraper.save_emails(all_emails)

