import os
import csv
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re

logging.basicConfig(level=logging.INFO)

class ProfessorScraper:
    """
    Parses CSRankings CSVs and scrapes professor homepages for research areas and contact info.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.professors = []

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

    def scrape_homepage(self, url: str) -> str:
        """Scrape homepage for research area text."""
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Simple heuristic: get all text
            text = soup.get_text(separator=' ', strip=True)
            return text[:2000]  # Limit to 2000 chars
        except Exception as e:
            logging.warning(f"Failed to scrape {url}: {e}")
            return ""

    def deduplicate_and_filter(self) -> List[Dict[str, Any]]:
        """Deduplicate by email and filter for valid emails."""
        seen = set()
        filtered = []
        for prof in self.professors:
            email = prof.get('email', '').strip()
            if email and self.is_valid_email(email) and email not in seen:
                seen.add(email)
                filtered.append(prof)
        logging.info(f"Deduplicated to {len(filtered)} unique professors with valid emails.")
        return filtered

    @staticmethod
    def is_valid_email(email: str) -> bool:
        return re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", email) is not None

# TODO: Add unit tests for ProfessorScraper 