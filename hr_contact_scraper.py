import requests
from bs4 import BeautifulSoup
import re
import time

class HRContactScraper:
    def __init__(self, companies):
        self.companies = companies
        self.hr_contacts = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_company_domain(self, company_name):
        domain_mappings = {
            "Reliance Industries Limited": "ril.com",
            "Discord": "discord.com",
            # Add other companies and their respective domains here
        }
        return domain_mappings.get(company_name, None)

    def find_hr_contacts(self, domain, company_name):
        print(f"🔍 Finding HR contacts for {company_name}")
        career_pages = [f"https://{domain}/careers", f"https://{domain}/jobs"]
        contact_pages = [f"https://{domain}/about", f"https://{domain}/contact", f"https://{domain}/about-us", f"https://{domain}/contact-us"]

        for page in career_pages + contact_pages:
            try:
                print(f"📧 Scraping: {page}")
                response = requests.get(page, headers=self.headers)
                response.raise_for_status()
                emails = self.extract_emails(response.text)
                self.hr_contacts.extend([{ 'company': company_name, 'email': email } for email in emails])
            except requests.RequestException as e:
                print(f"❌ Error scraping {page}: {e}")
            time.sleep(1)  # Be polite, avoid rapid requests

        print(f"✅ Found {len(self.hr_contacts)} unique HR contacts for {company_name}")

    def extract_emails(self, text):
        email_pattern = r'[\w\.-]+@[\w\.-]+'  # Simple email matching pattern
        emails = re.findall(email_pattern, text)
        return set(emails)  # Return unique emails

    def run(self):
        for i, company in enumerate(self.companies, start=1):
            print(f"\n📊 Processing {i}/{len(self.companies)}: {company}")
            domain = self.get_company_domain(company)
            if domain:
                print(f"✅ Found domain for {company}: {domain}")
                self.find_hr_contacts(domain, company)
            else:
                print(f"❌ Domain not found for {company}")

        # Output results
        for contact in self.hr_contacts:
            print(f"{contact}")

if __name__ == "__main__":
    companies_to_scrape = ["Reliance Industries Limited", "Discord"]  # Add more company names as needed
    scraper = HRContactScraper(companies_to_scrape)
    scraper.run()

