#!/usr/bin/env python3
"""
Mass Professor Scraper
Scrapes professors from all CSV files in data directory
"""

import pandas as pd
import os
import time
from datetime import datetime
import json

class MassProfessorScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.data_dir = "data"
        self.output_file = "mass_professors_scraped.csv"
        self.cache_file = "mass_scraping_cache.json"
        self.max_workers = 800  # As per your previous setup
        
        # Load cache if exists
        self.cache = self.load_cache()
        
        print(f"✅ Mass Professor Scraper initialized")
        print(f"✅ Data directory: {self.data_dir}")
        print(f"✅ Max workers: {self.max_workers}")

    def load_cache(self):
        """Load scraping cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_cache(self):
        """Save scraping cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def get_all_csv_files(self):
        """Get all CSV files in data directory"""
        csv_files = []
        
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(self.data_dir, file))
        
        print(f"Found {len(csv_files)} CSV files")
        return csv_files

    def process_csv_file(self, file_path):
        """Process a single CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            # Check if it's a professor CSV (has typical professor columns)
            professor_columns = ['name', 'affiliation', 'university', 'email', 'homepage']
            has_professor_data = any(col in df.columns for col in professor_columns)
            
            if has_professor_data:
                print(f"Processing {file_path}: {len(df)} rows")
                
                # Extract professor data
                professors = []
                for _, row in df.iterrows():
                    professor = {
                        'name': row.get('name', row.get('Name', '')),
                        'affiliation': row.get('affiliation', row.get('Affiliation', row.get('university', ''))),
                        'email': row.get('email', row.get('Email', '')),
                        'homepage': row.get('homepage', row.get('Homepage', '')),
                        'source_file': file_path,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    professors.append(professor)
                
                return professors
            else:
                print(f"Skipping {file_path}: No professor data found")
                return []
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []

    def scrape_all_professors(self):
        """Scrape professors from all CSV files"""
        print("Starting Mass Professor Scraping...")
        print("="*60)
        
        csv_files = self.get_all_csv_files()
        all_professors = []
        
        for i, file_path in enumerate(csv_files):
            print(f"\nProcessing file {i+1}/{len(csv_files)}: {os.path.basename(file_path)}")
            
            # Check cache
            if file_path in self.cache:
                print(f"Using cached data for {file_path}")
                all_professors.extend(self.cache[file_path])
            else:
                # Process file
                professors = self.process_csv_file(file_path)
                all_professors.extend(professors)
                
                # Cache results
                self.cache[file_path] = professors
                self.save_cache()
            
            # Progress update
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{len(csv_files)} files processed")
        
        # Remove duplicates
        unique_professors = self.remove_duplicates(all_professors)
        
        # Save results
        self.save_results(unique_professors)
        
        print(f"\n✅ Scraping Complete!")
        print(f"Total professors found: {len(unique_professors)}")
        print(f"Unique professors: {len(unique_professors)}")
        
        return unique_professors

    def remove_duplicates(self, professors):
        """Remove duplicate professors based on email and name"""
        seen_emails = set()
        seen_names = set()
        unique_professors = []
        
        for professor in professors:
            # Safely handle email (could be NaN/float)
            email_raw = professor.get('email', '')
            email = str(email_raw).lower().strip() if pd.notna(email_raw) else ''
            
            # Safely handle name (could be NaN/float)
            name_raw = professor.get('name', '')
            name = str(name_raw).lower().strip() if pd.notna(name_raw) else ''
            
            # Check if we've seen this email or name before
            if email and email not in seen_emails:
                unique_professors.append(professor)
                seen_emails.add(email)
            elif name and name not in seen_names:
                unique_professors.append(professor)
                seen_names.add(name)
        
        return unique_professors

    def save_results(self, professors):
        """Save scraped professors to CSV"""
        if professors:
            df = pd.DataFrame(professors)
            df.to_csv(self.output_file, index=False)
            print(f"✅ Results saved to {self.output_file}")
            
            # Also save to data directory with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            timestamped_file = f"data/mass_professors_{timestamp}.csv"
            df.to_csv(timestamped_file, index=False)
            print(f"✅ Timestamped results saved to {timestamped_file}")

    def analyze_results(self):
        """Analyze scraping results"""
        if os.path.exists(self.output_file):
            df = pd.read_csv(self.output_file)
            
            print("\n📊 SCRAPING RESULTS ANALYSIS")
            print("="*60)
            print(f"Total professors: {len(df)}")
            
            # Email analysis
            valid_emails = df[df['email'].str.contains('@', na=False)]
            print(f"Professors with valid emails: {len(valid_emails)}")
            
            # University analysis
            if 'affiliation' in df.columns:
                top_universities = df['affiliation'].value_counts().head(10)
                print(f"\nTop 10 Universities:")
                for uni, count in top_universities.items():
                    print(f"  {uni}: {count} professors")
            
            # Source file analysis
            if 'source_file' in df.columns:
                source_counts = df['source_file'].value_counts()
                print(f"\nTop 10 Source Files:")
                for file, count in source_counts.head(10).items():
                    print(f"  {os.path.basename(file)}: {count} professors")
            
            return df
        else:
            print("No results file found")
            return None

    def generate_scraping_report(self):
        """Generate comprehensive scraping report"""
        print("\n📋 MASS SCRAPING REPORT")
        print("="*60)
        
        # Check cache
        cache_size = len(self.cache)
        print(f"Files in cache: {cache_size}")
        
        # Check results
        if os.path.exists(self.output_file):
            df = pd.read_csv(self.output_file)
            print(f"Total professors scraped: {len(df)}")
            print(f"Professors with emails: {len(df[df['email'].str.contains('@', na=False)])}")
        
        # Check CSV files
        csv_files = self.get_all_csv_files()
        print(f"Total CSV files available: {len(csv_files)}")
        
        # Estimate total professors
        total_estimated = len(csv_files) * 1000  # Rough estimate
        print(f"Estimated total professors in all files: {total_estimated:,}")

def main():
    """Main function to run mass professor scraping"""
    print("Mass Professor Scraper")
    print("="*60)
    
    # Initialize scraper
    scraper = MassProfessorScraper()
    
    # Run scraping
    print("\n🚀 STARTING MASS SCRAPING")
    print("="*60)
    
    professors = scraper.scrape_all_professors()
    
    # Analyze results
    scraper.analyze_results()
    
    # Generate report
    scraper.generate_scraping_report()
    
    print("\n🎯 COMMANDS FOR SCRAPING:")
    print("="*60)
    print("1. Run mass scraping:")
    print("   python mass_professor_scraper.py")
    print()
    print("2. Analyze results:")
    print("   scraper.analyze_results()")
    print()
    print("3. Generate report:")
    print("   scraper.generate_scraping_report()")

if __name__ == "__main__":
    main() 