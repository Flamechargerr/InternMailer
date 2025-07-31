import csv

class EmailPatternGenerator:
    def __init__(self):
        self.companies = [
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
            "Google Alphabet", "Microsoft", "Apple", "Amazon", "Meta Facebook", "IBM", "Oracle",
            "Intel", "Cisco", "Salesforce", "Adobe", "Dell Technologies", "HP Inc", "SAP",
            "Tencent", "Baidu", "Alibaba", "Uber", "Airbnb", "Netflix",
            "Accenture", "Deloitte", "PwC PricewaterhouseCoopers", "EY Ernst & Young", "KPMG",
            "Capgemini", "Cognizant", "LTI Mindtree", "Genpact", "IBM Consulting",
            "JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Bank of America", "Wells Fargo",
            "CitiBank", "HSBC", "Barclays", "PayPal", "Mastercard", "Visa", "American Express",
            "Robinhood", "Square Block Inc", "Stripe",
            "Flipkart", "Myntra", "Walmart", "Target", "Costco", "eBay", "Shopify", "Best Buy",
            "Meesho", "Nykaa",
            "Unilever", "Procter & Gamble P&G", "Nestlé", "Johnson & Johnson", "Colgate‑Palmolive",
            "PepsiCo", "Coca‑Cola", "Britannia", "Marico",
            "Tesla", "Ford", "General Motors", "BMW", "Mercedes‑Benz", "Audi", "Toyota",
            "Boeing", "Lockheed Martin", "Raytheon Technologies", "Northrop Grumman", "Airbus",
            "DRDO", "HAL Hindustan Aeronautics Limited", "SpaceX", "ISRO", "Rolls‑Royce",
            "Pfizer", "Moderna", "Roche", "Novartis", "GlaxoSmithKline GSK", "AstraZeneca",
            "Sun Pharma", "Cipla", "Dr. Reddy's Labs"
        ]

    def get_company_domain(self, company_name):
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

    def generate_common_hr_emails(self, domain, company_name):
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
                'email': email
            })
        return hr_emails

    def run_generation(self):
        emails = []
        for company in self.companies:
            domain = self.get_company_domain(company)
            if domain:
                emails.extend(self.generate_common_hr_emails(domain, company))
        return emails

    def save_to_csv(self, emails, filename='hr_emails_generated.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['company', 'email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for email_data in emails:
                writer.writerow(email_data)
        print(f"Generated {len(emails)} HR emails and saved to {filename}")

if __name__ == "__main__":
    generator = EmailPatternGenerator()
    emails = generator.run_generation()
    generator.save_to_csv(emails)

