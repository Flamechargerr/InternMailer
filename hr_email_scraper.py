import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import random
from urllib.parse import urljoin, urlparse
import os
from dotenv import load_dotenv
import json

load_dotenv()

class HREmailScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.hunter_api_key = os.getenv('HUNTER_API_KEY')
        self.companies = [
            # Indian Companies
            "Reliance Industries Limited", "Indian Oil Corporation", "Life Insurance Corporation LIC",
            "Oil and Natural Gas Corporation ONGC", "Bharat Petroleum Corporation BPCL", "State Bank of India SBI",
            "Tata Motors", "Tata Steel", "Tata Consultancy Services TCS", "Hindalco Industries",
            "HDFC Bank", "Larsen & Toubro L&T", "ICICI Bank", "NTPC Limited", "JSW Steel",
            "Housing Development Finance Corporation HDFC", "Vedanta Resources", "GAIL India",
            "Infosys", "Coal India", "Bharti Airtel", "Mahindra & Mahindra", "Grasim Industries",
            "Maruti Suzuki India", "Nayara Energy", "Steel Authority of India SAIL", "Canara Bank",
            "Bank of Baroda", "Axis Bank", "HCL Technologies", "Punjab National Bank",
            "Union Bank of India", "Wipro", "Uttar Pradesh Power Corporation", "Bajaj Finserv",
            "Motherson Sumi Systems", "Power Finance Corporation", "ITC Limited", "Kotak Mahindra Bank",
            "IFFCO", "Hyundai Motor India", "Hindustan Unilever HUL", "Tata Power",
            "Petronet LNG", "IndiGo InterGlobe Aviation", "Bank of India", "Adani Wilmar",
            "Tech Mahindra", "UPL Ltd", "Jindal Steel & Power",
            
            # Global Tech Companies
            "Google Alphabet", "Microsoft", "Apple", "Amazon", "Meta Facebook", "IBM", "Oracle",
            "Intel", "Cisco", "Salesforce", "Adobe", "Dell Technologies", "HP Inc", "SAP",
            "Tencent", "Baidu", "Alibaba", "Uber", "Airbnb", "Netflix",
            
            # Consulting Companies
            "Accenture", "Deloitte", "PwC PricewaterhouseCoopers", "EY Ernst & Young", "KPMG",
            "Capgemini", "Cognizant", "LTI Mindtree", "Genpact", "IBM Consulting",
            
            # Financial Services
            "JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Bank of America", "Wells Fargo",
            "CitiBank", "HSBC", "Barclays", "PayPal", "Mastercard", "Visa", "American Express",
            "Robinhood", "Square Block Inc", "Stripe",
            
            # E-commerce & Retail
            "Flipkart", "Myntra", "Walmart", "Target", "Costco", "eBay", "Shopify", "Best Buy",
            "Meesho", "Nykaa",
            
            # Consumer Goods
            "Unilever", "Procter & Gamble P&G", "Nestlé", "Johnson & Johnson", "Colgate‑Palmolive",
            "PepsiCo", "Coca‑Cola", "Britannia", "Marico",
            
            # Automotive
            "Tesla", "Ford", "General Motors", "BMW", "Mercedes‑Benz", "Audi", "Toyota",
            
            # Aerospace & Defense
            "Boeing", "Lockheed Martin", "Raytheon Technologies", "Northrop Grumman", "Airbus",
            "DRDO", "HAL Hindustan Aeronautics Limited", "SpaceX", "ISRO", "Rolls‑Royce",
            
            # Pharmaceuticals
            "Pfizer", "Moderna", "Roche", "Novartis", "GlaxoSmithKline GSK", "AstraZeneca",
            "Sun Pharma", "Cipla", "Dr. Reddy's Labs"
        ]
        
        self.hr_emails = []
        self.processed_companies = set()

    def get_company_domain(self, company_name):
        """Extract likely domain from company name"""
        domain_mappings = {
            "Reliance Industries Limited": "ril.com",
            "Indian Oil Corporation": "iocl.com",
            "Life Insurance Corporation LIC": "licindia.in",
            "Oil and Natural Gas Corporation ONGC": "ongcindia.com",
            "Bharat Petroleum Corporation BPCL": "bharatpetroleum.in",
            "State Bank of India SBI": "sbi.co.in",
            "Tata Motors": "tatamotors.com",
            "Tata Steel": "tatasteel.com",
            "Tata Consultancy Services TCS": "tcs.com",
            "HDFC Bank": "hdfcbank.com",
            "ICICI Bank": "icicibank.com",
            "Infosys": "infosys.com",
            "Wipro": "wipro.com",
            "HCL Technologies": "hcltech.com",
            "Tech Mahindra": "techmahindra.com",
            "Google Alphabet": "google.com",
            "Microsoft": "microsoft.com",
            "Apple": "apple.com",
            "Amazon": "amazon.com",
            "Meta Facebook": "meta.com",
            "IBM": "ibm.com",
            "Oracle": "oracle.com",
            "Intel": "intel.com",
            "Cisco": "cisco.com",
            "Salesforce": "salesforce.com",
            "Adobe": "adobe.com",
            "Dell Technologies": "dell.com",
            "HP Inc": "hp.com",
            "SAP": "sap.com",
            "Uber": "uber.com",
            "Airbnb": "airbnb.com",
            "Netflix": "netflix.com",
            "Accenture": "accenture.com",
            "Deloitte": "deloitte.com",
            "PwC PricewaterhouseCoopers": "pwc.com",
            "EY Ernst & Young": "ey.com",
            "KPMG": "kpmg.com",
            "Cognizant": "cognizant.com",
            "JPMorgan Chase": "jpmorgan.com",
            "Goldman Sachs": "goldmansachs.com",
            "PayPal": "paypal.com",
            "Mastercard": "mastercard.com",
            "Visa": "visa.com",
            "Flipkart": "flipkart.com",
            "Tesla": "tesla.com",
            "Ford": "ford.com",
            "Boeing": "boeing.com",
            "Pfizer": "pfizer.com"
        }
        
        return domain_mappings.get(company_name, None)

    def search_hunter_io(self, domain, company_name):
        """Use Hunter.io API to find email addresses"""
        if not self.hunter_api_key:
            return []
        
        try:
            url = f"https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'api_key': self.hunter_api_key,
                'type': 'generic',
                'limit': 10
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                emails = []
                
                if 'data' in data and 'emails' in data['data']:
                    for email_data in data['data']['emails']:
                        email = email_data.get('value', '')
                        position = email_data.get('position', '').lower()
                        department = email_data.get('department', '').lower()
                        
                        # Filter for HR-related emails
                        if any(keyword in email.lower() for keyword in ['hr', 'human', 'recruiting', 'talent', 'people', 'careers']):
                            emails.append({
                                'company': company_name,
                                'email': email,
                                'position': email_data.get('position', ''),
                                'department': email_data.get('department', ''),
                                'source': 'hunter.io'
                            })
                        elif any(keyword in position for keyword in ['hr', 'human', 'recruiting', 'talent', 'people']):
                            emails.append({
                                'company': company_name,
                                'email': email,
                                'position': email_data.get('position', ''),
                                'department': email_data.get('department', ''),
                                'source': 'hunter.io'
                            })
                
                return emails
                
        except Exception as e:
            print(f"Hunter.io search failed for {domain}: {e}")
        
        return []

    def search_company_website(self, domain, company_name):
        """Search company website for HR contact information"""
        hr_emails = []
        
        try:
            # Common HR page URLs
            hr_urls = [
                f"https://{domain}/careers",
                f"https://{domain}/jobs",
                f"https://{domain}/contact",
                f"https://{domain}/about/contact",
                f"https://{domain}/hr",
                f"https://{domain}/human-resources",
                f"https://careers.{domain}",
                f"https://jobs.{domain}"
            ]
            
            for url in hr_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find email addresses in the page
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, response.text)
                        
                        for email in emails:
                            if any(keyword in email.lower() for keyword in ['hr', 'human', 'recruiting', 'talent', 'people', 'careers', 'jobs']):
                                hr_emails.append({
                                    'company': company_name,
                                    'email': email,
                                    'position': 'HR Contact',
                                    'department': 'Human Resources',
                                    'source': f'website_{url}'
                                })
                
                except Exception as e:
                    continue
                
                time.sleep(random.uniform(1, 3))  # Rate limiting
                
        except Exception as e:
            print(f"Website search failed for {domain}: {e}")
        
        return hr_emails

    def generate_common_hr_emails(self, domain, company_name):
        """Generate common HR email patterns"""
        common_patterns = [
            f"hr@{domain}",
            f"humanresources@{domain}",
            f"careers@{domain}",
            f"jobs@{domain}",
            f"recruiting@{domain}",
            f"talent@{domain}",
            f"people@{domain}",
            f"recruitment@{domain}",
            f"hrteam@{domain}",
            f"contact@{domain}"
        ]
        
        hr_emails = []
        for email in common_patterns:
            hr_emails.append({
                'company': company_name,
                'email': email,
                'position': 'HR Contact (Generated)',
                'department': 'Human Resources',
                'source': 'generated_pattern'
            })
        
        return hr_emails

    def scrape_company_hr_emails(self, company_name):
        """Scrape HR emails for a specific company"""
        print(f"Processing: {company_name}")
        
        if company_name in self.processed_companies:
            return
        
        self.processed_companies.add(company_name)
        
        # Get company domain
        domain = self.get_company_domain(company_name)
        if not domain:
            print(f"  No domain mapping found for {company_name}")
            return
        
        company_hr_emails = []
        
        # Method 1: Hunter.io API
        hunter_emails = self.search_hunter_io(domain, company_name)
        company_hr_emails.extend(hunter_emails)
        print(f"  Found {len(hunter_emails)} emails via Hunter.io")
        
        # Method 2: Website scraping
        website_emails = self.search_company_website(domain, company_name)
        company_hr_emails.extend(website_emails)
        print(f"  Found {len(website_emails)} emails via website scraping")
        
        # Method 3: Generate common patterns
        generated_emails = self.generate_common_hr_emails(domain, company_name)
        company_hr_emails.extend(generated_emails)
        print(f"  Generated {len(generated_emails)} common pattern emails")
        
        # Remove duplicates
        unique_emails = []
        seen_emails = set()
        for email_data in company_hr_emails:
            if email_data['email'] not in seen_emails:
                unique_emails.append(email_data)
                seen_emails.add(email_data['email'])
        
        self.hr_emails.extend(unique_emails)
        print(f"  Total unique emails for {company_name}: {len(unique_emails)}")
        
        # Rate limiting between companies
        time.sleep(random.uniform(2, 5))

    def save_to_csv(self, filename='hr_emails_database.csv'):
        """Save all HR emails to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['company', 'email', 'position', 'department', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for email_data in self.hr_emails:
                writer.writerow(email_data)
        
        print(f"\nSaved {len(self.hr_emails)} HR emails to {filename}")

    def run_full_scrape(self):
        """Run the complete scraping process"""
        print("Starting HR Email Scraping Process...")
        print(f"Processing {len(self.companies)} companies")
        
        for i, company in enumerate(self.companies, 1):
            print(f"\n[{i}/{len(self.companies)}] Processing: {company}")
            try:
                self.scrape_company_hr_emails(company)
            except Exception as e:
                print(f"  Error processing {company}: {e}")
                continue
        
        # Save results
        self.save_to_csv()
        
        # Create summary
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total companies processed: {len(self.processed_companies)}")
        print(f"Total HR emails found: {len(self.hr_emails)}")
        
        # Group by source
        source_counts = {}
        for email_data in self.hr_emails:
            source = email_data['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print("\nEmails by source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
        
        # Create a separate CSV for just email addresses (for mass mailing)
        with open('hr_emails_list.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['email', 'company'])
            for email_data in self.hr_emails:
                writer.writerow([email_data['email'], email_data['company']])
        
        print(f"\nAlso created simplified list: hr_emails_list.csv")

if __name__ == "__main__":
    scraper = HREmailScraper()
    scraper.run_full_scrape()
