#!/usr/bin/env python3
"""
🧹 DATABASE CLEANER & OPTIMIZER
===============================
Comprehensive cleaning for enhanced_background_emails.csv
- Fix corrupted email addresses with attached text
- Extract proper names from malformed data
- Validate affiliations and create missing ones
- Remove duplicates and invalid entries
- Create optimized, production-ready database
"""

import pandas as pd
import re
import logging
from datetime import datetime
from pathlib import Path
import unicodedata

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseCleaner:
    def __init__(self):
        """Initialize the database cleaner"""
        self.email_pattern = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
        self.domain_to_university = {
            'mit.edu': 'Massachusetts Institute of Technology',
            'stanford.edu': 'Stanford University',
            'berkeley.edu': 'University of California Berkeley',
            'harvard.edu': 'Harvard University',
            'cmu.edu': 'Carnegie Mellon University',
            'caltech.edu': 'California Institute of Technology',
            'gatech.edu': 'Georgia Institute of Technology',
            'cornell.edu': 'Cornell University',
            'washington.edu': 'University of Washington',
            'princeton.edu': 'Princeton University',
        }
        
    def extract_clean_email(self, email_text):
        """Extract clean email from corrupted text"""
        if pd.isna(email_text):
            return None
            
        email_text = str(email_text)
        match = self.email_pattern.search(email_text)
        
        if match:
            email = match.group(1).lower()
            # Additional validation
            if '@' in email and '.' in email and len(email) > 5:
                # Remove common corruptions
                email = re.sub(r'[^\w\.\-@]', '', email)
                return email
        
        return None
    
    def extract_name_from_email(self, email):
        """Extract a reasonable name from email address"""
        if not email or '@' not in email:
            return "Professor"
            
        username = email.split('@')[0]
        
        # Handle common patterns
        username = re.sub(r'[_\-\.]', ' ', username)
        username = re.sub(r'\d+', '', username)  # Remove numbers
        
        # Split into parts and capitalize
        parts = username.split()
        if len(parts) >= 2:
            name = ' '.join(part.capitalize() for part in parts if len(part) > 1)
            return name if len(name) > 3 else "Professor"
        elif len(parts) == 1 and len(parts[0]) > 2:
            return parts[0].capitalize()
        
        return "Professor"
    
    def extract_affiliation_from_email(self, email):
        """Extract university affiliation from email domain"""
        if not email or '@' not in email:
            return "University"
            
        domain = email.split('@')[1].lower()
        
        # Check if it's a known university
        if domain in self.domain_to_university:
            return self.domain_to_university[domain]
        
        # Extract university name from domain
        if '.edu' in domain:
            # Remove common prefixes
            domain = domain.replace('www.', '').replace('mail.', '')
            domain = domain.replace('.edu', '')
            
            # Handle common patterns
            if domain in ['uci', 'ucsd', 'ucla', 'ucb']:
                return f'University of California {domain.upper()}'
            
            # Capitalize and format
            university_name = domain.replace('.', ' ').replace('-', ' ')
            university_name = ' '.join(word.capitalize() for word in university_name.split())
            
            if 'university' not in university_name.lower():
                university_name += ' University'
                
            return university_name
        
        # Handle other domains
        domain_clean = domain.split('.')[0]
        return f"{domain_clean.capitalize()} Institution"
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if pd.isna(text):
            return ""
        
        text = str(text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def is_valid_email(self, email):
        """Validate email format"""
        if not email:
            return False
            
        pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        return bool(pattern.match(email))
    
    def clean_database(self, input_file='enhanced_background_emails.csv', output_file=None):
        """Clean the database comprehensively"""
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'cleaned_professor_database_{timestamp}.csv'
        
        logger.info(f"🧹 Starting database cleaning: {input_file}")
        
        try:
            # Load the database
            logger.info("📥 Loading database...")
            df = pd.read_csv(input_file, dtype=str)
            initial_count = len(df)
            logger.info(f"✅ Loaded {initial_count:,} records")
            
            # Step 1: Clean emails
            logger.info("🔧 Step 1: Cleaning email addresses...")
            df['email_clean'] = df['email'].apply(self.extract_clean_email)
            
            # Remove rows with invalid emails
            df = df[df['email_clean'].notna()]
            df = df[df['email_clean'].apply(self.is_valid_email)]
            logger.info(f"✅ Cleaned emails: {len(df):,} records remaining")
            
            # Step 2: Extract/fix names
            logger.info("🔧 Step 2: Fixing professor names...")
            def fix_name(row):
                # Try existing name first
                if pd.notna(row['name']) and len(str(row['name']).strip()) > 2:
                    name = self.clean_text(row['name'])
                    # Remove email artifacts
                    name = re.sub(r'[^a-zA-Z\s\.\-\']', ' ', name)
                    name = ' '.join(name.split())
                    if len(name) > 2:
                        return name
                
                # Extract from email
                return self.extract_name_from_email(row['email_clean'])
            
            df['name_clean'] = df.apply(fix_name, axis=1)
            logger.info("✅ Names fixed")
            
            # Step 3: Extract/fix affiliations  
            logger.info("🔧 Step 3: Fixing affiliations...")
            def fix_affiliation(row):
                # Try existing affiliation first
                if pd.notna(row.get('affiliation')) and len(str(row['affiliation']).strip()) > 3:
                    affiliation = self.clean_text(row['affiliation'])
                    if len(affiliation) > 3:
                        return affiliation
                
                # Extract from email
                return self.extract_affiliation_from_email(row['email_clean'])
            
            df['affiliation_clean'] = df.apply(fix_affiliation, axis=1)
            logger.info("✅ Affiliations fixed")
            
            # Step 4: Remove duplicates
            logger.info("🔧 Step 4: Removing duplicates...")
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['email_clean'])
            df = df.reset_index(drop=True)
            logger.info(f"✅ Removed {before_dedup - len(df):,} duplicates")
            
            # Step 5: Final validation and formatting
            logger.info("🔧 Step 5: Final validation...")
            
            # Create final clean dataset
            df_clean = pd.DataFrame({
                'email': df['email_clean'],
                'name': df['name_clean'],
                'affiliation': df['affiliation_clean'],
                'source_file': 'enhanced_background_emails.csv',
                'cleaned_at': datetime.now().isoformat(),
                'cleaning_method': 'comprehensive_cleaner_v1'
            })
            
            # Final validation
            df_clean = df_clean[df_clean['email'].apply(self.is_valid_email)]
            df_clean = df_clean[df_clean['name'].str.len() > 2]
            df_clean = df_clean[df_clean['affiliation'].str.len() > 3]
            
            final_count = len(df_clean)
            logger.info(f"✅ Final dataset: {final_count:,} clean records")
            
            # Save cleaned database
            df_clean.to_csv(output_file, index=False)
            logger.info(f"💾 Saved cleaned database to: {output_file}")
            
            # Generate report
            self.generate_cleaning_report(initial_count, final_count, output_file)
            
            return output_file, df_clean
            
        except Exception as e:
            logger.error(f"❌ Error cleaning database: {e}")
            return None, None
    
    def generate_cleaning_report(self, initial_count, final_count, output_file):
        """Generate a comprehensive cleaning report"""
        
        report = f"""
🧹 DATABASE CLEANING REPORT
===========================
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📊 STATISTICS:
• Initial records: {initial_count:,}
• Final records: {final_count:,}
• Records removed: {initial_count - final_count:,}
• Success rate: {(final_count / initial_count * 100):.1f}%

🔧 CLEANING OPERATIONS PERFORMED:
✅ Email extraction from corrupted text
✅ Email format validation
✅ Name extraction and cleaning
✅ Affiliation inference from domains
✅ Duplicate removal
✅ Final validation

📁 OUTPUT FILES:
• Cleaned database: {output_file}
• This report: database_cleaning_report.txt

💡 IMPROVEMENTS:
• All email addresses now properly formatted
• Names extracted from corrupted data
• University affiliations properly identified
• No duplicates or invalid entries
• Ready for email campaigns
"""
        
        with open('database_cleaning_report.txt', 'w') as f:
            f.write(report)
        
        logger.info("📋 Cleaning report generated: database_cleaning_report.txt")
        print(report)

def main():
    """Main function to run database cleaning"""
    
    cleaner = DatabaseCleaner()
    
    print("🧹 DATABASE CLEANER & OPTIMIZER")
    print("=" * 50)
    print("This tool will comprehensively clean the corrupted email database")
    print("and create an optimized, campaign-ready dataset.")
    print()
    
    # Check if file exists
    input_file = 'enhanced_background_emails.csv'
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Start cleaning
    proceed = input("🚀 Start database cleaning? (y/n): ").strip().lower()
    if proceed in ['y', 'yes', '']:
        output_file, df_clean = cleaner.clean_database(input_file)
        
        if output_file and df_clean is not None:
            print(f"\n🎉 Database cleaning completed successfully!")
            print(f"📁 Clean database saved as: {output_file}")
            print(f"📊 Final dataset contains {len(df_clean):,} clean professor records")
            print("\n💡 You can now use this cleaned database in your campaign system")
            print("   by updating the database path in your campaign configuration.")
        else:
            print("\n❌ Database cleaning failed. Check the logs for details.")

if __name__ == "__main__":
    main()
