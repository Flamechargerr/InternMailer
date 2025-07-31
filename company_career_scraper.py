import requests
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict

class CompanyCareerScraper:
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def scrape_company_career_page(self, company_name: str, career_url: str) -> List[Dict]:
        """
        Scrape company's career page to find HR contacts
        """
        print(f"Scraping HR contacts for {company_name} from {career_url}")
        contacts = []

        try:
            response = requests.get(career_url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing {career_url}: {e}")
            return contacts

        soup = BeautifulSoup(response.content, 'html.parser')

        # Example logic to extract HR emails and contact forms
        email_elements = soup.select("a[href^='mailto:']")
        for elem in email_elements:
            email = elem.get('href').replace('mailto:', '').strip()
            if email:
                contacts.append({'company': company_name, 'email': email})

        forms = soup.find_all('form')
        # Additional logic to identify contact forms can be added here

        print(f"Found {len(contacts)} HR contacts at {company_name}")
        return contacts

    def save_contacts_to_json(self, contacts: List[Dict], filename: str = "hr_contacts.json"):
        """
        Save HR contacts to JSON file
        """
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(contacts)} HR contacts to {file_path}")

# Example usage
def main():
    scraper = CompanyCareerScraper()
    companies = {
        'ExampleCorp': 'https://www.example.com/careers',
        # Add more companies and their career page URLs here
    }
    
    all_contacts = []
    for company, url in companies.items():
        contacts = scraper.scrape_company_career_page(company, url)
        all_contacts.extend(contacts)
    
    scraper.save_contacts_to_json(all_contacts)

if __name__ == "__main__":
    main()

