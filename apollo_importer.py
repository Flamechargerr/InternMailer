#!/usr/bin/env python3
"""
APOLLO.IO RECRUITER IMPORTER
Import HR/Recruiter contacts from Apollo.io CSV exports
"""

import csv
import sqlite3
import os
from datetime import datetime

class ApolloImporter:
    """Import recruiter contacts from Apollo.io CSV exports"""
    
    def __init__(self, db_path='data/recruiters.db'):
        self.db_path = db_path
        self.setup_database()
    
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
                source TEXT DEFAULT 'apollo',
                imported_at TEXT,
                contacted TEXT DEFAULT 'no'
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Database ready: {self.db_path}")
    
    def import_csv(self, csv_path, dry_run=False):
        """Import contacts from Apollo.io CSV export"""
        if not os.path.exists(csv_path):
            print(f"❌ File not found: {csv_path}")
            return 0
        
        print(f"📄 Reading: {csv_path}")
        
        imported = 0
        skipped = 0
        errors = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Apollo.io common column names
                contacts = []
                for row in reader:
                    # Try different column name patterns
                    first_name = row.get('First Name') or row.get('first_name') or row.get('firstName') or ''
                    last_name = row.get('Last Name') or row.get('last_name') or row.get('lastName') or ''
                    email = row.get('Email') or row.get('email') or row.get('Work Email') or ''
                    title = row.get('Title') or row.get('title') or row.get('Job Title') or ''
                    company = row.get('Company') or row.get('company') or row.get('Organization') or ''
                    industry = row.get('Industry') or row.get('industry') or ''
                    linkedin = row.get('LinkedIn URL') or row.get('linkedin_url') or row.get('Person Linkedin Url') or ''
                    location = row.get('Location') or row.get('City') or row.get('Country') or ''
                    
                    # Validate email
                    if not email or '@' not in email:
                        skipped += 1
                        continue
                    
                    full_name = f"{first_name} {last_name}".strip()
                    if not full_name:
                        full_name = email.split('@')[0].replace('.', ' ').title()
                    
                    contacts.append({
                        'first_name': first_name,
                        'last_name': last_name,
                        'full_name': full_name,
                        'email': email.lower().strip(),
                        'title': title,
                        'company': company,
                        'industry': industry,
                        'linkedin_url': linkedin,
                        'location': location
                    })
                
                print(f"📊 Found {len(contacts)} valid contacts, {skipped} skipped")
                
                if dry_run:
                    print("🔍 DRY RUN - Not importing")
                    for c in contacts[:5]:
                        print(f"   {c['full_name']} - {c['email']} - {c['company']}")
                    return len(contacts)
                
                # Insert into database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for contact in contacts:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO recruiters 
                            (first_name, last_name, full_name, email, title, company, industry, linkedin_url, location, imported_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            contact['first_name'],
                            contact['last_name'],
                            contact['full_name'],
                            contact['email'],
                            contact['title'],
                            contact['company'],
                            contact['industry'],
                            contact['linkedin_url'],
                            contact['location'],
                            datetime.now().isoformat()
                        ))
                        if cursor.rowcount > 0:
                            imported += 1
                    except Exception as e:
                        errors.append(str(e))
                
                conn.commit()
                conn.close()
                
                print(f"✅ Imported: {imported} new contacts")
                if errors:
                    print(f"⚠️ Errors: {len(errors)}")
                
                return imported
                
        except Exception as e:
            print(f"❌ Import error: {e}")
            return 0
    
    def get_fresh_recruiters(self, limit=50):
        """Get recruiters who haven't been contacted yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT full_name, email, company, title, linkedin_url
            FROM recruiters
            WHERE contacted = 'no'
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def mark_contacted(self, email):
        """Mark a recruiter as contacted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE recruiters SET contacted = 'yes' WHERE email = ?", (email,))
        conn.commit()
        conn.close()
    
    def show_stats(self):
        """Show importer statistics"""
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
        
        cursor.execute("SELECT company, COUNT(*) as cnt FROM recruiters GROUP BY company ORDER BY cnt DESC LIMIT 5")
        top_companies = cursor.fetchall()
        
        conn.close()
        
        print("\n📊 RECRUITER DATABASE STATS")
        print("=" * 40)
        print(f"   Total recruiters: {total}")
        print(f"   Fresh (not contacted): {fresh}")
        print(f"   Already contacted: {contacted}")
        print("\n   Top Companies:")
        for company, count in top_companies:
            print(f"      {company}: {count}")


def main():
    """Main function for testing"""
    import sys
    
    importer = ApolloImporter()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python apollo_importer.py <csv_file>          - Import from CSV")
        print("  python apollo_importer.py --stats             - Show stats")
        print("  python apollo_importer.py --preview <file>    - Preview import (dry run)")
        return
    
    if sys.argv[1] == '--stats':
        importer.show_stats()
    elif sys.argv[1] == '--preview' and len(sys.argv) > 2:
        importer.import_csv(sys.argv[2], dry_run=True)
    else:
        importer.import_csv(sys.argv[1])
        importer.show_stats()


if __name__ == "__main__":
    main()
