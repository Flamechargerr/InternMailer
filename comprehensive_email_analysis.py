#!/usr/bin/env python3
"""
Comprehensive Email Analysis
Analyzes all email files and identifies opportunities for improvement
"""

import os
import pandas as pd
import json
from datetime import datetime

def analyze_all_email_files():
    """Analyze all email files in the directory"""
    print("🔍 COMPREHENSIVE EMAIL ANALYSIS")
    print("=" * 60)
    
    # List of all email-related files
    email_files = [
        'enhanced_background_emails.csv',
        'background_scraped_emails.csv',
        'targeted_professors_scraped.csv',
        'professors_unified_scraped.csv',
        'mass_professors_scraped.csv',
        'hr_contacts_cleaned.csv'
    ]
    
    # List of all CSV files in data directory
    data_files = [f for f in os.listdir('data') if f.endswith('.csv')]
    
    print(f"📁 Total CSV files in data directory: {len(data_files)}")
    print(f"📧 Email files to analyze: {len(email_files)}")
    
    # Analyze each email file
    total_emails = 0
    email_breakdown = {}
    
    for file_name in email_files:
        if os.path.exists(file_name):
            try:
                df = pd.read_csv(file_name)
                email_count = len(df)
                total_emails += email_count
                email_breakdown[file_name] = email_count
                print(f"✅ {file_name}: {email_count:,} emails")
            except Exception as e:
                print(f"❌ {file_name}: Error reading file - {e}")
        else:
            print(f"❌ {file_name}: File not found")
    
    # Check data directory for additional email files
    print(f"\n📊 ANALYZING DATA DIRECTORY FILES:")
    print("-" * 40)
    
    data_email_files = []
    for file_name in data_files:
        if 'email' in file_name.lower() or 'professor' in file_name.lower() or 'contact' in file_name.lower():
            file_path = os.path.join('data', file_name)
            try:
                df = pd.read_csv(file_path)
                email_count = len(df)
                data_email_files.append((file_name, email_count))
                print(f"📧 data/{file_name}: {email_count:,} rows")
            except Exception as e:
                print(f"❌ data/{file_name}: Error - {e}")
    
    # Check csrankings files for potential
    print(f"\n🎯 ANALYZING CSRANKINGS FILES FOR POTENTIAL:")
    print("-" * 40)
    
    csrankings_files = [f for f in data_files if f.startswith('csrankings-')]
    total_csrankings_rows = 0
    
    for file_name in csrankings_files:
        file_path = os.path.join('data', file_name)
        try:
            df = pd.read_csv(file_path)
            row_count = len(df)
            total_csrankings_rows += row_count
            
            # Check if file has been processed by enhanced scraper
            cache_file = "enhanced_scraping_cache.json"
            processed = False
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                    if file_path in cache:
                        processed = True
            
            status = "✅ Processed" if processed else "❌ Not Processed"
            print(f"{file_name}: {row_count:,} rows - {status}")
            
        except Exception as e:
            print(f"❌ {file_name}: Error - {e}")
    
    # Check other professor files
    print(f"\n👨‍🏫 ANALYZING PROFESSOR FILES:")
    print("-" * 40)
    
    professor_files = [f for f in data_files if 'professor' in f.lower() or 'proffesor' in f.lower()]
    total_professor_rows = 0
    
    for file_name in professor_files:
        file_path = os.path.join('data', file_name)
        try:
            df = pd.read_csv(file_path)
            row_count = len(df)
            total_professor_rows += row_count
            print(f"{file_name}: {row_count:,} rows")
        except Exception as e:
            print(f"❌ {file_name}: Error - {e}")
    
    # Calculate potential improvements
    print(f"\n📈 POTENTIAL IMPROVEMENT ANALYSIS:")
    print("-" * 40)
    
    # Unprocessed csrankings files
    unprocessed_csrankings = []
    cache_file = "enhanced_scraping_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            for file_name in csrankings_files:
                file_path = os.path.join('data', file_name)
                if file_path not in cache:
                    unprocessed_csrankings.append(file_name)
    
    print(f"📧 Current total emails: {total_emails:,}")
    print(f"📊 Total csrankings rows: {total_csrankings_rows:,}")
    print(f"👨‍🏫 Total professor rows: {total_professor_rows:,}")
    print(f"❌ Unprocessed csrankings files: {len(unprocessed_csrankings)}")
    
    if unprocessed_csrankings:
        print("Unprocessed files:")
        for file_name in unprocessed_csrankings:
            print(f"  - {file_name}")
    
    # Estimate potential additional emails
    estimated_potential = len(unprocessed_csrankings) * 2000  # Average 2000 emails per csrankings file
    print(f"🎯 Estimated potential additional emails: {estimated_potential:,}")
    
    return {
        'total_emails': total_emails,
        'total_csrankings_rows': total_csrankings_rows,
        'total_professor_rows': total_professor_rows,
        'unprocessed_csrankings': len(unprocessed_csrankings),
        'estimated_potential': estimated_potential,
        'email_breakdown': email_breakdown
    }

def create_improvement_plan():
    """Create a plan for improving email extraction"""
    print(f"\n🚀 EMAIL EXTRACTION IMPROVEMENT PLAN")
    print("=" * 60)
    
    # Check current enhanced scraper status
    cache_file = "enhanced_scraping_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            processed_files = len(cache)
            print(f"📊 Files processed by enhanced scraper: {processed_files}")
    
    # Check for unprocessed files
    data_files = [f for f in os.listdir('data') if f.endswith('.csv')]
    csrankings_files = [f for f in data_files if f.startswith('csrankings-')]
    
    unprocessed = []
    for file_name in csrankings_files:
        file_path = os.path.join('data', file_name)
        if file_path not in cache:
            unprocessed.append(file_name)
    
    print(f"❌ Unprocessed csrankings files: {len(unprocessed)}")
    
    if unprocessed:
        print("\n📋 RECOMMENDED ACTIONS:")
        print("1. Continue enhanced scraper to process remaining files")
        print("2. Focus on csrankings files (t-z) that haven't been processed")
        print("3. Improve email generation patterns for better accuracy")
        print("4. Add more university domain mappings")
        print("5. Implement email validation to filter out invalid emails")
        
        print(f"\n🎯 IMMEDIATE NEXT STEPS:")
        print(f"1. Run enhanced scraper on remaining {len(unprocessed)} files")
        print(f"2. Expected additional emails: {len(unprocessed) * 2000:,}")
        print(f"3. Total potential emails: {len(unprocessed) * 2000 + 28679:,}")
    
    return unprocessed

if __name__ == "__main__":
    results = analyze_all_email_files()
    unprocessed_files = create_improvement_plan()
    
    # Save analysis results
    analysis_summary = {
        'analysis_date': datetime.now().isoformat(),
        'results': results,
        'unprocessed_files': unprocessed_files,
        'recommendations': [
            "Continue enhanced scraper on remaining csrankings files",
            "Improve email validation and filtering",
            "Add more university domain mappings",
            "Implement email quality scoring"
        ]
    }
    
    with open('comprehensive_email_analysis.json', 'w') as f:
        json.dump(analysis_summary, f, indent=2)
    
    print(f"\n✅ Analysis saved to: comprehensive_email_analysis.json") 