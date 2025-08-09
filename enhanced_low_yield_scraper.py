#!/usr/bin/env python3
"""
Enhanced Low-Yield Scraper
Specifically targets files that produced few or no emails to extract more professors
"""

import pandas as pd
import os
import json
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_low_yield_scraper.log'),
        logging.StreamHandler()
    ]
)

class EnhancedLowYieldScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Enhanced university domain mappings
        self.university_domains = {
            'Carnegie Mellon University': ['cmu.edu', 'cs.cmu.edu'],
            'Georgia Institute': ['gatech.edu', 'cc.gatech.edu'],
            'University of Michigan': ['umich.edu', 'eecs.umich.edu'],
            'Berkeley': ['berkeley.edu', 'eecs.berkeley.edu'],
            'University of Washington': ['washington.edu', 'cs.washington.edu'],
            'Cornell University': ['cornell.edu', 'cs.cornell.edu'],
            'University of Wisconsin': ['wisc.edu', 'cs.wisc.edu'],
            'University of Maryland': ['umd.edu', 'cs.umd.edu'],
            'New York University': ['nyu.edu', 'cs.nyu.edu'],
            'Purdue University': ['purdue.edu', 'cs.purdue.edu'],
            'University of Kentucky': ['uky.edu', 'cs.uky.edu'],
            'University of Utah': ['utah.edu', 'cs.utah.edu'],
            'University of Pennsylvania': ['upenn.edu', 'cis.upenn.edu'],
            'University of Central Florida': ['ucf.edu', 'cs.ucf.edu'],
            'University of Southern California': ['usc.edu', 'cs.usc.edu'],
            'Northwestern University': ['northwestern.edu', 'cs.northwestern.edu'],
            'North Carolina State University': ['ncsu.edu', 'csc.ncsu.edu'],
            'University of British Columbia': ['ubc.ca', 'cs.ubc.ca'],
            'University of Colorado Boulder': ['colorado.edu', 'cs.colorado.edu'],
            'Virginia Tech': ['vt.edu', 'cs.vt.edu'],
            'Columbia University': ['columbia.edu', 'cs.columbia.edu'],
            'Stanford University': ['stanford.edu', 'cs.stanford.edu'],
            'University of Illinois at Chicago': ['uic.edu', 'cs.uic.edu'],
            'Arizona State University': ['asu.edu', 'cs.asu.edu'],
            'University of Virginia': ['virginia.edu', 'cs.virginia.edu'],
            'Princeton University': ['princeton.edu', 'cs.princeton.edu'],
            'Oregon State University': ['oregonstate.edu', 'cs.oregonstate.edu'],
            'University of Texas at Austin': ['utexas.edu', 'cs.utexas.edu'],
            'University of Chicago': ['uchicago.edu', 'cs.uchicago.edu'],
            'Duke University': ['duke.edu', 'cs.duke.edu'],
            'University of Georgia': ['uga.edu', 'cs.uga.edu'],
            'Georgia State University': ['gsu.edu', 'cs.gsu.edu'],
            'University of Houston': ['uh.edu', 'cs.uh.edu'],
            'Massachusetts Institute': ['mit.edu', 'csail.mit.edu'],
            'Chinese Academy of Sciences': ['cas.cn', 'ict.ac.cn'],
            'University of Hong Kong': ['hku.hk', 'cs.hku.hk'],
            'East China Normal University': ['ecnu.edu.cn'],
            'Universidad de Chile': ['uchile.cl'],
            'Pontificia Universidad Catolica de Chile': ['uc.cl'],
            'University of Luxembourg': ['uni.lu'],
            'Indiana University': ['indiana.edu', 'cs.indiana.edu'],
            'University of Singapore': ['nus.edu.sg', 'comp.nus.edu.sg'],
            'Singapore Management University': ['smu.edu.sg'],
            'University of Malta': ['um.edu.mt'],
            'Czech Technical University': ['cvut.cz', 'fel.cvut.cz']
        }
        
        # Additional email patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}',
            r'[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}',
            r'[A-Za-z0-9._%+-]+\s*\(at\)\s*[A-Za-z0-9.-]+\s*\(dot\)\s*[A-Z|a-z]{2,}'
        ]

    def extract_emails_from_text(self, text):
        """Extract emails from text using multiple patterns"""
        if not text:
            return []
        
        emails = []
        text = str(text)
        
        for pattern in self.email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the email
                email = re.sub(r'\s+', '', match)
                email = email.replace('[at]', '@').replace('[dot]', '.')
                email = email.replace('(at)', '@').replace('(dot)', '.')
                
                if '@' in email and '.' in email.split('@')[1]:
                    emails.append(email.lower())
        
        return list(set(emails))

    def generate_email_from_name_affiliation(self, name, affiliation):
        """Generate possible email addresses from name and affiliation"""
        if not name or not affiliation:
            return []
        
        name = str(name).strip()
        affiliation = str(affiliation).strip()
        
        # Extract first and last name
        name_parts = name.split()
        if len(name_parts) < 2:
            return []
        
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower()
        
        # Find university domain
        domain = None
        for university, domains in self.university_domains.items():
            if university.lower() in affiliation.lower():
                domain = domains[0]
                break
        
        if not domain:
            return []
        
        # Generate email variations
        email_variations = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_name}{last_name}@{domain}",
            f"{first_name[0]}{last_name}@{domain}",
            f"{first_name}@{domain}",
            f"{last_name}@{domain}",
            f"{first_name}_{last_name}@{domain}",
            f"{first_name}-{last_name}@{domain}"
        ]
        
        return email_variations

    def scrape_homepage_for_emails(self, homepage_url):
        """Scrape homepage for email addresses"""
        if not homepage_url or pd.isna(homepage_url):
            return []
        
        try:
            response = self.session.get(homepage_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract emails from various elements
            emails = []
            
            # Check mailto links
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '').split('?')[0]
                if '@' in email:
                    emails.append(email.lower())
            
            # Check text content
            text_content = soup.get_text()
            emails.extend(self.extract_emails_from_text(text_content))
            
            # Check specific elements that might contain emails
            for element in soup.find_all(['p', 'div', 'span', 'td']):
                element_text = element.get_text()
                emails.extend(self.extract_emails_from_text(element_text))
            
            return list(set(emails))
            
        except Exception as e:
            logging.warning(f"Error scraping {homepage_url}: {e}")
            return []

    def process_low_yield_file(self, file_path):
        """Process a low-yield file to extract more emails"""
        logging.info(f"Processing low-yield file: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            logging.info(f"Loaded {len(df)} rows from {file_path}")
            
            extracted_emails = []
            
            for index, row in df.iterrows():
                emails_found = []
                
                # Extract emails from existing email columns
                email_columns = [col for col in df.columns if 'email' in col.lower()]
                for col in email_columns:
                    if pd.notna(row[col]):
                        emails_found.extend(self.extract_emails_from_text(row[col]))
                
                # Generate emails from name and affiliation
                name_cols = [col for col in df.columns if 'name' in col.lower()]
                affiliation_cols = [col for col in df.columns if 'affiliation' in col.lower() or 'university' in col.lower()]
                
                if name_cols and affiliation_cols:
                    name = row[name_cols[0]] if pd.notna(row[name_cols[0]]) else None
                    affiliation = row[affiliation_cols[0]] if pd.notna(row[affiliation_cols[0]]) else None
                    
                    if name and affiliation:
                        generated_emails = self.generate_email_from_name_affiliation(name, affiliation)
                        emails_found.extend(generated_emails)
                
                # Scrape homepage if available
                homepage_cols = [col for col in df.columns if 'homepage' in col.lower() or 'url' in col.lower()]
                if homepage_cols and pd.notna(row[homepage_cols[0]]):
                    homepage_emails = self.scrape_homepage_for_emails(row[homepage_cols[0]])
                    emails_found.extend(homepage_emails)
                
                # Extract emails from all text columns
                for col in df.columns:
                    if pd.notna(row[col]) and isinstance(row[col], str):
                        text_emails = self.extract_emails_from_text(row[col])
                        emails_found.extend(text_emails)
                
                # Add to results
                for email in set(emails_found):
                    if '@' in email and '.' in email.split('@')[1]:
                        extracted_emails.append({
                            'email': email.lower(),
                            'name': name if name else 'Unknown',
                            'affiliation': affiliation if affiliation else 'Unknown',
                            'source_file': os.path.basename(file_path),
                            'extraction_method': 'enhanced_low_yield'
                        })
                
                # Progress update
                if (index + 1) % 100 == 0:
                    logging.info(f"Processed {index + 1}/{len(df)} rows from {file_path}")
            
            logging.info(f"Extracted {len(extracted_emails)} emails from {file_path}")
            return extracted_emails
            
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            return []

    def process_all_low_yield_files(self):
        """Process all low-yield files"""
        logging.info("Starting enhanced low-yield scraping")
        
        # Identify low-yield files
        low_yield_files = [
            'data/country-info.csv',
            'data/list.csv'
        ]
        
        all_extracted_emails = []
        
        for file_path in low_yield_files:
            if os.path.exists(file_path):
                emails = self.process_low_yield_file(file_path)
                all_extracted_emails.extend(emails)
                
                # Save intermediate results
                if emails:
                    intermediate_file = f"enhanced_low_yield_{os.path.basename(file_path).replace('.csv', '')}.csv"
                    pd.DataFrame(emails).to_csv(intermediate_file, index=False)
                    logging.info(f"Saved intermediate results to {intermediate_file}")
        
        # Remove duplicates
        unique_emails = []
        seen_emails = set()
        
        for email_data in all_extracted_emails:
            if email_data['email'] not in seen_emails:
                unique_emails.append(email_data)
                seen_emails.add(email_data['email'])
        
        # Save final results
        if unique_emails:
            final_df = pd.DataFrame(unique_emails)
            final_file = "enhanced_low_yield_results.csv"
            final_df.to_csv(final_file, index=False)
            
            logging.info(f"Enhanced low-yield scraping completed!")
            logging.info(f"Total unique emails extracted: {len(unique_emails)}")
            logging.info(f"Results saved to: {final_file}")
            
            # Create summary
            summary = {
                'total_emails_extracted': len(unique_emails),
                'files_processed': len(low_yield_files),
                'extraction_methods': ['email_generation', 'homepage_scraping', 'text_extraction'],
                'generated_at': datetime.now().isoformat()
            }
            
            with open('enhanced_low_yield_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)
            
            return unique_emails
        else:
            logging.warning("No emails extracted from low-yield files")
            return []

def main():
    """Main function"""
    print("🔍 ENHANCED LOW-YIELD SCRAPER")
    print("=" * 50)
    
    scraper = EnhancedLowYieldScraper()
    results = scraper.process_all_low_yield_files()
    
    if results:
        print(f"\n✅ Enhanced low-yield scraping completed!")
        print(f"📧 Total emails extracted: {len(results):,}")
        print(f"📁 Results saved to: enhanced_low_yield_results.csv")
        
        # Show sample results
        print(f"\n📧 SAMPLE EXTRACTED EMAILS:")
        print("-" * 40)
        for i, email_data in enumerate(results[:10]):
            print(f"{i+1}. {email_data['email']} - {email_data['name']} - {email_data['affiliation']}")
    else:
        print(f"\n❌ No emails extracted from low-yield files")

if __name__ == "__main__":
    main() 