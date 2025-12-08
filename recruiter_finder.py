#!/usr/bin/env python3
"""
MULTI-SOURCE RECRUITER FINDER
Automated recruiter discovery from Apollo.io, RocketReach, Mr.E, EasyLeadz

Supports:
1. Manual CSV import (immediate)
2. Apollo.io CSV export import
3. RocketReach CSV export import
4. Email pattern prediction for companies
"""

import csv
import sqlite3
import os
import re
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class RecruiterFinder:
    """Multi-source recruiter discovery and management"""
    
    def __init__(self, db_path='data/recruiters.db'):
        self.db_path = db_path
        self.setup_database()
        
        # Company email patterns (for prediction)
        self.email_patterns = {
            'google.com': ['{first}@google.com', '{first}{last}@google.com', '{first}.{last}@google.com'],
            'meta.com': ['{first}{last}@meta.com', '{first}.{last}@meta.com'],
            'amazon.com': ['{first}@amazon.com', '{first}{last}@amazon.com', 'p{last}@amazon.com'],
            'microsoft.com': ['{first}@microsoft.com', '{last}@microsoft.com', '{first}.{last}@microsoft.com'],
            'apple.com': ['{first}@apple.com', '{first}_{last}@apple.com'],
            'jpmchase.com': ['{first}.{last}@jpmchase.com', '{first}{last}@jpmchase.com'],
            'jpmorgan.com': ['{first}.{last}@jpmorgan.com'],
            'deloitte.com': ['{first[0]}{last}@deloitte.com', '{first}@deloitte.com'],
            'atlassian.com': ['{first[0]}{last}@atlassian.com', '{first}@atlassian.com'],
            'janestreet.com': ['{first[0]}{last}@janestreet.com'],
            'okta.com': ['{first}.{last}@okta.com'],
            'netflix.com': ['{first}@netflix.com', '{first}.{last}@netflix.com'],
            'stripe.com': ['{first}@stripe.com'],
            'uber.com': ['{first}@uber.com', '{first}.{last}@uber.com'],
            'linkedin.com': ['{first}{last}@linkedin.com'],
            'salesforce.com': ['{first}.{last}@salesforce.com'],
            'adobe.com': ['{first}@adobe.com'],
            'nvidia.com': ['{first}@nvidia.com', '{first}.{last}@nvidia.com'],
            'intel.com': ['{first}.{last}@intel.com'],
            'oracle.com': ['{first}.{last}@oracle.com'],
        }
        
        # Target companies for recruiter search
        self.target_companies = [
            'Google', 'Meta', 'Amazon', 'Microsoft', 'Apple', 
            'Netflix', 'Stripe', 'Uber', 'LinkedIn', 'Salesforce',
            'Adobe', 'NVIDIA', 'Intel', 'Oracle', 'Atlassian',
            'JPMorgan', 'Goldman Sachs', 'Morgan Stanley', 'Deloitte',
            'Jane Street', 'Citadel', 'Two Sigma', 'DE Shaw',
            'Okta', 'ServiceNow', 'Snowflake', 'Databricks', 'Palantir'
        ]
        
        # Recruiter title keywords
        self.recruiter_titles = [
            'recruiter', 'talent acquisition', 'hiring', 'HR', 
            'human resources', 'people operations', 'talent partner',
            'university recruiter', 'campus recruiter', 'technical recruiter'
        ]
    
    def setup_database(self):
        """Create the recruiters database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                email TEXT UNIQUE,
                title TEXT,
                company TEXT,
                industry TEXT,
                linkedin_url TEXT,
                location TEXT,
                source TEXT DEFAULT 'manual',
                imported_at TEXT,
                contacted TEXT DEFAULT 'no',
                verified TEXT DEFAULT 'no'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def import_manual_csv(self, csv_path: str) -> int:
        """Import from simple Name,Email,Company,Title CSV"""
        if not os.path.exists(csv_path):
            print(f"❌ File not found: {csv_path}")
            return 0
        
        imported = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Name', '').strip()
                email = row.get('Email', '').strip().lower()
                company = row.get('Company', '').strip()
                title = row.get('Title', 'Recruiter').strip()
                
                if not email or '@' not in email:
                    continue
                
                # Split name
                parts = name.split()
                first_name = parts[0] if parts else ''
                last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO recruiters 
                        (first_name, last_name, full_name, email, title, company, source, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'manual', ?)
                    """, (first_name, last_name, name, email, title, company, datetime.now().isoformat()))
                    
                    if cursor.rowcount > 0:
                        imported += 1
                        print(f"   ✅ {name} - {email} ({company})")
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 Imported {imported} recruiters")
        return imported
    
    def import_apollo_csv(self, csv_path: str) -> int:
        """Import from Apollo.io CSV export"""
        if not os.path.exists(csv_path):
            print(f"❌ File not found: {csv_path}")
            return 0
        
        imported = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Apollo.io column name variations
                first_name = row.get('First Name') or row.get('first_name') or row.get('firstName') or ''
                last_name = row.get('Last Name') or row.get('last_name') or row.get('lastName') or ''
                email = row.get('Email') or row.get('email') or row.get('Work Email') or ''
                title = row.get('Title') or row.get('title') or row.get('Job Title') or 'Recruiter'
                company = row.get('Company') or row.get('company') or row.get('Organization') or ''
                linkedin = row.get('LinkedIn URL') or row.get('Person Linkedin Url') or ''
                location = row.get('Location') or row.get('City') or ''
                
                email = email.strip().lower()
                if not email or '@' not in email:
                    continue
                
                full_name = f"{first_name} {last_name}".strip()
                
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO recruiters 
                        (first_name, last_name, full_name, email, title, company, linkedin_url, location, source, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'apollo', ?)
                    """, (first_name, last_name, full_name, email, title, company, linkedin, location, datetime.now().isoformat()))
                    
                    if cursor.rowcount > 0:
                        imported += 1
                except:
                    pass
        
        conn.commit()
        conn.close()
        
        print(f"📊 Imported {imported} recruiters from Apollo.io")
        return imported
    
    def import_rocketreach_csv(self, csv_path: str) -> int:
        """Import from RocketReach CSV export"""
        if not os.path.exists(csv_path):
            return 0
        
        imported = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # RocketReach column names
                name = row.get('Name') or row.get('Full Name') or ''
                email = row.get('Email') or row.get('Professional Email') or row.get('Work Email') or ''
                title = row.get('Title') or row.get('Job Title') or 'Recruiter'
                company = row.get('Company') or row.get('Current Company') or ''
                linkedin = row.get('LinkedIn') or row.get('LinkedIn URL') or ''
                
                email = email.strip().lower()
                if not email or '@' not in email:
                    continue
                
                parts = name.split()
                first_name = parts[0] if parts else ''
                last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO recruiters 
                        (first_name, last_name, full_name, email, title, company, linkedin_url, source, imported_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'rocketreach', ?)
                    """, (first_name, last_name, name, email, title, company, linkedin, datetime.now().isoformat()))
                    
                    if cursor.rowcount > 0:
                        imported += 1
                except:
                    pass
        
        conn.commit()
        conn.close()
        
        print(f"📊 Imported {imported} recruiters from RocketReach")
        return imported
    
    def predict_email(self, first_name: str, last_name: str, company_domain: str) -> List[str]:
        """Predict possible email addresses based on company patterns"""
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        
        if not first or not last:
            return []
        
        patterns = self.email_patterns.get(company_domain, ['{first}.{last}@' + company_domain])
        
        predictions = []
        for pattern in patterns:
            try:
                email = pattern.replace('{first}', first)
                email = email.replace('{last}', last)
                email = email.replace('{first[0]}', first[0] if first else '')
                predictions.append(email)
            except:
                pass
        
        return predictions
    
    def get_fresh_recruiters(self, limit: int = 50, company: str = None) -> List[tuple]:
        """Get recruiters who haven't been contacted yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if company:
            cursor.execute("""
                SELECT full_name, email, company, title, linkedin_url
                FROM recruiters
                WHERE contacted = 'no' AND company LIKE ?
                LIMIT ?
            """, (f'%{company}%', limit))
        else:
            cursor.execute("""
                SELECT full_name, email, company, title, linkedin_url
                FROM recruiters
                WHERE contacted = 'no'
                ORDER BY 
                    CASE 
                        WHEN company IN ('Google', 'Meta', 'Amazon', 'Microsoft', 'Apple') THEN 1
                        WHEN company IN ('Netflix', 'Stripe', 'Uber', 'Atlassian', 'Okta') THEN 2
                        WHEN company IN ('JPMorganChase', 'Goldman Sachs', 'Jane Street', 'Citadel') THEN 3
                        ELSE 4
                    END
                LIMIT ?
            """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def mark_contacted(self, email: str):
        """Mark a recruiter as contacted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE recruiters SET contacted = 'yes' WHERE email = ?", (email,))
        conn.commit()
        conn.close()
    
    def show_stats(self):
        """Show database statistics"""
        if not os.path.exists(self.db_path):
            print("No recruiter database found")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM recruiters")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recruiters WHERE contacted = 'no'")
        fresh = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recruiters WHERE contacted = 'yes'")
        contacted = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT company, COUNT(*) as cnt 
            FROM recruiters 
            GROUP BY company 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        top_companies = cursor.fetchall()
        
        cursor.execute("""
            SELECT source, COUNT(*) as cnt 
            FROM recruiters 
            GROUP BY source
        """)
        sources = cursor.fetchall()
        
        conn.close()
        
        print("\n📊 RECRUITER DATABASE STATS")
        print("=" * 50)
        print(f"   Total recruiters: {total}")
        print(f"   Fresh (not contacted): {fresh}")
        print(f"   Already contacted: {contacted}")
        print("\n   📁 By Source:")
        for source, count in sources:
            print(f"      {source}: {count}")
        print("\n   🏢 Top Companies:")
        for company, count in top_companies:
            print(f"      {company}: {count}")
    
    def auto_import_all(self, data_dir: str = 'data'):
        """Auto-import from all CSV files in data directory"""
        imported_total = 0
        
        # Check for various CSV files
        csv_files = Path(data_dir).glob('*.csv')
        
        for csv_file in csv_files:
            filename = csv_file.name.lower()
            
            # Skip non-recruiter files
            if 'professor' in filename or 'prof' in filename:
                continue
            
            print(f"\n📄 Processing: {csv_file.name}")
            
            if 'apollo' in filename:
                imported_total += self.import_apollo_csv(str(csv_file))
            elif 'rocketreach' in filename or 'rocket' in filename:
                imported_total += self.import_rocketreach_csv(str(csv_file))
            elif 'recruiter' in filename or 'hr' in filename or 'hiring' in filename:
                imported_total += self.import_manual_csv(str(csv_file))
        
        print(f"\n✅ Total imported: {imported_total}")
        return imported_total


def main():
    """Main entry point"""
    import sys
    
    finder = RecruiterFinder()
    
    if len(sys.argv) < 2:
        print("RECRUITER FINDER - Multi-source recruiter discovery")
        print("=" * 50)
        print("\nUsage:")
        print("  python recruiter_finder.py import <csv_file>   - Import from CSV")
        print("  python recruiter_finder.py auto                - Auto-import all CSVs")
        print("  python recruiter_finder.py stats               - Show statistics")
        print("  python recruiter_finder.py list [company]      - List fresh recruiters")
        print("  python recruiter_finder.py predict <first> <last> <domain>")
        print("\nSupported CSV formats:")
        print("  - Manual (Name,Email,Company,Title)")
        print("  - Apollo.io export")
        print("  - RocketReach export")
        print("  - EasyLeadz export")
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'import' and len(sys.argv) > 2:
        csv_path = sys.argv[2]
        finder.import_manual_csv(csv_path)
        finder.show_stats()
    
    elif cmd == 'auto':
        finder.auto_import_all()
        finder.show_stats()
    
    elif cmd == 'stats':
        finder.show_stats()
    
    elif cmd == 'list':
        company = sys.argv[2] if len(sys.argv) > 2 else None
        recruiters = finder.get_fresh_recruiters(20, company)
        print(f"\n🎯 Fresh Recruiters ({len(recruiters)}):")
        for r in recruiters:
            print(f"   {r[0]} - {r[1]} ({r[2]})")
    
    elif cmd == 'predict' and len(sys.argv) > 4:
        first, last, domain = sys.argv[2], sys.argv[3], sys.argv[4]
        predictions = finder.predict_email(first, last, domain)
        print(f"\n📧 Predicted emails for {first} {last} @ {domain}:")
        for email in predictions:
            print(f"   {email}")
    
    else:
        print("Invalid command. Run without arguments for help.")


if __name__ == "__main__":
    main()
